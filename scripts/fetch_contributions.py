"""Baixa o calendário público de contribuições (sem token) e gera data/contributions.json."""

import json
import re
import urllib.request
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

USER = "TiaguinhoCode"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"

CELL_RE = re.compile(r'<td[^>]*class="ContributionCalendar-day"[^>]*>')
ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')
TIP_RE = re.compile(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>')


def fetch_html():
    req = urllib.request.Request(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "Mozilla/5.0 (profile-art bot)"},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        return res.read().decode("utf-8")


def parse(html):
    tips = {}
    for cell_id, text in TIP_RE.findall(html):
        m = re.match(r"\s*(\d+|No)\s+contribution", text)
        tips[cell_id] = 0 if not m or m.group(1) == "No" else int(m.group(1))

    days = []
    for tag in CELL_RE.findall(html):
        attrs = dict(ATTR_RE.findall(tag))
        if "data-date" not in attrs:
            continue
        days.append(
            {
                "date": attrs["data-date"],
                "level": int(attrs.get("data-level", 0)),
                "count": tips.get(attrs.get("id"), 0),
            }
        )
    days.sort(key=lambda d: d["date"])
    return days


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    current = 0
    rev = list(reversed(days))
    # Hoje ainda sem contribuição não quebra a sequência.
    if rev and rev[0]["count"] == 0:
        rev = rev[1:]
    for d in rev:
        if d["count"] == 0:
            break
        current += 1
    return current, longest


def main():
    days = parse(fetch_html())
    if not days:
        raise SystemExit("Nenhum dia encontrado — o HTML do GitHub mudou?")

    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    weekday = Counter()
    months = Counter()
    for d in days:
        dt = date.fromisoformat(d["date"])
        weekday[dt.weekday()] += d["count"]
        months[d["date"][:7]] += d["count"]

    stats = {
        "total": sum(d["count"] for d in days),
        "active_days": sum(1 for d in days if d["count"] > 0),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best,
        "busiest_weekday": weekday.most_common(1)[0][0] if weekday else 0,
        "months": dict(sorted(months.items())),
        "from": days[0]["date"],
        "to": days[-1]["date"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"user": USER, "stats": stats, "days": days}, indent=1))
    print(f"{len(days)} dias, {stats['total']} contribuições -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
