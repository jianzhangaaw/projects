#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把每个项目的 README 渲染成站点内的详情页（site/projects/*.html）。

背景：卡片原来直接跳 github.com / gitee.com 的项目目录。国内打开 github.com 会卡，
Gitee 的深链对部分访客会弹滑块验证，所以「了解详情」改成站内页面：
点开是本地 HTML，零跳转、不依赖任何代码托管站的可用性。

页面的源码链接（Gitee / GitHub）仍然保留在页头，想读完整代码的人再点出去。

输出（都不进仓库，由 Actions 在部署时生成）：
    site/projects/<项目目录>.html
    site/assets/docs/<项目目录>/<原始相对路径>

用法：
    python tools/build_site_docs.py [--root 仓库根] [--site 站点目录]

判据：README 里引用的图片必须全部存在且被复制，缺一张就非 0 退出。
"""
import argparse
import html
import io
import os
import re
import sys
from pathlib import Path

import markdown

GITEE = "https://gitee.com/jianzhangaaw/project"
GITHUB = "https://github.com/jianzhangaaw/projects"

CARD_RE = re.compile(r'<article class="card">(.*?)</article>', re.S)
H3_RE = re.compile(r'<h3><span class="num">(\d+)</span>(.*?)</h3>', re.S)
DOC_LINK_RE = re.compile(r'href="projects/([a-z0-9-]+)\.html"')
MD_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HTML_IMG_RE = re.compile(r"<img\b([^>]*?)\bsrc=\"([^\"]+)\"([^>]*?)>")
MD_LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")

TEMPLATE = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · 夏遂冬的作品集</title>
<meta name="description" content="{title}：项目说明、截图与运行方式">
<link rel="icon" type="image/png" href="../assets/favicon.png">
<style>
  :root {{ --bg:#f6f7f9; --card:#fff; --ink:#16181d; --muted:#666c78; --line:#e6e8ec; --accent:#2563eb; --accent-soft:#eef3ff; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
         font:16px/1.7 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
              "Hiragino Sans GB", "Microsoft YaHei", "Source Han Sans SC", sans-serif;
         -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:880px; margin:0 auto; padding:30px 24px 64px; }}
  .top {{ display:flex; align-items:center; justify-content:space-between; gap:16px;
          flex-wrap:wrap; margin-bottom:16px; }}
  .back {{ color:var(--accent); text-decoration:none; font-size:14px; }}
  .back:hover {{ text-decoration:underline; }}
  .src {{ font-size:13px; color:var(--muted); }}
  .src a {{ color:var(--muted); text-decoration:none; border-bottom:1px dashed var(--line); }}
  .src a:hover {{ color:var(--accent); border-color:var(--accent); }}
  main {{ background:var(--card); border:1px solid var(--line); border-radius:14px;
          padding:32px 34px 40px; }}
  main h1 {{ font-size:27px; margin:0 0 18px; line-height:1.35; letter-spacing:-.3px; }}
  main h2 {{ font-size:20px; margin:34px 0 12px; padding-top:18px; border-top:1px solid var(--line); }}
  main h3 {{ font-size:17px; margin:24px 0 10px; }}
  main p {{ margin:0 0 14px; }}
  main img {{ max-width:100%; height:auto; border-radius:8px; border:1px solid var(--line);
              display:block; margin:14px 0; }}
  main table {{ border-collapse:collapse; margin:14px 0; width:100%; font-size:14px; }}
  main td {{ border:1px solid var(--line); padding:8px 10px; vertical-align:top; }}
  main td img {{ margin:0; border:0; }}
  main th {{ border:1px solid var(--line); padding:8px 10px; background:#f6f7f9; }}
  main code {{ background:#f2f4f7; padding:2px 5px; border-radius:4px; font-size:.9em; }}
  main pre {{ background:#14161b; color:#e7e9ee; padding:14px 16px; border-radius:10px;
              overflow:auto; font-size:13px; line-height:1.6; }}
  main pre code {{ background:none; padding:0; color:inherit; }}
  main blockquote {{ margin:14px 0; padding:2px 14px; border-left:3px solid var(--accent-soft);
                     color:var(--muted); }}
  main ul, main ol {{ padding-left:22px; margin:0 0 14px; }}
  main li {{ margin:4px 0; }}
  main a {{ color:var(--accent); }}
  main hr {{ border:0; border-top:1px solid var(--line); margin:28px 0; }}
  footer {{ margin-top:24px; color:var(--muted); font-size:13px; }}
  @media (max-width:560px) {{
    .wrap {{ padding:20px 14px 40px; }}
    main {{ padding:22px 18px 28px; }}
    main h1 {{ font-size:23px; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <a class="back" href="../index.html">← 返回作品集</a>
    <span class="src">源码：<a href="{gitee_dir}">Gitee</a> · <a href="{github_dir}">GitHub</a></span>
  </div>
  <main>
{body}
  </main>
  <footer>{num} · {title}</footer>
</div>
</body>
</html>
"""


