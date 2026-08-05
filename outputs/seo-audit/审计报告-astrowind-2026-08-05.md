# ENCORE 独立站（AstroWind）SEO 审计报告

- **站点**：https://astrowindwopress.vercel.app（ENCORE 照明 B2B 制造商官网，Astro 静态站）
- **日期**：2026-08-05
- **方法**：qiaomu-seo skill（site_inventory 模式）— Python 爬虫 BFS 全站抓取 22 URL + sitemap 解析 + HTTP 层探测 + 页面级解析
- **模式**：只审计（未改动线上内容；仓库内仅修复验证闸门暴露的既有问题）
- **机器可读数据**：`outputs/seo-audit/audit.json`（已通过 qiaomu-seo `validate_audit.py` 契约校验 ✅）+ `crawl_data.json`（全量抓取原始数据）

---

## 一、执行摘要

**网站技术底子合格，问题集中在「结构化数据缺失」和「内容差异化」两个层面。**

没有发现 P0 级问题（无失索引、无坏链、无重定向损坏、无 JS 渲染依赖）。但有 3 个 P1 级问题会直接影响 AI 搜索可见性和 SERP 点击率，另有 7 个 P2 级优化点。最大的增长杠杆是**内容量**——全站仅 1 篇有效博客文章。

### 三大优先项

1. **全站结构化数据**（Organization / WebSite / Product / Breadcrumb）——AI 搜索（GEO）实体识别 + 富结果资格，B2B 官网最该有的信任基建
2. **标题去双品牌 + 每页唯一 meta description**——纯文案改动，低风险高可见
3. **博客内容扩展**（1 篇 → 按选题计划 8-10 篇）+ 清理模板残留外链

---

## 二、覆盖清单（Coverage Ledger）

| 项 | 数量 | 说明 |
|---|---|---|
| sitemap 声明 URL | 20 | sitemap-index.xml → sitemap-0.xml（20 URL） |
| 实际抓取 | 22 | BFS 发现含首页 308 变体 |
| 全部 200 | 22 | 无坏链、无失败 |
| HTML 页解析 | 21 | 排除 /rss.xml |
| 孤儿页 | 0 | sitemap 与爬虫发现完全一致 |
| 排除 | 1 | /rss.xml（feed） |
| 限制 | — | 无 GSC/CrUX/日志数据；PSI 匿名配额超限未跑 lab 性能 |

---

## 三、发现清单（按严重度）

### P1（高优先级）

| # | 类别 | 问题 | 证据 | 影响 | 建议 |
|---|---|---|---|---|---|
| F1 | 结构化数据 | **全站 0 条 JSON-LD**：无 Organization/WebSite，产品页无 Product/Breadcrumb | 21 页 jsonld 全部为空 | 高 | Layout 注入 Organization（logo/社媒 sameAs）+ WebSite；产品页加 BreadcrumbList |
| F2 | 标题 | **9-10 页品牌重复**：`…\| ENCORE — ENCORE`（products×4、pricing、oem-odm、quality-control、certifications、services、about、contact） | 抓取标题原文 | 中 | 删掉页面 title 里手写的 `\| ENCORE`，模板会自动追加 |
| F3 | Meta Description | **20/21 页共用同一条 183 字符描述**（全站默认值） | 去重后仅 2 条 | 中 | 每页写 120-160 字符唯一描述 |
| F5 | 内容 | **博客仅 1 篇有效文章** + 1 category + 3 tag 薄页面 | /blog 抓取 | 高（长期） | 按选题计划扩内容；薄页暂可 noindex |

### P2（中期优化）

| # | 类别 | 问题 | 证据 | 建议 |
|---|---|---|---|---|
| F4 | 标题结构 | **9 页主标题是 h2 不是 h1**（products×4、oem-odm、quality-control、certifications、services、pricing） | h1=[]，h2≥2 | Headline 组件主标题改 h1 |
| F6 | 模板残留 | footer 外链 **astro.build 推广 + GitHub 署名 ×21 页** | 外链统计 | 删除/替换为 ENCORE 链接 |
| F7 | 安全头 | 缺 X-Content-Type-Options / X-Frame-Options / Referrer-Policy / CSP（HSTS preload ✅） | 响应头 | vercel.json 补安全头 |
| F8 | Sitemap | **/sitemap.xml 404**（robots 声明 sitemap-index.xml 正常） | HTTP 探测 | 重定向到 sitemap-index.xml |
| F9 | 状态码 | /404 路由返回 200（软 404）；真实 404 正确 | HTTP 探测 | 可选，影响低 |
| F10 | 图片 | 110 图全有 alt ✅、hero eager ✅；44 张 png 可转 webp/avif | 图片统计 | 换图时用 webp/avif |

### ✅ 验证通过项（Passes）

- 22 URL 全 200，无坏链、无孤儿页
- robots.txt 正常（允许全部 + 声明 sitemap）
- http→https 308；HSTS preload
- 全部页面 canonical 自引用一致；robots meta index,follow 全在位
- og:title / og:image / twitter:card 全站齐备
- Astro 静态渲染，内容全在原始 HTML（无 JS 渲染依赖）
- rss.xml 存在；页面体积 29-66KB；Vercel 缓存 HIT + etag
- 单一语言 en（无 hreflang 需求）

---

## 四、缺失证据（后续可补）

- 字段级 Core Web Vitals（需 GSC 绑定 + CrUX）
- GSC 收录/索引覆盖率、搜索词、排名
- 外链/域名权威数据
- 询盘/转化数据

---

## 五、行动方案（action_plan，同 audit.json）

| 行动 | 对应发现 | 影响 | 工作量 | 验证 |
|---|---|---|---|---|
| A1 全站结构化数据 | F1 | 高 | M | Rich Results Test |
| A2 标题去重 + 每页 description | F2 F3 | 中 | M | 重抓比对 |
| A3 主标题 h2→h1 | F4 | 低 | XS | 复查 DOM |
| A4 清模板外链 + 安全头 + sitemap 重定向 | F6 F7 F8 | 低 | S | curl 复查 |
| A5 博客内容扩展 | F5 | 高 | L | GSC 30 天 |

---

*生成工具：qiaomu-seo v1.2.0（向阳乔木）· 审计契约校验通过 · 2026-08-05*
