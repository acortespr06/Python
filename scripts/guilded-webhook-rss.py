#!/usr/bin/python3

import feedparser
import asyncio
from datetime import datetime
import guilded_webhook as guilded
from bs4 import BeautifulSoup
import configparser
import pytz  # Import pytz for timezone conversion

# Define the script version
script_version = "1.0"

# Define the list of keywords to skip
skip_keywords = ["(Tamil Dub)", "(Telugu Dub)", "(Hindi Dub)", "(Italian Dub)", "(Castilian Dub)", "(French Dub)", "(German Dub)", "(Spanish Dub)", "(Portuguese Dub)"]

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

            # Parse the publication date from the entry
            pub_date_str = entry.published

            # Parse the RSS feed's timezone and local timezone
            rss_timezone_obj = pytz.timezone(rss_timezone)
            local_timezone_obj = pytz.timezone(local_timezone)

            # Convert the RSS feed's time to local time
            pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
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

# Read values from the configuration file
config = configparser.ConfigParser()
config.read('config.ini')

# Get the values from the config file
rss_feed_url = config.get('feed', 'rss_feed_url')
webhook_url = config.get('webhook', 'webhook_url')
rss_timezone = config.get('timezone', 'rss_timezone')
local_timezone = config.get('timezone', 'local_timezone')  # Specify your local timezone in the config.ini

# Run the asynchronous function
asyncio.run(post_to_guilded(rss_feed_url, webhook_url, rss_timezone, local_timezone))
