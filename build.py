#!/usr/bin/env python3
"""Validate loops.json and write doc_tables.md, the doc's four table sections.

Usage: python3 build.py   (exits 1 and prints every problem if loops.json is invalid)
"""
import datetime
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,80}$")
STATUSES = {"open", "blocked", "done", "dropped"}
TYPES = {"reply", "action", "decision", "prep", "waiting", "deadline", "rsvp", "fyi"}
DRAFT = re.compile(r"^(gmail:r-?\d+|slack:\S+#\d+)$")


def bad_date(v):
    if v is None:
        return False
    try:
        datetime.date.fromisoformat(v)
        return False
    except (TypeError, ValueError):
        return True


def validate(d):
    errs = []
    meta = d.get("meta", {})
    for f in ("swept_at", "previous_sweep"):
        if bad_date(meta.get(f)):
            errs.append(f"meta.{f}: not an ISO date")
    projects = d.get("projects", {})
    seen = set()
    for i in d.get("items", []):
        iid = i.get("id", "")
        if not ID.match(iid):
            errs.append(f"{iid!r}: id must be lowercase kebab-case")
        if iid in seen:
            errs.append(f"{iid}: duplicate id")
        seen.add(iid)
        for f in ("title", "detail", "project", "status"):
            if not i.get(f):
                errs.append(f"{iid}: missing {f}")
        if i.get("status") not in STATUSES:
            errs.append(f"{iid}: status must be one of {sorted(STATUSES)}")
        if i.get("type") and i["type"] not in TYPES:
            errs.append(f"{iid}: type must be one of {sorted(TYPES)}")
        if i.get("project") not in projects:
            errs.append(f"{iid}: unknown project {i.get('project')!r}")
        if i.get("status") in ("done", "dropped") and not i.get("closed"):
            errs.append(f"{iid}: closed item needs a closed date")
        for f in ("due", "since", "closed"):
            if bad_date(i.get(f)):
                errs.append(f"{iid}: {f} is not an ISO date")
        for r in i.get("drafts", []):
            if not DRAFT.match(r):
                errs.append(f"{iid}: draft {r!r} must be gmail:<draft id> or slack:<file>#<n>")
    for w in d.get("waiting", []):
        if not w.get("who") or not w.get("what") or bad_date(w.get("since")):
            errs.append(f"waiting {w.get('who')!r}: needs who, what and an ISO since")
    return errs


def day(iso):
    return datetime.date.fromisoformat(iso).strftime("%a %-d %b") if iso else ""


def doc_tables(d, today):
    """The doc's four table sections as markdown, each followed by the dropdown chips its Status column needs."""
    enum, area = d["meta"]["doc"]["status_enum"], d["projects"]
    cell = lambda s: s.replace("|", "/").rstrip(".")
    live = [i for i in d["items"] if i["status"] in ("open", "blocked")]
    rows = [i for i in live if not i.get("drafts")]  # the others sit under Send, next to their draft
    cut = today + datetime.timedelta(days=7)
    week = sorted((i for i in rows if i.get("due") and i["due"] <= cut.isoformat()), key=lambda i: i["due"])
    later = sorted((i for i in rows if i not in week), key=lambda i: (area[i["project"]], i.get("due") or "9999"))
    assert sorted(i["id"] for i in week + later + [i for i in live if i.get("drafts")]) == sorted(i["id"] for i in live)
    waiting = sorted(d.get("waiting", []), key=lambda w: w["since"])
    since = today - datetime.timedelta(days=10)
    closed = sorted((i for i in d["items"] if i["status"] in ("done", "dropped") and i["closed"] >= since.isoformat()),
                    key=lambda i: i["closed"], reverse=True)
    done = sum(i["status"] == "done" for i in closed)
    late = sum(i["due"] < today.isoformat() for i in week)
    due_today = sum(i["due"] == today.isoformat() for i in week)
    chips = lambda p, n: {f"{p}{k}": {"type": "dropdown", "enum": enum, "index": 0} for k in range(1, n + 1)}
    out = []

    def section(title, lead, header, lines, blocks=None):
        out.append(f"## {title}\n\n{lead}\n\n| {' | '.join(header)} |\n|{' --- |' * len(header)}\n" + "\n".join(lines))
        if blocks:
            out.append("```json\n" + json.dumps(blocks) + "\n```")

    section("This week", f"{len(week)} loops are due by {cut:%A %-d %B}: {late} are already late and {due_today} are due today. "
            "Set Status to Done or Drop, or type a steer.", ["Status", "Loop", "Due", "Your steer"],
            [f"| <?claude block w{n}?> | {cell(i['title'])} | {day(i['due'])} |  |" for n, i in enumerate(week, 1)],
            chips("w", len(week)))
    section("Waiting on others", f"You're waiting on {len(waiting)} things. Type \"chase\", \"drop\" or \"arrived\" in the last column.",
            ["Who", "What", "Since", "Your steer"],
            [f"| {cell(w['who'])} | {cell(w['what'])} | {day(w['since'])} |  |" for w in waiting])
    section("Later", f"{len(later)} loops have no date before {cut + datetime.timedelta(days=1):%-d %B}, sorted by area.",
            ["Status", "Loop", "Area", "Due", "Your steer"],
            [f"| <?claude block l{n}?> | {cell(i['title'])} | {area[i['project']]} | {day(i.get('due'))} |  |"
             for n, i in enumerate(later, 1)], chips("l", len(later)))
    section(f"Closed since {since:%-d %B}", f"{len(closed)} loops closed, {done} done and {len(closed) - done} dropped. "
            "If one is not really done, comment on it.", ["Loop", "Closed", "How"],
            [f"| {cell(i['title'])} | {'Done' if i['status'] == 'done' else 'Dropped'}, {day(i['closed'])} "
             f"| {cell(i.get('closed_note', '').split('. ')[0])} |" for i in closed])
    return "\n\n".join(out) + "\n"


def main():
    data = json.loads((HERE / "loops.json").read_text(encoding="utf-8"))
    errs = validate(data)
    if errs:
        print("loops.json has problems:\n- " + "\n- ".join(errs))
        sys.exit(1)
    (HERE / "doc_tables.md").write_text(doc_tables(data, datetime.date.today()), encoding="utf-8")
    items = data["items"]
    n_open = sum(i["status"] in ("open", "blocked") for i in items)
    n_send = sum(bool(i.get("drafts")) for i in items if i["status"] in ("open", "blocked"))
    print(f"doc_tables.md built: {n_open} open ({n_send} under Send), "
          f"{len(items) - n_open} closed, {len(data.get('waiting', []))} waiting")


if __name__ == "__main__":
    main()
