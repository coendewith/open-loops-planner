# Planner: Open Loops

{{NAME}}'s standing planner. Every few days {{NAME}} asks to "update the loops" (or "what's
open"): sweep every work tool, merge what changed into one prioritised list, and rebuild the
private Claude Doc **Open loops and drafts**, where {{NAME}} marks loops done, steers them and
edits the drafts.

- Doc: {{DOC_URL}} (private). Its ids sit in `loops.json` `meta.doc`: `project`
  (C = `{"kind":"project","id":…}`), `body` (the tab's prose node), `status_enum` (the Status
  dropdown: Open, Done, Drop) and `rev` (the last rev you wrote).
- `loops.json`: the source of truth. An item has `id`, `title`, `detail`, `project` (a key of
  `projects`), `status` (open, blocked, done, dropped), `type`, `due`, `since`, `who`, `source`,
  and once closed `closed` and `closed_note`. Its `drafts` lists the messages that close it
  (`gmail:<draft id>`, `slack:<file>#<n>`); those items sit under Send in the doc, not in its
  tables. `waiting` lists what others owe {{NAME}}.
- `build.py`: validates loops.json and writes `doc_tables.md`, the doc's four table sections
  with their dropdown chips.
- `sweep-brief.md`: the prompts for the source agents, plus the glossary of projects and people.
- `sweeps/<date>/`: each sweep's raw findings per source and `summary.md`.
- `prep/<date>/messages.md`: drafted messages, Slack ones included.

`loops.json`, `doc_tables.md`, `sweeps/` and `prep/` hold colleague names and message content:
they stay local and out of git.

## "Update the loops"

1. **Read state.** `loops.json`; SINCE = `meta.swept_at`.
2. **Pull {{NAME}}'s input from the doc.** Load the docs skill, `read` the body with
   `{"kind":"view","sinceRev":<meta.doc.rev>}` and `query` its comments. Rows match items by title.
   - Status set to Done or Drop: close the item (`closed` = today, `closed_note` "Marked done in
     the doc", or better evidence from the sweep).
   - Text in a "Your steer" cell, or a comment: do what it says or fold it into the item. Reply in
     each comment thread with what you did.
   - A draft edited under Send: put the new text in the Gmail draft or the Slack draft file.
     Updating a Gmail draft drops its attachments, so re-attach them. Never send.
3. **Sweep.** Launch one background `general-purpose` agent per source in one message, each
   with the shared preamble plus its source block from `sweep-brief.md`, placeholders filled.
   They write `sweeps/<today>/<source>.md`.
4. **Merge into loops.json.**
   - Keep ids stable. New id: `<project>-<short-slug>`, lowercase kebab-case, never reused.
   - `since` is the first-seen date and never changes.
   - Close with evidence (`status: done|dropped`, `closed`, `closed_note`). Closed items stay in
     the file; the doc shows those closed in the last ten days.
   - Set `drafts` on items whose next step is a drafted message; clear it once that message is sent.
   - Rewrite `meta` (`previous_sweep` = old `swept_at`, new `swept_at`) and `waiting`.
   - Glossary changes go into `sweep-brief.md`.
5. **Verify.** Agents misjudge "did {{NAME}} already reply?". Check every message under Send,
   and every loop due this week, against its source yourself.
6. **Build.** `python3 build.py` (fails loudly on bad ids, dates, projects or drafts).
7. **Rebuild the doc**, one section per call, after an outline read:
   - The as-of date chip in the byline.
   - Send: every unsent Gmail draft and every unposted Slack draft in `prep/`, numbered, each
     with a one-line status, an "Open in Gmail" link and its full text as a quote. Group them:
     before a deadline, ready, date passed, overtaken or not to send, Slack.
   - This week, Waiting on others, Later and Closed: paste each section of `doc_tables.md`, with
     the json block under it as the `blocks` map of its markdown.
   - Replace each section's blocks with `ifRev`. If words a comment hangs on would go, reply in
     that thread first, then resend with `"allowDetach":true`.
   - Save the last ack's rev in `meta.doc.rev`.
8. **Log.** Write `sweeps/<today>/summary.md`: counts, new, closed, changed, gaps.
9. **Answer {{NAME}}** with the doc link and the five things that matter most this week.

## Rules

- Read-only everywhere. Never send, reply, RSVP, react, label, move or share. Draft a message
  only when {{NAME}} asks, and send nothing without an explicit yes.
- Absolute ISO dates in data.
- Meeting-note attendee lists are unreliable and names get garbled. Don't assign an owner from
  a summary alone; check the transcript.
- The doc holds colleague and partner names and email summaries. Keep it private.
