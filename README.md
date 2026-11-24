# Open Loops planner

A Claude Code setup that sweeps your work tools (Gmail, Slack, calendar, Drive, meeting notes),
keeps one list of everything you owe or are owed, drafts the messages you still have to send,
and puts it all in a private Claude Doc. In the doc you mark loops done, steer them and edit the
drafts; Claude reads that back on the next run.

## How it works

1. You say "update the loops".
2. Claude reads what you changed in the doc: ticked loops, steers, comments, edited drafts.
3. One background agent per tool sweeps the days since the last run, read-only.
4. Claude merges the findings into `loops.json`, checks the urgent ones itself and rebuilds the doc.

Nothing is ever sent for you. Drafts wait in Gmail or in `prep/` until you send them yourself.

## What the doc shows

Four sections ranked like an Eisenhower matrix: do now, plan, quick or hand off, later or drop.
Each lists your **tasks** first, then the **messages to send**, as checklists you tick off. Every
line has a time estimate, its due date and a link to where it came from (the meeting note, email
thread, Slack message or file), and each section shows its total time. The drafts sit in full
under their section, to edit in place. Then what others owe you, and what closed recently.

## Set it up

Paste the prompt in [SETUP_PROMPT.md](SETUP_PROMPT.md) into Claude Code. It clones this repo,
fills in your details and glossary, checks your connectors, creates your doc and runs the first
sweep.

## Files

| File | What it is |
| --- | --- |
| `CLAUDE.md` | The instructions Claude follows when you say "update the loops" |
| `sweep-brief.md` | The prompts for the source agents, and your glossary of projects and people |
| `build.py` | Checks `loops.json` and writes the doc's ranked checklists, with time estimates and source links |
| `loops.example.json` | The data format; copied to `loops.json` at setup |

`loops.json`, `doc_tables.md`, `sweeps/` and `prep/` stay on your machine (see `.gitignore`):
they hold colleague names and message content.

## Make it yours

Everything is plain text. Tell Claude what you don't like about the list or the doc, and ask
it to change `CLAUDE.md` or `sweep-brief.md`. The glossary is what makes sweeps accurate: keep
adding projects, people and the words your meeting notes get wrong.
