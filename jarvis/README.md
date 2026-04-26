# JARVIS — Second Brain + Content Production System

An Obsidian vault wired to Claude Code. Captures raw thoughts, finds non-obvious connections across them, generates content briefs, and writes in the owner's voice.

Owner: **Alido Martin** — N1 Performance Lab PH.

## Quick Start

1. **Install prerequisites**

   ```bash
   npm install -g @anthropic-ai/claude-code
   export ANTHROPIC_API_KEY=your_key_here
   ```

   The original blog post had `@anthropic/claude-code`. The correct package is `@anthropic-ai/claude-code`.

2. **Open the vault in Obsidian**

   In Obsidian, "Open folder as vault" → select this `jarvis/` directory.

3. **Install community plugins** (Settings → Community plugins → Browse)

   - Templater
   - Dataview
   - QuickAdd
   - Obsidian Git

4. **Launch Claude Code from the vault root**

   ```bash
   cd jarvis
   claude
   ```

   Claude Code auto-loads `CLAUDE.md` from the vault root. It also auto-loads any Skills under `.claude/skills/`.

5. **Sanity check**

   ```
   Read my CLAUDE.md and tell me in one paragraph what you understand about this vault and what your role is inside it.
   ```

   If the summary is specific and accurate, you are connected.

## Two Skill Layers

This vault ships with **both** styles described in the post:

- **Real auto-invoking Skills** in `.claude/skills/<name>/SKILL.md` — Claude Code reads the `description` frontmatter and invokes them automatically when the trigger phrase or intent matches.
- **Prompt-template skills** in `05-CLAUDE/skills/<name>.md` — plain markdown procedures you reference manually ("run the process inbox skill"). Useful as a fallback or for editing the spec without touching the live Skill.

The two are kept in sync. Edit either; the spec lives in the prompt-template version, and the real Skill mirrors it.

## Daily Ritual (20 minutes)

| Min | Action |
|----:|---|
| 1–5 | Drop raw captures into `00-INBOX/` (voice memos, observations, numbers, reactions) |
| 6–10 | `process my inbox` |
| 11–15 | `find connections from the last 14 days` |
| 16–20 | `generate a brief for [the connection that surprised you most]` |

## Weekly (Sundays)

```
run weekly connections
```

Reads everything added to `01-CAPTURES/` in the last 7 days and surfaces 3–5 non-obvious connections. Pick the two strongest and brief them.

## Monthly (Performance Review)

```
Read everything in my 04-PUBLISHED folder. Tell me:
1. Which topics drove the most bookmarks per impression
2. Which hook formats outperformed their topic average
3. What three content angles my best performing posts suggest I have not tried yet
4. Which combinations of topic and format I should double down on this month

Only insights specific to this exact data. No generic advice.
```

## Folder Structure

```
jarvis/
├── CLAUDE.md                       # vault context auto-loaded by Claude Code
├── 00-INBOX/                       # raw, unsorted captures
├── 01-CAPTURES/
│   ├── observations/               # things noticed
│   ├── reactions/                  # gut responses
│   ├── patterns/                   # same principle, two domains
│   ├── questions/                  # genuine unknowns
│   └── numbers/                    # real data points
├── 02-CONNECTIONS/                 # synthesized insights
├── 03-BRIEFS/                      # structured pre-write briefs
├── 04-PUBLISHED/                   # shipped content + performance data
├── 05-CLAUDE/
│   ├── skills/                     # prompt-template skills (post-style)
│   └── context/                    # additional context files (papers, glossaries)
├── .claude/skills/                 # real auto-invoking Skills
└── templates/                      # Obsidian Templater capture templates
```

## Why organize CAPTURES by *type* and not by *topic*

A note about *attention in volleyball training* and a note about *attention as a psychological construct* will never meet if you organize by topic. They both land in `patterns/` if you organize by type — and that collision is where the best content comes from.

## Notes on the Original Post

The original blog post by Cyril is solid in spirit, with two adjustments applied here:

- `CLAUDE.md` lives at the **vault root**, not nested under `05-CLAUDE/`. Claude Code only auto-loads from the project root or `.claude/CLAUDE.md`.
- The npm package is `@anthropic-ai/claude-code`, not `@anthropic/claude-code`.
- "Skills" are implemented twice: once as real auto-invoking Skills, once as prompt-template specs. The post conflates the two.
