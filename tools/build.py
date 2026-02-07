import re
import shutil
from pathlib import Path
from markdown import markdown

ROOT = Path(".").resolve()
OUT = ROOT / "_site"

# ✅ 关键：md_in_html 让 HTML 块更稳定（callout 不会被吞/转义）
MD_EXTS = ["tables", "fenced_code", "md_in_html"]


def convert_obsidian_callouts(md_text: str) -> str:
    """
    Convert Obsidian callouts:

    > [!tip] Title
    > body...

    Supports:
    > [!summary]+ Title
    > [!warning]- Title

    Output HTML blocks:
      <div class="callout tip">
        <div class="callout-title">Title</div>
        <div class="callout-body"> ... </div>
      </div>
    """
    lines = md_text.splitlines()
    out = []
    i = 0

    # > [!type] + optional_flag + optional_title
    head_re = re.compile(
        r'^\s*>\s*\[!(?P<type>[A-Za-z0-9_-]+)\]\s*(?P<flag>[+-])?\s*(?P<title>.*)\s*$'
    )

    def strip_one_quote(line: str) -> str:
        # remove one leading '>' and one optional space
        return re.sub(r'^\s*>\s?', '', line)

    while i < len(lines):
        m = head_re.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue

        callout_type = (m.group("type") or "note").lower()
        raw_title = (m.group("title") or "").strip()
        title = raw_title if raw_title else callout_type

        # collect subsequent quoted lines as body
        body_lines = []
        i += 1
        while i < len(lines) and re.match(r'^\s*>', lines[i]):
            body_lines.append(strip_one_quote(lines[i]))
            i += 1

        body_md = "\n".join(body_lines).strip()
        # 这里把 callout 内部再跑一次 markdown，生成 <p>/<ul> 等
        body_html = markdown(body_md, extensions=MD_EXTS) if body_md else ""

        out.append("")  # spacing
        out.append(f'<div class="callout {callout_type}">')
        out.append(f'  <div class="callout-title">{title}</div>')
        out.append('  <div class="callout-body">')
        out.append(body_html)
        out.append('  </div>')
        out.append('</div>')
        out.append("")

    return "\n".join(out)


# ========== clean ==========
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True, exist_ok=True)

# ========== copy assets ==========
if (ROOT / "assets").exists():
    shutil.copytree(ROOT / "assets", OUT / "assets")

# ========== copy static files ==========
keep = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".pdf",
    ".css", ".js", ".json", ".yml", ".yaml",
    ".woff", ".woff2", ".ttf", ".otf", ".mp3", ".ogg",
    ".canvas",  # ✅ 让 canvas 原文件也被复制到 _site
}

for f in ROOT.rglob("*"):
    if f.is_dir():
        continue
    if any(p in f.parts for p in [".obsidian", "_site", ".github", "tools"]):
        continue
    if f.suffix.lower() in keep:
        dest = OUT / f.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)

# ========== md -> html ==========
for md in ROOT.rglob("*.md"):
    if any(p in md.parts for p in [".obsidian", "_site", ".github", "tools"]):
        continue

    rel = md.relative_to(ROOT)
    out_html = OUT / rel.with_suffix(".html")
    out_html.parent.mkdir(parents=True, exist_ok=True)

    raw_md = md.read_text(encoding="utf-8")

    # ✅ title 先从原始 md 里抓第一个 H1（别被 callout 转换影响）
    m = re.search(r'^\s*#\s+(.+?)\s*$', raw_md, flags=re.M)
    title = m.group(1).strip() if m else rel.stem

    # ✅ callout 转换（Obsidian 私有语法 → HTML）
    md_text = convert_obsidian_callouts(raw_md)

    # ✅ 主体 markdown
    body = markdown(md_text, extensions=MD_EXTS)

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <link rel="stylesheet" href="/assets/style.css">
</head>
<body>
  <main class="wrap content">
    <article class="card">
      <div class="md">{body}</div>
    </article>
  </main>
</body>
</html>"""

    out_html.write_text(html, encoding="utf-8")
