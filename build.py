#!/usr/bin/env python3
"""Validate loops.json and write doc_tables.md, the doc's sections in ranked order.

One section per Eisenhower quadrant, most urgent and important first. Each lists its Tasks (loops
without a draft), then its Messages to send (loops closed by a draft): checklist lines with a time
estimate, due date, draft numbers and a link to the source. Then Waiting on others and Closed.

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
        live = i.get("status") in ("open", "blocked")
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
        if live and i.get("q") not in (1, 2, 3, 4):
            errs.append(f"{iid}: open item needs q, its Eisenhower quadrant (1 to 4)")
        if live and not (isinstance(i.get("est"), int) and i["est"] > 0):
            errs.append(f"{iid}: open item needs est, its time estimate in minutes")
        if i.get("url") and not str(i["url"]).startswith("http"):
            errs.append(f"{iid}: url must be a web link")
    for w in d.get("waiting", []):
        if not w.get("who") or not w.get("what") or bad_date(w.get("since")):
            errs.append(f"waiting {w.get('who')!r}: needs who, what and an ISO since")
    return errs


def day(iso):
    return datetime.date.fromisoformat(iso).strftime("%a %-d %b") if iso else ""


QUADRANTS = {  # Eisenhower: (heading, lead)
    1: ("Do now: urgent and important", "{n} loops that matter and can't wait. Start at the top: tick a loop when it's done, or type a steer under it."),
    2: ("Plan: important, not urgent", "{n} loops that matter but have time. Give each a slot this week."),
    3: ("Quick or hand off: urgent, less important", "{n} loops with a date but little at stake. Do them in minutes or hand them off."),
    4: ("Later or drop: not urgent, less important", "{n} loops with no date and little at stake. Drop what no longer matters: type \"drop\" under it."),
}


def quadrant(i, today):
    """The item's stored quadrant `q`, made urgent (2 to 1, 4 to 3) once its due date is two days away or past."""
    if i["q"] in (2, 4) and i.get("due") and i["due"] <= (today + datetime.timedelta(days=2)).isoformat():
        return i["q"] - 1
    return i["q"]


def mins(m):
    """A time estimate in minutes as the doc shows it: 45 min, 1.5 h, 8 h (hours to the nearest half)."""
    return f"{m} min" if m < 60 else f"{int(m / 30 + 0.5) / 2:g} h"


def doc_tables(d, today):
    """The doc's sections as markdown, most urgent and important first.

    Each quadrant: a Tasks checklist, a Messages to send checklist, then the list of drafts (number,
    reference, loop) to paste in full under it. Then Waiting on others and Closed.
    """
    cell = lambda s: s.replace("|", "/").rstrip(".")
    live = [i for i in d["items"] if i["status"] in ("open", "blocked")]
    groups = {q: sorted((i for i in live if quadrant(i, today) == q), key=lambda i: (i.get("due") or "9999", i["title"]))
              for q in QUADRANTS}
    assert sum(map(len, groups.values())) == len(live)

    def line(i, nums=()):
        src = i.get("src")
        tail = [mins(i["est"]), day(i.get("due")),
                (("draft " if len(nums) == 1 else "drafts ") + ", ".join(nums)) if nums else "",
                (f"[{src}]({i['url']})" if i.get("url") else src) if src else ""]
        return "- [ ] " + cell(i["title"]) + "".join(f" · {x}" for x in tail if x)

    out, n_draft = [], 0
    for q, (title, lead) in QUADRANTS.items():
        group = groups[q]
        if not group:
            continue
        tasks = [i for i in group if not i.get("drafts")]
        msgs = [i for i in group if i.get("drafts")]
        parts = [f"## {title}", lead.format(n=len(group)) + f" About {mins(sum(i['est'] for i in group))} in all."]
        if tasks:
            parts += [f"**Tasks** · {len(tasks)}, about {mins(sum(i['est'] for i in tasks))}",
                      "\n".join(line(i) for i in tasks)]
        rows, drafts = [], []
        for i in msgs:
            nums = []
            for ref in i["drafts"]:
                n_draft += 1
                nums.append(str(n_draft))
                drafts.append(f"{n_draft} | {ref} | {i['id']} | {cell(i['title'])}")
            rows.append(line(i, nums))
        if msgs:
            parts += [f"**Messages to send** · {len(msgs)}, about {mins(sum(i['est'] for i in msgs))}", "\n".join(rows)]
        out.append("\n\n".join(parts))
        if drafts:
            out.append("Drafts to paste in full under this section (number | draft | loop id | loop):\n\n" + "\n".join(drafts))

    waiting = sorted(d.get("waiting", []), key=lambda w: w["since"])
    link = lambda w: (f"[{w['src']}]({w['url']})" if w.get("url") else w["src"]) if w.get("src") else ""
    out.append(f"## Waiting on others\n\nYou're waiting on {len(waiting)} things. Type \"chase\", \"drop\" or \"arrived\" "
               "in the last column.\n\n| Who | What | Since | Source | Your steer |\n| --- | --- | --- | --- | --- |\n"
               + "\n".join(f"| {cell(w['who'])} | {cell(w['what'])} | {day(w['since'])} | {link(w)} |  |" for w in waiting))
    since = today - datetime.timedelta(days=10)
    closed = sorted((i for i in d["items"] if i["status"] in ("done", "dropped") and i["closed"] >= since.isoformat()),
                    key=lambda i: i["closed"], reverse=True)
    done = sum(i["status"] == "done" for i in closed)
    out.append(f"## Closed since {since:%-d %B}\n\n{len(closed)} loops closed, {done} done and {len(closed) - done} dropped. "
               "If one is not really done, comment on it.\n\n| Loop | Closed | How |\n| --- | --- | --- |\n"
               + "\n".join(f"| {cell(i['title'])} | {'Done' if i['status'] == 'done' else 'Dropped'}, {day(i['closed'])} "
                           f"| {cell(i.get('closed_note', '').split('. ')[0])} |" for i in closed))
    return "\n\n".join(out) + "\n"


def _check():
    t = datetime.date(2026, 11, 23)
    assert quadrant({"q": 2, "due": "2026-11-25"}, t) == 1   # due in two days: urgent now
    assert quadrant({"q": 2, "due": "2026-11-26"}, t) == 2
    assert quadrant({"q": 4, "due": "2026-10-20"}, t) == 3   # overdue and unimportant: quick
    assert quadrant({"q": 3, "due": None}, t) == 3
    assert [mins(m) for m in (5, 45, 75, 90, 120, 480)] == ["5 min", "45 min", "1.5 h", "1.5 h", "2 h", "8 h"]


def main():
    _check()
    data = json.loads((HERE / "loops.json").read_text(encoding="utf-8"))
    errs = validate(data)
    if errs:
        print("loops.json has problems:\n- " + "\n- ".join(errs))
        sys.exit(1)
    (HERE / "doc_tables.md").write_text(doc_tables(data, datetime.date.today()), encoding="utf-8")
    items = data["items"]
    live = [i for i in items if i["status"] in ("open", "blocked")]
    n_msg = sum(bool(i.get("drafts")) for i in live)
    print(f"doc_tables.md built: {len(live)} open ({len(live) - n_msg} tasks, {n_msg} messages, about "
          f"{mins(sum(i['est'] for i in live))} of work), {len(items) - len(live)} closed, "
          f"{len(data.get('waiting', []))} waiting")


if __name__ == "__main__":
    main()
