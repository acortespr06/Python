#!/usr/bin/python3

import feedparser
import asyncio
from datetime import datetime
import guilded_webhook as guilded
from bs4 import BeautifulSoup
import configparser
import pytz
import os

# Define the script version
script_version = "1.0"

# Define the list of keywords to skip
skip_keywords = ["(Tamil Dub)", "(Telugu Dub)", "(Hindi Dub)", "(Italian Dub)", "(Castilian Dub)", "(French Dub)", "(German Dub)", "(Spanish Dub)", "(Portuguese Dub)"]

# Get the directory path where the script is located
script_directory = os.path.dirname(os.path.abspath(__file__))

# Function to get the list of processed entry links
def get_processed_entries():
    try:
        with open('processed_entries.txt', 'r') as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

# Function to save the processed entry link to the file
def save_processed_entry(entry_link):
    with open('processed_entries.txt', 'a') as file:
        file.write(entry_link + '\n')

# Enhanced date parsing function
def parse_date(pub_date_str, rss_timezone):
    timezone_offsets = {
        "GMT": "+0000",
        "UTC": "+0000",
        "EST": "-0500",
        "PST": "-0800",
        # Add more timezone offsets as needed
    }

    supported_formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S %Z",
        "%a, %d %b %Y %H:%M:%S",
    ]

    for format_str in supported_formats:
        for tz_name, tz_offset in timezone_offsets.items():
            formatted_date_str = pub_date_str.replace("+0000", tz_offset).replace("+00:00", tz_offset).replace("GMT", tz_name).replace("UTC", tz_name)
            try:
                return datetime.strptime(formatted_date_str, format_str)
            except ValueError:
                pass
    
    raise ValueError("Unable to parse date")

async def post_to_guilded(rss_feed_url, webhook_url, rss_timezone, local_timezone):
    try:
        # Fetch and parse the RSS feed
        feed = feedparser.parse(rss_feed_url)

        # Check if the feed has entries
        if not feed.entries:
            raise ValueError('No entries found in the RSS feed.')

        # Create a Guilded webhook
        hook = guilded.AsyncWebhook(webhook_url)

        # Get the list of processed entry links
        processed_entries = get_processed_entries()

        # Process each entry
        for entry in feed.entries:
            title = entry.title

            # Check if any of the skip keywords are present in the title
            if any(keyword in title for keyword in skip_keywords):
                print(f'Skipping entry with title: {title}')
                continue

            link = entry.link
            description = entry.description if hasattr(entry, 'description') else ''

            # Check for a thumbnail URL in media_thumbnail or media_content
            thumbnail_url = None
            if hasattr(entry, 'media_thumbnail') and len(entry.media_thumbnail) > 0:
                thumbnail_url = entry.media_thumbnail[0]['url']
            elif hasattr(entry, 'media_content'):
                for media in entry.media_content:
                    if media['type'] == 'image/jpeg' or media['type'] == 'image/png':
                        thumbnail_url = media['url']
                        break

            # Use BeautifulSoup to remove img and br tags from the description
            soup = BeautifulSoup(description, 'html.parser')
            for tag in soup.find_all(['img', 'br']):
                tag.decompose()

            # Parse the publication date from the entry using the enhanced function
            pub_date_str = entry.published
            pub_date = parse_date(pub_date_str, rss_timezone)

            # Convert the RSS feed's time to local time
            rss_timezone_obj = pytz.timezone(rss_timezone)
            local_timezone_obj = pytz.timezone(local_timezone)
            pub_date_local = pub_date.astimezone(rss_timezone_obj).astimezone(local_timezone_obj)

            # Create a Guilded embed
            embed = guilded.Embed(title=title, description=f'{str(soup)}\n\n[Read more]({link})', color=0x00ffff, timestamp=pub_date_local)
            
            if thumbnail_url:
                embed.set_image(thumbnail_url)

            # Check if this entry has been processed before
            if entry.link not in processed_entries:
                # Send data to the webhook
                await hook.send(content='', embeds=embed)

                print(f'Webhook successfully triggered for {title}')

                # Update the list of processed entry links
                save_processed_entry(entry.link)
            else:
                print(f'Skipping previously posted entry: {title}')

    except Exception as e:
        print(f'An error occurred: {str(e)}')

# Get the directory path where the script is located
script_directory = os.path
