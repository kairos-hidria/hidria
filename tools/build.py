import re
import shutil
from pathlib import Path
from markdown import markdown

ROOT = Path(".").resolve()
OUT = ROOT / "_site"

MD_EXTS = ["tables", "fenced_code"]


def convert_obsidian_callouts(md_text: str) -> str:
    """
    Convert Obsidian callouts:

    > [!tip] Title
    > body...

    into HTML blocks compatible with your CSS:
      .callout .callout-title .callout-body and .callout.tip/.summary/...
    """
    lines = md_text.splitlines()
    out = []
    i = 0

    # match:
    # > [!summary] optional title
    # > [!tip]+ optional title
    # > [!warning]- optional title  (we just ignore +/- marker except stripping it)
    head_re = re.compile(r'^\s*>\s*\[!(?P<type>[A-Za-z0-9_-]+)\]\s*(?P<rest>.*)\s*$')
    # also accept the + / - immediately after ] like: [!tip]+ Title
    head_re2 = re.compile(r'^\s*>\s*\[!(?P<type>[A-Za-z0-9_-]+)\]\s*(?P<flag>[+-])?\s*(?P<rest>.*)\s*$')

    def strip_quote_prefix(s: str) -> str:
        # remove one leading '>' and one optional space
        s = re.sub(r'^\s*>\s?', '', s)
        return s

    while i < len(lines):
        m = head_re2.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue

        callout_type = (m.group("type") or "note").lower()
        title = (m.group("rest") or "").strip()
        if not title:
            # fallback title if user didn't provide one
            title = callout_type

        # collect body lines: subsequent blockquote lines that belong to this callout
        body_lines = []
        i += 1
        while i < len(lines):
            line = lines[i]
            # still in blockquote?
            if re.match(r'^\s*>', line):
                body_lines.append(strip_quote_prefix(line))
                i += 1
                continue
            break

        body_md = "\n".join(body_lines).strip()
        body_html = ""
        if body_md:
            body_html = markdown(body_md, extensions=MD_EXTS)

        # emit HTML block (blank lines around help markdown keep layout stable)
        out.append("")
        out.append(f'<div class="callout {callout_type}">')
        out.append(f'  <div class="callout-title">{title}</div>')
        out.append('  <div class="callout-body">')
        out.append(body_html)
        out.append('  </div>')
        out.append('</div>')
        out.append("")

    return "\n".join(out)


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
    ".canvas",  # ✅ 让 canvas 原文件也被拷贝过去（避免 404 / 被当成别的东西）
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

    # ✅ 先把 Obsidian callout 转成 HTML（否则会显示成 [!tip] 文本）
    md_text = convert_obsidian_callouts(md_text)

    # ✅ 用第一个 H1 当页面标题（解决“全是 index”）
    m = re.search(r'^\s*#\s+(.+?)\s*$', md_text, flags=re.M)
    title = m.group(1).strip() if m else rel.stem

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

    out.write_text(html, encoding="utf-8")
