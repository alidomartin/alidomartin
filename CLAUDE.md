# Karpathy-Inspired Claude Code Guidelines

Every task, goal, or problem prompt is governed by these four principles.

---

## 1. Think Before Coding

**Addresses: wrong assumptions, hidden confusion, missing tradeoffs**

- Before writing a single line, restate the goal in your own words and confirm understanding.
- Surface any ambiguity, edge cases, or conflicting requirements before proceeding.
- Identify tradeoffs (performance vs. simplicity, speed vs. correctness) and present them.
- If anything is unclear, ask — do not assume and run with it.
- Never start implementation when the problem statement is fuzzy.

---

## 2. Simplicity First

**Addresses: overcomplication, bloated abstractions**

- Default to the simplest solution that correctly solves the problem.
- Do not introduce abstractions, layers, or patterns unless they are clearly needed today.
- Three similar lines of code beat a premature abstraction every time.
- Prefer flat over nested, explicit over implicit, small over large.
- If the solution exceeds what the task requires, cut it back.

---

## 3. Surgical Changes

**Addresses: orthogonal edits, touching code you shouldn't**

- Change only what is required to achieve the stated goal — nothing more.
- Do not refactor, rename, reformat, or "clean up" surrounding code unless explicitly asked.
- Do not add docstrings, comments, or type hints to code you did not modify.
- One task = one focused diff. Side-effect edits break trust and introduce regressions.
- If you notice something worth fixing nearby, flag it to the user instead of silently fixing it.

---

## 4. Goal-Driven Execution

**Addresses: vague progress, unverifiable outcomes**

- Define a clear, verifiable success criterion before starting.
- Prefer tests-first thinking: what does "done" look like, and how will we know?
- Work toward the goal in the smallest verifiable steps possible.
- Report progress against the goal, not just activity.
- If the approach isn't working, diagnose and pivot — do not thrash.
