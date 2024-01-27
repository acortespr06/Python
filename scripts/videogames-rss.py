#!/usr/bin/python3

import feedparser
import asyncio
from datetime import datetime
import guilded_webhook as guilded
from bs4 import BeautifulSoup
import pytz

# Define the list of keywords to skip
skip_keywords = ["Uncensored"]

# Function to get the list of processed entry links
def get_processed_entries_games():
    try:
        with open('processed_entries_games.txt', 'r') as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

# Function to save the processed entry link to the file
def save_processed_entry(entry_link):
    with open('processed_entries_games.txt', 'a') as file:
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
        processed_entries_games = get_processed_entries_games()

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
                for tag in soup.find_all(['img', 'br', 'p']):
                    tag.decompose()

                # Create a Guilded embed
                embed = guilded.Embed(title=title, description=f'{str(soup)}\n\n[Read more]({link})', color=0x00ffff, timestamp=pub_date_gmt)
                embed.set_image(thumbnail_url)

                # Check if this entry has been processed before
                if entry.link not in processed_entries_games:
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
rss_feed_url = 'https://kotaku.com/rss'
webhook_url = 'https://media.guilded.gg/webhooks/89fa8969-bccd-4744-b7d8-3b81b78a0f21/W3jWn6SwwKyyEEoiMwWU0AgKKweuq8OuGs4MYiqKue0GEWmiCUQWk6weasUOiKwaaSioMsGWk2qO684wwEIA02'

# Run the asynchronous function
asyncio.run(post_to_guilded(rss_feed_url, webhook_url))
