"""Refresh local SVG cards using public GitHub data; no third-party packages."""

from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = "SevenJL"
ASSETS = Path(__file__).resolve().parents[1] / "assets"


def fetch(path):
    headers = {"User-Agent": "SevenJL-profile", "Accept": "application/vnd.github+json"}
    if token := os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(f"https://api.github.com/{path}", headers=headers), timeout=30) as response:
        return json.load(response)


def render(user, repos, dark):
    bg, panel, text, muted, line = (
        ("#0d1117", "#161b22", "#f0f6fc", "#9daec1", "#30363d") if dark else
        ("#f6f8fa", "#ffffff", "#182538", "#576579", "#d8e0eb")
    )
    original = [repo for repo in repos if not repo["fork"]]
    languages = Counter(repo["language"] for repo in original if repo["language"])
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="380" viewBox="0 0 1200 380" role="img" aria-labelledby="title desc">
<title id="title">SevenJL public GitHub activity</title>
<desc id="desc">Public repository snapshot. Languages count primary languages of non-fork repositories. Updated {stamp}.</desc>
<rect x="1" y="1" width="1198" height="378" rx="24" fill="{bg}" stroke="{line}"/>
<g font-family="Segoe UI, Arial, sans-serif">
<text x="40" y="49" fill="{text}" font-size="24" font-weight="700">OPEN SOURCE / SevenJL</text>
<text x="40" y="77" fill="{muted}" font-size="14">Public repositories · A snapshot of what I build</text>''']
    metrics = [("PUBLIC REPOS", len(repos)), ("NON-FORK REPOS", len(original)),
               ("STARS / NON-FORK", sum(repo["stargazers_count"] for repo in original)),
               ("FOLLOWERS", user["followers"])]
    for i, (label, value) in enumerate(metrics):
        x = 40 + i * 285
        parts.append(f'<rect x="{x}" y="102" width="265" height="104" rx="14" fill="{panel}" stroke="{line}"/><text x="{x+20}" y="131" fill="{muted}" font-size="12" letter-spacing="1">{label}</text><text x="{x+20}" y="183" fill="{text}" font-size="38" font-weight="700">{value}</text>')
    parts.append(f'<text x="40" y="246" fill="{muted}" font-size="13">PRIMARY LANGUAGES / non-fork repositories with a detected language</text>')
    palette = ["#f0a354", "#39bcd0", "#a78bfa", "#4fc69a", "#609bf4", "#ed7e9b"]
    total = sum(languages.values())
    top = languages.most_common(5)
    remainder = total - sum(count for _, count in top)
    if remainder:
        top.append(("Other", remainder))
    x = 40.0
    for i, (name, count) in enumerate(top):
        width = 1120 * count / total
        color = palette[i]
        parts.append(f'<rect x="{x:.2f}" y="267" width="{width:.2f}" height="14" fill="{color}"/><circle cx="{46+i*185}" cy="307" r="5" fill="{color}"/><text x="{60+i*185}" y="312" fill="{text}" font-size="13">{escape(name)} · {count}</text>')
        x += width
    if not total:
        parts.append(f'<text x="40" y="302" fill="{muted}" font-size="14">No detected repository languages yet.</text>')
    parts.append(f'<text x="40" y="353" fill="{muted}" font-size="12">Source: GitHub public API · Updated {stamp}</text></g></svg>')
    return "\n".join(parts) + "\n"


def main():
    user = fetch(f"users/{USERNAME}")
    repos = []
    page = 1
    while True:
        batch = fetch(f"users/{USERNAME}/repos?per_page=100&page={page}&type=owner")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    # Fetch all data before writing: API failures preserve the last successful cards.
    for theme in ("light", "dark"):
        (ASSETS / f"github-activity-{theme}.svg").write_text(render(user, repos, theme == "dark"), encoding="utf-8")
    print(f"Updated {USERNAME}: {len(repos)} public repositories")


if __name__ == "__main__":
    main()
