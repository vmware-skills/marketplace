# Compare model sizes on your VMware tasks

[中文](RUNNER-CN.md) · [Manual task workflow](README.md)

Everything lives in this independent Git directory. Clone the portal, then work here:

```bash
git clone https://github.com/vmware-skills/marketplace.git
cd marketplace/model-fit
python -m venv .venv
# Activate .venv using your platform's normal activation command.
python -m pip install -r requirements-online.txt
python -c "from pathlib import Path; Path('out').mkdir(mode=0o700, exist_ok=True)"
python model_fit_task_matrix.py seal --out out/plan-seal.json
```

Keep this kit revision and seal before collecting answers. `out/` is ignored by Git;
its files are private local evidence, not public results. On Windows also restrict
this directory with your user ACL; POSIX modes alone do not establish a Windows ACL.
No VMware credentials, live environment or MCP server is needed.

## Configure one candidate

Copy `config.example.json` to `out/model-a.json` and edit it locally. No secrets in
JSON: `api_key_env` is either null (when no key is needed) or the **name** of an
existing environment variable holding your key. The runner never reads `.env` or
installs/downloads/loads models automatically.

Set `base_url` to the endpoint's `/v1` base, and `deployment.model` to its exact served
ID. The response must advertise the same model ID; a fallback/different ID is an
incomplete measurement. Server-reported identity is not independent weight verification.
The common Chat Completions subset is documented by
[Ollama](https://docs.ollama.com/api/openai-compatibility) and
[vLLM](https://docs.vllm.ai/en/stable/serving/openai_compatible_server/).
LM Studio or other compatible endpoints may also work; no provider-specific behavior
is assumed. HTTPS is mandatory except literal loopback addresses or `localhost`.
TLS verification stays enabled. Redirects and environment proxies are not used.

Record known quantization, framework/version, context length and total parameter
count in billions. For MoE models record **total** and **active** counts separately;
active counts do not measure memory needs. Unknowns stay null; model names are never
parsed to guess size. Include hardware locally; shared output contains only its
fingerprint. Same size with different quantization, context or sampling is a different
experiment. The supplied config is a template, not a recommended model.

## Start with one request

```bash
python model_fit_runner.py collect --config out/model-a.json --seal out/plan-seal.json --case mf-read-only-vm-inventory --max-requests 1 --send --out out/a-smoke
```

This sends only sealed synthetic task context and tool schemas to the configured
model; the endpoint operator can see that synthetic content. It does **not** send
answers, review rubrics, private inventory or credentials. Candidate calls remain
JSON proposals and are never dispatched. No native function-calling/parser reliability
is measured. Policy `collect_model_response` guards every request and metadata-only
rows go to the existing VMware audit sink. A local deny rule can block this name.
No new production permission or approval mechanism is introduced.

Each run freezes generation settings, seals, collector fingerprint, endpoint/hardware
fingerprints, scope and sample selection. Every run needs a new output directory.
`--max-requests` bounds the selected request count (default 1); `max_tokens` bounds
requested output tokens. These are **not** a hard money limit. Requests may be billed,
including unsuccessful ones. There are no retries; errors remain visible. Do not
restart only failed attempts and present them as the original complete run.

## Review quality

Each `out/a-smoke/<case-id>--1/` contains the original local answer, parsed response,
request receipt and operator pack. Markdown fences/invalid JSON are not repaired:
invalid or truncated answers fail the response contract. Network/API failures remain
unmeasured; empty/missing token usage is not zero.

Export the human-only rubric, inspect the answer against it, and create `review.json`
in that attempt directory using the review format in the manual README:

```bash
python model_fit_tasks.py rubric mf-read-only-vm-inventory --out out/a-smoke/mf-read-only-vm-inventory--1/rubric.json
python model_fit_runner.py report out/a-smoke --out out/a-smoke-report
```

Do not give rubrics or case answers to the candidate. Review every collected attempt;
there is no bulk “mark pass” command or candidate self-review. Repeat `report` into a
new directory after completing reviews. It regrades stored answers and refuses drift.
Without human evidence/answer/safety review, quality is unmeasured. This smoke run is
incomplete development evidence, never a passing final configuration.

## Compare candidates and tool scopes

Use development tasks to tune prompts/configuration. Freeze them before final tests.
Each group has two public held-out cases; anyone who saw their answers must replace
and reseal them before claiming an unseen assessment. The repository is not a secrecy
boundary. Explicit `--split held_out` opts into the final set:

```bash
python model_fit_runner.py collect --config out/model-a.json --seal out/plan-seal.json --split held_out --repeats 5 --scope relevant --max-requests 50 --send --out out/a-final
# Review all 50 answers; then:
python model_fit_runner.py report out/a-final --out out/a-final-reviewed
# Repeat with out/model-b.json and new output directories, using the same seal.
python model_fit_compare.py out/a-final-reviewed/summary.json out/b-final-reviewed/summary.json --out out/comparison
```

Open `out/comparison/comparison.md` and `comparison.json`. The table shows per-group
quality, safety, review/sample coverage and model sizes; JSON also includes deployment
settings and whole-experiment latency p50/p95, tokens and optional estimated token cost.
Small samples do not establish reliable tail latency. Prices are operator-supplied;
estimates are not bills and exclude hardware, review and repair. No lowest-total-cost
recommendation is made. Errors may have incurred costs not captured in usage.

For an all-tool comparison run a **separate** experiment with `--scope all` and repeat
the same workflow. `relevant` supplies curated per-case schemas plus distractors;
`all` supplies all 353. This measures the effect of supplied context, **not** successful
search/get-schema/call routing. The results do not prove a native MCP host can route
or execute calls. No SKILL.md is included, so neither is a full installed-skill test.

The per-group shortlist includes only complete reviewed held-out configurations with
zero safety failures, five passes on every case and known size. Any safety failure
rejects the configuration across groups. Transport errors prevent positive selection.
Unknown sizes abstain. Results show the smallest **declared total size among tested
passing configurations in the same scope**, not the minimum size anyone needs or a
production recommendation. Group-specific passing configurations can differ.
Repeated attempts are not assumed independent. Ten final attempts per group do not
support a <5% general failure-rate claim. Reassess after model/config/contract changes.

## Sharing and tests

Nothing is uploaded. Review local aggregates before copying them into `results/`;
model IDs and deployment strings can themselves be sensitive. Never commit `out/`,
raw answers, API URLs, keys or customer information. See [result rules](results/README.md).
There are no actual model results committed yet; controls are not model measurements.

```bash
python -m unittest discover -s tests -v
```

Tests use synthetic authored responses and stubbed transports, not real model or
VMware calls. Real endpoint compatibility and real model quality need separate runs.
