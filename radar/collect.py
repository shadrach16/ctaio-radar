"""Step 1 - collect: pull the week's agentic-coding signals from Hacker News.

Deterministic, no LLM. Output is the single source of truth every later
step must cite - agents are never allowed to introduce facts that are not
in signals.json.
"""
import json
import sys
import time
import urllib.parse
import urllib.request

QUERIES = ["Claude Code", "agentic coding", "Cursor AI", "Aider"]
WINDOW_DAYS = 7
MIN_POINTS = 20

def fetch(query: str) -> list[dict]:
    since = int(time.time()) - WINDOW_DAYS * 86400
    url = (
        "https://hn.algolia.com/api/v1/search?"
        + urllib.parse.urlencode(
            {
                "query": query,
                "tags": "story",
                "numericFilters": f"created_at_i>{since},points>{MIN_POINTS}",
                "hitsPerPage": 10,
            }
        )
    )
    with urllib.request.urlopen(url, timeout=20) as r:
        hits = json.load(r)["hits"]
    return [
        {
            "title": h["title"],
            "url": h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
            "hn": f"https://news.ycombinator.com/item?id={h['objectID']}",
            "points": h["points"],
            "comments": h.get("num_comments", 0),
            "query": query,
        }
        for h in hits
        if h.get("title")
    ]

def main() -> None:
    seen, signals = set(), []
    for q in QUERIES:
        for s in fetch(q):
            if s["url"] not in seen:
                seen.add(s["url"])
                signals.append(s)
    signals.sort(key=lambda s: -s["points"])
    if len(signals) < 3:
        sys.exit("collect: fewer than 3 signals - refusing to draft from thin air")
    with open("artifacts/signals.json", "w", encoding="utf-8") as f:
        json.dump(signals, f, indent=2)
    print(f"collect: {len(signals)} signals -> artifacts/signals.json")

if __name__ == "__main__":
    main()
