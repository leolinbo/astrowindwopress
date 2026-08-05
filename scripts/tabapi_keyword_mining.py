#!/usr/bin/env python3
"""TabAPI 关键词挖掘：SERP organic 标题 + People Also Ask + related searches 聚合"""
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from collections import Counter, OrderedDict
from pathlib import Path

BASE_URL = os.environ.get("TABAPI_BASE_URL", "https://tabapi.com/api/v1")
PROXY = "http://127.0.0.1:7897"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "seo-audit" / "keywords"
OUT.mkdir(parents=True, exist_ok=True)

QUERIES = [
    "led track lighting",
    "commercial track lighting",
    "museum lighting fixtures",
    "art gallery lighting",
    "magnetic track lighting kit",
    "led downlight",
    "recessed downlight 6 inch",
    "commercial led downlight",
    "led lighting manufacturer",
    "wholesale led lighting",
    "led lighting factory china",
    "custom track lighting",
    "track lighting for kitchen",
    "dimmable led track light",
    "track lighting beam angle",
    "cri 95 track lighting",
]


def load_key():
    key = os.environ.get("TABAPI_API_KEY", "")
    if key:
        return key
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("TABAPI_API_KEY="):
                return line.split("=", 1)[1].strip()
    print("❌ 未找到 TABAPI_API_KEY")
    sys.exit(1)


def search(q, key, country="us", lang="en", page=1):
    params = urllib.parse.urlencode({"q": q, "country": country, "language": lang, "page": page})
    url = f"{BASE_URL}/search/google?{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}", "User-Agent": UA})
    proxy = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy)
    with opener.open(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    key = load_key()
    all_titles = []
    all_paa = []
    all_related = []
    raw = OrderedDict()
    for i, q in enumerate(QUERIES, 1):
        try:
            d = search(q, key)
            raw[q] = d
            org = d.get("organic_results") or []
            titles = [r.get("title", "") for r in org if r.get("title")]
            all_titles.extend(titles)
            paa = d.get("people_also_ask") or []
            paas = []
            for item in paa:
                if isinstance(item, dict):
                    t = item.get("question") or item.get("title")
                    if t:
                        paas.append(t)
                elif isinstance(item, str):
                    paas.append(item)
            all_paa.extend(paas)
            rel = d.get("related_searches") or []
            all_related.extend([x if isinstance(x, str) else (x.get("query") or "") for x in rel])
            print(f"[{i}/{len(QUERIES)}] {q}: organic={len(titles)} PAA={len(paas)} related={len(rel)}")
        except Exception as e:
            print(f"[{i}/{len(QUERIES)}] {q}: ❌ {str(e)[:100]}")
        time.sleep(0.5)

    # 保存原始
    (OUT / "keyword-mining-raw.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")

    # 聚合报告
    def words(ts, n=20):
        c = Counter()
        for t in ts:
            for w in t.lower().split():
                w = w.strip("|,.;:()[]—-–“”\"'")
                if len(w) > 2 and w not in {"the", "and", "for", "with", "you", "your", "our", "how", "what", "why", "are", "from", "that", "this", "lighting", "led"}:
                    c[w] += 1
        return c.most_common(n)

    report = {
        "query_count": len(QUERIES),
        "total_organic_titles": len(all_titles),
        "total_questions": len(all_paa),
        "total_related": len(all_related),
        "title_frequency": dict(words(all_titles)),
        "people_also_ask": sorted(set(all_paa)),
        "related_searches": sorted(set(all_related)),
        "raw": {q: {"organic_titles": [r.get("title") for r in (raw.get(q, {}).get("organic_results") or [])],
                     "people_also_ask": [x.get("question") if isinstance(x, dict) else x for x in (raw.get(q, {}).get("people_also_ask") or [])],
                     "related": raw.get(q, {}).get("related_searches") or []} for q in QUERIES},
    }
    (OUT / "keyword-mining-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n=== 汇总 ===")
    print(f"organic 标题 {len(all_titles)} 条 | PAA 问题 {len(all_paa)} 个 | related {len(all_related)} 条")
    print("\n--- 标题高频词 Top 25 ---")
    for w, n in list(report["title_frequency"].items())[:25]:
        print(f"  {w}: {n}")
    print("\n--- People Also Ask（全部去重）---")
    for q in report["people_also_ask"]:
        print(f"  ? {q}")
    print("\n--- Related Searches（全部去重）---")
    for r in report["related_searches"]:
        print(f"  ~ {r}")


if __name__ == "__main__":
    main()
