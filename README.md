# Open Loops planner

A Claude Code setup that sweeps your work tools (Gmail, Slack, calendar, Drive, meeting notes),
keeps one list of everything you owe or are owed, drafts the messages you still have to send,
and puts it all in a private Claude Doc. In the doc you mark loops done, steer them and edit the
drafts; Claude reads that back on the next run.

## How it works

1. You say "update the loops".
2. Claude reads what you changed in the doc: Done or Drop, steers, comments, edited drafts.
3. One background agent per tool sweeps the days since the last run, read-only.
4. Claude merges the findings into `loops.json`, checks the urgent ones itself and rebuilds the doc.

Nothing is ever sent for you. Drafts wait in Gmail or in `prep/` until you send them yourself.

## Set it up

Paste the prompt in [SETUP_PROMPT.md](SETUP_PROMPT.md) into Claude Code. It clones this repo,
fills in your details and glossary, checks your connectors, creates your doc and runs the first
sweep.

## Files

| File | What it is |
| --- | --- |
| `CLAUDE.md` | The instructions Claude follows when you say "update the loops" |
| `sweep-brief.md` | The prompts for the source agents, and your glossary of projects and people |
| `build.py` | Checks `loops.json` and writes the doc's four tables |
| `loops.example.json` | The data format; copied to `loops.json` at setup |

`loops.json`, `doc_tables.md`, `sweeps/` and `prep/` stay on your machine (see `.gitignore`):
they hold colleague names and message content.

## Make it yours

Everything is plain text. Tell Claude what you don't like about the list or the doc, and ask
it to change `CLAUDE.md` or `sweep-brief.md`. The glossary is what makes sweeps accurate: keep
adding projects, people and the words your meeting notes get wrong.
