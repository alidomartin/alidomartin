# Skill: Process Inbox

## Trigger phrases
"process my inbox" / "run morning capture" / "clear the inbox"

## Process
1. Read every note in `00-INBOX/`.
2. For each note:
   a. Determine which `01-CAPTURES/<subfolder>/` it belongs to (`observations`, `reactions`, `patterns`, `questions`, `numbers`).
   b. Sharpen the raw note into one punchy sentence in the owner's voice (see `CLAUDE.md`).
   c. Add exactly three tags. No more, no fewer. Tags should be specific (e.g. `#cmj`, `#asymmetry`, `#volleyball`) not generic (`#training`).
   d. Move the sharpened note to the correct subfolder. Filename format: `YYYY-MM-DD-<slug>.md`.
3. After processing all notes, provide:
   - Total notes processed and where each one went.
   - Any patterns noticed across today's batch.
   - One connection worth exploring from today's batch.

## Quality bar
A sharpened note should be specific enough that a stranger would understand exactly what was observed without any additional context. If it still needs explanation, it is not sharp enough. Rewrite it.

## Filing rules
- A note containing a specific number → `numbers/`
- A note phrased as "I noticed…" or describing what happened → `observations/`
- A note that is a reaction to something external (paper, post, claim) → `reactions/`
- A note that names the same idea showing up in two contexts → `patterns/`
- A note that ends in a `?` and the owner does not know the answer → `questions/`

When ambiguous, prefer `patterns/` over `observations/` — patterns produce better connections.
