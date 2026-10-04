---
name: mp-implement
description: "Implement a piece of work based on a spec or set of tickets."
license: MIT
metadata:
  author: "Matt Pocock (original), tea24864 (port)"
  version: "0.1.0"
  source-revision: "d81f3a183412e71a5b1e84ca21bc1a35eea03a60"
---

Implement the work described by the user in the spec or tickets.

{{runtime.skill_loading}}

If independent delegation is unavailable in this runtime, do the same work sequentially in this session, keeping outputs separate and labeled as same-agent perspectives.

Use mp-tdd where possible, at pre-agreed seams.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Once done, use mp-code-review to review the work.

Commit your work to the current branch.

