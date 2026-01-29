# tools/rewriter.py
import re
from pathlib import Path

BASE = "/hidria/"  # 你的站点项目路径（repo 名）

# 只重写站内相对链接：不动 http/https/mailto/#/javascript/ 开头的
SKIP_PREFIX = ("http://", "https://", "mailto:", "#", "javascript:")

def rewrite_attr(html: str, attr: str) -> str:
    # 匹配 href="..." / src="..."
    pattern = re.compile(rf'{attr}="([^"]+)"')

    def repl(m):
        url = m.group(1)

        # 跳过外链、锚点等
        if url.startswith(SKIP_PREFIX):
            return m.group(0)

        # 跳过已经是站点根路径的（以 / 开头）
        if url.startswith("/"):
            return m.group(0)

        # 跳过纯查询/纯锚点这种
        if url.startswith("?"):
            return m.group(0)

        # 归一化：去掉开头的 ./ 
        if url.startswith("./"):
            url2 = url[2:]
        else:
            url2 = url

        # ⭐ 核心：把“你写的 vault 根相对路径”强制变成“站点根路径”
        # 也就是：hs/... -> /hidria/hs/...
        new = BASE + url2

        return f'{attr}="{new}"'

    return pattern.sub(repl, html)

def main():
    site = Path("_site")
    for p in site.rglob("*.html"):
        html = p.read_text(encoding="utf-8")
        html = rewrite_attr(html, "href")
        html = rewrite_attr(html, "src")
        p.write_text(html, encoding="utf-8")

if __name__ == "__main__":
    main()
