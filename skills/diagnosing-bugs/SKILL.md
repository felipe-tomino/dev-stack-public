---
name: diagnosing-bugs
description: Diagnose hard bugs, intermittent failures, and performance regressions when the cause is uncertain, using symptom-specific feedback and falsifiable hypotheses. Skip this ceremony for a trivial or already-proven cause.
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/diagnosing-bugs
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---
Read `~/.agents/skills/POLICY.md` unless already current. Use for uncertain hard bugs, intermittent failures or performance regressions; a proven cause needs no hypothesis ceremony.

## Symptom-specific feedback

Treat supplied failures as observations, not something to rerun merely for confirmation. Establish the cheapest signal that distinguishes this defect from nearby failures: an existing behavior test, real CLI/API request, browser interaction, captured trace or narrowly isolated harness. Fixtures can isolate a hypothesis but cannot prove real integration.

Keep the signal sharp (the exact wrong result, rejection, timing or state), repeatable where possible, and fast enough for diagnosis. Pin time/seeds or narrow setup when useful. For intermittent failures, report conditions, trial count and failure rate rather than claiming determinism. Minimize only enough to distinguish causes; preserve the original scenario.

If an unavoidable human action prevents automation, adapt [the HITL template](scripts/hitl-loop.template.sh) to the real host and symptom. Run only with an interactive terminal that can relay prompts/responses; otherwise request the specific observation. Never execute the untouched example.

## Falsifiable investigation

Rank only hypotheses the evidence supports. Each predicts an observable difference: “If X causes this, changing Y should produce Z.” Probe the prediction, changing one variable at a time. Prefer debugger/REPL inspection or targeted boundary instrumentation over logging everything.

For performance, establish a like-for-like baseline with workload and conditions, then use timing, profiles, query plans or bisection to locate the cost. Measure the same scenario after the fix; a faster toy harness is not evidence about the original regression. Arbitrary sleeps are probes, not fixes.

Redact secrets before recording commands, outputs or artifacts; credentials stay in the environment. Tag temporary instrumentation so it can be removed. Inspect reachable code/artifacts before requesting inaccessible access or evidence; production instrumentation needs explicit authorization.

## Fix and proof

Once the cause is supported and implementation is authorized, make the smallest causal fix. Add a permanent regression test when it protects plausible risky behavior at a seam that reaches the real bug pattern. A shallow test that omits the triggering caller chain gives false confidence; use an established integration seam or state the coverage limitation. Test-first is useful when it resolves uncertainty, not a universal gate.

Exercise the changed real path under the execution method. Compare the original symptom, or measured original workload, with the supplied/baseline evidence. Remove temporary probes and sensitive captures unless requested as deliverables.

**Complete when:** root cause and remedy are supported by symptom-specific evidence, the original scenario's result and relevant regression protection are accounted for, and limitations are explicit. If no trustworthy feedback is accessible, finish reachable investigation and name the exact missing prerequisite; do not claim a confirmed cause or fix from mocked success.
