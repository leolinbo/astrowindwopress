#!/usr/bin/env python3
"""qiaomu-seo 全站审计爬虫：发现 -> 抓取 -> 解析 -> 覆盖清单"""
import json
import re
import time
import urllib.request
import urllib.parse
from html.parser import HTMLParser
from collections import Counter, defaultdict
from pathlib import Path

BASE = "https://astrowindwopress.vercel.app"
PROXY = "http://127.0.0.1:7897"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
OUT = Path(r"C:\Users\Administrator\Desktop\astrowind\outputs\seo-audit")
OUT.mkdir(parents=True, exist_ok=True)


def fetch(url, method="GET"):
    """返回 (status, headers, body_bytes)；跟随重定向记录链。"""
    proxy = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    chain = []
    try:
        resp = opener.open(req, timeout=30)
        body = resp.read()
        chain.append((resp.geturl(), resp.status))
        return resp.status, {k.lower(): v for k, v in resp.headers.items()}, body, chain
    except urllib.error.HTTPError as e:
        body = e.read()
        chain.append((e.geturl(), e.code))
        return e.code, {k.lower(): v for k, v in e.headers.items()}, body, chain
    except Exception as e:
        return None, {}, b"", [str(e)[:120]]


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = None
        self.meta = {}          # name -> content
        self.property = {}      # property -> content
        self.canonical = None
        self.h1 = []
        self.h2 = []
        self.links = []         # (href, text)
        self.imgs = []          # (src, alt, loading, width, height)
        self.jsonld = []
        self.robots = None
        self.lang = None
        self._in_title = False
        self._buf = []
        self._in_h = None
        self._h_buf = []
        self._in_a = False
        self._a_href = None
        self._a_buf = []
        self._script_type = None
        self._script_buf = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "noscript"):
            self._skip += 1
            if tag == "script" and a.get("type", "").lower() in ("application/ld+json", "application/json"):
                self._script_type = a.get("type")
                self._script_buf = []
            return
        if self._skip:
            return
        if tag == "title":
            self._in_title = True
            self._buf = []
        elif tag == "h1":
            self._in_h = "h1"
            self._h_buf = []
        elif tag == "h2":
            self._in_h = "h2"
            self._h_buf = []
        elif tag == "meta":
            name = a.get("name")
            prop = a.get("property")
            content = a.get("content", "")
            if name:
                self.meta[name.lower()] = content
            if prop:
                self.property[prop.lower()] = content
            if a.get("rel") == "canonical":
                pass
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        elif tag == "a":
            self._in_a = True
            self._a_href = a.get("href")
            self._a_buf = []
        elif tag == "img":
            self.imgs.append({
                "src": a.get("src") or a.get("data-src") or "",
                "alt": a.get("alt"),
                "loading": a.get("loading"),
                "w": a.get("width"),
                "h": a.get("height"),
            })
        elif tag == "html":
            self.lang = a.get("lang")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            if self._skip:
                self._skip -= 1
            if tag == "script" and self._script_type:
                self.jsonld.append("".join(self._script_buf).strip())
                self._script_type = None
            return
        if self._skip:
            return
        if tag == "title" and self._in_title:
            self.title = " ".join("".join(self._buf).split())
            self._in_title = False
        elif tag == "h1" and self._in_h == "h1":
            self.h1.append(" ".join("".join(self._h_buf).split()))
            self._in_h = None
        elif tag == "h2" and self._in_h == "h2":
            self.h2.append(" ".join("".join(self._h_buf).split()))
            self._in_h = None
        elif tag == "a" and self._in_a:
            self.links.append((self._a_href, " ".join("".join(self._a_buf).split())))
            self._in_a = False

    def handle_data(self, data):
        if self._skip:
            if self._script_type:
                self._script_buf.append(data)
            return
        if self._in_title:
            self._buf.append(data)
        elif self._in_h:
            self._h_buf.append(data)
        elif self._in_a:
            self._a_buf.append(data)


def parse_page(html: str, url: str) -> dict:
    p = PageParser()
    try:
        p.feed(html)
    except Exception:
        pass
    robots = p.meta.get("robots") or p.meta.get("googlebot")
    return {
        "url": url,
        "title": p.title,
        "title_len": len(p.title) if p.title else 0,
        "meta_desc": p.meta.get("description"),
        "meta_desc_len": len(p.meta.get("description", "")),
        "robots": robots,
        "canonical": p.canonical,
        "h1": p.h1,
        "h2_count": len(p.h2),
        "og_title": p.property.get("og:title"),
        "og_desc": p.property.get("og:description"),
        "og_image": p.property.get("og:image"),
        "twitter_card": p.meta.get("twitter:card"),
        "jsonld": p.jsonld,
        "imgs": p.imgs,
        "links": [h for h, _ in p.links if h],
        "lang": p.lang,
        "html_len": len(html),
    }