def read_cards(index_path):
    """从 site/index.html 读出卡片顺序：编号、标题、项目目录。标题与链接只有一处来源。"""
    text = io.open(index_path, encoding="utf-8").read()
    cards = []
    for block in CARD_RE.findall(text):
        head = H3_RE.search(block)
        link = DOC_LINK_RE.search(block)
        if not head or not link:
            continue
        title = re.sub(r"<[^>]+>", "", head.group(2))
        title = re.sub(r"\s+", " ", title).strip()
        cards.append({"num": head.group(1), "title": title, "dir": link.group(1)})
    return cards


def copy_asset(project_root, site_dir, project_dir, src):
    """把 README 里的相对图片复制到 site/assets/docs/<项目>/，返回页面里的相对路径。"""
    source = (project_root / project_dir / src).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"{project_dir}: README 引用的图片不存在 {src}")
    target = site_dir / "assets" / "docs" / project_dir / src
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or target.stat().st_size != source.stat().st_size:
        target.write_bytes(source.read_bytes())
    return "../assets/docs/{}/{}".format(project_dir, src.replace(os.sep, "/"))


def render(text, project_root, site_dir, project_dir):
    copied = []

    def repl_md_img(match):
        alt, src = match.group(1), match.group(2)
        if src.startswith(("http://", "https://", "data:")):
            return match.group(0)
        new = copy_asset(project_root, site_dir, project_dir, src)
        copied.append(src)
        return "![{}]({})".format(alt, new)

    def repl_html_img(match):
        before, src, after = match.group(1), match.group(2), match.group(3)
        if src.startswith(("http://", "https://", "data:")):
            return match.group(0)
        new = copy_asset(project_root, site_dir, project_dir, src)
        copied.append(src)
        return '<img{}src="{}"{}>'.format(before, new, after)

    def repl_link(match):
        label, target = match.group(1), match.group(2)
        if target.startswith(("http://", "https://", "#", "mailto:")):
            return match.group(0)
        # README 里的相对链接在站点上没有对应文件，指向托管站的同一路径
        return "[{}]({}/blob/main/projects/{}/{})".format(
            label, GITEE, project_dir, target.lstrip("./"))

    text = MD_IMG_RE.sub(repl_md_img, text)
    text = HTML_IMG_RE.sub(repl_html_img, text)
    text = MD_LINK_RE.sub(repl_link, text)
    body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "sane_lists", "md_in_html"],
        output_format="html5",
    )
    return body, copied


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--site", default=None)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    site_dir = Path(args.site).resolve() if args.site else root / "site"
    index_path = site_dir / "index.html"
    if not index_path.is_file():
        raise SystemExit(f"找不到 {index_path}")

    cards = read_cards(index_path)
    if len(cards) != 6:
        raise SystemExit(f"site/index.html 里解析出 {len(cards)} 张卡片，期望 7 张")

    out_dir = site_dir / "projects"
    out_dir.mkdir(parents=True, exist_ok=True)

    total_assets = 0
    for card in cards:
        readme = root / "projects" / card["dir"] / "README.md"
        if not readme.is_file():
            raise SystemExit(f"缺少 {readme}")
        body, copied = render(readme.read_text(encoding="utf-8"), root / "projects", site_dir, card["dir"])
        page = TEMPLATE.format(
            title=html.escape(card["title"]),
            body=body,
            num=card["num"],
            gitee_dir=f"{GITEE}/tree/main/projects/{card['dir']}",
            github_dir=f"{GITHUB}/tree/main/projects/{card['dir']}",
        )
        target = out_dir / f"{card['dir']}.html"
        target.write_text(page, encoding="utf-8", newline="\n")
        total_assets += len(copied)
        print(f"{card['num']} {card['dir']:<28} -> site/projects/{target.name}  "
              f"{len(page):>6} 字符  图片 {len(copied)}")

    print(f"\n共生成 {len(cards)} 页，复制图片 {total_assets} 个")


if __name__ == "__main__":
    sys.exit(main())
