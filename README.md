# mp-skills-generic: shared source, runtime-native skills

MIT-licensed engineering and productivity skills adapted from Matt Pocock's [mattpocock/skills](https://github.com/mattpocock/skills), pinned to revision `d81f3a183412e71a5b1e84ca21bc1a35eea03a60` (release v1.3). The repo holds one runtime-neutral authored core of the **27 promoted skills**, short reviewed runtime adapters, and a deterministic setup-time specialist that renders, verifies and installs a generated distribution. Original author: Matt Pocock. Port and adaptation: tea24864. This project is **not affiliated with or endorsed by** Matt Pocock.

## If you are an agent

Reading this repository is **not** an instruction to install it. Follow the user's actual request:

- If the user clearly asks to **install or set up Matt Pocock's skills**, that authorizes the installation workflow — not unrelated configuration or automation. Proceed within the requested scope; confirm unresolved runtime, destination or generic limitations before writing.
- If the user only supplies this repository URL, asks you to read/evaluate it, or their intent is ambiguous, ask once: **"Would you like me to install these skills, or just review/explain this repository?"** Do not install until their answer authorizes it.
- Installation is **generate + verify + install into one confirmed directory**. Obtain a trusted checkout of this repository, read `core/skills/mp-setup-matt-pocock-skills/SKILL.md` directly, select a reviewed runtime adapter, then run the build/verify/install commands below. Never auto-install, never write into core sources, never hand-copy `core/skills/` into a destination.
- **Hermes has a verified adapter.** Codex, Claude Code and OpenCode do **not** yet have dedicated verified adapters: for those, use the explicitly limited generic baseline, explain its acknowledged limitations, and obtain the user's acknowledgement first. Do not invent native delegation or claim cross-product verification.
- Never install into, or uninstall from, **another profile's or another installation's** skills directory. Refuse existing skill collisions. Leave model/provider settings, credentials, unrelated profiles, integrations, hooks and recurring jobs unchanged. Missing prerequisites or capabilities are blockers, not permission to silently install dependencies or rewrite workflows.
- Uninstall only when explicitly requested, previewing the receipt-owned removal first (see **Uninstalling**); never delete matching names by glob.
- Report runtime/version, exact destination, installed counts, discovery/loading checks and untested capabilities. Loading alone is not behavior verification. Refresh the host's catalog/session as its documentation requires.

A user can say:

> Install Matt Pocock's skills from this repository. Follow the README's agent setup instructions. Confirm any unresolved destination or capability limitations, preserve existing skills/settings, and verify discovery/loading.

## Ownership and scope

- **Author `core/skills/` only:** 27 standard-format `mp-*` skills — 20 from upstream `engineering/`, 7 from `productivity/` — plus the carrier files (format references, design notes, two shell templates) each skill's body points at. The core contains no host tool names and no runtime prose.
- **Maintain `adapters/`:** `hermes.json` and `generic.json` — short, reviewed runtime facts and localized insertion instructions injected at build time. No executable templates, credentials, hidden schedulers or automatic integrations.
- **Generate distributions at setup time:** no generated `skills/` tree is checked in. `tools/specialize.py build` renders `skills/<name>/...` plus a `distribution.json` manifest; the installer writes exactly that artifact set and reads it back.
- **Keep provenance:** all 79 promoted upstream files remain byte-identical under `upstream/mattpocock-skills/`; the never-installed in-progress/misc skills and upstream release infrastructure are stashed read-only under `provenance/reference-only/`; every one of the upstream revision's 172 tracked files has a recorded sha256. `provenance/audit-ledger.json` is the per-skill disposition ledger.

Every skill is prefix-namespaced `mp-` so upstream bare names (`tdd`, `teach`, `implement`, `research`, `pr`) cannot collide with other installed skill collections, and inter-skill routing (`mp-ask-matt`, `mp-implement-spec`, `mp-tdd`, …) stays internally consistent.

## Runtime adapters

