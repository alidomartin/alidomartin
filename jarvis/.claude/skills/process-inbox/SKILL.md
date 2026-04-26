---
name: process-inbox
description: Process the JARVIS vault inbox. Use when the user says "process my inbox", "run morning capture", or "clear the inbox". Reads every note in 00-INBOX/, sharpens each, files it into the correct 01-CAPTURES/ subfolder, and returns a report of what moved where plus one connection worth exploring.
---

# Process Inbox

You are operating inside the JARVIS Obsidian vault. The owner's identity, voice rules, and banned words are in `CLAUDE.md` at the vault root. Read it first if not already loaded.

## Steps

1. List every note in `00-INBOX/`.
2. For each note, read its contents.
3. Decide the destination subfolder under `01-CAPTURES/` using these rules:
   - Contains a specific number, athlete delta, group mean, or study result → `numbers/`
   - Phrased as "I noticed…" or describes something that happened → `observations/`
   - Reaction to an external paper, post, or claim → `reactions/`
   - Names the same idea showing up in two contexts → `patterns/`
   - Ends in `?` and the owner does not know the answer → `questions/`
   - When ambiguous, prefer `patterns/` over `observations/`.
4. Sharpen the note into one punchy sentence in the owner's voice. The rewritten note should be self-contained — a stranger should understand the observation without extra context. If still unclear, rewrite again.
5. Add exactly three specific tags. No more, no fewer. Prefer domain tags (`#cmj`, `#asymmetry`, `#volleyball`, `#return-to-play`) over generic ones (`#training`).
6. Write the sharpened note to `01-CAPTURES/<subfolder>/YYYY-MM-DD-<slug>.md` with frontmatter:
   ```
   ---
   created: <original timestamp from inbox if present, else today>
   processed: YYYY-MM-DD
   tags: [tag1, tag2, tag3]
   source: 00-INBOX/<original-filename>
   ---
   ```
7. Delete the original from `00-INBOX/` only after the new file is written successfully.

## Output Report

After processing, return:
- **Total notes processed** and a table of `original → destination`.
- **Patterns noticed** across today's batch (1–3 bullets).
- **One connection worth exploring** between today's batch and the existing vault.

## Voice and Rules

Apply every rule in `CLAUDE.md`. No banned words. No em dashes. No emoji. Short sentences. Real numbers.

## Mirror

This Skill mirrors `05-CLAUDE/skills/process-inbox.md`. Keep them in sync if either is edited.
