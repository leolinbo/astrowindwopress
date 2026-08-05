#!/usr/bin/env python3
"""分析 crawl_data.json，产出 qiaomu-seo 审计发现清单"""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(r"C:\Users\Administrator\Desktop\astrowind\outputs\seo-audit")
data = json.loads((OUT / "crawl_data.json").read_text(encoding="utf-8"))
pages = data["pages"]

html_pages = {u: r for u, r in pages.items() if r.get("title") is not None or r.get("html_len", 0) > 5000}
html_pages = {u: r for u, r in html_pages.items() if "rss" not in u}

print("=== 1) 标题 ===")
dups = defaultdict(list)
for u, r in html_pages.items():
    t = (r.get("title") or "").strip()
    dups[t].append(u)
for t, us in dups.items():
    if len(us) > 1:
        print(f"  重复标题 ({len(us)}): {t!r} -> {[u.replace(data['base'],'') for u in us]}")
for u, r in html_pages.items():
    t = r.get("title") or ""
    if "— ENCORE" in t and t.rstrip().endswith("— ENCORE — ENCORE"):
        pass
    if t.count("ENCORE") >= 3:
        print(f"  品牌重复: {u.replace(data['base'],'')} -> {t}")
print("  标题长度范围:", min(r.get('title_len',0) for r in html_pages.values()), "-",
      max(r.get('title_len',0) for r in html_pages.values()))

print("\n=== 2) Meta Description ===")
missing_desc = [u for u, r in html_pages.items() if not r.get("meta_desc")]
short_desc = [(u, r.get("meta_desc_len")) for u, r in html_pages.items()
              if r.get("meta_desc") and (r.get("meta_desc_len") < 50 or r.get("meta_desc_len") > 165)]
print(f"  缺失: {len(missing_desc)} {[u.replace(data['base'],'') for u in missing_desc]}")
print(f"  长度异常(<50 或 >165): {short_desc}")
for u, r in list(html_pages.items()):
    d = r.get("meta_desc") or ""
    if d and (d.startswith("ENCORE") or "|" in d[:20]):
        pass

print("\n=== 3) Canonical / robots ===")
no_canon = [u for u, r in html_pages.items() if not r.get("canonical")]
mismatch = [(u, r.get("canonical")) for u, r in html_pages.items()
            if r.get("canonical") and r["canonical"].rstrip("/") != u.rstrip("/")]
print(f"  缺 canonical: {no_canon}")
print(f"  canonical 不一致: {mismatch}")
no_robots = [u for u, r in html_pages.items() if not r.get("robots")]
print(f"  无 robots meta (正常): {len(no_robots)} 页")

print("\n=== 4) H1 ===")
no_h1 = [u for u, r in html_pages.items() if not r.get("h1")]
multi_h1 = [(u, len(r.get("h1", []))) for u, r in html_pages.items() if len(r.get("h1", [])) > 1]
print(f"  缺 H1: {no_h1}")
print(f"  多 H1: {multi_h1}")

print("\n=== 5) JSON-LD 结构化数据 ===")
for u, r in html_pages.items():
    for j in r.get("jsonld", []):
        try:
            d = json.loads(j)
            types = d.get("@type") if isinstance(d, dict) else None
            if isinstance(types, list):
                types = ",".join(types)
            print(f"  {u.replace(data['base'],'')}: {types}")
        except Exception:
            print(f"  {u.replace(data['base'],'')}: JSONLD 解析失败 {j[:80]!r}")

print("\n=== 6) 图片 ===")
tot_img, no_alt, no_src = 0, 0, 0
formats = Counter()
loading = Counter()
for u, r in html_pages.items():
    for im in r.get("imgs", []):
        tot_img += 1
        src = im.get("src") or ""
        if not src:
            no_src += 1
        elif not im.get("alt"):
            no_alt += 1
        ext = re.search(r"\.([a-z0-9]{2,4})(\?|$)", src.split("/")[-1], re.I)
        formats[ext.group(1).lower() if ext else "?"] += 1
        loading[im.get("loading") or "无"] += 1
print(f"  总图 {tot_img}, 无alt {no_alt}, 无src {no_src}")
print(f"  格式: {dict(formats)}")
print(f"  loading: {dict(loading)}")

print("\n=== 7) OG / Twitter ===")
no_og = [u for u, r in html_pages.items() if not r.get("og_title")]
no_tw = [u for u, r in html_pages.items() if not r.get("twitter_card")]
print(f"  缺 og:title: {len(no_og)} {no_og[:6]}")
print(f"  缺 twitter:card: {len(no_tw)} {no_tw[:6]}")

print("\n=== 8) 内链 / 外链 ===")
ext_links = Counter()
for u, r in html_pages.items():
    for h in r.get("links", []):
        if h.startswith("http") and not h.startswith(data["base"]):
            ext_links[re.sub(r"https?://([^/]+).*", r"\1", h)] += 1
print("  外链域名 Top:", ext_links.most_common(10))

print("\n=== 9) 页面体积 (HTML) ===")
for u, r in sorted(html_pages.items(), key=lambda x: -x[1].get("html_len", 0))[:8]:
    print(f"  {r.get('html_len')//1024}KB {u.replace(data['base'],'')}")

print("\n=== 10) 首页 H1/H2 结构 ===")
home = html_pages.get(data["base"] + "/", {})
print("  H1:", home.get("h1"))
print("  H2 数量:", home.get("h2_count"), home.get("h2", [])[:8])

print("\n=== 11) 外链锚文本（找模板残留）===")
for u, r in html_pages.items():
    if u in (data["base"] + "/", data["base"] + "/about"):
        for h, txt in zip(r.get("links", []), []):
            pass
