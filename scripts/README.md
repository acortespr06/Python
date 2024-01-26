# RSS Feed to Guilded Webhook

This Python script fetches data from an RSS feed and posts new entries to a Guilded webhook while avoiding reposting previously seen entries. It also cleans up the state files periodically.

## Features

- Fetches and parses an RSS feed for new entries.
- Posts new entries to a Guilded webhook.
- Avoids reposting entries that have been processed before.
- Cleans up the state files to keep them manageable.

## Requirements

- Python 3.x
- Install required Python packages using `pip`:

```bash
pip install requests feedparser asyncio guilded-webhook beautifulsoup4

## Usage

Replace the placeholders in the script with your actual RSS feed URL and Guilded webhook URL.

rss_feed_url = 'YOUR_RSS_FEED_URL'
webhook_url = 'YOUR_GUILDED_WEBHOOK_URL'


## Configuration

The script keeps track of processed entries in the processed_entries.txt file.
The latest_entry.txt file stores the link to the latest entry to check for new updates.
The script will clean up the latest_entry.txt file every 90 days to prevent it from growing too large.

## License

This script is provided under the MIT License.