def norm(href: str, base: str):
    if not href or href.startswith(("mailto:", "tel:", "javascript:", "#")):
        return None
    u = urllib.parse.urljoin(base, href)
    if not u.startswith(BASE):
        return None
    u = u.split("#")[0]
    if u.startswith("http://"):
        u = "https://" + u[len("http://"):]
    return u


def main():
    # 1) sitemap 清单
    sitemap_urls = set()
    sm_index_status, _, sm_body, _ = fetch(BASE + "/sitemap-index.xml")
    sm_index_urls = re.findall(r"<loc>\s*(.*?)\s*</loc>", sm_body.decode("utf-8", "ignore"))
    for sm in sm_index_urls:
        st, _, b, _ = fetch(sm)
        locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", b.decode("utf-8", "ignore"))
        sitemap_urls.update(locs)
        print(f"[sitemap] {sm} -> {st}, {len(locs)} URLs")

    # 2) BFS 爬站
    queue = [BASE + "/"]
    visited = {}
    order = []
    while queue and len(visited) < 250:
        url = queue.pop(0)
        if url in visited:
            continue
        st, hdrs, body, chain = fetch(url)
        is_html = (hdrs.get("content-type", "") or "").startswith("text/html")
        rec = {
            "status": st,
            "content_type": hdrs.get("content-type"),
            "size": len(body),
            "encoding": hdrs.get("content-encoding"),
            "cache_control": hdrs.get("cache-control"),
            "chain": chain,
            "redirect_final": chain[-1][0] if chain else url,
        }
        if is_html and body:
            rec.update(parse_page(body.decode("utf-8", "ignore"), url))
        visited[url] = rec
        order.append(url)
        if is_html and st == 200:
            for href in rec.get("links", []):
                u = norm(href, url)
                if u and u not in visited and u not in queue:
                    queue.append(u)
        time.sleep(0.15)

    # 3) 额外探测
    extra = {}
    for path, label in [("/sitemap.xml", "sitemap.xml"), ("/sitemap-index.xml", "sitemap-index.xml"),
                        ("/nonexistent-page-xyz", "404-test"), ("/404", "/404页"),
                        ("/index.html", "index.html")]:
        st, hdrs, body, chain = fetch(BASE + path)
        ct = hdrs.get("content-type", "")
        extra[label] = {
            "status": st, "content_type": ct, "size": len(body),
            "is_html_404_page": "Error 404" in body.decode("utf-8", "ignore")[:2000],
            "chain": chain,
        }
        time.sleep(0.15)

    # 4) 首页响应头（安全头等）
    st, hdrs, _, _ = fetch(BASE + "/")
    headers = {k.lower(): v for k, v in hdrs.items()}
    security = {k: headers.get(k) for k in
                ["strict-transport-security", "x-frame-options", "x-content-type-options",
                 "content-security-policy", "referrer-policy", "permissions-policy",
                 "server", "content-encoding", "cache-control", "x-vercel-cache",
                 "age", "cdn-cache-control", "etag", "last-modified"]}

    report = {
        "base": BASE,
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sitemap_index_status": sm_index_status,
        "sitemap_url_count": len(sitemap_urls),
        "sitemap_urls": sorted(sitemap_urls),
        "crawl_order": order,
        "pages": visited,
        "extra_probes": extra,
        "home_headers": security,
    }
    with open(OUT / "crawl_data.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    # 控制台摘要
    pages200 = [u for u, r in visited.items() if r["status"] == 200]
    print(f"\n=== 爬取摘要: {len(visited)} URLs, {len(pages200)} 个 200 ===")
    for u in order:
        r = visited[u]
        t = r.get("title", "")[:60]
        print(f"{r['status']} {u.replace(BASE, '')} | {r['size']}B | title={t!r}")
    print("\n=== 额外探测 ===")
    for k, v in extra.items():
        print(f"{k}: HTTP {v['status']} | {v['content_type']} | 404页内容={v['is_html_404_page']}")
    print("\n=== 首页安全/缓存头 ===")
    for k, v in security.items():
        print(f"{k}: {v}")
    # sitemap vs crawl
    crawled = set(visited.keys())
    in_sm_not_crawled = sorted(sitemap_urls - crawled)
    print(f"\n=== sitemap 有但爬虫没发现/没抓: {len(in_sm_not_crawled)} ===")
    for u in in_sm_not_crawled[:30]:
        print(" ", u)


if __name__ == "__main__":
    main()
