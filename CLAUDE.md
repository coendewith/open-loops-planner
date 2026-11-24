# Planner: Open Loops

{{NAME}}'s standing planner. Every few days {{NAME}} asks to "update the loops" (or "what's
open"): sweep every work tool, merge what changed into one prioritised list, and rebuild the
private Claude Doc **Open loops and drafts**, where {{NAME}} ticks loops off, steers them and
edits the drafts.

- Doc: {{DOC_URL}} (private). Its ids sit in `loops.json` `meta.doc`: `project`
  (C = `{"kind":"project","id":…}`), `body` (the tab's prose node) and `rev` (the last rev you
  wrote). {{NAME}} ticks a loop's checkbox when it is done.
- `loops.json`: the source of truth. An item has `id`, `title`, `detail`, `project` (a key of
  `projects`), `status` (open, blocked, done, dropped), `type`, `due`, `since`, `who`, `source`,
  and once closed `closed` and `closed_note`. Every open item also has `q` (its Eisenhower
  quadrant), `est` ({{NAME}}'s own time in minutes), `src` (a short label such as "Granola, 17
  Nov") and, wherever one exists, `url` (the meeting note, Gmail thread, Slack permalink or Drive
  file it came from). Its `drafts` lists the messages that close it (`gmail:<draft id>`,
  `slack:<file>#<n>`). `waiting` lists what others owe {{NAME}}, each with `src` and `url` too.
- `build.py`: validates loops.json and writes `doc_tables.md`, the doc's sections in ranked
  order: per quadrant a **Tasks** checklist (loops without drafts) and a **Messages to send**
  checklist (loops closed by a draft), each line with its time, due date, draft numbers and
  source link, plus time totals; then Waiting on others and Closed.
- `sweep-brief.md`: the prompts for the source agents, plus the glossary of projects and people.
- `sweeps/<date>/`: each sweep's raw findings per source and `summary.md`.
- `prep/<date>/messages.md`: drafted messages, Slack ones included.

`loops.json`, `doc_tables.md`, `sweeps/` and `prep/` hold colleague names and message content:
they stay local and out of git.

## "Update the loops"

1. **Read state.** `loops.json`; SINCE = `meta.swept_at`.
2. **Pull {{NAME}}'s input from the doc.** Load the docs skill, `read` the body with
   `{"kind":"view","sinceRev":<meta.doc.rev>}` and `query` its comments. Lines match items by title.
   - A ticked checkbox: close the item (`closed` = today, `closed_note` "Ticked in the doc", or
     better evidence from the sweep). A steer that says drop: close it as dropped.
   - Text typed under a loop, in a Waiting "Your steer" cell, or a comment: do what it says or
     fold it into the item. Reply in each comment thread with what you did.
   - A draft edited in the doc: put the new text in the Gmail draft or the Slack draft file.
     Updating a Gmail draft drops its attachments, so re-attach them. Never send.
3. **Sweep.** Launch one background `general-purpose` agent per source in one message, each
   with the shared preamble plus its source block from `sweep-brief.md`, placeholders filled.
   They write `sweeps/<today>/<source>.md`.
4. **Merge into loops.json.**
   - Keep ids stable. New id: `<project>-<short-slug>`, lowercase kebab-case, never reused.
   - `since` is the first-seen date and never changes.
   - Close with evidence (`status: done|dropped`, `closed`, `closed_note`). Closed items stay in
     the file; the doc shows those closed in the last ten days.
   - Set `drafts` on items whose next step is a drafted message; clear it once that message is
     sent. When a loop needs real work as well as a message, split the work into its own task loop.
   - Set `est`, `src` and `url` on every open item. Mine every meeting since SINCE for
     {{NAME}}'s tasks (owner clear from the transcript), each with its note link.
   - Set `q` on every open item: 1 do now (urgent and important), 2 plan (important, not
     urgent), 3 quick or hand off (urgent, less important), 4 later or drop. Urgent = a date this
     week or someone actively waiting; important = it moves {{NAME}}'s main work, a partner or a
     colleague's work, rather than admin. `build.py` moves 2 and 4 up once the due date is two
     days away or past, so clear a due date that has passed without a new one instead of letting
     it fake urgency.
   - Rewrite `meta` (`previous_sweep` = old `swept_at`, new `swept_at`) and `waiting`.
   - Glossary changes go into `sweep-brief.md`.
5. **Verify.** Agents misjudge "did {{NAME}} already reply?". Check every drafted message, and
   every loop in quadrants 1 and 3, against its source yourself. Then check the loops no source
   touched this sweep and close those that are done or overtaken: an open loop the conversations
   already settled is the worst thing the doc can show.
6. **Build.** `python3 build.py` (fails loudly on bad ids, dates, projects or drafts, and on an
   open item without `q` or `est`).
7. **Rebuild the doc**, one section per call, after an outline read, in the order of
   `doc_tables.md`: most urgent and important at the top.
   - The as-of date chip in the byline.
   - Each quadrant: its Tasks and Messages checklists, then the full text of each draft listed
     under it, numbered as in the checklists, with a one-line status and an "Open in Gmail" link.
     Drafts come from the Gmail drafts list and the unposted Slack drafts in `prep/`.
   - Then Waiting on others and Closed.
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
