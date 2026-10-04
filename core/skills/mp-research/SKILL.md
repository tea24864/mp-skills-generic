---
name: mp-research
description: "Delegate research against primary sources into a cited file."
license: MIT
metadata:
  author: "Matt Pocock (original), tea24864 (port)"
  version: "0.1.0"
  source-revision: "d81f3a183412e71a5b1e84ca21bc1a35eea03a60"
---

Spin up a **background agent** to do the research, so you keep working while it reads.

{{runtime.delegation}}

If independent delegation is unavailable in this runtime, do the same work sequentially in this session, keeping outputs separate and labeled as same-agent perspectives.

Its job:

1. Investigate the question against **primary sources** (official docs, source code, specs, first-party APIs), not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save it where the repo already keeps such notes; match the existing convention, and if there is none, put it somewhere sensible and say where.

