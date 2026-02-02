import re
import shutil
from pathlib import Path
from markdown import markdown

ROOT = Path(".").resolve()
OUT = ROOT / "_site"

# ---------- helpers ----------

def convert_obsidian_callouts(md_text: str) -> str:
    """
    Convert Obsidian callouts:
    > [!summary]+ Title
    > content...
    into HTML blocks compatible with CSS:
    .callout.summary / .callout-title / .callout-body
    """
    lines = md_text.splitlines()
    out = []
    i = 0

    callout_head = re.compile(r'^\s*>\s*\[!(\w+)\]\s*(?:\+|-)?\s*(.*)\s*$')

    while i < len(lines):
        m = callout_head.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue

        ctype = m.group(1).lower().strip()           # summary/tip/note/warning
        title = m.group(2).strip() or ctype.title()

        # collect all following quoted lines ("> ...")
        i += 1
        body_lines = []
        while i < len(lines) and re.match(r'^\s*>\s?', lines[i]):
            body_lines.append(re.sub(r'^\s*>\s?', '', lines[i]))
            i += 1

        body_md = "\n".join(body_lines).strip()
        body_html = markdown(body_md, extensions=["tables", "fenced_code"])

        # build HTML
        block = f"""
<div class="callout {ctype}">
  <div class="callout-title">{title}</div>
  <div class="callout-body">
    {body_html}
  </div>
</div>
""".strip()

        out.append(block)

    return "\n".join(out)


def cleanup_md(md_text: str) -> str:
    # 1) 修正你经常写的 "</br>"，这种会在HTML里直接显示出来
    md_text = md_text.replace("</br>", "<br>")
    md_text = md_text.replace("</br/>", "<br>")
    md_text = md_text.replace("</br />", "<br>")

    # 2) 也顺手把 Obsidian 的 ==高亮== 变成 <mark>
    md_text = re.sub(r"==(.+?)==", r"<mark>\1</mark>", md_text)

    return md_text


def extract_title(md_text: str, fallback: str) -> str:
    # 取第一个 H1 作为 title
    m = re.search(r'^\s*#\s+(.+?)\s*$', md_text, flags=re.M)
    return m.group(1).strip() if m else fallback


# ---------- build ----------

# clean
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True, exist_ok=True)

# copy assets
if (ROOT / "assets").exists():
    shutil.copytree(ROOT / "assets", OUT / "assets")

# copy non-md static files
keep = {
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".pdf",
    ".css", ".js", ".json", ".yml", ".yaml",
    ".woff", ".woff2", ".ttf", ".otf", ".mp3", ".ogg",
    ".canvas"
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

# md -> html
for md in ROOT.rglob("*.md"):
    if any(p in md.parts for p in [".obsidian", "_site", ".github", "tools"]):
        continue

    rel = md.relative_to(ROOT)
    out = OUT / rel.with_suffix(".html")
    out.parent.mkdir(parents=True, exist_ok=True)

    md_text = md.read_text(encoding="utf-8")
    md_text = cleanup_md(md_text)

    # ✅ callout 转换（在 markdown 渲染之前做）
    md_text = convert_obsidian_callouts(md_text)

    title = extract_title(md_text, rel.stem)

    body = markdown(
        md_text,
        extensions=["tables", "fenced_code"],
        output_format="html5"
    )

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <link rel="stylesheet" href="/assets/style.css">
</head>
<body>
  <div class="bg"></div>
  <main class="wrap content">
    <article class="card">
      <div class="md">{body}</div>
    </article>
  </main>
</body>
</html>"""

    out.write_text(html, encoding="utf-8")

print("Build OK")
