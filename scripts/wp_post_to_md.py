#!/usr/bin/env python3
"""WP 文章 HTML → 本地 MD 转换（一次性迁移脚本）"""
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

HOME = Path.home()
ROOT = Path(r"C:\Users\Administrator\Desktop\astrowind")
IMG_PREFIX = "/images/blog/custom-track/"
ASSET_IMG = "~/assets/images/custom-track-factory.jpg"


class MDConverter(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip = 0
        self.in_fig = False
        self.fig_img = None
        self.fig_caption = []
        self.in_table = False
        self.table_rows = []
        self.row = []
        self.cell = []
        self.in_cell = False
        self.is_header_row = False
        self.list_stack = []
        self.in_a = 0
        self.a_href = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style"):
            self.skip += 1
            return
        if self.skip:
            return
        if tag == "h2":
            self.out.append("\n\n## ")
        elif tag == "h3":
            self.out.append("\n\n### ")
        elif tag == "h4":
            self.out.append("\n\n#### ")
        elif tag == "p":
            self.out.append("\n\n")
        elif tag == "strong":
            self.out.append("**")
        elif tag == "em":
            self.out.append("*")
        elif tag == "a":
            self.in_a += 1
            self.a_href = a.get("href")
            self.out.append("[")
        elif tag == "ul":
            self.list_stack.append("- ")
            self.out.append("\n\n")
        elif tag == "ol":
            self.list_stack.append("1. ")
            self.out.append("\n\n")
        elif tag == "li":
            self.out.append("\n" + self.list_stack[-1])
        elif tag == "blockquote":
            self.out.append("\n\n> ")
        elif tag == "br":
            self.out.append("\n")
        elif tag == "figure":
            self.in_fig = True
            self.fig_img = None
            self.fig_caption = []
        elif tag == "img" and self.in_fig:
            src = a.get("src", "")
            alt = a.get("alt", "")
            name = src.rsplit("/", 1)[-1]
            self.fig_img = (name, alt)
        elif tag == "figcaption":
            self.fig_caption = []
        elif tag == "table":
            self.in_table = True
            self.table_rows = []
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.in_cell = True
            self.cell = []
            if tag == "th":
                self.is_header_row = True
        elif tag == "hr":
            self.out.append("\n\n---\n\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            if self.skip:
                self.skip -= 1
            return
        if self.skip:
            return
        if tag == "h2" or tag == "h3" or tag == "h4":
            self.out.append("\n")
        elif tag == "p":
            self.out.append("\n")
        elif tag == "strong":
            self.out.append("**")
        elif tag == "em":
            self.out.append("*")
        elif tag == "a":
            self.in_a -= 1
            self.out.append(f"]({self.a_href})" if self.a_href else "]()")
            self.a_href = None
        elif tag == "li":
            self.out.append("\n")
        elif tag == "figure":
            if self.fig_img:
                name, alt = self.fig_img
                cap = "".join(self.fig_caption).strip()
                self.out.append(f"\n\n![{alt}]({IMG_PREFIX}{name})\n\n")
                if cap:
                    self.out.append(f"*{cap}*\n\n")
            self.in_fig = False
        elif tag == "figcaption":
            pass
        elif tag in ("td", "th"):
            self.in_cell = False
            self.row.append("".join(self.cell).strip())
        elif tag == "tr":
            self.table_rows.append(self.row)
            self.row = []
        elif tag == "table":
            self.in_table = False
            self.out.append("\n\n")
            if self.table_rows:
                header = self.table_rows[0]
                self.out.append("| " + " | ".join(header) + " |\n")
                self.out.append("| " + " | ".join(["---"] * len(header)) + " |\n")
                for r in self.table_rows[1:]:
                    self.out.append("| " + " | ".join(r) + " |\n")
            self.out.append("\n")

    def handle_data(self, data):
        if self.skip:
            return
        if self.in_fig and self.fig_caption is not None and self.fig_img is None:
            pass
        if self.in_cell:
            self.cell.append(data)
        elif self.in_fig:
            self.fig_caption.append(data)
        else:
            self.out.append(data)


def main():
    posts = json.loads((HOME / "wp_posts.json").read_text(encoding="utf-8"))
    p = posts[0]
    raw_html = p["content"]["rendered"]

    conv = MDConverter()
    conv.feed(raw_html)
    body = "".join(conv.out)
    # 清理多余空行
    body = re.sub(r"\n{4,}", "\n\n\n", body)
    body = body.strip() + "\n"

    excerpt = re.sub(r"<[^>]+>", "", p["excerpt"]["rendered"]).strip()
    title = html.unescape(p["title"]["rendered"])
    date = p["date"].replace("T", "T")  # 2026-07-24T09:38:09

    fm = f"""---
publishDate: {date}
title: '{title}'
excerpt: '{excerpt}'
image: '{ASSET_IMG}'
category: 'Custom & OEM Lighting'
tags:
  - custom track lighting manufacturer
  - ODM lighting
  - OEM track lighting
author: ENCORE
metadata:
  description: '{excerpt}'
---

{body}"""
    dest = ROOT / "src" / "data" / "post" / "custom-track-lighting-manufacturer-what-custom-really-means.md"
    dest.write_text(fm, encoding="utf-8")
    print(f"✅ 已生成 {dest.name} ({len(fm)//1024}KB)")
    print("=== 前 60 行预览 ===")
    print("\n".join(fm.split("\n")[:60]))


if __name__ == "__main__":
    main()
