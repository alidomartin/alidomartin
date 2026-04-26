# Skill: Weekly Connections

## Trigger phrases
"run connection session" / "find this week's connections" / "weekly connections" / "find connections from the last N days"

## Process
1. Read all notes added to `01-CAPTURES/` in the last 7 days (or N days if specified).
2. Search for connections across **all subfolders simultaneously**. Cross-type connections (e.g. a `numbers/` note + a `patterns/` note) are usually the strongest.
3. A strong connection is one of these four types:
   - **TYPE A**: Same underlying principle in two different domains.
   - **TYPE B**: Contradiction between two notes that creates interesting tension.
   - **TYPE C**: Pattern connecting three or more notes into one unnamed insight.
   - **TYPE D**: A question from one note that another note accidentally answers.
4. For each strong connection:
   a. Name the connection type (A/B/C/D).
   b. Write a one-sentence bridge between the ideas.
   c. Write a potential content hook using this connection.
   d. Create a new note in `02-CONNECTIONS/` linking the source notes via wikilinks. Filename: `YYYY-MM-DD-<slug>.md`.

## Quality bar
If the connection is obvious, it does not qualify. Only surface connections that would genuinely surprise the person who wrote the notes.
**Minimum: 3 connections. Maximum: 5. Quality over quantity.**

## Output template per connection
```
# [Connection title]

**Type:** A / B / C / D
**Bridge:** [one sentence]
**Potential hook:** [one sentence]

## Source notes
- [[link to source 1]]
- [[link to source 2]]
- [[link to source 3]]

## Why this is non-obvious
[2–3 sentences]
```