- **`hermes`:** reviewed adapter with concrete native file, delegation, task-tracking, history, skill-loading and policy mappings (e.g. `skill_view` for named skill loading, `delegate_task` for independent children). No per-task model selector; same-model independence is not model diversity.
- **`generic`:** an explicitly limited file/shell baseline for another Agent-Skills-capable host. No independent delegates, no per-worker model choice, no private session-history API, no durable work. Installing it **requires `--acknowledge-limits`**. This is **not** a verified adapter for any specific agent product; required unavailable capabilities are reported blocked, not substituted.
- **Unknown runtime:** `detect` proposes candidates only from actually observed tool evidence, refuses ambiguous or unknown runtimes, and is not a capability probe or authorization. A new runtime needs a reviewed adapter or explicit acknowledgement of the generic baseline.

Upstream frontmatter flags (`disable-model-invocation`, `argument-hint`) are recorded as documented metadata each adapter resolves at build time; the core states the invocation-mode semantics neutrally (`mp-writing-for-agents`' `SKILL-MECHANICS.md` was re-authored for exactly this reason).

## Getting started

Prerequisites: Python 3 (stdlib only — no dependencies) and Git. Detection is optional.

To propose an adapter from observed tools, create a local JSON file containing `{"tool_names": ["actually-observed-tool", "..."]}` — do not use the example names literally — then run:

```bash
python3 tools/specialize.py detect --evidence observed-tools.json
```

Inspect the proposal against the host's documented skill-loading paths, then select explicitly:

```bash
python3 tools/specialize.py build --runtime hermes --output build/hermes-new
python3 tools/specialize.py verify --distribution build/hermes-new
python3 tools/specialize.py install --distribution build/hermes-new \
  --home /confirmed/hermes-home
```

`build` refuses an existing output directory. `--home` is Hermes-only: it writes skills beneath the explicitly selected home (`<home>/skills`). Every other destination must be named with an explicit `--skills-dir`. Optionally add `--runtime-version <observed-version>` to `build` when the version is actually observed; otherwise the installed receipt records it as unreported, not inferred.

For an acknowledged generic baseline (no native loader assumptions, user-selected destination):

```bash
python3 tools/specialize.py build --runtime generic --output build/generic-new
python3 tools/specialize.py verify --distribution build/generic-new
python3 tools/specialize.py install --distribution build/generic-new \
  --skills-dir /confirmed/host-skill-directory --acknowledge-limits
```

Omitting `--acknowledge-limits` on the generic baseline is refused. Installation verifies the exact generated artifact set and hashes, refuses existing `mp-*` skills or a prior `.mp-runtime.json` record in the destination, rolls back its own copies on failure, and reads back every installed file before writing the receipt (`.mp-runtime.json`) at the skills-directory root. The manifest is an integrity record, not a cryptographic signature; trust and review the checkout you install.

**Loading, generation and installation never authorize settings changes, credential/provider changes, external writes, dependency installation, hooks or recurring jobs.** The setup skill (below) configures the project only.

After installation, refresh the host's catalog/session so it discovers the new skills, then verify a named skill actually loads before declaring success.

## The skills

All 27 promoted upstream skills are ported. Upstream's `in-progress/` (6 skills, 13 files) and `misc/` (4 skills, 9 files) categories are deliberately **not** included — they are stashed reference-only under `provenance/reference-only/`, with the decision recorded in `provenance/reference-only-stash.json`. One-line descriptions below are each skill's own core `SKILL.md` description.

**Engineering (20):**

- `mp-ask-matt` — Router: which mp skill fits your situation now.
- `mp-code-review` — Two-axis review (Standards and Spec) since a fixed point.
- `mp-codebase-design` — Shared vocabulary for designing deep modules.
- `mp-diagnosing-bugs` — Disciplined diagnosis loop for hard bugs and regressions.
- `mp-domain-modeling` — Build and sharpen a project's domain model as you design.
- `mp-grill-with-docs` — Grill an idea and build a glossary and ADRs as you go.
- `mp-implement` — Implement a piece of work based on a spec or set of tickets.
- `mp-implement-spec` — Implement the result of mp-to-spec and mp-to-tickets.
- `mp-improve-codebase-architecture` — Find deepening opportunities, report as HTML, grill a pick.
- `mp-pr` — Use when writing a PR body.
- `mp-prototype` — Build a throwaway prototype to answer a design question.
- `mp-research` — Delegate research against primary sources into a cited file.
- `mp-retro` — Improve the agent's environment from a session post-mortem.
- `mp-setup-matt-pocock-skills` — Configure a repo's tracker, triage labels, domain docs.
- `mp-tdd` — Test-driven development: the red-green loop with good tests.
- `mp-to-spec` — Turn the current conversation into a spec and publish it.
- `mp-to-tickets` — Break a plan, spec, or chat into tracer-bullet tickets.
- `mp-triage` — Run issues through triage states; write agent-ready briefs.
- `mp-wayfinder` — Chart huge work as a map of decision tickets, one at a time.
- `mp-wizard` — Generate a bash wizard for steps only a human can do.

**Productivity (7):**

- `mp-grill-me` — A relentless interview to sharpen a plan or design.
- `mp-grilling` — Grill the user relentlessly to stress-test their thinking.
- `mp-handoff` — Compact this session into a handoff doc for the next agent.
- `mp-teach` — Teach the user a new skill or concept in this workspace.
- `mp-to-questionnaire` — Turn an unanswerable decision into a questionnaire.
- `mp-wait-what` — Stop. That last message did not land: re-pitch it.
- `mp-writing-for-agents` — How to write any document an agent consumes.

## Setup flow

`mp-setup-matt-pocock-skills` is the first skill to run in a project adopting this collection. It is prompt-driven, not a script: it explores the repo, presents findings, and asks one section at a time — then writes the per-repo configuration the other engineering skills assume:

- **Issue tracker** (GitHub via `gh`, GitLab via `glab`, local markdown under `.scratch/`, or freeform prose for others) → `docs/agents/issue-tracker.md`, from the seed templates carried inside the skill (`issue-tracker-github.md`, `issue-tracker-gitlab.md`, `issue-tracker-local.md`).
- **Triage labels** — the five canonical role strings, defaulted and changeable in one question → `docs/agents/triage-labels.md`.
- **Domain docs** — where `GLOSSARY.md` and ADRs live and how they are consumed → `docs/agents/domain.md`.

Skills like `mp-to-tickets`, `mp-triage`, `mp-to-spec`, `mp-code-review` and `mp-wayfinder` read that configuration; it is never silently substituted with a default tracker.

The **agent-instruction file is configurable**, not hardcoded: setup asks which file the user's runtime uses (`AGENTS.md`, `CLAUDE.md`, or another name) and edits the one that exists, never assuming a name. All of this configuration lives in **project docs (`docs/agents/*`) and the chosen project file** — not in host/runtime configuration: running these skills does not change Hermes or host settings.

## Uninstalling

Use the **same explicitly confirmed destination** used at install time. Removal is receipt-owned: `.mp-runtime.json` in the skills directory records every owned file's hash.

Preview only (no deletion):

```bash
python3 tools/specialize.py uninstall --home /confirmed/hermes-home
# Or, for an explicitly selected skills directory:
python3 tools/specialize.py uninstall --skills-dir /confirmed/host-skill-directory
```

After the user authorizes removal, apply the preview by adding `--yes`:

```bash
python3 tools/specialize.py uninstall --home /confirmed/hermes-home --yes
```

Uninstall validates every recorded hash and the entire owned directory contents **before any removal**. It refuses: edited, added or missing files; unrecorded directories; symlinks anywhere in the owned tree; and absent, linked, malformed or legacy receipts (an install recorded without per-file hashes cannot be safely removed — use a separately reviewed migration). There is no force option: preserve and review local edits first. Stop active writers of the skill tree during installation or removal; the tool is not a concurrent-writer lock. It stages the validated skills and receipt by rename and restores them if staging fails; a cleanup failure reports the remaining staging path rather than claiming success — inspect and recover staging manually before retrying, as crash-safe recovery is not claimed. Successful removal reads back absence of all owned targets; **unrelated skills, configuration, the parent skill directory, the source checkout and generated build output stay intact**. Skills whose names merely begin with `mp-` but are not in the receipt are never touched. Refresh the host catalog/session afterward.

## Verification

Run the test suite from the checkout (current total: 72 tests, all green; no network, no dependencies):

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

Coverage accounting, as recorded in `provenance/`, is exact:

- **79 promoted files** staged byte-identical under `upstream/mattpocock-skills/` (27 `SKILL.md` entrypoints + 27 `agents/openai.yaml` + 25 carrier files), checked by the test suite against recorded per-file hashes.
- **87 stashed files** held read-only under `provenance/reference-only/`: the 13 in-progress + 9 misc skill files, plus 65 upstream infrastructure files (plugin manifest, changesets, docs tree, install/invocation conventions, the dev-only symlink installer).
- The **remainder of the 172 tracked upstream files** (upstream LICENSE and .gitignore, the release workflow, two dev scripts, one ADR) are accounted only in `provenance/upstream-full-revision-hashes.json`, which records a sha256 for **all 172** tracked files at the pin; the repo-root `LICENSE` is byte-identical to the upstream LICENSE it covers.

Dispositions of all 27 skills — **17 adapted / 5 metadata-only / 5 preserved**, with the two mandated shell carriers (`mp-wizard/template.sh`, `mp-diagnosing-bugs/scripts/hitl-loop.template.sh`) verified byte-identical — live in `provenance/audit-ledger.json` (and its human-readable `.md` twin).

There is no separate verification driver beyond the two commands above: `specialize.py verify --distribution <dir>` checks a generated artifact set against its manifest, and the unit tests cover build/verify/install/uninstall refusals, rollback, exact-set readback, unrelated-state preservation, provenance integrity and disposable repeated install/uninstall cycles. **Live behavioral verification is claim-based**: the test suite proves build/install integrity, not how a model behaves while running a skill.

Local probe/test reports live under `/reports/` (gitignored); none are committed.

## Attribution

- MIT licensed, both upstream and here. Upstream copyright (Matt Pocock) is preserved in `LICENSE` (byte-identical to upstream's) and replicated in every skill's frontmatter: `license: MIT`; `metadata.author` records `Matt Pocock (original), tea24864 (port)`; `metadata.source-revision` records the pinned hash — the same revision pinned in `inventory.json` and across `provenance/`.
- `mp-pr` carries upstream `pr/CREDITS.md` verbatim, crediting Dex Horthy (Humanlayer) for the visual-menu content; do not paraphrase it.
- This project is not affiliated with or endorsed by Matt Pocock.

## Maintenance

- **Never hand-edit** the authored core's `SKILL.md` bodies away from their upstream-derived meaning, the byte-identical `upstream/mattpocock-skills/` snapshot, or `provenance/` hashes. Where a runtime decision is needed, resolve it with an adapter slot at build time, not a prose rewrite. Generated distributions are outputs under `build/` (gitignored) — rebuild and re-verify instead of editing them.
- **Re-pinning upstream:** re-clone the target revision, re-verify every tracked file hash against `provenance/upstream-full-revision-hashes.json`, re-stage the snapshot, update `inventory.json` and `provenance/` (including the audit ledger, whose `corrections` field must record any disposition fix with its rule and evidence), then rerun the full test suite and the build/verify/install cycles above.
- **No GitHub Actions, no npm, no remote publishing.** Reports and local probe transcripts stay gitignored. Behavioral verification remains claim-based unless disposable probe sessions are actually run and reported — failures included.
