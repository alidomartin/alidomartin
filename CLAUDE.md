# CLAUDE.md

## DESIGN.md is the source of design truth

Read `DESIGN.md` before generating UI or component code. If a change you make matches any of the triggers below, update `DESIGN.md` in the **same** change — don't defer it.

### Update DESIGN.md when:

1. A new component pattern appears twice
2. A designer changes the visual direction
3. A PM notices repeated agent mistakes
4. A review comment keeps coming back
5. A feature area needs different density rules
6. A mobile pattern diverges from desktop
7. The team decides a one-off pattern should become standard

A `SessionStart` hook injects the current `DESIGN.md` contents into context, and a `PostToolUse` hook on `Write|Edit` re-injects the trigger checklist after every file change. Both are configured in `.claude/settings.json`.
