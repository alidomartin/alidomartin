---
name: generate-brief
description: Generate a structured content brief from a connection or topic. Use when the user says "generate a brief for [X]", "brief this connection", or "make a brief". Produces a five-field brief (One Thing, Proof, Reader Transformation, Three Hooks ranked, Three Closers ranked) saved to 03-BRIEFS/. Pushes back if the One Thing is fuzzy.
---

# Generate Brief

You are operating inside the JARVIS Obsidian vault. Identity, voice, and audience are in `CLAUDE.md`.

## Steps

1. Identify the source. Either a `02-CONNECTIONS/` note or a topic the user names. Read the source note and every wikilinked capture in full.
2. Draft the brief with these five fields, in this order:

   - **ONE THING** — the single insight in one sentence. If you cannot reduce it to one sentence, **stop and tell the user the idea is not ready, and ask one specific question that would sharpen it**. Do not proceed.
   - **PROOF** — the most specific real example, number, or peer-reviewed result that proves the One Thing. For Alido's audience, prefer force-plate metrics, group means, individual athlete deltas, or cited findings. Vague proof invalidates the brief.
   - **READER TRANSFORMATION** — what an S&C coach or sport scientist knows or feels at the end that they did not before. One sentence.
   - **THREE HOOKS (ranked)**:
     1. Aggressive — a contrarian or pointed claim.
     2. Curious — a clean question or a number that demands explanation.
     3. Personal — something seen in the lab or with an athlete this week.
   - **THREE CLOSERS (ranked)** — by urgency and memorability. Write the closer before the middle.

3. Save to `03-BRIEFS/YYYY-MM-DD-<slug>.md` with frontmatter:

   ```
   ---
   created: YYYY-MM-DD
   tags: [ready-to-write]
   sources:
     - [[source connection]]
     - [[source capture]]
   ---
   ```

4. Return the brief in the chat and confirm where it was saved.

## Quality Bar

- Reject fuzzy One Things rather than ship a fuzzy brief.
- Numbers must be real and traceable to a source note.
- Hooks must be different in approach, not just rephrased.

## Voice and Rules

Apply every rule in `CLAUDE.md`. No banned words. No em dashes. No emoji.

## Mirror

This Skill mirrors `05-CLAUDE/skills/generate-brief.md`. Keep in sync.
