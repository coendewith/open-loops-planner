# Setup prompt

Open Claude Code (the desktop app's Code tab works), start a new session, and paste this:

```
Set up my own Open Loops planner from https://github.com/coendewith/open-loops-planner. It's Coen's planner with his data taken out. I want my own copy that I can keep changing, not his.

1. Clone it into ~/Planner, or ask me for another folder. Then make it my own repo: remove Coen's remote, so nothing I change goes back to his. If the clone asks for a GitHub login, help me log in first.
2. Copy loops.example.json to loops.json and delete the two example items.
3. Make it mine. I'm Pavel Cholakov and I work on the Future of Compute vertical at Techleap. Fill the {{...}} placeholders in CLAUDE.md and sweep-brief.md. Ask me for the projects and people I deal with most, and write them as the glossary in sweep-brief.md and as "projects" in loops.json.
4. Check which tools you can reach: Gmail, Google Calendar, Google Drive, Slack, my meeting notes (Granola or Gemini) and Claude Docs. Tell me what's missing so I can connect it, then rewrite the source blocks in sweep-brief.md with the exact tool names, and drop the sources I don't have.
5. Create my private Claude Doc "Open loops and drafts" with the sections Send, This week, Waiting on others, Later and Closed, and a Status dropdown with Open, Done and Drop. Put its ids in loops.json under meta.doc, and its link in CLAUDE.md.
6. Run a first "update the loops" over the last 14 days and fill the doc.
7. Then ask me what to change. Also offer to build a writing-style skill from my sent emails and Slack messages, so the drafts sound like me.

Stay read-only throughout: never send, reply, RSVP or post anything, and only draft messages when I ask.
```

After that, say "update the loops" whenever you want a fresh list.
