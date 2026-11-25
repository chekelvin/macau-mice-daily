#!/usr/bin/env python3
"""Build the macau-mice-daily static site from newsletter HTML files.

Usage: python3 build.py <source_dir> <out_dir>
Source files must be named macau-mice-ai-newsletter-YYYYMMDD.html
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
NAME_RE = re.compile(r"macau-mice-ai-newsletter-(\d{4})(\d{2})(\d{2})\.html$")
SITE_TITLE = "澳門會展 × AI 每日精選電子報"

NAV_CSS = """<style id="mmd-nav-style">
.mmd-nav{background:#0b1f33;color:#cbd5e1;font:13px/1.4 -apple-system,BlinkMacSystemFont,"PingFang TC","Microsoft JhengHei",sans-serif;padding:8px 16px;display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}
.mmd-nav a{color:#fff;text-decoration:none;padding:4px 10px;border:1px solid rgba(255,255,255,.25);border-radius:6px;white-space:nowrap}
.mmd-nav a:hover{background:rgba(255,255,255,.12)}
.mmd-nav .mmd-off{opacity:.35;padding:4px 10px;border:1px solid rgba(255,255,255,.15);border-radius:6px;white-space:nowrap}
.mmd-nav .mmd-mid{display:flex;gap:6px}
@media print{.mmd-nav{display:none}}
</style>"""


def nav_html(prev_issue, next_issue):
    def link(issue, label):
        if not issue:
            return f'<span class="mmd-off">{label}</span>'
        return f'<a href="/{issue["path"]}">{label}</a>'
    return (
        '<nav class="mmd-nav" data-html2canvas-ignore="true">'
        f'{link(prev_issue, "← 上一期")}'
        '<span class="mmd-mid"><a href="/archive/">往期目錄</a><a href="/latest">最新一期</a></span>'
        f'{link(next_issue, "下一期 →")}'
        '</nav>'
    )


def extract_titles(text):
    return [html.unescape(re.sub(r"<[^>]+>", "", t)).strip()
            for t in re.findall(r'<h2 class="card-title">(.*?)</h2>', text, re.S)]


issues = []
for f in sorted(SRC.glob("macau-mice-ai-newsletter-*.html")):
    m = NAME_RE.search(f.name)
    if not m:
        continue
    y, mo, d = m.groups()
    text = f.read_text(encoding="utf-8")
    issues.append({
        "date": f"{y}-{mo}-{d}",
        "path": f"{y}/{mo}/{d}/",
        "titles": extract_titles(text),
        "src": f,
    })

if not issues:
    sys.exit("No newsletter files found")

issues.sort(key=lambda i: i["date"])
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)

for idx, issue in enumerate(issues):
    prev_i = issues[idx - 1] if idx > 0 else None
    next_i = issues[idx + 1] if idx + 1 < len(issues) else None
    text = issue["src"].read_text(encoding="utf-8")
    text = text.replace("</head>", NAV_CSS + "\n</head>", 1)
    text = re.sub(r"<body([^>]*)>", lambda m: f"<body{m.group(1)}>\n{nav_html(prev_i, next_i)}", text, count=1)
    dest = OUT / issue["path"] / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")

latest = issues[-1]

# issues.json (newest first)
(OUT / "issues.json").write_text(json.dumps(
    [{"date": i["date"], "path": "/" + i["path"], "titles": i["titles"]} for i in reversed(issues)],
    ensure_ascii=False, indent=1), encoding="utf-8")

# Redirects: home and /latest go to newest issue
(OUT / "_redirects").write_text(
    f"/ /{latest['path']} 302\n/latest /{latest['path']} 302\n", encoding="utf-8")

PAGE_CSS = """body{margin:0;background:#f3f5f8;color:#1e293b;font-family:-apple-system,BlinkMacSystemFont,"PingFang TC","Microsoft JhengHei","Noto Sans TC",sans-serif;line-height:1.6}
header{background:#0f2942;color:#fff;padding:28px 20px}
header h1{margin:0 0 4px;font-size:22px}header p{margin:0;color:#cbd5e1;font-size:14px}
main{max-width:820px;margin:0 auto;padding:20px}
input{width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #cbd5e1;border-radius:8px;font-size:15px;margin-bottom:16px}
h2{font-size:16px;color:#0f2942;border-bottom:2px solid #c6922c;padding-bottom:4px;margin:24px 0 10px}
a.issue{display:block;background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px 16px;margin-bottom:10px;text-decoration:none;color:inherit}
a.issue:hover{border-color:#007a5e}
.date{font-weight:700;color:#007a5e}.tag{font-size:12px;background:#c6922c;color:#fff;border-radius:4px;padding:1px 6px;margin-left:6px}
ul{margin:6px 0 0;padding-left:18px;font-size:14px;color:#475569}
footer{text-align:center;color:#94a3b8;font-size:12px;padding:24px}"""

weekdays = "一二三四五六日"


def archive_page():
    import datetime
    groups = {}
    for i in reversed(issues):
        groups.setdefault(i["date"][:7], []).append(i)
    parts = []
    for month, items in groups.items():
        y, m = month.split("-")
        parts.append(f"<h2>{y}年{int(m)}月</h2>")
        for i in items:
            dt = datetime.date.fromisoformat(i["date"])
            tag = '<span class="tag">最新</span>' if i is latest else ""
            lis = "".join(f"<li>{html.escape(t)}</li>" for t in i["titles"][:3])
            search = html.escape(" ".join(i["titles"]), quote=True)
            parts.append(
                f'<a class="issue" href="/{i["path"]}" data-search="{search}">'
                f'<span class="date">{dt.year}年{dt.month}月{dt.day}日（{weekdays[dt.weekday()]}）</span>{tag}'
                f'<ul>{lis}</ul></a>')
    return f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>往期目錄 | {SITE_TITLE}</title><style>{PAGE_CSS}</style></head>
<body><header><h1>{SITE_TITLE}</h1><p>往期目錄・共 {len(issues)} 期</p></header>
<main><input id="q" type="search" placeholder="搜尋標題關鍵字，例如：MIF、AI、橫琴">
{''.join(parts)}</main>
<footer><a href="/latest">返回最新一期</a></footer>
<script>
document.getElementById('q').addEventListener('input',function(e){{var q=e.target.value.trim().toLowerCase();
document.querySelectorAll('a.issue').forEach(function(a){{a.style.display=!q||a.dataset.search.toLowerCase().indexOf(q)>-1?'':'none';}});}});
</script></body></html>"""


(OUT / "archive").mkdir()
(OUT / "archive" / "index.html").write_text(archive_page(), encoding="utf-8")

(OUT / "404.html").write_text(f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>找不到頁面 | {SITE_TITLE}</title><style>{PAGE_CSS}</style></head>
<body><header><h1>{SITE_TITLE}</h1><p>找不到這個頁面</p></header>
<main><p>這一期可能尚未出版或網址有誤。</p><p><a href="/latest">前往最新一期</a>　｜　<a href="/archive/">查看往期目錄</a></p></main>
</body></html>""", encoding="utf-8")

print(f"Built {len(issues)} issue(s); latest {latest['date']}")
for p in sorted(OUT.rglob("*")):
    if p.is_file():
        print(p.relative_to(OUT), p.stat().st_size)
