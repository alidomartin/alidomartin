# Skill: Write Content

## Trigger phrases
"write the brief for [topic]" / "write this brief" / "produce content from brief"

## Process
1. Read the specified brief in `03-BRIEFS/`.
2. Read every source note linked in the brief (follow wikilinks fully).
3. Write the full piece in Alido's exact voice as defined in `CLAUDE.md`.
4. Structure: **hook → proof → body → closer**.
5. Every section must add specific value. No filler.
6. Where relevant, include at least one of:
   - a copyable code block (e.g. R/Python snippet for a force-plate calculation)
   - a concrete metric threshold the reader can apply tomorrow
   - a labelled diagram reference (link to the relevant `images/` file if applicable)
7. End with a bookmark CTA and one follow instruction.

## Voice requirements
Apply every rule in `CLAUDE.md` precisely.
- Short sentences. Hard stops.
- Bold key terms on first appearance.
- Real numbers. No vague claims.
- No banned words. No em dashes. No emoji.
- Domain vocabulary used confidently. Do not over-explain.
- If in doubt, **make it shorter and more direct**.
- The output should be indistinguishable from content Alido wrote himself.

## Output
Save the draft beside the brief in `03-BRIEFS/` as `YYYY-MM-DD-<slug>--draft.md`.
Tag it `#written`.
Do not move it to `04-PUBLISHED/` until Alido explicitly confirms it has shipped and provides performance data.
