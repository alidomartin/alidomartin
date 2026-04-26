---
name: write-content
description: Write a finished piece of content from an approved brief in Alido's exact voice. Use when the user says "write the brief for [X]", "write this brief", or "produce content from brief". Reads the brief and every linked source note, then writes the full piece structured hook → proof → body → closer, saved beside the brief as a draft.
---

# Write Content

You are operating inside the JARVIS Obsidian vault. The owner's voice rules and banned words are in `CLAUDE.md`. The output must be indistinguishable from something Alido wrote himself.

## Steps

1. Read the specified brief in `03-BRIEFS/`. If multiple match, ask which one.
2. Follow every wikilink in the brief and read each source note in full. Do not skip captures — the specific numbers and observations live there.
3. Write the piece using the brief's chosen hook (rank 1 by default; ask if the user wants a different one) and chosen closer.
4. Structure: **hook → proof → body → closer.**
5. Every paragraph must add a specific claim, number, or example. No filler. No wind-up. No "in this post we will explore".
6. Where relevant, include at least one of:
   - a concrete metric threshold the reader can apply tomorrow (e.g. "asymmetry > 15% on propulsive impulse warrants a load-management conversation")
   - a copyable snippet (R/Python/Sheets formula) for a force-plate calculation
   - a labelled phase reference linking to the relevant CMJ phase image if applicable
7. End with a bookmark CTA and one follow instruction.

## Voice Requirements

Apply every rule in `CLAUDE.md` precisely.

- Short sentences. Hard stops. One idea per line where possible.
- **Bold** key terms on first appearance only.
- Real numbers always. No "many", "often", "significantly" without a number behind them.
- No banned words: delve, leverage (verb), robust, unleash, tapestry, meticulous, navigate (figurative), realm, foster (figurative), "in today's fast-paced world", "it's important to note", "moreover", "furthermore", "let's dive in", "deep dive", "game-changer".
- No em dashes. Replace with a period or comma.
- No emoji.
- Domain vocabulary used confidently. Do not over-explain CMJ, GRF, eccentric, or RSI to a coaching audience.
- If in doubt, **make it shorter and more direct**.

## Output

Save the draft beside the brief at `03-BRIEFS/YYYY-MM-DD-<slug>--draft.md` with frontmatter:

```
---
created: YYYY-MM-DD
tags: [written]
brief: [[YYYY-MM-DD-<slug>]]
---
```

Do **not** move the file to `04-PUBLISHED/`. That happens only after Alido confirms the post has shipped and provides impression and bookmark data.

## Mirror

This Skill mirrors `05-CLAUDE/skills/write-content.md`. Keep in sync.
