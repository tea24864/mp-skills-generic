---
name: mp-handoff
description: "Compact this session into a handoff doc for the next agent."
license: MIT
metadata:
  author: "Matt Pocock (original), tea24864 (port)"
  version: "0.1.0"
  source-revision: "d81f3a183412e71a5b1e84ca21bc1a35eea03a60"
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to the temporary directory of the user's OS - not the current workspace.

{{runtime.history}}

Include a "suggested skills" section in the document, naming which skills the next agent should load, and how to load them in its runtime.

{{runtime.skill_loading}}

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.

