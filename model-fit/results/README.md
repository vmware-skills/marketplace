# Judgment results

[中文](README-CN.md)

**No actual candidate model has been measured yet.** `model-results.json` is an
empty result index with status `not_measured`; an empty list is not a success rate.

`controls-2026-11-12.json` contains authored positive/injected-negative inputs that
check the grader. Its review fields are synthesized control data, not independent
human reviews of a model. `validation-2026-11-12.json` records the standalone test
execution. Neither is a model score, autonomous run, live appliance result, approval
or deployment recommendation.

To contribute a model assessment:

1. Follow the parent README, preserve the pre-response seal, and use the explicit
   final split only after tuning is frozen. State if you inspected its answers.
2. Add a sanitized `model_fit_task_matrix.py report` JSON here under a dated filename.
   Record date, actual model/quantization/framework/version/parser/context length,
   scope, instruction/tool/case/protocol hashes, repeats, per-group failures and
   not-measured fields, human review provenance and limitations. Keep unknowns null.
3. Update the index to point to that file. No global score or universal model-size inference.
   Static proposed-action results must stay separate from future autonomous/lab runs.
4. Do not commit raw responses, operator packs, provider URLs, credentials, real
   inventory or customer data. Those belong in ignored local `out/`, if retained at all.

The seal is operator-held and review identity/repeated generation are not independently
verified by this offline kit. A passing group does not establish production safety,
independent approval, low failure probability or lowest cost. Repeat the assessment
when its configuration or contracts change materially.

## Automated collection reports

The optional collector in [RUNNER.md](../RUNNER.md) writes local experiment summaries.
Its comparison command can show the smallest operator-declared total parameter size
among fully reviewed passing held-out configurations, separately for each task group
and tool scope. This is limited to measured configurations, not a model-size threshold
or autonomous-deployment recommendation. Keep the complete generation configuration,
seal/fingerprints, review provenance and error counts when sharing sanitized summaries.
An estimated token cost is not a bill or total-cost result. Raw answers stay local.
