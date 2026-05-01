# Skills & Agent Roster

## Team Structure

```
           CEO
          /   \
founding-engineer  [specialist agents hired as needed]
          \
       qa-engineer
```

---

## Agents

### `ceo`
**Role:** Vision, prioritization, team coordination, and hiring.

**When to invoke:**
- Setting or clarifying product direction
- Breaking a large goal into delegated work
- Making product/business tradeoffs
- Identifying a capability gap and hiring a new agent
- Orchestrating multiple agents toward a shared outcome

**Key power:** Can create new agent files in `.claude/agents/` to expand the team.

---

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
CEO sets goal & delegates
        ↓
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
   GO  → CEO ships
   NO-GO → founding-engineer fixes → qa-engineer re-tests
```

## Hiring New Agents

The CEO hires new agents by:
1. Creating `.claude/agents/<role>.md` with frontmatter + system prompt
2. Adding the agent to the roster and workflow in this file

**Roles available to hire:**

| Role | Trigger |
|---|---|
| `growth-engineer` | Acquisition, analytics, or A/B experimentation work |
| `designer` | UI/UX, design system, or Figma handoff needed |
| `data-engineer` | Data pipelines, warehousing, or analytics infra |
| `devops-engineer` | Deployment, monitoring, scaling, or incident response |
| `product-manager` | Requirements docs, user research, roadmap planning |
| `security-engineer` | Threat modeling, pentesting, or compliance audit |
| `technical-writer` | Docs, runbooks, or onboarding guides |

---

## Technical Standards

| Area | Standard |
|---|---|
| Security | OWASP Top 10 — validate at system boundaries only |
| Comments | Only when the *why* is non-obvious |
| Abstractions | Only when duplication is genuinely harmful |
| Error handling | Only for real, reachable failure modes |
| Commits | Descriptive messages focused on why, never skip hooks |
| Tests | Required before any feature ships |
