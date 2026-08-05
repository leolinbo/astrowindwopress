#!/usr/bin/env python3
"""
TabAPI 标题 SEO 优化工具
========================
核心：Google Search API 抓取 SERP → 提取竞品标题/关键词 → 辅助标题优化。

用法：
  python scripts/tabapi_seo.py --q "recessed lighting design" [--country us] [--lang en] [--pages 2]
  python scripts/tabapi_seo.py --q "无主灯 筒灯" --country cn --lang zh-CN

输出：
  - 前 N 条竞品标题（直接可参考）
  - 标题高频词统计（关键词权重）
  - 标题长度分析（SEO 截断提示）
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from collections import Counter

BASE_URL = os.environ.get("TABAPI_BASE_URL", "https://tabapi.com/api/v1")
API_KEY = os.environ.get("TABAPI_API_KEY", "")


def load_key():
    """从 .env 读 key（如果环境变量没设）"""
    if API_KEY:
        return API_KEY
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("TABAPI_API_KEY="):
                    return line.split("=", 1)[1].strip()
    print("❌ 未找到 TABAPI_API_KEY（检查 .env）")
    sys.exit(1)


def google_search(q, country="us", lang="en", page=1, key=None):
    """调用 TabAPI Google Search 端点"""
    params = urllib.parse.urlencode({"q": q, "country": country, "language": lang, "page": page})
    url = f"{BASE_URL}/search/google?{params}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {key}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None


def analyze(q, country, lang, pages):
    key = load_key()
    print(f"🔍 搜索: {q} (country={country}, lang={lang}, pages={pages})\n")
    all_titles = []
    for page in range(1, pages + 1):
        data = google_search(q, country, lang, page, key)
        if not data:
            break
        results = data.get("organic_results", [])
        if not results:
            print(f"(第 {page} 页无结果)")
            break
        print(f"=== 第 {page} 页 ===")
        for r in results:
            title = r.get("title", "")
            link = r.get("link", "")
            pos = r.get("position", "?")
            print(f"[{pos}] {title}")
            print(f"     {link}")
            all_titles.append(title)
        time.sleep(1.5)  # 避免过快请求

    if not all_titles:
        return

    # 关键词权重分析（去掉停用词）
    stopwords = set("a an the of to in for on with and or is are was were be by from at as it its this that these those your you we our how what why which who when where can could should would will do does did not no".split())
    words = Counter()
    for t in all_titles:
        for w in t.lower().split():
            w = w.strip(":;,()[]\"'!?.")
            if w and w not in stopwords and len(w) > 1:
                words[w] += 1

    print("\n=== 标题高频词（关键词权重）===")
    for word, cnt in words.most_common(15):
        print(f"  {word}: {cnt}")

    # 标题长度分析
    print("\n=== 标题长度分析 ===")
    lens = [len(t) for t in all_titles]
    if lens:
        print(f"  平均 {sum(lens)/len(lens):.0f} 字符 | 最短 {min(lens)} | 最长 {max(lens)}")
        print(f"  >60 字符会被 Google 截断: {sum(1 for l in lens if l > 60)}/{len(lens)} 个标题超限")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="TabAPI 标题 SEO 优化")
    ap.add_argument("--q", required=True, help="搜索关键词")
    ap.add_argument("--country", default="us", help="国家代码 (us/cn/...)")
    ap.add_argument("--lang", default="en", help="语言 (en/zh-CN/...)")
    ap.add_argument("--pages", type=int, default=1, help="抓取页数 (默认 1)")
    args = ap.parse_args()
    analyze(args.q, args.country, args.lang, args.pages)
