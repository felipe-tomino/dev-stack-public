---
name: diagnosing-bugs
description: Diagnose hard bugs, intermittent failures, and performance regressions when the cause is uncertain, using symptom-specific feedback and falsifiable hypotheses. Skip this ceremony for a trivial or already-proven cause.
metadata:
  source: https://github.com/mattpocock/skills/tree/49dd158d1076134a641b33efb035946536778336/skills/engineering/diagnosing-bugs
  revision: 49dd158d1076134a641b33efb035946536778336
  variant: personal-shared
---
Read `~/.agents/skills/POLICY.md` before applying this skill. It governs personal workflow; mandatory repository rules remain binding.


# Diagnosing Bugs

A discipline for hard bugs and performance regressions, not ceremony for every fix. Use supplied failures and observations as ground truth. Skip phases with a brief evidence-based reason: a known repro need not be rebuilt, a supplied failure need not be rerun to confirm it, and an already-proven cause needs no speculative theory list. Keep the symptom-specific feedback and final measured scenario that are still needed.

When exploring the codebase, read `GLOSSARY.md` (if it exists) to get a clear mental model of the relevant modules, and check ADRs in the area you're touching.

## Redact

This skill has you show commands, outputs and captured artifacts. **Redact every secret first**: write `<REDACTED>` in its place. Build loops against env vars, so the credential stays in the environment rather than in what you show. Captured artifacts carry auth headers: quote only the lines that carry the signal.

If available redacted evidence is insufficient, finish reachable inspection first. Ask only for the specific inaccessible prerequisite, batching independent requests with a recommendation.

## Phase 1: Build a feedback loop

**This is the skill.** Everything else is mechanical. If you have a **tight** pass/fail signal for the bug (one that goes red on _this_ bug), you will find the cause; bisection, hypothesis-testing, and instrumentation all just consume it. If you don't have one, no amount of staring at code will save you.

Spend disproportionate effort here. **Be aggressive. Be creative. Refuse to give up.**

### Ways to construct one, in roughly this order

1. **Failing test** at the behavior seam that reaches the bug: unit, integration, e2e. Reuse a supplied test and failure as ground truth rather than rerunning it just to confirm the report.
2. **Curl / HTTP script** against a running dev server.
3. **CLI invocation** with a fixture input, diffing stdout against a known-good snapshot.
4. **Headless browser script** (Playwright / Puppeteer) that drives the UI and asserts on DOM/console/network.
5. **Replay a captured trace.** Save a real network request / payload / event log to disk; replay it through the code path in isolation.
6. **Throwaway harness.** Isolate the bug's real logic with the minimum dependencies. Fixtures or mocks may isolate a local hypothesis, but cannot prove a real integration works.
7. **Property / fuzz loop.** If the bug is "sometimes wrong output", run 1000 random inputs and look for the failure mode.
8. **Bisection harness.** If the bug appeared between two known states (commit, dataset, version), automate "boot at state X, check, repeat" so you can `git bisect run` it.
9. **Differential loop.** Run the same input through old-version vs new-version (or two configs) and diff outputs.
10. **HITL bash script.** Last resort for an unavoidable human action. Read and adapt [scripts/hitl-loop.template.sh](scripts/hitl-loop.template.sh) to the exact symptom and real host first. Run the adapted script only with an available interactive terminal that can relay the human prompts and responses. If the runtime lacks this capability, ask for the required human observation instead. Never execute the untouched example or install scripts. Capture observations, never credentials.

Build the right feedback loop, and the bug is 90% fixed.

### Tighten the loop

Treat the loop as a product. Once you have _a_ loop, **tighten** it:

- Can I make it faster? (Cache setup, skip unrelated init, narrow the test scope.)
- Can I make the signal sharper? (Assert on the specific symptom, not "didn't crash".)
- Can I make it more deterministic? (Pin time, seed RNG, isolate filesystem, freeze network.)

A 30-second flaky loop is barely better than no loop; a 2-second deterministic one is tight, a debugging superpower.

### Non-deterministic bugs

Aim for a measurable reproduction rate, not a false claim of determinism. Repeat safe triggers, pin seeds where possible, and use targeted stress or timing probes when justified. Report the number of trials, failure rate, and conditions; arbitrary sleeps are experiments, not fixes.

### When you genuinely cannot build a loop

Complete reachable code, artifact, and environment inspection first. State exactly what remains inaccessible and what you tried. Request the smallest prerequisite: environment access, a redacted HAR/log/core dump/recording, or explicit authorization for temporary production instrumentation. Do not invent runtime evidence or use mocked success as proof. A bounded hypothesis may guide the request, but label it unconfirmed.

### Completion criterion: a tight loop that goes red

Phase 1 is done when you can name a **tight, symptom-specific command** (script, test invocation, curl) and show its observed evidence, or cite the supplied failure without needlessly rerunning it. The loop must be:

- [ ] **Red-capable**: it drives the actual bug code path and asserts the **user's exact symptom**, so it can go red on this bug and green once fixed. Not "runs without erroring"; it must be able to _catch this specific bug_.
- [ ] **Deterministic where possible**: same verdict; for intermittent bugs report controlled conditions and measured reproduction rate.
- [ ] **Fast**: seconds, not minutes.
- [ ] **Agent-runnable**: unattended where possible; unavoidable human actions use the adapted HITL template.

Inspect code as needed to construct the loop. For an uncertain hard bug, avoid speculative edits before a trustworthy signal exists; explain any evidence-based phase skip.

## Phase 2: Reproduce + minimise

Use the known failure evidence; run only what adds missing diagnostic information, not another confirmation of the user's observation.

Confirm:

- [ ] The loop produces the failure mode the **user** described, not a different failure that happens to be nearby. Wrong bug = wrong fix.
- [ ] The failure is reproducible across multiple runs (or, for non-deterministic bugs, reproducible at a high enough rate to debug against).
- [ ] You have captured the exact symptom (error message, wrong output, slow timing) so later phases can verify the fix actually addresses it.

### Minimise

Shrink the repro only as far as needed to distinguish causes and expose a correct regression seam. Cut inputs, callers, config, data, and steps one at a time, retaining the same symptom. Preserve a known minimal repro instead of minimizing it again.

The smallest useful repro reduces competing explanations without spending time proving every remaining element indispensable. State why further minimization would add no useful evidence.

## Phase 3: Hypothesise

For an uncertain cause, rank a small set of plausible hypotheses before testing. Use only as many as the evidence supports; do not manufacture 3–5 theories for a proven cause.

Each hypothesis must be **falsifiable**: state the prediction it makes.

> Format: "If <X> is the cause, then <changing Y> will make the bug disappear / <changing Z> will make it worse."

If you cannot state the prediction, the hypothesis is a vibe: discard or sharpen it.

Briefly present the ranked hypotheses and predictions with their evidence. Ask only about a material unresolved decision or inaccessible fact, not for approval of each probe. Incorporate supplied domain evidence without reopening settled scope.

## Phase 4: Instrument

Each probe must map to a specific prediction from Phase 3. **Change one variable at a time.**

Tool preference:

1. **Debugger / REPL inspection** if the env supports it. One breakpoint beats ten logs.
2. **Targeted logs** at the boundaries that distinguish hypotheses.
3. Never "log everything and grep".

**Tag every debug log** with a unique prefix, e.g. `[DEBUG-a4f2]`. Cleanup at the end becomes a single grep. Untagged logs survive; tagged logs die.

**Perf branch.** For performance regressions, logs are usually wrong. Instead: establish a baseline measurement (timing harness, `performance.now()`, profiler, query plan), then bisect. Measure first, fix second.

## Phase 5: Fix + regression test

Write the regression test **before the fix**, but only if there is a **correct seam** for it.

A correct seam is one where the test exercises the **real bug pattern** as it occurs at the call site. If the only available seam is too shallow (single-caller test when the bug needs multiple callers, unit test that can't replicate the chain that triggered the bug), a regression test there gives false confidence.

**If no correct seam exists, that itself is the finding.** Note it. The codebase architecture is preventing the bug from being locked down. Flag this for the next phase.

If a correct seam exists:

1. Turn the minimised repro into a failing test at that seam.
2. Establish red evidence at the correct seam; an existing supplied failure suffices. If artificial mutation was necessary to check test sensitivity, show its exact difference and restore it; do not confuse artificial red with reproduction of the real defect.
3. Apply the fix.
4. Watch it pass.
5. Re-run the original (un-minimised) scenario and compare its exact symptom or timing against the original evidence. For performance, report like-for-like workload, conditions, and measured before/after results.

## Phase 6: Cleanup

Required before declaring done:

- [ ] Original symptom no longer occurs in the measured original scenario; report any unexercised integration honestly
- [ ] Regression test passes at the correct seam (or the missing seam and validation limitation are stated)
- [ ] Tagged `[DEBUG-...]` logs and other temporary probes removed using the grep tool
- [ ] Throwaway harnesses and captured sensitive artifacts removed unless explicitly requested as deliverables
- [ ] Root cause, evidence, fix, and remaining limitations recorded in the requested destination or response

Do not commit, push, create a PR, or update an issue/tracker unless the current task requests it.
