"""Opt-in synthetic model collection; never execute candidate tool calls."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import http.client
import ipaddress
import json
import math
import os
from pathlib import Path
import ssl
import sys
import time
from urllib.parse import urlsplit

import model_fit_tasks as tasks
import model_fit_task_matrix as matrix

VERSION = 1
MAX_BODY = 4_000_000


class CollectionError(ValueError):
    """Safe, fixed error code; never contains remote text or credentials."""


def number(value, name, minimum=0, maximum=1e12):
    if type(value) not in (int, float) or not minimum <= value <= maximum or not math.isfinite(value):
        raise ValueError(f"invalid {name}")
    return value


def endpoint(value):
    if not isinstance(value, str):
        raise ValueError("base_url required")
    url = urlsplit(value)
    if (url.scheme not in {"http", "https"} or not url.hostname or url.username
            or url.password or url.query or url.fragment or url.path.rstrip("/") != "/v1"):
        raise ValueError("base_url must be a credential-free /v1 URL")
    try:
        loopback = ipaddress.ip_address(url.hostname).is_loopback
    except ValueError:
        loopback = url.hostname == "localhost"
    if url.scheme == "http" and not loopback:
        raise ValueError("HTTP is allowed only for loopback endpoints")
    if any(ord(c) < 33 for c in value):
        raise ValueError("invalid endpoint characters")
    _ = url.port
    return url


def load_config(path):
    value = tasks.read_json(path)
    required = {"base_url", "deployment", "parameters_billion", "active_parameters_billion",
                "hardware", "temperature", "max_tokens", "timeout_seconds", "api_key_env"}
    optional = {"input_usd_per_million", "output_usd_per_million"}
    if not isinstance(value, dict) or set(value) - required - optional or required - set(value):
        raise ValueError("invalid config fields")
    endpoint(value["base_url"])
    dep = value["deployment"]
    if not isinstance(dep, dict) or set(dep) != set(tasks.MEASUREMENTS):
        raise ValueError("invalid deployment fields")
    for key, item in dep.items():
        if item is None and key != "model":
            continue
        if key == "context_length":
            if type(item) is not int or item < 1:
                raise ValueError("invalid context_length")
        elif not isinstance(item, str) or not item.strip() or len(item) > 300:
            raise ValueError("invalid deployment string")
    for key in ("parameters_billion", "active_parameters_billion", *optional):
        if value.get(key) is not None:
            number(value[key], key, 0.000001 if "parameters" in key else 0)
    total, active = value["parameters_billion"], value["active_parameters_billion"]
    if total is not None and active is not None and active > total:
        raise ValueError("active parameters exceed total parameters")
    if value["hardware"] is not None and (not isinstance(value["hardware"], str) or len(value["hardware"]) > 300):
        raise ValueError("invalid hardware")
    number(value["temperature"], "temperature", 0, 2)
    if type(value["max_tokens"]) is not int:
        raise ValueError("max_tokens must be integer")
    number(value["max_tokens"], "max_tokens", 1, 131072)
    number(value["timeout_seconds"], "timeout_seconds", 1, 600)
    key = value["api_key_env"]
    if key is not None and (not isinstance(key, str) or not key.isidentifier()):
        raise ValueError("invalid api_key_env")
    return value


def fingerprint():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def public_config(config):
    # No endpoint, key variable name or free-form hardware text leaves the local config.
    return {key: config.get(key) for key in ("deployment", "parameters_billion",
            "active_parameters_billion", "temperature", "max_tokens",
            "input_usd_per_million", "output_usd_per_million", "timeout_seconds")} | {
                "hardware_sha256": tasks.digest(config["hardware"]),
                "endpoint_sha256": tasks.digest(config["base_url"])}


def send(config, prompt):
    """One bounded request with existing Policy guard/audit; no retries/redirects."""
    try:
        from vmware_policy.guard import guard, audit_call
    except ImportError:
        raise CollectionError("policy_dependency_required") from None
    params = {"prompt_sha256": tasks.digest(prompt),
              "endpoint_sha256": tasks.digest(config["base_url"]), "synthetic": True}
    status, started = "error", time.monotonic()
    connection = None
    try:
        try:
            guard("model-fit", "collect_model_response", params, target=params["endpoint_sha256"])
        except Exception:
            status = "denied"
            raise CollectionError("policy_denied_or_unavailable") from None
        key = os.environ.get(config["api_key_env"], "") if config["api_key_env"] else ""
        if config["api_key_env"] and not key:
            raise CollectionError("api_key_missing")
        if any(c in key for c in "\r\n"):
            raise CollectionError("invalid_api_key")
        url = endpoint(config["base_url"])
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = "Bearer " + key
        payload = {"model": config["deployment"]["model"], "temperature": config["temperature"],
                   "max_tokens": config["max_tokens"], "stream": False,
                   "messages": [{"role": "system", "content": prompt["instructions"]},
                                {"role": "user", "content": json.dumps(
                                    {k: v for k, v in prompt.items() if k != "instructions"},
                                    ensure_ascii=False)}]}
        if url.scheme == "https":
            connection = http.client.HTTPSConnection(url.hostname, url.port,
                timeout=config["timeout_seconds"], context=ssl.create_default_context())
        else:
            connection = http.client.HTTPConnection(url.hostname, url.port,
                timeout=config["timeout_seconds"])
        connection.request("POST", "/v1/chat/completions", json.dumps(payload).encode(), headers)
        response = connection.getresponse()
        if response.status != 200:
            raise CollectionError("http_error")
        body = response.read(MAX_BODY + 1)
        if len(body) > MAX_BODY:
            raise CollectionError("response_too_large")
        def reject(_):
            raise ValueError("non-finite response")
        try:
            result = json.loads(body, parse_constant=reject)
            content = result["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("missing text")
            finish = result["choices"][0].get("finish_reason")
            usage = result.get("usage") or {}
            metrics = {}
            for source, dest in (("prompt_tokens", "input_tokens"), ("completion_tokens", "output_tokens")):
                item = usage.get(source)
                metrics[dest] = item if type(item) is int and item >= 0 else None
            returned_model = result.get("model")
            if returned_model != config["deployment"]["model"]:
                raise CollectionError("model_identity_mismatch")
        except CollectionError:
            raise
        except (KeyError, IndexError, TypeError, ValueError):
            raise CollectionError("invalid_api_response") from None
        metrics["elapsed_ms"] = round((time.monotonic() - started) * 1000, 3)
        status = "ok"
        return content, metrics, finish, tasks.digest(returned_model)
    except CollectionError:
        raise
    except Exception:
        raise CollectionError("transport_error") from None
    finally:
        try:
            if connection is not None:
                connection.close()
        finally:
            audit_call("model-fit", "collect_model_response", params=params, status=status,
                       duration_ms=int((time.monotonic() - started) * 1000), surface="cli",
                       result={"synthetic_only": True})


def collect(config, sealed, destination, split="development", scope="relevant", repeats=1,
            case_ids=None, max_requests=300, transport=send):
    matrix.validate_seal(sealed)
    if split not in {"development", "held_out"} or scope not in {"relevant", "all"}:
        raise ValueError("invalid split/scope")
    if type(repeats) is not int or not 1 <= repeats <= 5:
        raise ValueError("repeats must be 1–5")
    selected = [c for c in tasks.cases().values() if c["task_template"]["split"] == split
                and (case_ids is None or c["id"] in case_ids)]
    if not selected or (case_ids is not None and set(case_ids) != {c["id"] for c in selected}):
        raise ValueError("unknown, duplicate or wrong-split case selection")
    count = len(selected) * repeats
    if type(max_requests) is not int or not 1 <= max_requests <= 300 or count > max_requests:
        raise ValueError("request count exceeds explicit limit")
    destination.mkdir(parents=True, mode=0o700, exist_ok=False)
    run = {"schema_version": VERSION, "created_at": datetime.now(timezone.utc).isoformat(),
           "collector_sha256": fingerprint(), "config": public_config(config), "seal": sealed,
           "split": split, "scope": scope, "repeats": repeats,
           "case_ids": [c["id"] for c in selected], "planned_requests": count}
    tasks.owner_json(destination / "run.json", run)
    for case in selected:
        for repeat in range(1, repeats + 1):
            directory = destination / f'{case["id"]}--{repeat}'
            pack = tasks.prepare(case["id"], directory, scope, split == "held_out")
            pack["configuration"].update(config["deployment"])
            # prepare created this metadata here; do not overwrite any collected answer.
            (directory / "operator.json").write_text(json.dumps(pack, ensure_ascii=False, indent=2) + "\n")
            prompt = tasks.read_json(directory / "prompt.json")
            try:
                content, metrics, finish, model_hash = transport(config, prompt)
                tasks.owner_json(directory / "raw-answer.json", {"content": content})
                try:
                    def reject(_):
                        raise ValueError("nonfinite")
                    answer = json.loads(content, parse_constant=reject)
                    if finish != "stop":
                        answer = {}
                except (ValueError, TypeError):
                    answer = {}  # Invalid model JSON must fail, never be repaired silently.
                tasks.owner_json(directory / "response.json", answer)
                receipt = {"status": "collected", "metrics": metrics,
                           "finish_reason": finish if finish in {"stop", "length", "tool_calls", "content_filter"} else "other",
                           "returned_model_sha256": model_hash, "response_sha256": tasks.digest(answer)}
            except CollectionError as error:
                receipt = {"status": "not_measured", "error_code": str(error)}
            tasks.owner_json(directory / "receipt.json", receipt)
    return run


def checked_run(directory):
    run = tasks.read_json(directory / "run.json")
    matrix.validate_seal(run["seal"])
    if run["collector_sha256"] != fingerprint():
        raise ValueError("collector changed; keep the original runner or start a new sealed run")
    if run["schema_version"] != VERSION or run["split"] not in {"development", "held_out"}:
        raise ValueError("invalid run")
    available = tasks.cases()
    selected = run.get("case_ids")
    if (not isinstance(selected, list) or not selected or len(selected) != len(set(selected))
            or any(c not in available or available[c]["task_template"]["split"] != run["split"] for c in selected)
            or type(run.get("repeats")) is not int or not 1 <= run["repeats"] <= 5
            or run.get("planned_requests") != len(selected) * run["repeats"]
            or run.get("scope") not in {"relevant", "all"}):
        raise ValueError("invalid experiment manifest")
    return run


def report(directory, destination):
    run = checked_run(directory)
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    records, receipts, errors = [], [], 0
    records_dir = destination / "records"
    records_dir.mkdir(mode=0o700)
    for case_id in run["case_ids"]:
        for repeat in range(1, run["repeats"] + 1):
            pack = directory / f"{case_id}--{repeat}"
            try:
                receipt = tasks.read_json(pack / "receipt.json")
            except FileNotFoundError:
                errors += 1
                continue
            if receipt["status"] != "collected":
                errors += 1
                continue
            response = tasks.read_json(pack / "response.json")
            if receipt["response_sha256"] != tasks.digest(response):
                raise ValueError("response drift")
            operator = tasks.read_json(pack / "operator.json")
            if any(operator["configuration"][k] != run["config"]["deployment"][k] for k in tasks.MEASUREMENTS):
                raise ValueError("deployment drift")
            if operator["configuration"]["tool_scope"] != run["scope"]:
                raise ValueError("scope drift")
            review = pack / "review.json"
            record = tasks.grade_pack(pack, pack / "response.json", review if review.exists() else None, repeat)
            record["metrics"].update(receipt["metrics"])
            tasks.owner_json(records_dir / f"{case_id}--{repeat}.json", record)
            records.append(record)
            receipts.append(receipt)
    summary = matrix.summarize(run["seal"], records, run["split"]) if records else {"configurations": []}
    # A transport error anywhere prevents this experiment's positive shortlist.
    if errors:
        for cohort in summary["configurations"]:
            for group in cohort["groups"]:
                if group["task_gate"] == "pass":
                    group["task_gate"] = "not_measured"
    values = [r["metrics"]["elapsed_ms"] for r in receipts]
    values.sort()
    def percentile(p):
        return values[max(0, math.ceil(len(values) * p) - 1)] if values else None
    tokens = {}
    for key in ("input_tokens", "output_tokens"):
        measured = [r["metrics"].get(key) for r in receipts]
        tokens[key] = sum(measured) if measured and all(v is not None for v in measured) else None
    prices = [run["config"].get(k) for k in ("input_usd_per_million", "output_usd_per_million")]
    estimate = (sum(v * p / 1e6 for v, p in zip(tokens.values(), prices))
                if all(v is not None for v in (*tokens.values(), *prices)) else None)
    result = {"schema_version": VERSION, "run_sha256": tasks.digest(run),
              "protocol_sha256": run["seal"]["protocol_sha256"],
              "case_hashes_sha256": tasks.digest(run["seal"]["case_hashes"]),
              "tool_snapshot_sha256": run["seal"]["tool_snapshot_sha256"],
              "evaluator_sha256": run["seal"]["evaluator_sha256"],
              "collector_sha256": run["collector_sha256"], "split": run["split"],
              "config": run["config"], "scope": run["scope"], "planned_requests": run["planned_requests"],
              "collected": len(records), "transport_errors_or_missing": errors,
              "latency_ms": {"p50": percentile(.5), "p95": percentile(.95), "n": len(values), "method": "nearest-rank; includes service/network time"},
              "usage": tokens, "estimated_token_cost_usd": estimate, "billed_cost_usd": None,
              "assessment": summary,
              "limits": "Synthetic proposed-action reasoning, human reviews required; no real MCP execution. "
                        "Sizes are operator-declared. Token estimates exclude hardware, review and repair. "
                        "Results do not establish deployment safety or a universal model-size threshold."}
    tasks.owner_json(destination / "summary.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("collect")
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--seal", type=Path, required=True)
    run.add_argument("--out", type=Path, required=True)
    run.add_argument("--split", choices=("development", "held_out"), default="development")
    run.add_argument("--scope", choices=("relevant", "all"), default="relevant")
    run.add_argument("--repeats", type=int, default=1)
    run.add_argument("--case", action="append", dest="cases")
    run.add_argument("--max-requests", type=int, default=1)
    run.add_argument("--send", action="store_true", help="explicitly permit synthetic prompts to the configured endpoint")
    rep = sub.add_parser("report")
    rep.add_argument("run", type=Path)
    rep.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "collect":
        if not args.send:
            raise ValueError("collection requires --send; it may incur provider charges")
        config = load_config(args.config)
        if args.cases and len(args.cases) != len(set(args.cases)):
            raise ValueError("duplicate case selection")
        collect(config, tasks.read_json(args.seal), args.out, args.split, args.scope,
                args.repeats, args.cases, args.max_requests)
        print("Collection finished. Review each local answer before reporting; errors remain unmeasured.")
    else:
        result = report(args.run, args.out)
        print(f'Report saved: {result["collected"]}/{result["planned_requests"]} responses collected.')
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, OSError, TypeError):
        print("Model-fit stopped: invalid configuration, stale evidence, inaccessible file or existing output. No remote error body is printed.", file=sys.stderr)
        raise SystemExit(2)
