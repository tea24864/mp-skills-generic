# mp-skills-generic: per-skill disposition audit ledger

Generated: 2026-10-03 · Upstream snapshot: mattpocock/skills `d81f3a183412e71a5b1e84ca21bc1a35eea03a60` (v1.3 (merge of PR #1120); package.json says 1.2.3 - version drift, not authoritative)
Scope: 27 promoted skills (20 engineering, 7 productivity), 79 staged files under upstream/mattpocock-skills/skills/. Read-only upstream clone verified byte-identical against the staged snapshot for every file hashed.

- **adapted** — body requires slot insertion and/or runtime-token stripping; meaning preserved
- **preserved** — no runtime dependency found anywhere in the file; body transports verbatim (a uniform port frontmatter envelope - mp- name, license, author/source metadata - is still added at build time and does not count as adaptation)
- **metadata-only** — body is clean; the only runtime-specific content lives in frontmatter (disable-model-invocation / argument-hint), recorded as documented metadata each adapter resolves
- **preserved-byte-identical** — carrier file installed byte-for-byte (verified; wizard/template.sh and diagnosing-bugs/scripts/hitl-loop.template.sh per handoff)
- **adapted-with-parent** — carrier shares the parent skill's runtime constructs and follows the parent's disposition
- **reference-only** — pure reference/seed content with no host tokens of its own; installs with the skill as carried reference, needs no adaptation. NOT the handoff's 'reference-only stash' meaning, which applies to never-installed upstream infra (in reference-only/ infra tree)

## Method

Every one of the 27 SKILL.md files was read in full, plus all 25 non-yaml carrier files (and both shell templates line by line). All 79 staged files were scanned for host-runtime tokens: disable-model-invocation, CLAUDE.md, AGENTS.md, gh <cmd> (strict word-boundary regex; the loose 'gh ' substring had 98 noisy matches incl. 'through'), Skill tool, subagent, sub-agent, Task tool, .claude, .agents, background agent (supplementary).

Token-scan totals: `disable-model-invocation: 16`, `strict gh <cmd> lines: 31`, `Skill tool: 18`, `subagent: 15`, `sub-agent: 21`, `CLAUDE.md: 7`, `AGENTS.md: 11`, `Task tool: 0`, `.claude: 0`, `.agents: 0` (loose `gh ` substring: 98, mostly `through`/`throughout`; the strict regex found 31 real command lines).

Zero hits: Task tool, .claude, .agents — the collection never touches Claude-Code-only cwd/state layout from the text side; `disable-model-invocation` is the only plugin-manifest-coupled construct that reaches skill text (frontmatter only).

## Byte-identity verification (the two mandated carriers)

- `engineering/wizard/template.sh` — prompt-read confirmed, no host-specific tool calls. none required by template design: gh calls are guarded by `command -v gh` with in-script skip recording (SKIPPED array) so the human-run script degrades gracefully without gh. clone↔staged byte-identical: `True` (sha256 `33cbe9dfb1d0e918…`).
- `engineering/diagnosing-bugs/scripts/hitl-loop.template.sh` — prompt-read confirmed, no host-specific tool calls. none (pure bash: tput, read, printf, grep, mktemp; no host-agent API). clone↔staged byte-identical: `True` (sha256 `35103539fc36873e…`).

## Dispositions

| Skill | Bucket | Disposition | Slots needed | Carrier files |
|---|---|---|---|---|
| mp-ask-matt | engineering | **adapted** | skill_loading, delegation, delegation-fallback, history | `PHASE-BOUNDARIES.md` adapted-with-parent |
| mp-code-review | engineering | **adapted** | delegation, delegation-fallback | — |
| mp-codebase-design | engineering | **adapted** | delegation, delegation-fallback | `DEEPENING.md` adapted-with-parent, `DESIGN-IT-TWICE.md` adapted-with-parent |
| mp-diagnosing-bugs | engineering | **preserved** | — | `scripts/hitl-loop.template.sh` preserved-byte-identical |
| mp-domain-modeling | engineering | **preserved** | — | `ADR-FORMAT.md` reference-only, `GLOSSARY-FORMAT.md` reference-only |
| mp-grill-with-docs | engineering | **adapted** | skill_loading | — |
| mp-implement | engineering | **adapted** | skill_loading | — |
| mp-implement-spec | engineering | **adapted** | delegation, delegation-fallback, task_tracking, skill_loading | — |
| mp-improve-codebase-architecture | engineering | **adapted** | delegation, delegation-fallback, skill_loading | `HTML-REPORT.md` reference-only |
| mp-pr | engineering | **preserved** | — | `CREDITS.md` reference-only |
| mp-prototype | engineering | **preserved** | — | `LOGIC.md` reference-only, `UI.md` reference-only |
| mp-research | engineering | **adapted** | delegation, delegation-fallback | — |
| mp-retro | engineering | **adapted** | skill_loading, history, configuration | — |
| mp-setup-matt-pocock-skills | engineering | **adapted** | configuration, integrations | `domain.md` reference-only, `issue-tracker-github.md` reference-only, `issue-tracker-gitlab.md` reference-only, `issue-tracker-local.md` reference-only, `triage-labels.md` reference-only |
| mp-tdd | engineering | **adapted** | skill_loading | `mocking.md` reference-only, `tests.md` reference-only |
| mp-to-spec | engineering | **metadata-only** | — | — |
| mp-to-tickets | engineering | **metadata-only** | — | — |
| mp-triage | engineering | **adapted** | skill_loading | `AGENT-BRIEF.md` adapted-with-parent, `OUT-OF-SCOPE.md` reference-only |
| mp-wayfinder | engineering | **adapted** | delegation, delegation-fallback, task_tracking, skill_loading | — |
| mp-wizard | engineering | **preserved** | — | `template.sh` preserved-byte-identical |
| mp-grill-me | productivity | **adapted** | skill_loading | — |
| mp-grilling | productivity | **adapted** | delegation, delegation-fallback | — |
| mp-handoff | productivity | **adapted** | history, skill_loading | — |
| mp-teach | productivity | **metadata-only** | — | `GLOSSARY-FORMAT.md` reference-only, `LEARNING-RECORD-FORMAT.md` reference-only, `MISSION-FORMAT.md` reference-only, `RESOURCES-FORMAT.md` reference-only |
| mp-to-questionnaire | productivity | **metadata-only** | — | — |
| mp-wait-what | productivity | **metadata-only** | — | — |
| mp-writing-for-agents | productivity | **adapted** | skill_loading, configuration | `SKILL-MECHANICS.md` adapted-with-parent |

Totals: **adapted 17**, **metadata-only 5**, **preserved 5** — 27 skills.

## Per-skill detail

### mp-ask-matt (engineering) — adapted

Carries:
- `PHASE-BOUNDARIES.md` — phase-boundary decision tree the router points at → adapted-with-parent

Runtime-token evidence:
- `engineering/ask-matt/PHASE-BOUNDARIES.md:5` [subagent/sub-agent] “The **phase boundary** is the gap between two phases, and it is the only place this decision belongs. Mid-phase there is no decision to make: continue, or split the work ”
- `engineering/ask-matt/PHASE-BOUNDARIES.md:14` [subagent/sub-agent] “| **Subagent** | Send the task to its own context window and get a report back.     |”
- `engineering/ask-matt/PHASE-BOUNDARIES.md:36` [subagent/sub-agent] “**4. Can the task be done AFK?** Is it scoped tightly enough to run with you away from the keyboard, no steering? Then send it to a **subagent** and leave this session un”
- `engineering/ask-matt/SKILL.md:4` [disable-model-invocation] “disable-model-invocation: true”
- `engineering/ask-matt/SKILL.md:25` [subagent/sub-agent] “- **`/implement-spec`** for the whole spec in one run. It reads the tickets as a **task graph**, runs implementer subagents across the ready **frontier** in parallel, and”
- `engineering/ask-matt/SKILL.md:74` [subagent/sub-agent] “- **Subagent**: send a tightly-scoped task to its own window and get a report back.”
- `engineering/ask-matt/SKILL.md:77` [subagent/sub-agent] “Read [PHASE-BOUNDARIES.md](PHASE-BOUNDARIES.md) for the ordered tree: the five questions, the reasoning behind each branch, and why the primary-source cost makes **Contin”
- `engineering/ask-matt/SKILL.md:86` [background agent] “- **`/research`**: delegate reading legwork to a **background agent**: it investigates a question against **primary sources**, then leaves a cited Markdown file in the re”
- `engineering/ask-matt/SKILL.md:91` [AGENTS.md] “- **`/writing-for-agents`** is the reference for writing documents agents consume: skills, AGENTS.md, pointed-at docs.”

Needs slots: skill_loading, delegation, delegation-fallback, history.

Router must be rewritten to reference mp-* names throughout (handoff design decision 2). Phase-boundary options include /clear, /compact and a subagent hand-off: host motion words that need the history/delegation slots. Smart-zone sizes (~150k) are runtime claims carried in prose.

### mp-code-review (engineering) — adapted

User-config dependencies: docs/agents/issue-tracker.md (written by setup-matt-pocock-skills).

Runtime-token evidence:
- `engineering/code-review/SKILL.md:3` [subagent/sub-agent] “description: "Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow this repo's documented coding st”
- `engineering/code-review/SKILL.md:11` [subagent/sub-agent] “Both axes run as **parallel sub-agents** so they don't pollute each other's context, then this skill aggregates their findings.”
- `engineering/code-review/SKILL.md:23` [subagent/sub-agent] “Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref or empty diff should fail here, not inside two”
- `engineering/code-review/SKILL.md:32` [subagent/sub-agent] “4. If nothing is found, ask the user where the spec is. If they say there isn't one, the **Spec** sub-agent will skip and report "no spec available".”
- `engineering/code-review/SKILL.md:58` [subagent/sub-agent] “### 4. Spawn both sub-agents in parallel”
- `engineering/code-review/SKILL.md:60` [subagent/sub-agent] “**Standards sub-agent prompt** should include:”
- `engineering/code-review/SKILL.md:63` [subagent/sub-agent] “- The list of standards-source files you found in step 3, **plus the smell baseline from step 3** pasted in full (the sub-agent has no other access to it).”
- `engineering/code-review/SKILL.md:66` [subagent/sub-agent] “**Spec sub-agent prompt** should include:”
- `engineering/code-review/SKILL.md:72` [subagent/sub-agent] “If the spec is missing, skip the Spec sub-agent and note this in the final report.”

Needs slots: delegation, delegation-fallback.

Defining behavior is two parallel sub-agents re-aggregated; needs a delegation slot plus an explicit sequential fallback (run Standards then Spec in one context, same-model caveat). Insists the fixed point resolves before spawning, so the fallback differs from the parallel path only in execution, not in findings format.

### mp-codebase-design (engineering) — adapted

Carries:
- `DEEPENING.md` — dependency categories, seam discipline, replace-don't-layer testing → adapted-with-parent
- `DESIGN-IT-TWICE.md` — parallel 3+ sub-agent design pattern → adapted-with-parent

User-config dependencies: GLOSSARY.md / docs/adr/ (created lazily by domain-modeling).

Runtime-token evidence:
- `engineering/codebase-design/DESIGN-IT-TWICE.md:3` [subagent/sub-agent] “When the user wants to explore alternative interfaces for a chosen deepening candidate, use this parallel sub-agent pattern. Based on "Design It Twice" (Ousterhout): your”
- `engineering/codebase-design/DESIGN-IT-TWICE.md:11` [subagent/sub-agent] “Before spawning sub-agents, write a user-facing explanation of the problem space for the chosen candidate:”
- `engineering/codebase-design/DESIGN-IT-TWICE.md:17` [subagent/sub-agent] “Show this to the user, then immediately proceed to Step 2. The user reads and thinks while the sub-agents work in parallel.”
- `engineering/codebase-design/DESIGN-IT-TWICE.md:19` [subagent/sub-agent] “### 2. Spawn sub-agents”
- `engineering/codebase-design/DESIGN-IT-TWICE.md:21` [subagent/sub-agent] “Spawn 3+ sub-agents in parallel. Each must produce a **radically different** interface for the deepened module.”
- `engineering/codebase-design/DESIGN-IT-TWICE.md:23` [subagent/sub-agent] “Prompt each sub-agent with a separate technical brief (file paths, coupling details, dependency category from [DEEPENING.md](DEEPENING.md), what sits behind the seam). Th”
- `engineering/codebase-design/DESIGN-IT-TWICE.md:30` [subagent/sub-agent] “Include both [SKILL.md](SKILL.md) vocabulary and GLOSSARY.md vocabulary in the brief so each sub-agent names things consistently with the architecture language and the pr”
- `engineering/codebase-design/DESIGN-IT-TWICE.md:32` [subagent/sub-agent] “Each sub-agent outputs:”
- `engineering/codebase-design/SKILL.md:114` [subagent/sub-agent] “- **Exploring alternative interfaces**, see [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md): spin up parallel sub-agents to design the interface several radically different ways”

Needs slots: delegation, delegation-fallback.

SKILL.md is pure vocabulary; the coupling is only the 'Going deeper' pointer to DESIGN-IT-TWICE's parallel sub-agents. DEEPENING.md itself is token-free (could ride as reference-only); DESIGN-IT-TWICE.md delegates for its entire step 2 and must gain the serial fallback.

### mp-diagnosing-bugs (engineering) — preserved

Carries:
- `scripts/hitl-loop.template.sh` — human-in-the-loop replay script the agent edits and runs → preserved-byte-identical

Needs slots: none beyond the mechanical mp- prefix rewrite.

Phases presume only file/terminal tools plus git bisect, curl, a headless browser - all user toolchain, no host API. Byte-identity claim for the HITL template verified (no host-specific tool calls; pure bash read/printf).

### mp-domain-modeling (engineering) — preserved

Carries:
- `ADR-FORMAT.md` — ADR template and offering rules → reference-only
- `GLOSSARY-FORMAT.md` — glossary structure and rules → reference-only

User-config dependencies: GLOSSARY.md / GLOSSARY-MAP.md / docs/adr/ (it creates them lazily inside the project).

Needs slots: none beyond the mechanical mp- prefix rewrite.

Writes only inside the project (GLOSSARY.md, docs/adr/). No host tokens anywhere in SKILL.md or its carriers.

### mp-grill-with-docs (engineering) — adapted

User-config dependencies: GLOSSARY.md / docs/adr/ (via domain-modeling side effects).

Runtime-token evidence:
- `engineering/grill-with-docs/SKILL.md:4` [disable-model-invocation] “disable-model-invocation: true”
- `engineering/grill-with-docs/SKILL.md:7` [Skill tool] “Call the Skill tool twice, for "grilling" and "domain-modeling".”

Needs slots: skill_loading.

One-line router whose body IS a Skill-tool invocation (grilling + domain-modeling): the invocation sentence is the whole runtime dependence.

### mp-implement (engineering) — adapted

User-config dependencies: spec/tickets supplied by the user.

Runtime-token evidence:
- `engineering/implement/SKILL.md:4` [disable-model-invocation] “disable-model-invocation: true”

Needs slots: skill_loading.

Tiny runner; body references /tdd and /code-review by name (prefixed mechanically at build). Commits to the current branch. No other tokens.

### mp-implement-spec (engineering) — adapted

User-config dependencies: issue tracker config; worktree-capable git.

Runtime-token evidence:
- `engineering/implement-spec/SKILL.md:4` [disable-model-invocation] “disable-model-invocation: true”
- `engineering/implement-spec/SKILL.md:15` [subagent/sub-agent] “Communication to and from subagents should be sparse. Communicate primarily through **context pointers**: to the spec, tickets, research notes, and previous commits. Don'”
- `engineering/implement-spec/SKILL.md:17` [subagent/sub-agent] “**Implementer subagents** should be run in the background where possible for maximum concurrency.”
- `engineering/implement-spec/SKILL.md:23` [subagent/sub-agent] “2. (optional) Use an **exploration subagent** to conduct any exploration required by the tickets - relevant codebase files or external documentation. Ensure the explorati”
- `engineering/implement-spec/SKILL.md:27` [subagent/sub-agent] “4. Use **implementer subagents** to implement each ticket, each in its own worktree on its own branch. Each implementer subagent:”
- `engineering/implement-spec/SKILL.md:29` [Skill tool] “- calls the Skill tool with `tdd` to build the ticket;”
- `engineering/implement-spec/SKILL.md:32` [subagent/sub-agent] “5. Once an **implementer subagent** completes, merge its work to the integration branch with a **merger subagent**.”
- `engineering/implement-spec/SKILL.md:34` [subagent/sub-agent] “6. If this changes the **frontier** of available tickets, kick off more **implementer subagents** to work on the new tickets. This allows for maximum concurrency.”
- `engineering/implement-spec/SKILL.md:36` [Skill tool] “7. Once all tickets are complete, call the Skill tool with `code-review` on the integration branch. Fix all issues raised by the code review in a single **implementer sub”
- `engineering/implement-spec/SKILL.md:36` [subagent/sub-agent] “7. Once all tickets are complete, call the Skill tool with `code-review` on the integration branch. Fix all issues raised by the code review in a single **implementer sub”
- `engineering/implement-spec/SKILL.md:40` [subagent/sub-agent] “9. Clean up all **implementer subagent** worktrees.”

Needs slots: delegation, delegation-fallback, task_tracking, skill_loading.

Highest runtime dependence after wayfinder: background implementer subagents, explorer subagent with a notes dir outside the repo, merger subagent, Skill-tool calls into tdd/code-review, worktrees per ticket. Needs the delegation slot, a task_tracking slot for frontier semantics, and an explicit serial fallback (one ticket at a time in-session, frontier order preserved).

### mp-improve-codebase-architecture (engineering) — adapted

Carries:
- `HTML-REPORT.md` — HTML report scaffold, diagram patterns, style guide → reference-only

User-config dependencies: GLOSSARY.md / docs/adr/ (read opportunistically).

Runtime-token evidence:
- `engineering/improve-codebase-architecture/SKILL.md:4` [disable-model-invocation] “disable-model-invocation: true”
- `engineering/improve-codebase-architecture/SKILL.md:13` [Skill tool] “- Call the Skill tool with "codebase-design" for the architecture vocabulary (**module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality**) and”
- `engineering/improve-codebase-architecture/SKILL.md:27` [subagent/sub-agent] “Then spawn a sub-agent to walk the codebase. Don't follow rigid heuristics; explore organically and note where you experience friction:”
- `engineering/improve-codebase-architecture/SKILL.md:64` [Skill tool] “Once the user picks a candidate, call the Skill tool with "grilling" to walk the decision tree with them: constraints, dependencies, the shape of the deepened module, wha”
- `engineering/improve-codebase-architecture/SKILL.md:66` [Skill tool] “Side effects happen inline as decisions crystallize; call the Skill tool with "domain-modeling" to keep the domain model current as you go:”
- `engineering/improve-codebase-architecture/SKILL.md:71` [Skill tool] “- **Want to explore alternative interfaces for the deepened module?** Call the Skill tool with "codebase-design" and use its design-it-twice parallel sub-agent pattern.”
- `engineering/improve-codebase-architecture/SKILL.md:71` [subagent/sub-agent] “- **Want to explore alternative interfaces for the deepened module?** Call the Skill tool with "codebase-design" and use its design-it-twice parallel sub-agent pattern.”

Needs slots: delegation, delegation-fallback, skill_loading.

Skill-tool calls (codebase-design, grilling, domain-modeling), a spawned codebase-walker sub-agent, and design-it-twice sub-agents. Writes a self-contained HTML report to the OS temp dir and opens it (xdg-open/open/start) - benign, user-facing, recorded as side-effect evidence rather than a portability blocker. Serial fallback: walker and design-it-twice run inline.

### mp-pr (engineering) — preserved

Carries:
- `CREDITS.md` — attribution to Dex Horthy / Humanlayer for the visual-menu content - preserve verbatim → reference-only

User-config dependencies: GLOSSARY.md (domain language for the body).

Needs slots: none beyond the mechanical mp- prefix rewrite.

Pure PR-body template; CREDITS.md travels with it and must not be paraphrased (handoff requirement to preserve the credit).

### mp-prototype (engineering) — preserved

Carries:
- `LOGIC.md` — logic/state-machine prototype branch → reference-only
- `UI.md` — UI-prototype branch (variants on a route) → reference-only

Needs slots: none beyond the mechanical mp- prefix rewrite.

Throwaway-code discipline names only project tooling. UI.md's framework examples (Next router, process.env.NODE_ENV) are project-level, not host-runtime.

### mp-research (engineering) — adapted

Runtime-token evidence:
- `engineering/research/SKILL.md:3` [background agent] “description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched”
- `engineering/research/SKILL.md:6` [background agent] “Spin up a **background agent** to do the research, so you keep working while it reads.”

Needs slots: delegation, delegation-fallback.

The entire skill is 'spin up a background agent'. Needs the delegation slot plus a trivial serial fallback (do the reading inline in this session, still write the cited markdown file into the repo).

### mp-retro (engineering) — adapted

User-config dependencies: session log / transcript location (host-specific); repo steering files; name of the repo's own agent-instruction file.

Runtime-token evidence:
- `engineering/retro/SKILL.md:4` [disable-model-invocation] “disable-model-invocation: true”
- `engineering/retro/SKILL.md:11` [Skill tool] “1. Call the Skill tool with `writing-for-agents` for the writing style guide.”
- `engineering/retro/SKILL.md:20` [AGENTS.md] “- **Global AGENTS.md**: are there any steering instructions that should be moved to coding standards (or automated checks) instead? _Use when_ the AGENTS.md file is parti”
- `engineering/retro/SKILL.md:41` [CLAUDE.md] “- `CLAUDE.md`/`AGENTS.md`: these files are pushed to the context window of any agent working in this repo. They should be used incredibly sparingly, usually only for **na”
- `engineering/retro/SKILL.md:41` [AGENTS.md] “- `CLAUDE.md`/`AGENTS.md`: these files are pushed to the context window of any agent working in this repo. They should be used incredibly sparingly, usually only for **na”

Needs slots: skill_loading, history, configuration.

Skill-tool call into writing-for-agents; reads session logs on the host (history slot); its candidate category 'Global AGENTS.md' hardcodes AGENTS.md and needs the same configurable-instruction-file treatment as setup-matt-pocock-skills (configuration slot).

### mp-setup-matt-pocock-skills (engineering) — adapted

Carries:
- `domain.md` — domain-doc consumer rules seed template → reference-only
- `issue-tracker-github.md` — GitHub tracker seed template → reference-only
- `issue-tracker-gitlab.md` — GitLab tracker seed template → reference-only
- `issue-tracker-local.md` — local-markdown tracker seed template → reference-only
- `triage-labels.md` — triage label mapping seed template → reference-only

User-config dependencies: user choice of issue tracker (GitHub/GitLab/local/other); user choice of agent-instruction file; whether the triage skill is installed.

Runtime-token evidence:
- `engineering/setup-matt-pocock-skills/SKILL.md:4` [disable-model-invocation] “disable-model-invocation: true”
- `engineering/setup-matt-pocock-skills/SKILL.md:24` [CLAUDE.md] “- `AGENTS.md` and `CLAUDE.md` at the repo root: does either exist? Is there already an `## Agent skills` section in either?”
- `engineering/setup-matt-pocock-skills/SKILL.md:24` [AGENTS.md] “- `AGENTS.md` and `CLAUDE.md` at the repo root: does either exist? Is there already an `## Agent skills` section in either?”
- `engineering/setup-matt-pocock-skills/SKILL.md:40` [gh <cmd>] “> Explainer: The "issue tracker" is where issues live for this repo. Skills like `to-tickets`, `triage`, and `to-spec` read from and write to it. They need to know whethe”
- `engineering/setup-matt-pocock-skills/SKILL.md:67` [CLAUDE.md] “- The `## Agent skills` block to add to whichever of `CLAUDE.md` / `AGENTS.md` is being edited (see step 4 for selection rules)”
- `engineering/setup-matt-pocock-skills/SKILL.md:67` [AGENTS.md] “- The `## Agent skills` block to add to whichever of `CLAUDE.md` / `AGENTS.md` is being edited (see step 4 for selection rules)”
- `engineering/setup-matt-pocock-skills/SKILL.md:76` [CLAUDE.md] “- If `CLAUDE.md` exists, edit it.”
- `engineering/setup-matt-pocock-skills/SKILL.md:77` [AGENTS.md] “- Else if `AGENTS.md` exists, edit it.”
- `engineering/setup-matt-pocock-skills/SKILL.md:80` [CLAUDE.md] “Never create `AGENTS.md` when `CLAUDE.md` already exists (or vice versa); always edit the one that's already there.”
- `engineering/setup-matt-pocock-skills/SKILL.md:80` [AGENTS.md] “Never create `AGENTS.md` when `CLAUDE.md` already exists (or vice versa); always edit the one that's already there.”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:7` [gh <cmd>] “- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:8` [gh <cmd>] “- **Read an issue**: `gh issue view <number> --comments`, filtering comments by `jq` and also fetching labels.”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:9` [gh <cmd>] “- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:10` [gh <cmd>] “- **Comment on an issue**: `gh issue comment <number> --body "..."`”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:11` [gh <cmd>] “- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:12` [gh <cmd>] “- **Close**: `gh issue close <number> --comment "..."`”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:20` [gh <cmd>] “When set to `yes`, PRs run through the same labels and states as issues, using the `gh pr` equivalents:”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:22` [gh <cmd>] “- **Read a PR**: `gh pr view <number> --comments` and `gh pr diff <number>` for the diff.”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:23` [gh <cmd>] “- **List external PRs for triage**: `gh pr list --state open --json number,title,body,labels,author,authorAssociation,comments` then keep only `authorAssociation` of `CON”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:24` [gh <cmd>] “- **Comment / label / close**: `gh pr comment`, `gh pr edit --add-label`/`--remove-label`, `gh pr close`.”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:26` [gh <cmd>] “GitHub shares one number space across issues and PRs, so a bare `#42` may be either: resolve with `gh pr view 42` and fall back to `gh issue view 42`.”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:34` [gh <cmd>] “Run `gh issue view <number> --comments`.”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:40` [gh <cmd>] “- **Map**: a single issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body. `gh issue create --label wayfinder:map`.”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:41` [gh <cmd>] “- **Child ticket**: an issue linked to the map as a GitHub sub-issue (`gh api` on the sub-issues endpoint). Where sub-issues aren't enabled, add the child to a task list ”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:42` [gh <cmd>] “- **Blocking**: GitHub's **native issue dependencies**, the canonical, UI-visible representation. Add an edge with `gh api --method POST repos/<owner>/<repo>/issues/<chil”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:43` [gh <cmd>] “- **Frontier query**: list the map's open children (`gh issue list --state open`, scoped to the map's sub-issues / task list), drop any with an open blocker (`issue_depen”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:44` [gh <cmd>] “- **Claim**: `gh issue edit <n> --add-assignee @me`, the session's first write.”
- `engineering/setup-matt-pocock-skills/issue-tracker-github.md:45` [gh <cmd>] “- **Resolve**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then append a context pointer (gist + link) to the map's Decisions-so-far.”
- `engineering/setup-matt-pocock-skills/issue-tracker-gitlab.md:13` [gh <cmd>] “- **Merge requests**: GitLab calls PRs "merge requests". Use `glab mr create`, `glab mr view`, `glab mr note`, etc., the same shape as `gh pr ...` with `mr` in place of `”

Needs slots: configuration, integrations.

Step 4 hardcodes CLAUDE.md/AGENTS.md with edit-if-exists rules. Per handoff decision, the agent-instruction file must become a configurable (user-named) file, not a hardcoded pair. gh/glab commands live inside the seed templates by design: they are the per-tracker configuration the user chose, so they travel reference-only, not as core prose.

### mp-tdd (engineering) — adapted

Carries:
- `mocking.md` — when/what to mock at system boundaries → reference-only
- `tests.md` — good vs bad test examples → reference-only

User-config dependencies: GLOSSARY.md / docs/adr/ (read opportunistically).

Runtime-token evidence:
- `engineering/tdd/SKILL.md:26` [Skill tool] “When the shape of that interface is itself in question (how deep the module is, where the seam belongs, what the interface should expose), call the Skill tool with "codeb”

Needs slots: skill_loading.

Single Skill-tool call into codebase-design when the seam shape itself is the question. Everything else is neutral method.

### mp-to-spec (engineering) — metadata-only

User-config dependencies: issue tracker config; triage label vocabulary.

Runtime-token evidence:
- `engineering/to-spec/SKILL.md:4` [disable-model-invocation] “disable-model-invocation: true”

Needs slots: none beyond the mechanical mp- prefix rewrite.

Body is a clean spec template; the only runtime content is frontmatter (disable-model-invocation) plus the configured-tracker/triage-label dependency it states in prose.

### mp-to-tickets (engineering) — metadata-only

User-config dependencies: issue tracker config (native blocking vs .scratch/ file convention); triage label vocabulary.

Runtime-token evidence:
- `engineering/to-tickets/SKILL.md:4` [disable-model-invocation] “disable-model-invocation: true”

Needs slots: none beyond the mechanical mp- prefix rewrite.

Body already handles both tracker shapes (local file per ticket / native blocking links). Frontmatter DMI is the only host-coupled part.

### mp-triage (engineering) — adapted

Carries:
- `AGENT-BRIEF.md` — agent-brief writing principles and templates → adapted-with-parent
- `OUT-OF-SCOPE.md` — .out-of-scope/ knowledge-base format and flow → reference-only

User-config dependencies: issue tracker config; triage label mapping; .out-of-scope/ knowledge base; external-PR surface flag.

Runtime-token evidence:
- `engineering/triage/AGENT-BRIEF.md:32` [gh <cmd>] “- **Good:** "Running `gh issue list --label needs-triage` returns issues that have been through initial classification"”
- `engineering/triage/SKILL.md:4` [disable-model-invocation] “disable-model-invocation: true”
- `engineering/triage/SKILL.md:76` [Skill tool] “4. **Grill (if needed).** If the request needs fleshing out, call the Skill tool twice, for "grilling" and "domain-modeling", and grill it into shape a round of questions”

Needs slots: skill_loading.

Skill-tool calls (grilling, domain-modeling) when grilling is needed. AGENT-BRIEF.md quotes one gh-based acceptance-criterion example - tracker-flavoured, rides the parent's adapted disposition. OUT-OF-SCOPE.md is token-free reference.

### mp-wayfinder (engineering) — adapted

User-config dependencies: issue tracker's 'Wayfinding operations' section (map, child tickets, blocking, frontier, claim, resolve).

Runtime-token evidence:
- `engineering/wayfinder/SKILL.md:4` [disable-model-invocation] “disable-model-invocation: true”
- `engineering/wayfinder/SKILL.md:77` [Skill tool] “- **Research** (AFK): Reading documentation, third-party APIs, or local resources like knowledge bases to surface a fact a decision waits on. Resolved by a subagent that ”
- `engineering/wayfinder/SKILL.md:77` [subagent/sub-agent] “- **Research** (AFK): Reading documentation, third-party APIs, or local resources like knowledge bases to surface a fact a decision waits on. Resolved by a subagent that ”
- `engineering/wayfinder/SKILL.md:78` [Skill tool] “- **Prototype** (HITL): Raise the fidelity of the discussion by making a cheap, rough, concrete artifact to react to (an outline, a rough take, a stub, or UI/logic code) ”
- `engineering/wayfinder/SKILL.md:79` [Skill tool] “- **Grilling** (HITL): Conversation. The default case. Always call the Skill tool twice, for "grilling" and "domain-modeling".”
- `engineering/wayfinder/SKILL.md:111` [Skill tool] “1. **Name the destination.** Call the Skill tool twice, for "grilling" and "domain-modeling", to pin down what this map is finding its way to: the spec, decision, or chan”
- `engineering/wayfinder/SKILL.md:115` [Skill tool] “5. **Fire the research subagents.** For each `research` ticket you just created, spin up a subagent that calls the Skill tool with "research" to resolve it in parallel, c”
- `engineering/wayfinder/SKILL.md:115` [subagent/sub-agent] “5. **Fire the research subagents.** For each `research` ticket you just created, spin up a subagent that calls the Skill tool with "research" to resolve it in parallel, c”
- `engineering/wayfinder/SKILL.md:124` [Skill tool] “3. Resolve it. **Zoom as needed**: fetch the full body of any related or closed ticket on demand; call the Skill tool for whichever skills the `## Notes` block names. If ”

Needs slots: delegation, delegation-fallback, task_tracking, skill_loading.

Research tickets resolve via subagents calling the Skill tool with research; grilling/prototype tickets are Skill-tool calls; map/child/blocking/frontier physical shape is tracker-owned. Needs delegation + serial fallback (resolve research tickets inline) and the task_tracking slot for frontier semantics.

### mp-wizard (engineering) — preserved

Carries:
- `template.sh` — generated-wizard bash library incl. ask_secret/write_env/set_secret/set_var → preserved-byte-identical

User-config dependencies: gh availability only inside the human-run script (with in-script graceful skip).

Runtime-token evidence:
- `engineering/wizard/SKILL.md:10` [gh <cmd>] “The delightful UX is already solved by [template.sh](template.sh): stage-by-stage progress, confirmation gates, cross-platform URL opening (including WSL), hidden secret ”
- `engineering/wizard/template.sh:29` [gh <cmd>] “SKIPPED=()        # things we couldn't do (e.g. gh missing)”
- `engineering/wizard/template.sh:142` [gh <cmd>] “# to a warning (and records it) if gh is unavailable or unauthenticated.”
- `engineering/wizard/template.sh:145` [gh <cmd>] “if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then”
- `engineering/wizard/template.sh:146` [gh <cmd>] “if printf '%s' "$value" | gh secret set "$name" >/dev/null 2>&1; then”
- `engineering/wizard/template.sh:152` [gh <cmd>] “SKIPPED+=("GitHub secret $name (set it manually: gh secret set $name)")”
- `engineering/wizard/template.sh:153` [gh <cmd>] “warn "skipped GitHub secret $name: gh not ready; set it later"”
- `engineering/wizard/template.sh:159` [gh <cmd>] “if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then”
- `engineering/wizard/template.sh:160` [gh <cmd>] “if gh variable set "$name" --body "$value" >/dev/null 2>&1; then”
- `engineering/wizard/template.sh:166` [gh <cmd>] “warn "skipped GitHub variable $name, gh not ready; set it later"”

Needs slots: none beyond the mechanical mp- prefix rewrite.

Genuinely agent-neutral: the agent only authors stages; the human runs the script in their terminal. template.sh touches gh only behind command -v guards with SKIPPED recording. Byte-identity verified.

### mp-grill-me (productivity) — adapted

Runtime-token evidence:
- `productivity/grill-me/SKILL.md:4` [disable-model-invocation] “disable-model-invocation: true”
- `productivity/grill-me/SKILL.md:7` [Skill tool] “Call the Skill tool with "grilling".”

Needs slots: skill_loading.

One-line router: body is a Skill-tool invocation with 'grilling'.

### mp-grilling (productivity) — adapted

Runtime-token evidence:
- `productivity/grilling/SKILL.md:26` [subagent/sub-agent] “Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don'”

Needs slots: delegation, delegation-fallback.

'Finding facts is your job': a frontier question may dispatch a sub-agent to look things up while the interview continues. Needs the delegation slot with a serial fallback (perform the lookup with own file/terminal tools; only questions downstream of the fact wait).

### mp-handoff (productivity) — adapted

User-config dependencies: OS temp-dir convention; next agent's available skill roster.

Runtime-token evidence:
- `productivity/handoff/SKILL.md:4` [argument-hint] “argument-hint: "What will the next session be used for?"”
- `productivity/handoff/SKILL.md:5` [disable-model-invocation] “disable-model-invocation: true”
- `productivity/handoff/SKILL.md:10` [Skill tool] “Include a "suggested skills" section in the document, naming which skills the next agent should call the Skill tool for.”

Needs slots: history, skill_loading.

Writes a handoff doc to the OS temporary directory, deliberately outside the workspace (recorded as an out-of-project side effect; per handoff scope rules this is intended behaviour, upstream-authored, question-free). 'Suggested skills' section reaches the Skill tool by name.

### mp-teach (productivity) — metadata-only

Carries:
- `GLOSSARY-FORMAT.md` — teaching-workspace glossary format → reference-only
- `LEARNING-RECORD-FORMAT.md` — learning-record format and triggers → reference-only
- `MISSION-FORMAT.md` — mission statement format → reference-only
- `RESOURCES-FORMAT.md` — trusted resources + communities format → reference-only

User-config dependencies: all state lives in the current workspace (MISSION.md, lessons/, reference/, learning-records/, assets/, NOTES.md).

Runtime-token evidence:
- `productivity/teach/SKILL.md:4` [disable-model-invocation] “disable-model-invocation: true”
- `productivity/teach/SKILL.md:5` [argument-hint] “argument-hint: "What would you like to learn about?"”

Needs slots: none beyond the mechanical mp- prefix rewrite.

Stateful but entirely in-project. 'Open the lesson by running a CLI command' is generic. Frontmatter carries disable-model-invocation + argument-hint (adapter metadata). Four format files are pure reference.

### mp-to-questionnaire (productivity) — metadata-only

Runtime-token evidence:
- `productivity/to-questionnaire/SKILL.md:4` [disable-model-invocation] “disable-model-invocation: true”

Needs slots: none beyond the mechanical mp- prefix rewrite.

Writes one markdown file in the current directory. Frontmatter DMI only.

### mp-wait-what (productivity) — metadata-only

User-config dependencies: GLOSSARY.md / GLOSSARY-MAP.md (optional, read if present).

Runtime-token evidence:
- `productivity/wait-what/SKILL.md:4` [disable-model-invocation] “disable-model-invocation: true”

Needs slots: none beyond the mechanical mp- prefix rewrite.

One-paragraph corrective; frontmatter DMI only.

### mp-writing-for-agents (productivity) — adapted

Carries:
- `SKILL-MECHANICS.md` — frontmatter, invocation choice, router-skill mechanics → adapted-with-parent

User-config dependencies: the repo's agent-instruction file name (generic examples name AGENTS.md/CLAUDE.md).

Runtime-token evidence:
- `productivity/writing-for-agents/SKILL-MECHANICS.md:9` [disable-model-invocation] “- A **model-invoked** skill keeps a `description`, so the agent can fire it autonomously, and other skills can reach it. You can still type its name: model-invocation alw”
- `productivity/writing-for-agents/SKILL-MECHANICS.md:10` [disable-model-invocation] “- A **user-invoked** skill strips the description from the agent's reach: only the human typing its name can invoke it, and no other skill can. Zero context load, but it ”
- `productivity/writing-for-agents/SKILL.md:3` [CLAUDE.md] “description: Writing documents for agents. Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md.”
- `productivity/writing-for-agents/SKILL.md:3` [AGENTS.md] “description: Writing documents for agents. Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md.”
- `productivity/writing-for-agents/SKILL.md:6` [CLAUDE.md] “Reference for writing any document an agent consumes: a skill, an `AGENTS.md` / `CLAUDE.md`, a doc reached by a pointer. The packaging differs; the writing does not: the ”
- `productivity/writing-for-agents/SKILL.md:6` [AGENTS.md] “Reference for writing any document an agent consumes: a skill, an `AGENTS.md` / `CLAUDE.md`, a doc reached by a pointer. The packaging differs; the writing does not: the ”
- `productivity/writing-for-agents/SKILL.md:12` [AGENTS.md] “A **context pointer** is a reference held in the agent's context that names some out-of-context material and encodes the condition for reaching it. A skill's description ”
- `productivity/writing-for-agents/SKILL.md:24` [AGENTS.md] “- **Context load** is the cost of always-loaded material on the agent's window: an `AGENTS.md` line, a skill description, anything sitting in context every turn, spending”
- `productivity/writing-for-agents/SKILL.md:49` [subagent/sub-agent] “- **Clarity**: can the agent tell done from not-done? A vague bound ("understanding reached") invites **premature completion**: ending the step before it is genuinely don”

Needs slots: skill_loading, configuration.

No delegation. Its examples and SKILL-MECHANICS.md lean on upstream frontmatter semantics (disable-model-invocation as the invocation switch, description-stripping). Adaptation: generalize the agent-instruction-file naming and record invocation flags as documented metadata each adapter resolves; meaning preserved.

## Findings

### Cleanest skills (preserved)

**diagnosing-bugs, domain-modeling, pr, prototype, wizard**. Genuine zero-adaptation bodies: the skill text never names a host tool. Notably, the collection's two most complex skills (diagnosing-bugs, wizard) are its cleanest — the human/user side carries all the tool burden. domain-modeling and pr write pilot-side artifact rules only; pr's `CREDITS.md` must ride verbatim (attribution obligation).

### Which skills need delegation slots

| Skill | Why | Serial fallback requirement |
|---|---|---|
| wayfinder | research tickets fire subagents calling Skill tool with "research"; grilling/prototype tickets are Skill-tool calls | resolve research tickets inline in one session when no delegation means exists — meaning preserved, map semantics unchanged |
| implement-spec | background implementer subagents, explorer subagent, merger subagent, worktrees per ticket | one ticket at a time in-session, frontier order preserved, task graph still explicit |
| code-review | the two-axis split is *implemented as* two parallel sub-agents; aggregation is the skill's deliverable | sequential lenses in one context with a same-model caveat, fold-then-report rather than aggregate from separate reports |
| codebase-design (DESIGN-IT-TWICE.md) | stripes 3+ parallel design sub-agents | design sequentially one after another, same comparison rubric (depth/locality/seam placement) |
| grilling | fact-finding sub-agents dispatched mid-interview | perform the lookup with own file/terminal tools, block only downstream questions |
| research | the whole skill is a background-agent dispatch | do the reading inline, still write the cited markdown into the repo |
| ask-matt / improve-codebase-architecture | router + phase-boundary trees reference Subagent as one of five boundary options; walker-isolated scan is a sub-agent | not standalone skills — the fallback rides whichever delegation slot the adapter provides (or "no subagent support: pick Continue | /handoff | /compact only") |

### Surprises vs. the handoff's expectations

1. **wizard is even more portable than the handoff's byte-identical claim implies** — not just agent-neutral, but the gh-calling helpers inside template.sh are already degradation-safe (`command -v gh` guards + SKIPPED recording). No port changes needed to keep it byte-identical.
2. **retro hardcodes AGENTS.md in a category name** — the handoff flagged setup-matt-pocock-skills for the configurable-instruction-file treatment, but retro's step-3 category “Global AGENTS.md” is a second site with the same problem (it should read “the user's global agent-instruction file”). Easy slot fix; easy to miss because the mention is a category label, not an instruction.
3. **writing-for-agents' SKILL-MECHANICS.md teaches upstream's own frontmatter semantics** (`disable-model-invocation` as the invocation switch, description-stripping on user-invoked skills). It cannot be transported verbatim: the section *is* an upstream-runtime feature list. Adaptation must rewrite it as runtime-neutral invocation-mode principles plus per-adapter metadata, or the port will concentrate unportable semantics in its self-reference document.
4. **to-spec and to-tickets dropped to metadata-only**, below the handoff's implicit “everything reads OK” bar — their bodies are genuinely clean (to-tickets even pre-handles native-blocking vs. local-file shape itself), so only frontmatter DMI plus the mechanical tracker dependency remain.
5. **teach is metadata-only, not preserved** — the handoff mentions it as productivity statefulness, but the audit found no runtime constructs at all outside frontmatter; it missed the preserved pile only because its frontmatter carries DMI + argument-hint, which are exactly the adapter-injected metadata category.
6. **grill-me and grill-with-docs cannot be preserved** — their *entire bodies* are Skill-tool invocations. The handoff didn't flag them (it flagged wayfinder/implement-spec/code-review/DESIGN-IT-TWICE); a one-line “call the Skill tool with X” renderer that reduces to a single sentence needs the skill_loading slot to say it host-neutrally.
7. **hitl-loop.template.sh is byte-identical, but hitl provision is singleton** — it is the only thing making diagnosing-bugs require any carrier handling at all. Everything else in that skill is genuinely neutral. Good confirmation that the handoff's fingerprint was right.
8. **26/27 forced-name consistency, no silent collision** — the ONLY skill whose mp- name needed thought was setup-matt-pocock-skills (see naming_review in audit-ledger.json); all others take mp- mechanically. Nothing in the actual text argues for or against a shorter alias.

### Where the handoff's predicted disposition seems wrong (based on actual text)

- **codebase-design is less coupled than the handoff implies** — the handoff lists codebase-design among “needs delegation slots”, but the SKILL.md body itself is pure vocabulary with zero runtime tokens; only its DESIGN-IT-TWICE.md carrier carries delegation. The slot need is real but lives entirely in the carrier; the core could in principle be preserved with the carrier adapted. Keeping both at `adapted` is still the right call (the Going-deeper cross-reference means the two can't split dispositions), but the parent should know the trait is carrier-local, not skill-wide.
- **retro is more coupled than the handoff implies** — the handoff's “skills needing dedicated attention” list does not include retro, but it contains (a) a Skill-tool call, (b) host-session-log access (the history slot), (c) hardcoded AGENTS.md in a category name. Its slot list is longer than several skills the handoff did flag.
- **implement-spec and wayfinder confirmed as the two heaviest**, exactly as the handoff predicted — 11 and 7 evidence lines respectively, with implement-spec additionally needing the task_tracking slot for frontier walks and a worktree discipline the generic host may not have.

### Skills where no handoff attention was needed but the audit still notes runtime content

No additional skill produced a mid-severity rating. `handoff` deliberately writes outside the project (OS temp dir) — upstream-authored and intentional per the handoff's scope rules, but recorded as the one deliberate out-of-project side effect in the promoted set. `teach`'s “open the lesson by running a CLI command” is generic, not host-specific.
