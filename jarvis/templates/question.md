<%*
const t = tp.date.now("YYYY-MM-DD-HHmm");
await tp.file.rename(`${t}-question`);
-%>
---
created: <% tp.date.now("YYYY-MM-DD HH:mm") %>
type: question
tags: []
---

# <% tp.date.now("YYYY-MM-DD HH:mm") %> — Question

The question:

What I have already ruled out:

What would settle it:
