# Live behavioral probes — mp-skills (2026-10-03)

Harness: `tools/probe_mp.py` (adapted from pstack-generic `tools/live_specialized.py`).
Provider `openai-codex` / model `gpt-6.1-sol`, budget 1200s, one run per case, zero
retries, files+terminal toolsets only (no delegation). Transcripts under
`reports/probes-mp/` (gitignored) — claims below are checked against those files.

## Verdicts

| Case | Skill exercised | Verdict | Duration |
|------|-----------------|---------|----------|
| tdd | mp-tdd | PASS (6/6 criteria) | 46s |
| diagnosing | mp-diagnosing-bugs | PASS (5/5 criteria) | 127s |
| design | mp-codebase-design | PASS (4/4 criteria) | 109s |

## Evidence highlights (all quoted from the saved transcripts)

- **tdd**: test written and run showing `AssertionError: 0.0 != 10.0` (red) BEFORE the
  one-line fix; one slice only; asserts `bulk_discount_rate(10) == 10.0` (public
  contract, not implementation trivia); independent post-run
  `python3 -m unittest discover` reports the single test OK.
- **diagnosing**: pre-fix evidence recorded first (`count_events() -> 0 (expected 3)`);
  hypotheses acted on via real probes (default-list identity, explicit/implicit count);
  cause reproduced through an identity probe before the fix; empty-batch non-discriminating
  probe results reported with equal prominence; post-run `python3 simulate.py` prints
  `count_events() -> 3 (expected 3)`.
- **design**: three structurally distinct candidates (typed snapshot + partial patch /
  generic field operations / caller-specific operations), 5-axis rubric stated before
  scoring, selection justified with the losing candidate's genuine strengths conceded;
  committed signatures named (`get_profile`/`update_profile` over `UserProfile`/`ProfilePatch`
  with error contract); callers' burden quantified (public operations 11→2, 81.8% reduction);
  fixture sources proven unchanged (sha256 before/after); same-agent perspectives honestly
  labeled (no independence claims).

## Limitations and neutral observations

- Three cases passed; these are the three probes the plan called for (tdd/measurement,
  diagnosis, design analogues of pstack's probes). No claim is made that every one of the
  27 skills behaves correctly in a fresh session — probe coverage is structural, not total.
- diagnosing: hypotheses were acted on in tool calls rather than labeled "H1/H2" in prose;
  the discipline was followed, the labeling convention was partial.
- design: the word "leverage" appeared only in tool-call context (vocabulary usage was
  otherwise verbatim from the distribution's rubric axes), recorded as neutral.
- All cases ran with the generic-baseline discipline (no independent delegates available
  in-session), which matches the serial-fallback sentence embedded in the ported skills.

## Reproducing

```
python3 tools/probe_mp.py --attempt r1 --cases tdd diagnosing design
```

Requires a configured Hermes environment (transcripts under `reports/probes-mp/`).
This is not proof of any other product's support for the generic baseline.
