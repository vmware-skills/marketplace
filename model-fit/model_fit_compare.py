"""Compare local experiment summaries; shortlist only measured held-out task gates."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import model_fit_tasks as tasks
import model_fit_runner as runner


def compare(summaries):
    if not summaries or len(summaries) > 100:
        raise ValueError("provide 1–100 summaries")
    identities = set()
    rows, experiments = [], []
    reference = None
    for summary in summaries:
        keys = ("protocol_sha256", "case_hashes_sha256", "tool_snapshot_sha256", "evaluator_sha256", "collector_sha256")
        identity = tuple(summary[key] for key in keys)
        if reference is not None and identity != reference:
            raise ValueError("incompatible sealed assessments; rerun against the same kit")
        reference = identity
        run_id = summary["run_sha256"]
        if run_id in identities:
            raise ValueError("duplicate experiment")
        identities.add(run_id)
        experiments.append({key: summary[key] for key in (
            "run_sha256", "config", "split", "scope", "planned_requests", "collected",
            "transport_errors_or_missing", "latency_ms", "usage", "estimated_token_cost_usd")})
        config = summary["config"]
        size = config["parameters_billion"]
        if size is not None:
            runner.number(size, "parameters_billion", .000001)
        for cohort in summary["assessment"]["configurations"]:
            for group in cohort["groups"]:
                eligible = (summary["split"] == "held_out" and group["task_gate"] == "pass"
                            and group["complete"] and group["pass_pow_k"] == 1
                            and not group["failures"] and not group["not_measured"]
                            and cohort["configuration_complete"] and not cohort["safety_failure"]
                            and summary["transport_errors_or_missing"] == 0
                            and summary["collected"] == summary["planned_requests"])
                rows.append({"run_sha256": run_id, "model": config["deployment"]["model"],
                             "configuration": config["deployment"], "parameters_billion": size,
                             "active_parameters_billion": config["active_parameters_billion"],
                             "scope": summary["scope"], "split": summary["split"],
                             "group": group["group"], "task_gate": group["task_gate"],
                             "pass_pow_k": group["pass_pow_k"], "attempts": group["attempts"],
                             "required_cases": group["required_cases"],
                             "distinct_cases_observed": group["distinct_cases_observed"],
                             "unreviewed_or_unmeasured": group["not_measured"],
                             "safety_failure": cohort["safety_failure"],
                             "transport_errors_or_missing": summary["transport_errors_or_missing"],
                             "experiment_latency_ms": summary["latency_ms"],
                             "experiment_usage": summary["usage"],
                             "experiment_estimated_token_cost_usd": summary["estimated_token_cost_usd"],
                             "quality_eligible": eligible})
    shortlists = []
    for group in sorted({r["group"] for r in rows}):
        for scope in sorted({r["scope"] for r in rows if r["group"] == group}):
            passed = [r for r in rows if r["group"] == group and r["scope"] == scope and r["quality_eligible"]]
            known = [r for r in passed if r["parameters_billion"] is not None]
            size = min(r["parameters_billion"] for r in known) if known else None
            shortlists.append({"group": group, "scope": scope,
                "smallest_measured_total_parameters_billion": size,
                "experiment_ids": sorted({r["run_sha256"] for r in known if r["parameters_billion"] == size}),
                "passing_experiments_with_unknown_size": len([r for r in passed if r["parameters_billion"] is None]),
                "meaning": "Smallest declared total size among tested passing configurations in this scope only; not a minimum required size or deployment recommendation."})
    return {"schema_version": 1, "comparator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "experiments": experiments, "rows": rows, "shortlists": shortlists,
            "limits": "Operator-supplied metadata and human reviews. Synthetic plan reasoning only. "
                      "No autonomous MCP, universal size threshold, cheapest-model claim or production safety guarantee. "
                      "Latency/usage/cost are whole-experiment metrics, not per-group. Scopes are compared separately."}


def markdown(result):
    def cell(value):
        return str(value if value is not None else "unmeasured").replace("|", "\\|").replace("\n", " ").replace("\r", " ").replace("<", "&lt;")
    lines = ["# Model configuration comparison", "", result["limits"], "",
             "| Model | Total B | Active B | Quantization | Scope | Split | Task group | Gate | pass^5 | Attempts | Human/unmeasured | Safety failure |",
             "|---|---:|---:|---|---|---|---|---|---:|---:|---:|---|"]
    for row in result["rows"]:
        values = [row["model"], row["parameters_billion"], row["active_parameters_billion"],
                  row["configuration"]["quantization"], row["scope"], row["split"], row["group"],
                  row["task_gate"], row["pass_pow_k"], row["attempts"], row["unreviewed_or_unmeasured"], row["safety_failure"]]
        lines.append("| " + " | ".join(cell(v) for v in values) + " |")
    lines += ["", "## Whole-experiment measurements", "",
              "| Experiment | Model | Scope | Collected/planned | Errors/missing | p50 ms | p95 ms | Input tokens | Output tokens | Estimated token USD |",
              "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for item in result["experiments"]:
        values = [item["run_sha256"][:12], item["config"]["deployment"]["model"], item["scope"],
                  f'{item["collected"]}/{item["planned_requests"]}', item["transport_errors_or_missing"],
                  item["latency_ms"]["p50"], item["latency_ms"]["p95"], item["usage"]["input_tokens"],
                  item["usage"]["output_tokens"], item["estimated_token_cost_usd"]]
        lines.append("| " + " | ".join(cell(v) for v in values) + " |")
    lines += ["", "## Smallest tested passing configurations", ""]
    for item in result["shortlists"]:
        lines.append(f'- {cell(item["group"])} / {cell(item["scope"])}: {cell(item["smallest_measured_total_parameters_billion"])} B; experiment IDs: {cell(", ".join(item["experiment_ids"]) or None)}.')
    lines += ["", "Unknown sizes abstain. Review JSON for deployment metadata, sample coverage, whole-experiment latency, tokens and estimated cost.", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summaries", type=Path, nargs="+")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    result = compare([tasks.read_json(p) for p in args.summaries])
    args.out.mkdir(parents=True, mode=0o700, exist_ok=False)
    tasks.owner_json(args.out / "comparison.json", result)
    with (args.out / "comparison.md").open("x", encoding="utf-8") as output:
        output.write(markdown(result))
    (args.out / "comparison.md").chmod(0o600)
    print("Local comparison saved. Inspect metadata before sharing; no results uploaded.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError):
        print("Comparison stopped: incompatible, invalid or duplicate input, or existing output.", file=sys.stderr)
        raise SystemExit(2)
