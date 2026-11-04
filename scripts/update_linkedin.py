"""Render up to four curated LinkedIn posts as GitHub-safe SVG tiles.

Add/update posts via the 'Add LinkedIn post' GitHub Actions workflow, or edit
linkedin/posts.json manually. No LinkedIn scraping or private API is used.
"""
import json
import re
from pathlib import Path
from urllib.parse import urlparse
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "linkedin" / "posts.json"
README = ROOT / "README.md"
ASSETS = ROOT / "assets"
START = "<!-- LINKEDIN:START -->"
END = "<!-- LINKEDIN:END -->"
COLORS = ["#DAB0D4", "#A788D1", "#C69AC6", "#D6B7E0"]


def normalize_post(post):
    link = str(post.get("url", "")).strip()
    parsed = urlparse(link)
    if parsed.scheme != "https" or parsed.hostname not in {"lnkd.in", "www.linkedin.com", "linkedin.com"}:
        raise ValueError(f"Not a LinkedIn HTTPS post URL: {link}")
    return {"url": link, "title": str(post.get("title") or "A new update on LinkedIn")[:90],
            "date": str(post.get("date") or "")[:30],
            "image": str(post.get("image") or "").strip()}


def card_svg(post, index):
    title = escape(post["title"])
    date = escape(post["date"] or "LATEST UPDATE")
    accent = COLORS[index % len(COLORS)]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="680" height="400" viewBox="0 0 680 400">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#241629"/><stop offset="1" stop-color="#493050"/></linearGradient></defs>
<rect x="1" y="1" width="678" height="398" rx="22" fill="url(#bg)" stroke="#815D88" stroke-width="2"/>
<circle cx="595" cy="68" r="110" fill="none" stroke="{accent}" stroke-opacity=".16" stroke-width="2"/>
<circle cx="595" cy="68" r="75" fill="none" stroke="{accent}" stroke-opacity=".27" stroke-width="2"/>
<circle cx="595" cy="68" r="40" fill="{accent}" fill-opacity=".12"/>
<path d="M28 100 H652" stroke="#6C4A72" stroke-width="2"/>
<rect x="30" y="30" width="54" height="54" rx="10" fill="{accent}"/>
<text x="44" y="68" font-family="Arial,sans-serif" font-weight="bold" font-size="31" fill="#241629">in</text>
<text x="103" y="63" font-family="Arial,sans-serif" letter-spacing="3" font-weight="bold" font-size="18" fill="#F3E8F2">LINKEDIN / POST {index + 1:02d}</text>
<text x="36" y="150" font-family="Arial,sans-serif" font-size="17" fill="{accent}">{date}</text>
<text x="36" y="228" font-family="Arial,sans-serif" font-weight="bold" font-size="30" fill="#F8EAF7">SHARED ON LINKEDIN</text>
<text x="36" y="268" font-family="Arial,sans-serif" font-size="17" fill="#CDB8CE">{title[:51]}</text>
<rect x="30" y="324" width="620" height="48" rx="12" fill="#63436A"/>
<text x="52" y="354" font-family="Arial,sans-serif" font-weight="bold" font-size="17" fill="#FFFFFF">VIEW ORIGINAL POST</text>
<path d="M602 348 h20 m-9 -9 9 9 -9 9" fill="none" stroke="#FFFFFF" stroke-width="3"/>
</svg>'''


def render(posts):
    cells = []
    for index, post in enumerate(posts[:4]):
        path = f"assets/linkedin-post-{index + 1}.svg"
        (ROOT / path).write_text(card_svg(post, index), encoding="utf-8")
        # When a verified user-supplied image is present, use it as the preview.
        image = post["image"] if post["image"].startswith("https://") else path
        title = escape(post["title"], {'"': '&quot;'})
        cells.append(f'<td width="50%" align="center" valign="top"><a href="{escape(post["url"], {chr(34): "&quot;"})}"><img src="{escape(image, {chr(34): "&quot;"})}" alt="{title}" width="100%" /></a></td>')
    rows = []
    for offset in range(0, len(cells), 2):
        rows.append("<tr>" + "".join(cells[offset:offset + 2]) + ("<td width=\"50%\"></td>" if offset + 1 == len(cells) else "") + "</tr>")
    return ('## 💬 Latest on LinkedIn\n\n'
            '<p><em>Ideas, projects and lessons beyond the commit history. Click a tile to read the original post.</em></p>\n\n'
            '<table>\n' + "\n".join(rows) + '\n</table>\n\n'
            '<p align="center"><a href="https://www.linkedin.com/in/nikhilnarsipalli/recent-activity/all/">Explore more on LinkedIn</a></p>\n')


def main():
    posts = [normalize_post(p) for p in json.loads(DATA.read_text(encoding="utf-8"))][:4]
    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        raise ValueError("LinkedIn section markers missing from README")
    begin, tail = readme.split(START, 1)
    _, end = tail.split(END, 1)
    README.write_text(begin + START + "\n" + render(posts) + END + end, encoding="utf-8")


if __name__ == "__main__":
    main()
