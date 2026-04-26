---
name: weekly-connections
description: Find non-obvious connections across recent JARVIS captures. Use when the user says "run connection session", "find this week's connections", "weekly connections", or "find connections from the last N days". Reads notes in 01-CAPTURES/ from the requested window, surfaces 3–5 strong connections classified into Types A/B/C/D, and writes each as a new note in 02-CONNECTIONS/.
---

# Weekly Connections

You are operating inside the JARVIS Obsidian vault. Identity and voice rules are in `CLAUDE.md`.

## Steps

1. Determine the window. Default is the last 7 days. If the user says "last N days", honor that.
2. Read every note in `01-CAPTURES/` whose `created` or `processed` frontmatter falls within the window. Read across all five subfolders simultaneously — cross-type connections are the strongest.
3. Identify candidate connections. A strong connection is exactly one of:
   - **TYPE A** — Same underlying principle in two different domains.
   - **TYPE B** — Contradiction between two notes that creates interesting tension.
   - **TYPE C** — Pattern connecting three or more notes into one unnamed insight.
   - **TYPE D** — A question from one note that another note accidentally answers.
4. Apply the quality bar: **if it is obvious, it does not qualify.** Only surface connections that would surprise the person who wrote the notes.
5. Produce 3–5 connections. Quality over quantity. Better to return three sharp ones than five soft ones.
6. For each connection, write a new file in `02-CONNECTIONS/YYYY-MM-DD-<slug>.md`:

   ```
   ---
   created: YYYY-MM-DD
   type: A | B | C | D
   tags: [connection]
   ---

   # [Connection title]

   **Bridge:** [one-sentence link between the ideas]

   **Potential hook:** [one-sentence content hook]

   ## Source notes
   - [[wikilink to source 1]]
   - [[wikilink to source 2]]
   - [[wikilink to source 3]]

   ## Why this is non-obvious
   [2–3 sentences]
   ```

7. Return a summary listing all connection titles and which one the user should brief first, with a one-sentence reason.

## Voice and Rules

Apply every rule in `CLAUDE.md`. No banned words. No em dashes. No emoji.

## Mirror

This Skill mirrors `05-CLAUDE/skills/weekly-connections.md`. Keep in sync.
