#!/usr/bin/python3

import feedparser
import asyncio
from datetime import datetime
import guilded_webhook as guilded
from bs4 import BeautifulSoup
import pytz

# Define the list of keywords to skip
skip_keywords = ["xoxoxo"]

# Function to get the list of processed entry links
def get_processed_entries_cyber():
    try:
        with open('processed_entries_cyber.txt', 'r') as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

# Function to save the processed entry link to the file
def save_processed_entry(entry_link):
    with open('processed_entries_cyber.txt', 'a') as file:
        file.write(entry_link + '\n')

async def post_to_guilded(rss_feed_url, webhook_url):
    try:
        # Fetch and parse the RSS feed
        feed = feedparser.parse(rss_feed_url)

        # Check if the feed has entries
        if not feed.entries:
            raise ValueError('No entries found in the RSS feed.')

        # Create a Guilded webhook
        hook = guilded.AsyncWebhook(webhook_url)

        # Get the list of processed entry links
        processed_entries_cyber = get_processed_entries_cyber()

        # Get the ct timezone object
        ct = pytz.timezone('ct')

        # Process each entry
        for entry in feed.entries:
            # Parse the publication date from the entry and convert to ct
            pub_date_str = entry.published
            pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
            pub_date_ct = pub_date.astimezone(ct)

            # Check if the entry is from today in ct
            if pub_date_ct.date() == datetime.now(ct).date():
                title = entry.title

                # Check if any of the skip keywords are present in the title
                if any(keyword in title for keyword in skip_keywords):
                    print(f'Skipping entry with title: {title}')
                    continue

                link = entry.link
                thumbnail_url = entry.media_content[0]['url'] 
                description = entry.description if hasattr(entry, 'description') else ''

                # Use BeautifulSoup to remove img and br tags from the description
                soup = BeautifulSoup(description, 'html.parser')
                for tag in soup.find_all(['img', 'br']):
                    tag.decompose()

                # Create a Guilded embed
                embed = guilded.Embed(title=title, description=f'{str(soup)}\n\n[Read more]({link})', color=0x00ffff, timestamp=pub_date_ct)
                embed.set_image(thumbnail_url)

                # Check if this entry has been processed before
                if entry.link not in processed_entries_cyber:
                    # Send data to the webhook
                    await hook.send(content='', embeds=embed)

                    print(f'Webhook successfully triggered for {title}')

                    # Update the list of processed entry links
                    save_processed_entry(entry.link)
                else:
                    print(f'Skipping previously posted entry: {title}')
                    
                # Add a 3-second delay between posts
                await asyncio.sleep(3)

    except Exception as e:
        print(f'An error occurred: {str(e)}')

# Replace with your actual URLs
rss_feed_url = 'https://www.armytimes.com/arc/outboundfeeds/rss/category/news/?outputType=xml'
webhook_url = 'https://media.guilded.gg/webhooks/4df42a1c-2144-4b55-9528-d8fe03b788de/wKqR2N9tOCQOwOGMcIIU4oMC6Ge2kc66ey2SikKWWg2guUQAQMY0q4UQ2ymYQW6gIIq6kAKQ8cYWaUmoooukQ0'

# Run the asynchronous function
asyncio.run(post_to_guilded(rss_feed_url, webhook_url))
