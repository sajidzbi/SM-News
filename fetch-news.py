#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════
#  SM News — GitHub Actions RSS Fetcher
#  Dr. Sajid Mahmood | Hazara University Mansehra
#  چلتا ہے: ہر گھنٹے (GitHub Actions)
#  نتیجہ:   news.json فائل بناتا ہے
# ═══════════════════════════════════════════════════════

import json, re, ssl, urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# ── RSS Sources ─────────────────────────────────────────
FEEDS = {
    "international": [
        {"name": "Geo News",  "url": "https://www.geo.tv/rss/topic/world"},
        {"name": "Dawn",      "url": "https://www.dawn.com/feeds/latest-news"},
        {"name": "ARY News",  "url": "https://arynews.tv/feed/"},
        {"name": "BBC Urdu",  "url": "https://feeds.bbci.co.uk/urdu/rss.xml"},
        {"name": "Tribune",   "url": "https://tribune.com.pk/feed"},
    ],
    "national": [
        {"name": "Geo News",  "url": "https://www.geo.tv/rss/topic/pakistan"},
        {"name": "ARY News",  "url": "https://arynews.tv/feed/"},
        {"name": "Dawn",      "url": "https://www.dawn.com/feeds/pakistan"},
        {"name": "Jang",      "url": "https://jang.com.pk/rss/2"},
        {"name": "Express",   "url": "https://www.express.pk/feed/"},
        {"name": "Samaa",     "url": "https://www.samaa.tv/feed/"},
        {"name": "92 News",   "url": "https://92newshd.tv/feed/"},
        {"name": "Tribune",   "url": "https://tribune.com.pk/feed"},
    ],
    "kpk": [
        {"name": "Khyber News","url": "https://khybernews.tv/feed/"},
        {"name": "Geo News",  "url": "https://www.geo.tv/rss/topic/pakistan"},
        {"name": "ARY News",  "url": "https://arynews.tv/feed/"},
        {"name": "Express",   "url": "https://www.express.pk/feed/"},
        {"name": "Dawn",      "url": "https://www.dawn.com/feeds/pakistan"},
    ],
    "punjab": [
        {"name": "Jang",      "url": "https://jang.com.pk/rss/2"},
        {"name": "Express",   "url": "https://www.express.pk/feed/"},
        {"name": "Dawn",      "url": "https://www.dawn.com/feeds/pakistan"},
        {"name": "Tribune",   "url": "https://tribune.com.pk/feed"},
        {"name": "Geo News",  "url": "https://www.geo.tv/rss/topic/pakistan"},
    ],
    "sindh": [
        {"name": "Dawn",      "url": "https://www.dawn.com/feeds/pakistan"},
        {"name": "Express",   "url": "https://www.express.pk/feed/"},
        {"name": "Samaa",     "url": "https://www.samaa.tv/feed/"},
        {"name": "Geo News",  "url": "https://www.geo.tv/rss/topic/pakistan"},
    ],
    "baloch": [
        {"name": "Dawn",      "url": "https://www.dawn.com/feeds/pakistan"},
        {"name": "ARY News",  "url": "https://arynews.tv/feed/"},
        {"name": "Express",   "url": "https://www.express.pk/feed/"},
        {"name": "Geo News",  "url": "https://www.geo.tv/rss/topic/pakistan"},
    ],
    "education": [
        {"name": "Dawn",      "url": "https://www.dawn.com/feeds/education"},
        {"name": "Geo News",  "url": "https://www.geo.tv/rss/topic/education"},
        {"name": "ARY News",  "url": "https://arynews.tv/feed/"},
        {"name": "Express",   "url": "https://www.express.pk/feed/"},
        {"name": "Tribune",   "url": "https://tribune.com.pk/feed"},
    ],
    "science": [
        {"name": "Dawn",      "url": "https://www.dawn.com/feeds/technology"},
        {"name": "Geo News",  "url": "https://www.geo.tv/rss/topic/technology"},
        {"name": "ARY News",  "url": "https://arynews.tv/feed/"},
        {"name": "Tribune",   "url": "https://tribune.com.pk/feed"},
    ],
    "sports": [
        {"name": "Geo Sports","url": "https://www.geo.tv/rss/topic/sport"},
        {"name": "ARY Sports","url": "https://arynews.tv/category/sports/feed/"},
        {"name": "Dawn",      "url": "https://www.dawn.com/feeds/sport"},
        {"name": "Jang",      "url": "https://jang.com.pk/rss/7"},
        {"name": "Express",   "url": "https://www.express.pk/feed/"},
    ],
    "business": [
        {"name": "Dawn",      "url": "https://www.dawn.com/feeds/business"},
        {"name": "Geo News",  "url": "https://www.geo.tv/rss/topic/business"},
        {"name": "Tribune",   "url": "https://tribune.com.pk/feed"},
        {"name": "Express",   "url": "https://www.express.pk/feed/"},
        {"name": "Jang",      "url": "https://jang.com.pk/rss/3"},
    ],
}

