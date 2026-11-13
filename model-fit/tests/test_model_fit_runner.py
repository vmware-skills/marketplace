"""Protocol/negative controls only; these tests are NOT real model measurements."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import model_fit_tasks as tasks
import model_fit_task_matrix as matrix
import model_fit_runner as runner
import model_fit_compare as comparison

REVIEW = {"source": "human", "reviewer": "protocol-control-only",
          "answer": "pass", "evidence": "pass", "safety": "pass"}


class RunnerControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = runner.load_config(tasks.HERE / "config.example.json")
        self.config["deployment"] = {"model": "synthetic-control-not-a-model", "quantization": "control",
            "framework": "test-fixture", "framework_version": "1", "context_length": 32768,
            "tool_call_parser": "not-applicable"}
        self.config["parameters_billion"] = 8
        self.case_id = "mf-read-only-vm-inventory"

    def fake(self, config, prompt):
        self.assertNotIn("oracle", json.dumps(prompt))
        oracle = tasks.cases()[self.case_id]["task_template"]["oracle"]
        value = {"target": oracle["target"], "proposed_calls": oracle["calls"],
                 "findings": oracle["findings"], "answer": "Synthetic fixture; no operation executed."}
        return json.dumps(value), {"elapsed_ms": 12, "input_tokens": 100, "output_tokens": 50}, "stop", tasks.digest(config["deployment"]["model"])

    def collect(self, transport=None):
        destination = self.root / "run"
        runner.collect(self.config, matrix.seal(), destination, case_ids=[self.case_id], transport=transport or self.fake)
        return destination

    def test_unreviewed_stays_unmeasured_and_review_does_not_create_full_matrix(self):
        directory = self.collect()
        summary = runner.report(directory, self.root / "report1")
        groups = summary["assessment"]["configurations"][0]["groups"]
        self.assertTrue(all(g["task_gate"] == "not_measured" for g in groups))
        tasks.owner_json(directory / (self.case_id + "--1") / "review.json", REVIEW)
        summary = runner.report(directory, self.root / "report2")
        self.assertTrue(all(g["task_gate"] == "not_measured" for g in summary["assessment"]["configurations"][0]["groups"]))
        self.assertTrue(all(s["experiment_ids"] == [] for s in comparison.compare([summary])["shortlists"]))
        self.assertEqual(summary["usage"]["input_tokens"], 100)
        self.assertIsNone(summary["estimated_token_cost_usd"])
        self.assertNotIn("base_url", json.dumps(summary))
        self.assertEqual((directory / (self.case_id + "--1") / "raw-answer.json").stat().st_mode & 0o777, 0o600)
        with self.assertRaises(FileExistsError):
            runner.report(directory, self.root / "report1")

    def test_transport_error_is_incomplete_not_a_passing_or_model_failure(self):
        def broken(*_):
            raise runner.CollectionError("transport_error")
        directory = self.collect(broken)
        summary = runner.report(directory, self.root / "report")
        self.assertEqual(summary["transport_errors_or_missing"], 1)
        self.assertEqual(summary["assessment"]["configurations"], [])
        self.assertIsNone(summary["usage"]["input_tokens"])

    def test_invalid_json_is_failed_contract_not_repaired(self):
        def malformed(*_):
            return "```json\n{}\n```", {"elapsed_ms": 1, "input_tokens": None, "output_tokens": None}, "stop", "hash"
        directory = self.collect(malformed)
        summary = runner.report(directory, self.root / "report")
        self.assertTrue(summary["assessment"]["configurations"][0]["safety_failure"])

    def test_truncated_valid_json_is_not_counted_as_pass(self):
        def truncated(*args):
            content, metrics, _, model = self.fake(*args)
            return content, metrics, "length", model
        directory = self.collect(truncated)
        summary = runner.report(directory, self.root / "report")
        self.assertTrue(summary["assessment"]["configurations"][0]["safety_failure"])

    def test_budget_and_held_out_split_fail_before_call(self):
        with self.assertRaises(ValueError):
            runner.collect(self.config, matrix.seal(), self.root / "run", max_requests=1, transport=self.fake)
        self.assertFalse((self.root / "run").exists())
        with self.assertRaises(ValueError):
            runner.collect(self.config, matrix.seal(), self.root / "run", split="held_out", case_ids=[self.case_id], transport=self.fake)

    def test_response_and_deployment_drift_rejected(self):
        directory = self.collect()
        response = directory / (self.case_id + "--1") / "response.json"
        response.write_text('{}')
        with self.assertRaisesRegex(ValueError, "response drift"):
            runner.report(directory, self.root / "report")

    def test_endpoint_credentials_remote_http_and_query_rejected(self):
        for value in ("http://192.0.2.1/v1", "https://user:pass@example.com/v1", "https://example.com/v1?key=secret", "https://example.com/v1#x", "https://example.com/other"):
            with self.assertRaises(ValueError):
                runner.endpoint(value)
        self.assertEqual(runner.endpoint("http://127.0.0.1:8080/v1").hostname, "127.0.0.1")

    def test_no_send_flag_never_calls_service(self):
        with patch.object(runner, "collect") as call:
            with self.assertRaises(ValueError):
                runner.main(["collect", "--config", str(tasks.HERE / "config.example.json"), "--seal", "none", "--out", "none"])
            call.assert_not_called()

    def test_policy_denial_audited_without_http_or_credentials(self):
        with patch("vmware_policy.guard.guard", side_effect=RuntimeError("secret-value")), patch("vmware_policy.guard.audit_call") as audit, patch("http.client.HTTPConnection") as http:
            with self.assertRaisesRegex(runner.CollectionError, "policy_denied_or_unavailable"):
                runner.send(self.config, {"instructions": "synthetic"})
            http.assert_not_called()
            self.assertEqual(audit.call_args.kwargs["status"], "denied")
            self.assertNotIn("secret-value", str(audit.call_args))

    def test_http_error_does_not_print_body_or_follow_redirect(self):
        with patch("vmware_policy.guard.guard"), patch("vmware_policy.guard.audit_call") as audit, patch("http.client.HTTPConnection") as http:
            http.return_value.getresponse.return_value.status = 302
            with self.assertRaisesRegex(runner.CollectionError, "http_error"):
                runner.send(self.config, {"instructions": "synthetic"})
            http.return_value.getresponse.return_value.read.assert_not_called()
            self.assertEqual(audit.call_args.kwargs["status"], "error")

    def test_api_usage_and_no_native_tool_execution(self):
        body = {"model": self.config["deployment"]["model"], "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 10, "completion_tokens": 2}}
        with patch("vmware_policy.guard.guard"), patch("vmware_policy.guard.audit_call") as audit, patch("http.client.HTTPConnection") as http:
            response = http.return_value.getresponse.return_value
            response.status = 200
            response.read.return_value = json.dumps(body).encode()
            content, metrics, finish, _ = runner.send(self.config, {"instructions": "synthetic", "question": "test"})
            self.assertEqual((content, metrics["input_tokens"], finish), ("{}", 10, "stop"))
            sent = json.loads(http.return_value.request.call_args.args[2])
            self.assertNotIn("tools", sent)
            self.assertFalse(sent["stream"])
            self.assertEqual(audit.call_args.kwargs["status"], "ok")
            body["model"] = "unexpected-fallback-model"
            response.read.return_value = json.dumps(body).encode()
            with self.assertRaisesRegex(runner.CollectionError, "model_identity_mismatch"):
                runner.send(self.config, {"instructions": "synthetic"})

    def test_loopback_http_with_real_policy_and_metadata_only_audit(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import threading
        from vmware_policy.audit import AuditEngine
        from vmware_policy.policy import PolicyEngine
        calls = []
        model = self.config["deployment"]["model"]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass
            def do_POST(self):
                calls.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                body = json.dumps({"model": model, "choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.addCleanup(server.server_close)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        self.config["base_url"] = f"http://127.0.0.1:{server.server_port}/v1"
        rules = self.root / "rules.yaml"
        rules.write_text("deny: []\n")
        engine = AuditEngine(self.root / "audit.db")
        with patch("vmware_policy.guard.get_policy_engine", return_value=PolicyEngine(rules)), patch("vmware_policy.guard.resolve_environment", return_value=""), patch("vmware_policy.guard.get_engine", return_value=engine):
            answer, usage, _, _ = runner.send(self.config, {"instructions": "private-synthetic-marker"})
        self.assertEqual(answer, "{}")
        self.assertIsNone(usage["input_tokens"])
        self.assertEqual(len(calls), 1)
        rows = engine.query(tool="collect_model_response")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "ok")
        self.assertNotIn("private-synthetic-marker", json.dumps(rows))
        self.assertNotIn(self.config["base_url"], json.dumps(rows))
        self.assertEqual(rows[0]["surface"], "cli")

    def test_full_held_out_matrix_and_smaller_failing_configuration(self):
        cases = tasks.cases()
        by_question = {c["q"]: c for c in cases.values()}
        def fixture(config, prompt):
            oracle = by_question[prompt["question"]]["task_template"]["oracle"]
            value = {"target": oracle["target"], "proposed_calls": oracle["calls"],
                     "findings": oracle["findings"], "answer": "Synthetic oracle control; not a model."}
            return json.dumps(value), {"elapsed_ms": 1, "input_tokens": 10, "output_tokens": 5}, "stop", "fixture"
        directory = self.root / "full"
        runner.collect(self.config, matrix.seal(), directory, split="held_out", repeats=5,
                       max_requests=50, transport=fixture)
        for pack in directory.iterdir():
            if pack.is_dir():
                tasks.owner_json(pack / "review.json", REVIEW)
        summary = runner.report(directory, self.root / "full-report")
        self.assertEqual(summary["collected"], 50)
        self.assertTrue(all(g["task_gate"] == "pass" for g in summary["assessment"]["configurations"][0]["groups"]))
        self.assertTrue(all(s["smallest_measured_total_parameters_billion"] == 8 for s in comparison.compare([summary])["shortlists"]))
        small = copy.deepcopy(summary)
        small["run_sha256"] = "smaller-but-unsafe-control"
        small["config"]["parameters_billion"] = 3
        small["assessment"]["configurations"][0]["safety_failure"] = True
        self.assertTrue(all(s["smallest_measured_total_parameters_billion"] == 8 for s in comparison.compare([summary, small])["shortlists"]))

    def test_comparison_abstains_on_development_unknown_size_and_errors(self):
        summary = runner.report(self.collect(), self.root / "report")
        # Controlled synthetic report, NOT a real model score.
        summary["split"] = "held_out"
        summary["collected"] = summary["planned_requests"]
        cohort = summary["assessment"]["configurations"][0]
        for group in cohort["groups"]:
            group.update(task_gate="pass", complete=True, pass_pow_k=1, failures=0, not_measured=0)
        result = comparison.compare([summary])
        self.assertTrue(all(s["smallest_measured_total_parameters_billion"] == 8 for s in result["shortlists"]))
        unknown = copy.deepcopy(summary)
        unknown["run_sha256"] = "another-control"
        unknown["config"]["parameters_billion"] = None
        self.assertTrue(all(s["smallest_measured_total_parameters_billion"] is None for s in comparison.compare([unknown])["shortlists"]))
        for field, value in (("split", "development"), ("transport_errors_or_missing", 1)):
            bad = copy.deepcopy(summary)
            bad[field] = value
            self.assertTrue(all(not s["experiment_ids"] for s in comparison.compare([bad])["shortlists"]))
        with self.assertRaises(ValueError):
            comparison.compare([summary, summary])
        other = copy.deepcopy(summary)
        other["run_sha256"] = "different"
        other["tool_snapshot_sha256"] = "drift"
        with self.assertRaises(ValueError):
            comparison.compare([summary, other])


if __name__ == "__main__":
    unittest.main()
