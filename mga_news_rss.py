import requests
import sys
import hashlib
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator

URL = "https://www.mga.org.mt/who-we-are/news"

def fetch_page():
    print("🌐 Fetching MGA News page...")
    try:
        response = requests.get(URL, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"❌ Failed to fetch MGA News: {e}")
        sys.exit(1)

def parse_items(soup):
    items = soup.select("article")
    if not items:
        print("⚠️ No news items found on MGA page.")
        sys.exit(1)

    print(f"📦 Found {len(items)} news items.")
    return items

def parse_feed(items):
    fg = FeedGenerator()
    fg.id(URL)
    fg.title("MGA – Who We Are News")
    fg.link(href=URL, rel="alternate")
    fg.description("Latest news from the Malta Gaming Authority – Who We Are section")
    fg.language("en")

    # ⭐ REQUIRED FOR FEEDER — Atom self-link (feedgen 0.9.0 syntax)
    fg.link(
        href="https://anonymousus3r.github.io/MGA-news/mga_news.xml",
        rel="self"
    )

    for item in items:
        link_tag = item.select_one("a")
        title_tag = item.select_one("h2, h3, h4")
        if not link_tag or not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        href = link_tag["href"]
        full_link = href if href.startswith("http") else "https://www.mga.org.mt" + href

        date_tag = item.select_one("div.bg-purple time")
        if not date_tag:
            print(f"⚠️ No date found for: {title}")
            continue

        date_text = date_tag.get_text(strip=True)

        try:
            dt = datetime.strptime(date_text, "%d %B %Y")
            pub_date = datetime(dt.year, dt.month, dt.day, 12, 0, 0, tzinfo=timezone.utc)
        except Exception as e:
            print(f"⚠️ Date parse issue for {title}: {e}")
            pub_date = datetime.now(timezone.utc)

        guid = hashlib.md5((title + full_link).encode("utf-8")).hexdigest()

        entry = fg.add_entry()
        entry.id(guid)
        entry.guid(guid, permalink=False)
        entry.title(title)
        entry.link(href=full_link)
        entry.pubDate(pub_date)
        entry.updated(pub_date)

        print(f"✅ {title} — {pub_date.date()}")

    fg.rss_file("mga_news.xml")
    print("📄 Saved MGA RSS to mga_news.xml")

if __name__ == "__main__":
    soup = fetch_page()
    items = parse_items(soup)
    parse_feed(items)
