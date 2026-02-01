import re
import shutil
from pathlib import Path
from markdown import markdown

ROOT = Path(".").resolve()
OUT = ROOT / "_site"

# clean
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True, exist_ok=True)

# copy assets
if (ROOT / "assets").exists():
    shutil.copytree(ROOT / "assets", OUT / "assets")

# copy non-md static files
keep = {
    ".png",".jpg",".jpeg",".webp",".gif",".svg",".pdf",
    ".css",".js",".json",".yml",".yaml",
    ".woff",".woff2",".ttf",".otf",".mp3",".ogg"
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

    # ✅ 用第一个 H1 当页面标题（解决“全是 index”）
    m = re.search(r'^\s*#\s+(.+?)\s*$', md_text, flags=re.M)
    title = m.group(1).strip() if m else rel.stem

    body = markdown(md_text, extensions=["tables", "fenced_code"])

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