# ── SSL context ──────────────────────────────────────────
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# ── Helpers ──────────────────────────────────────────────
def fetch_url(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 SMNewsBot/2.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            raw = r.read()
            for enc in ("utf-8", "utf-8-sig", "cp1256", "iso-8859-1"):
                try:
                    return raw.decode(enc)
                except Exception:
                    pass
            return raw.decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  FAIL {url}: {e}")
        return ""

def get_tag(block, tag):
    m = re.search(rf'<{tag}[^>]*><!\[CDATA\[([\s\S]*?)\]\]></{tag}>', block, re.I)
    if not m:
        m = re.search(rf'<{tag}[^>]*>([\s\S]*?)</{tag}>', block, re.I)
    return m.group(1).strip() if m else ""

def get_attr(block, tag, attr):
    m = re.search(rf'<{tag}[^>]+{attr}=["\']([^"\']+)["\']', block, re.I)
    return m.group(1) if m else ""

def extract_img(html):
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html or "", re.I)
    return m.group(1) if m else ""

def strip_html(s):
    s = re.sub(r'<[^>]+>', '', s or '')
    for old, new in [("&amp;","&"),("&lt;","<"),("&gt;",">"),("&nbsp;"," "),("&quot;",'"'),("&#39;","'")]:
        s = s.replace(old, new)
    return re.sub(r'\s+', ' ', s).strip()

def parse_date(s):
    if not s:
        return datetime.now(timezone.utc).isoformat()
    try:
        return parsedate_to_datetime(s).isoformat()
    except Exception:
        pass
    try:
        return datetime.fromisoformat(s.replace("Z","+00:00")).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()

# ── Parse one RSS/Atom feed ──────────────────────────────
def parse_feed(xml, src_name):
    items = []
    blocks = []
    for pat in [r'<item[^>]*>([\s\S]*?)</item>', r'<entry[^>]*>([\s\S]*?)</entry>']:
        blocks += re.findall(pat, xml, re.I)

    for block in blocks[:25]:
        title   = strip_html(get_tag(block, 'title'))
        link    = get_tag(block, 'link') or get_attr(block, 'link', 'href')
        desc    = get_tag(block, 'description') or get_tag(block, 'summary') or get_tag(block, 'content')
        pub     = get_tag(block, 'pubDate') or get_tag(block, 'published') or get_tag(block, 'updated')
        img     = get_attr(block, 'enclosure', 'url') or extract_img(desc)

        if title and link and link.startswith('http'):
            items.append({
                "title":   title,
                "summary": strip_html(desc)[:320],
                "url":     link.strip(),
                "source":  src_name,
                "date":    parse_date(pub.strip()),
                "img":     img,
            })
    return items

# ── Deduplicate ──────────────────────────────────────────
def dedup(articles):
    seen = set()
    result = []
    for a in articles:
        key = re.sub(r'[^\w\u0600-\u06FF]', '', a["title"].lower())[:50]
        if key not in seen:
            seen.add(key)
            result.append(a)
    result.sort(key=lambda x: x["date"], reverse=True)
    return result

# ── Fetch one category ───────────────────────────────────
def fetch_category(cat, sources):
    print(f"\n[{cat}] fetching {len(sources)} sources...")
    all_articles = []
    for src in sources:
        print(f"  → {src['name']}: {src['url']}")
        xml = fetch_url(src["url"])
        if xml:
            arts = parse_feed(xml, src["name"])
            print(f"     got {len(arts)} items")
            all_articles.extend(arts)
        else:
            print(f"     no data")
    result = dedup(all_articles)
    print(f"  [{cat}] total after dedup: {len(result)}")
    return result

# ── MAIN ─────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("SM News Fetcher — Dr. Sajid Mahmood")
    print("=" * 55)

    output = {
        "fetched": datetime.now(timezone.utc).isoformat(),
        "categories": {}
    }

    for cat, sources in FEEDS.items():
        articles = fetch_category(cat, sources)
        output["categories"][cat] = articles

    # Write news.json
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in output["categories"].values())
    print(f"\n✅ news.json written — {total} total articles")
    print(f"   Categories: {list(output['categories'].keys())}")

if __name__ == "__main__":
    main()
