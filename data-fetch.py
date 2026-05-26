#!/usr/bin/env python3
"""
2026世界杯 每日数据更新脚本
从免费API抓取最新数据 → 更新 index.html
运行环境: GitHub Actions (Python 3 + curl + jq)
"""

import json, re, urllib.request, urllib.error, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

HTML_FILE = Path("index.html")
LOG = []

def log(m):
    LOG.append(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {m}")
    print(m)

def fetch(url, timeout=15, headers=None):
    try:
        req = urllib.request.Request(url, headers=headers or {
            "User-Agent": "Mozilla/5.0 (compatible; WC2026Bot/1.0; +https://github.com/saadddd1/ShiJieBei)"
        })
        r = urllib.request.urlopen(req, timeout=timeout)
        return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        log(f"  ⚠️ 请求失败: {url[:60]}… → {e}")
        return ""

# ── 1. FIFA Rankings（Wikipedia） ──────────────────────────────
def update_fifa_rankings():
    log("→ 正在获取FIFA排名数据...")
    # 从FIFA官网API获取（实时数据）
    # FIFA uses: https://api.fifa.com/api/v3/ranking/men
    fifa_data = fetch(
        "https://api.fifa.com/api/v3/ranking/men",
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    )
    if fifa_data:
        try:
            j = json.loads(fifa_data)
            results = j.get("results", [])
            name_rank = {}
            for item in results:
                name_en = item.get("nameEn", item.get("name", ""))
                rank = item.get("rank", 0)
                if name_en and rank:
                    name_rank[name_en] = rank
            if name_rank:
                log(f"  ✅ FIFA API获取 {len(name_rank)} 个排名")
            else:
                log("  ⚠️ FIFA API返回空数据")
                name_rank = None
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            log("  ⚠️ FIFA API解析失败")
            name_rank = None
    else:
        log("  ⚠️ FIFA API无返回")
        name_rank = None

    if not name_rank:
        log("  → 尝试Wikipedia页面解析...")
        wiki_html = fetch(
            "https://en.wikipedia.org/wiki/FIFA_World_Rankings",
            headers={"User-Agent": "Mozilla/5.0 (compatible; WC2026Bot/1.0)"}
        )
        if not wiki_html:
            log("  ⚠️ Wikipedia页面无返回")
            return

        name_rank = {}
        # Find all wikitable tables
        tables = re.findall(r'<table[^>]*wikitable[^>]*>.*?</table>', wiki_html, re.DOTALL)
        for table in tables:
            rows = re.findall(r'<tr>(.*?)</tr>', table, re.DOTALL)
            for row in rows:
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if len(cells) >= 3:
                    rank_text = re.sub(r'<[^>]+>', '', cells[0]).strip()
                    name_text = re.sub(r'<[^>]+>', '', cells[2]).strip()
                    # Decode HTML entities
                    name_text = name_text.replace('&#160;', '').strip()
                    if rank_text.isdigit() and name_text:
                        name_rank[name_text] = int(rank_text)

        if not name_rank:
            log("  ⚠️ Wikipedia排名表格解析失败")
            return
        # 过滤异常值（排名应在1-250之间，排除年份数据误抓）
        name_rank = {k:v for k,v in name_rank.items() if 1 <= v <= 250}
        if not name_rank:
            log("  ⚠️ 所有排名值超出合理范围(1-250)")
            return
        log(f"  ✅ Wikipedia获取 {len(name_rank)} 个排名（备选）")

    # 名称映射: English → Chinese team names used in HTML
    name_map = {
        "Argentina": "阿根廷", "Australia": "澳大利亚", "Austria": "奥地利",
        "Belgium": "比利时", "Bosnia and Herzegovina": "波黑",
        "Brazil": "巴西", "Cameroon": "喀麦隆",
        "Canada": "加拿大", "Cape Verde": "佛得角",
        "China": "中国", "Colombia": "哥伦比亚", "Croatia": "克罗地亚",
        "Curacao": "库拉索", "Czech Republic": "捷克",
        "DR Congo": "刚果金", "Denmark": "丹麦",
        "Ecuador": "厄瓜多尔", "Egypt": "埃及", "England": "英格兰",
        "France": "法国",
        "Germany": "德国", "Ghana": "加纳",
        "Haiti": "海地", "Hungary": "匈牙利",
        "Iran": "伊朗", "Iraq": "伊拉克",
        "Japan": "日本", "Jordan": "约旦",
        "Korea Republic": "韩国", "Korea DPR": "朝鲜",
        "Mexico": "墨西哥", "Morocco": "摩洛哥",
        "Netherlands": "荷兰", "New Zealand": "新西兰", "Nigeria": "尼日利亚",
        "Norway": "挪威",
        "Panama": "巴拿马", "Paraguay": "巴拉圭", "Poland": "波兰",
        "Portugal": "葡萄牙",
        "Qatar": "卡塔尔",
        "Romania": "罗马尼亚",
        "Saudi Arabia": "沙特", "Scotland": "苏格兰", "Senegal": "塞内加尔",
        "Serbia": "塞尔维亚", "Slovakia": "斯洛伐克", "Slovenia": "斯洛文尼亚",
        "South Africa": "南非", "South Korea": "韩国", "Spain": "西班牙",
        "Sweden": "瑞典", "Switzerland": "瑞士",
        "Tunisia": "突尼斯", "Turkey": "土耳其",
        "Ukraine": "乌克兰",
        "United States": "美国", "Uruguay": "乌拉圭", "Uzbekistan": "乌兹别克",
        "Venezuela": "委内瑞拉", "Vietnam": "越南",
        "Wales": "威尔士",
    }

    html = HTML_FILE.read_text("utf-8")
    updated = 0
    not_found = []

    for en_name, cn_name in name_map.items():
        if en_name not in name_rank:
            continue
        rank = name_rank[en_name]
        if not isinstance(rank, int) or rank < 1 or rank > 250:
            continue  # 跳过异常值
        # Match pattern: name:'中国名',rank:'~XX'
        pattern = rf"(name:'{cn_name}',rank:'~)\d+"
        replacement = rf"\g<1>{rank}"
        new_html, count = re.subn(pattern, replacement, html)
        if count > 0:
            html = new_html
            updated += 1
        else:
            not_found.append(cn_name)

    if not_found:
        log(f"  以下队伍未匹配（队名可能不一致）: {', '.join(not_found[:5])}…")

    if updated > 0:
        HTML_FILE.write_text(html, "utf-8")
        log(f"  ✅ 已更新 {updated} 个队伍的FIFA排名")
    else:
        log("  ℹ️ 无排名更新（名称匹配可能失败）")

# ── 2. BBC新闻抓取 ────────────────────────────────────────────
def fetch_news():
    log("→ 正在获取最新世界杯新闻...")
    xml_text = fetch("https://feeds.bbci.co.uk/sport/football/rss.xml")
    if not xml_text:
        log("  ⚠️ BBC RSS无返回")
        return ["暂无最新新闻"]

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        log("  ⚠️ BBC RSS XML解析失败")
        return ["暂无最新新闻"]

    ns = {"": "http://www.w3.org/2005/Atom"}
    items = []
    # Try standard RSS format
    for item in root.iter("item"):
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        desc = item.findtext("description", "")
        items.append((title, link, desc))
        if len(items) >= 5:
            break

    # Fallback to Atom
    if not items:
        for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
            title = entry.findtext("{http://www.w3.org/2005/Atom}title", "")
            link_el = entry.find("{http://www.w3.org/2005/Atom}link")
            link = link_el.get("href", "") if link_el is not None else ""
            items.append((title, link, ""))
            if len(items) >= 5:
                break

    if not items:
        log("  未提取到新闻条目")
        return ["暂无最新新闻"]

    headlines = []
    for t, l, d in items:
        t = t.strip() if t else ""
        if t:
            headlines.append(t)
            log(f"  📰 {t[:80]}")

    log(f"  ✅ 获取 {len(headlines)} 条新闻")
    return headlines if headlines else ["暂无最新新闻"]

# ── 3. 更新新闻到HTML ──────────────────────────────────────────
def update_news_section(headlines):
    html = HTML_FILE.read_text("utf-8")

    # 生成新闻HTML片段
    news_html = '<div style="margin-top:16px">'
    for h in headlines[:5]:
        news_html += f'<div style="padding:6px 0;font-size:13px;color:var(--text-dim);border-bottom:1px solid var(--border-glass)">📰 {h[:120]}</div>'
    news_html += "</div>"

    # In the overview section, find and replace existing news block, or insert after timeline table
    # First, remove any existing news block (to avoid duplicates)
    html = re.sub(
        r'<div style="background:var\(--bg-glass\).*?最新动态.*?</div>\s*</div>',
        '',
        html,
        flags=re.DOTALL
    )
    # Insert fresh news block after the timeline table
    pattern = r'(</table>\s*\n\s*</section>\s*\n\s*<div class="divider">)'
    news_block = '\n  <div style="background:var(--bg-glass);border:1px solid var(--border-glass);border-radius:var(--radius);padding:20px;margin-top:16px">'
    news_block += '<h3 style="font-size:15px;font-weight:700;color:var(--gold-light);margin-bottom:8px">📰 最新动态</h3>'
    news_block += f'<div style="font-size:11px;color:var(--text-dim);margin-bottom:8px">自动抓取 · {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}</div>'
    news_block += news_html + '</div>\n\n\\1'

    if re.search(pattern, html, re.DOTALL):
        html = re.sub(pattern, news_block, html, count=1, flags=re.DOTALL)
        HTML_FILE.write_text(html, "utf-8")
        log("  ✅ 已更新最新动态栏")
    else:
        log("  ⚠️ 未找到插入位置")

# ── 4. 更新时间戳 ──────────────────────────────────────────────
def update_timestamp():
    html = HTML_FILE.read_text("utf-8")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    # Update footer
    html = re.sub(
        r'2026 世界杯赛事信息看板[^<]*</p>',
        f'2026 世界杯赛事信息看板 · 数据来源: FIFA, Opta AI, Transfermarkt · 最后更新: {now}</p>',
        html
    )
    HTML_FILE.write_text(html, "utf-8")
    log(f"  ✅ 时间戳已更新: {now}")

# ── MAIN ────────────────────────────────────────────────────────
def main():
    log("=" * 50)
    log("2026世界杯 每日数据更新开始")
    log("=" * 50)

    update_fifa_rankings()
    headlines = fetch_news()
    update_news_section(headlines)
    update_timestamp()

    log("=" * 50)
    log("✅ 数据更新完成")
    log("=" * 50)

if __name__ == "__main__":
    main()
