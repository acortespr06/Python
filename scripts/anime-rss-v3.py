#!/usr/bin/python3

import feedparser
import asyncio
from datetime import datetime
import guilded_webhook as guilded
from bs4 import BeautifulSoup
import pytz

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
        processed_entries = get_processed_entries()

        # Get the GMT timezone object
        gmt = pytz.timezone('GMT')

        # Process each entry
        for entry in feed.entries:
            # Parse the publication date from the entry and convert to GMT
            pub_date_str = entry.published
            pub_date = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %Z")
            pub_date_gmt = pub_date.astimezone(gmt)

            # Check if the entry is from today in GMT
            if pub_date_gmt.date() == datetime.now(gmt).date():
                title = entry.title

                # Check if any of the skip keywords are present in the title
                if any(keyword in title for keyword in skip_keywords):
                    print(f'Skipping entry with title: {title}')
                    continue

                link = entry.link
                thumbnail_url = entry.media_thumbnail[0]['url'] 
                description = entry.description if hasattr(entry, 'description') else ''

                # Use BeautifulSoup to remove img and br tags from the description
                soup = BeautifulSoup(description, 'html.parser')
                for tag in soup.find_all(['img', 'br']):
                    tag.decompose()

                # Create a Guilded embed
                embed = guilded.Embed(title=title, description=f'{str(soup)}\n\n[Read more]({link})', color=0x00ffff, timestamp=pub_date_gmt)
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

# Replace with your actual URLs
rss_feed_url = 'https://feeds.feedburner.com/crunchyroll/rss/anime'
<<<<<<< HEAD
webhook_url = 'https://media.guilded.gg/webhooks/9c671bcb-445a-4d0e-8f64-b3b415e12f8b/ywJ8exQClwsmCSYseQsAKOQGOuEG064Yic2O8Q4WqiU2OASSuwQ2qWO8ggEGOks6m4AukcmGgcK0W8q0ic4Ws'
=======
webhook_url = 'YOUR WEBHOOK HERE'
>>>>>>> 24f23af78afc027543a2a664bc095f146f64c4da

# Run the asynchronous function
asyncio.run(post_to_guilded(rss_feed_url, webhook_url))
