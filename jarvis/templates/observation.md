<%*
const t = tp.date.now("YYYY-MM-DD-HHmm");
await tp.file.rename(`${t}-observation`);
-%>
---
created: <% tp.date.now("YYYY-MM-DD HH:mm") %>
type: observation
tags: []
---

# <% tp.date.now("YYYY-MM-DD HH:mm") %> — Observation

What I noticed:

Where:

Why it might matter:
