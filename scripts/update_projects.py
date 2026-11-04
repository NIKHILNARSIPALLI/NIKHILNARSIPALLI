#!/usr/bin/env python3
"""Refresh profile project sections from the owner's public GitHub pushes.

Only edits the delimited PROJECTS block. Uses repository `pushed_at`, never
`updated_at` (which also changes for metadata edits). Runs daily in Actions.
"""

from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
import json
import os
import re
import urllib.request

OWNER = "NIKHILNARSIPALLI"
UTILITY_REPOS = {"Fonts"}  # Asset-only utility repository, not a standalone project.
README = Path(__file__).resolve().parents[1] / "README.md"
VISIBILITY = Path(__file__).resolve().parents[1] / ".github" / "portfolio-visibility.md"
WINDOW = timedelta(days=30)
START = "<!-- PROJECTS:START -->"
END = "<!-- PROJECTS:END -->"

FEATURED = {
    "Telco-Customer-Churn-Prediction-End-to-End-ML-Engineering-Deployment": (
        "featured-telco.gif", "Telco Churn MLOps", "ROC-AUC 0.84 and test accuracy 79.43%",
        "Built a FastAPI/scikit-learn ML service with MLflow, Docker, AWS deployment, CI/CD and monitoring. Evaluated 28 configurations across four classifiers."
    ),
    "StockAnalysisMadeSimple": (
        "featured-stocks.gif", "Stocks Screening Application", "Illustrative stock-screening animation",
        "Python desktop screener using market-data APIs, scraping, configurable filters, and visual results. Animation shows conceptual, not live, market data."
    ),
    "Tweets-Sentiment-prediction": (
        "featured-sentiment.gif", "Tweets Sentiment Prediction", "Illustrative sentiment NLP animation",
        "Sentiment140-based NLP sentiment classifier with a Streamlit interface. Animation is conceptual, not live inference."
    ),
}


def get_repositories():
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-project-updater"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    results = []
    for page in range(1, 4):
        url = f"https://api.github.com/users/{OWNER}/repos?type=owner&per_page=100&page={page}"
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as response:
            batch = json.load(response)
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected response from GitHub repository API")
        results.extend(batch)
        if len(batch) < 100:
            break
    return results


def hidden_repositories():
    """Checked items in the private-to-README checklist are hidden from cards."""
    if not VISIBILITY.exists():
        return set()
    return set(re.findall(r"(?im)^\s*-\s*\[x\]\s*`([^`]+)`\s*$",
                          VISIBILITY.read_text(encoding="utf-8")))


def project_image(repo):
    filename, title, summary, _ = FEATURED[repo["name"]]
    link = f"https://github.com/{OWNER}/{repo['name']}"
    return (f'  <a href="{escape(link, quote=True)}" title="View {escape(title, quote=True)} repository">'
            f'<img src="assets/{filename}" width="30%" alt="{escape(title + ": " + summary, quote=True)}" />'
            f'</a>')


def featured_grid(repos):
    if not repos:
        return ""
    images = "&nbsp;&nbsp;\n".join(project_image(repo) for repo in repos)
    details = "\n\n".join(
        f"  **{FEATURED[repo['name']][1]}**  \n  {FEATURED[repo['name']][3]}"
        for repo in repos
    )
    return (f'<div align="center">\n{images}\n</div>\n\n'
            '<details>\n  <summary><strong>Explore these featured builds</strong></summary>\n\n'
            f'{details}\n</details>')


def other_table(repos):
    if not repos:
        return ""
    cells = []
    for repo in repos:
        name = repo["name"]
        label = name.replace("-", " ")
        description = (repo.get("description") or "Explore the repository and its source code.").strip()
        description = description[:155].rstrip() + ("…" if len(description) > 155 else "")
        language = repo.get("language") or "Project"
        cells.append(f'<td width="50%" valign="top"><a href="https://github.com/{OWNER}/{escape(name, quote=True)}"><strong>{escape(label)}</strong></a><br />{escape(description)}<br /><sub>{escape(language)}</sub></td>')
    rows = []
    for index in range(0, len(cells), 2):
        pair = cells[index:index + 2]
        if len(pair) == 1:
            pair.append('<td width="50%"></td>')
        rows.append("  <tr>" + "".join(pair) + "</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def render(repositories, now=None, hidden=None):
    now = now or datetime.now(timezone.utc)
    hidden = hidden_repositories() if hidden is None else set(hidden)
    threshold = now - WINDOW
    eligible = [r for r in repositories if r.get("name") != OWNER and r.get("name") not in UTILITY_REPOS
                and r.get("name") not in hidden and not r.get("private")
                and not r.get("fork") and not r.get("archived") and r.get("size", 0) > 0
                and r.get("pushed_at")]
    eligible.sort(key=lambda r: r["pushed_at"], reverse=True)
    active = [r for r in eligible if datetime.fromisoformat(r["pushed_at"].replace("Z", "+00:00")) >= threshold]
    inactive = [r for r in eligible if r not in active]
    parts = []
    active_featured = [r for r in active if r["name"] in FEATURED]
    active_other = [r for r in active if r["name"] not in FEATURED]
    if active_featured:
        parts.append(featured_grid(active_featured))
    if active_other:
        parts.append(other_table(active_other))
    if not active:
        parts.append('<p><em>No public project repositories have received a push in the past 30 days. Private or local work may still be in progress.</em></p>')
    parts.append('## ✨ A Few of My Projects')
    inactive_featured = [r for r in inactive if r["name"] in FEATURED]
    inactive_other = [r for r in inactive if r["name"] not in FEATURED]
    if inactive_featured:
        parts.append(featured_grid(inactive_featured))
    if inactive_other:
        parts.append(other_table(inactive_other))
    if not inactive:
        parts.append('<p><em>All listed projects have seen activity in the past 30 days.</em></p>')
    parts.append('<p><em>Project placement refreshes daily using each repository’s last public push date (30-day window).</em></p>')
    return "\n\n".join(parts)


def main():
    text = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if len(pattern.findall(text)) != 1:
        raise RuntimeError("Expected exactly one delimited projects block")
    replacement = f"{START}\n{render(get_repositories())}\n{END}"
    updated = pattern.sub(lambda _: replacement, text)
    if updated != text:
        README.write_text(updated, encoding="utf-8")
        print("Updated README project sections")
    else:
        print("Project sections unchanged")


if __name__ == "__main__":
    main()
