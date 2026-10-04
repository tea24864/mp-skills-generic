---
name: mp-grilling
description: "Grill the user relentlessly to stress-test their thinking."
license: MIT
metadata:
  author: "Matt Pocock (original), tea24864 (port)"
  version: "0.1.0"
  source-revision: "d81f3a183412e71a5b1e84ca21bc1a35eea03a60"
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Format a round like so:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>

---

❓ **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself.

{{runtime.delegation}}

If independent delegation is unavailable in this runtime, do the same work sequentially in this session, keeping outputs separate and labeled as same-agent perspectives.

Facts are never the user's job: perform the lookup with your own file and terminal tools, tag the findings in the transcript like an explorer's report so they stay distinct from the interview, and only the questions downstream of the fact wait; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.

