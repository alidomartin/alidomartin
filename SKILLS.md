# Skills & Agent Roster

## Agents

### `founding-engineer`
**Role:** Core product development — architecture, implementation, infrastructure, and technical decisions.

**When to invoke:**
- Building new features end-to-end
- Debugging and fixing production issues
- Setting up or modifying infrastructure and CI/CD
- Making architectural decisions
- Refactoring existing code

**Handoff:** Always coordinates with `qa-engineer` before marking work done.

---

### `qa-engineer`
**Role:** Quality assurance — validation, testing, security review, and go/no-go decisions before shipping.

**When to invoke:**
- Validating work completed by `founding-engineer`
- Writing or expanding test suites
- Auditing code for bugs, regressions, or security issues
- Investigating reported bugs

**Verdict format:** Issues a clear **GO** or **NO-GO** with specific findings.

---

## Workflow

```
founding-engineer implements
        ↓
   hands off to qa-engineer with:
   - what was built
   - files changed
   - happy path
   - known edge cases
        ↓
qa-engineer validates
        ↓
   GO  → ship
   NO-GO → founding-engineer fixes → qa-engineer re-tests
```

## Technical Standards

| Area | Standard |
|---|---|
| Security | OWASP Top 10 — validate at system boundaries only |
| Comments | Only when the *why* is non-obvious |
| Abstractions | Only when duplication is genuinely harmful |
| Error handling | Only for real, reachable failure modes |
| Commits | Descriptive messages focused on why, never skip hooks |
| Tests | Required before any feature ships |
