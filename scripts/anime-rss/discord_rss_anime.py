#!/usr/bin/python3
# -*- coding: utf-8 -*-

import asyncio
from datetime import datetime
import feedparser
import aiohttp
from bs4 import BeautifulSoup
import pytz
import os

# ------------------ CONFIG ------------------
RSS_FEED_URL = "https://feeds.feedburner.com/crunchyroll/rss/anime"
DISCORD_WEBHOOK_URL = "YOUR DISCORD WEBHOOK URL HERE"
# --------------------------------------------

# Keywords to skip if they appear in the title
SKIP_KEYWORDS = [
    "(Tamil Dub)", "(Telugu Dub)", "(Hindi Dub)", "(Italian Dub)",
    "(Castilian Dub)", "(French Dub)", "(German Dub)", "(Spanish Dub)",
    "(Portuguese Dub)"
]

PROCESSED_FILE = "processed_entries.txt"
MAX_EMBED_DESC = 4000  # Discord limit for embed.description is 4096; keep a buffer
EMBED_COLOR = 0x00FFFF  # Cyan-ish

def get_processed_entries() -> set:
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_processed_entry(entry_link: str) -> None:
    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(entry_link + "\n")

def to_utc_datetime(entry) -> datetime:
    """
    Try to convert the feed entry's published date to a timezone-aware UTC datetime.
    Works with either 'published_parsed' or 'published' string.
    """
    utc = pytz.UTC
    # Prefer structured time if available
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        dt = datetime(*entry.published_parsed[:6])
        return utc.localize(dt)
    # Fallback: try parsing 'published'
    if hasattr(entry, "published"):
        for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S %z"):
            try:
                dt = datetime.strptime(entry.published, fmt)
                # Normalize to UTC
                if dt.tzinfo is None:
                    return utc.localize(dt)
                return dt.astimezone(utc)
            except ValueError:
                continue
    # If no date, use now (not ideal, but prevents crash)
    return datetime.now(utc)

def clean_description(html: str) -> str:
    """
    Remove <img> and <br> tags, strip other HTML to text, and trim to Discord limits.
    """
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup.find_all(["img", "br"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    return (text[:MAX_EMBED_DESC - 20] + "…") if len(text) > MAX_EMBED_DESC else text

def get_thumbnail(entry) -> str | None:
    """
    Try a few common locations for media thumbnails in RSS entries.
    """
    # feedparser often exposes media thumbnails like entry.media_thumbnail[0]['url']
    try:
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            url = entry.media_thumbnail[0].get("url")
            if url:
                return url
    except Exception:
        pass
    # Some feeds use media_content
    try:
        if hasattr(entry, "media_content") and entry.media_content:
            for c in entry.media_content:
                if isinstance(c, dict) and c.get("url"):
                    return c["url"]
    except Exception:
        pass
    # As a last resort, None
    return None

async def post_to_discord(session: aiohttp.ClientSession, title: str, link: str,
                          description: str, timestamp_utc: datetime, thumbnail_url: str | None):
    """
    Send a single embed to the Discord webhook.
    """
    embed = {
        "title": title,
        "description": f"{description}\n\n[Read more]({link})" if description else f"[Read more]({link})",
        "url": link,
        "color": EMBED_COLOR,
        # Discord expects ISO8601 with timezone; ensure UTC with 'Z'
        "timestamp": timestamp_utc.replace(tzinfo=pytz.UTC).isoformat()
    }

    if thumbnail_url:
        # Use "image" for a big image across the embed; "thumbnail" is small on the right.
        embed["image"] = {"url": thumbnail_url}

    payload = {
        "content": "",      # optional message content outside of embed
        "embeds": [embed]
    }

    async with session.post(DISCORD_WEBHOOK_URL, json=payload) as resp:
        if 200 <= resp.status < 300:
            return True
        text = await resp.text()
        raise RuntimeError(f"Discord webhook error {resp.status}: {text}")

async def run():
    if not DISCORD_WEBHOOK_URL or "discord.com/api/webhooks" not in DISCORD_WEBHOOK_URL:
        raise SystemExit("Please set DISCORD_WEBHOOK_URL to a valid Discord webhook.")

    feed = feedparser.parse(RSS_FEED_URL)
    if not feed.entries:
        raise ValueError("No entries found in the RSS feed.")

    processed = get_processed_entries()
    utc = pytz.UTC
    today_utc = datetime.now(utc).date()

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        for entry in feed.entries:
            pub_dt_utc = to_utc_datetime(entry)
            if pub_dt_utc.date() != today_utc:
                continue

            title = getattr(entry, "title", "(no title)")
            if any(k in title for k in SKIP_KEYWORDS):
                print(f"Skipping (keyword): {title}")
                continue

            link = getattr(entry, "link", None)
            if not link:
                print(f"Skipping (no link): {title}")
                continue

            if link in processed:
                print(f"Skipping previously posted: {title}")
                continue

            desc_html = getattr(entry, "description", "") or ""
            description = clean_description(desc_html)
            thumb = get_thumbnail(entry)

            try:
                await post_to_discord(session, title, link, description, pub_dt_utc, thumb)
                print(f"Posted: {title}")
                save_processed_entry(link)
            except Exception as e:
                print(f"Failed to post '{title}': {e}")

if __name__ == "__main__":
    asyncio.run(run())
