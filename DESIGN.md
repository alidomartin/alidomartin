# DESIGN.md

This document captures the project's design conventions. Keep it current — out-of-date guidance is worse than none.

## When to update DESIGN.md

Update this document when any of the following happen:

- **A new component pattern appears twice.** The second occurrence is the signal to write it down before a third diverges.
- **A designer changes the visual direction.** Capture the new direction here so implementation follows the latest intent, not the old one.
- **A PM notices repeated agent mistakes.** Recurring agent errors mean the rules aren't explicit enough — add the missing constraint.
- **A review comment keeps coming back.** If reviewers repeat the same feedback, promote it from tribal knowledge to written rule.
- **A feature area needs different density rules.** Document the area-specific exception (spacing, type scale, control sizing) so it isn't treated as a bug later.
- **A mobile pattern diverges from desktop.** Record both patterns and the breakpoint or context that selects between them.
- **The team decides a one-off pattern should become standard.** When an exception is promoted to a rule, move it into this document and remove the "one-off" caveat.
