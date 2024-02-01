# RSS Feed to Guilded Webhook Script

## Overview

This Python script is designed to fetch and process updates from an RSS feed and post them to a Guilded webhook. It performs the following tasks:

1. Parses an RSS feed and extracts relevant information from its entries.
2. Filters out entries with specific keywords (e.g., "(Tamil Dub)", "(Telugu Dub)") from being posted to the webhook.
3. Checks for a thumbnail image associated with each entry. If a thumbnail is not found, it looks for a media content URL with an image (e.g., JPEG or PNG).
4. Removes HTML tags such as `<img>` and `<br>` from the entry descriptions for cleaner formatting.
5. Converts the publication date of each entry to the specified local timezone for timestamping.
6. Creates a Guilded embed with the title, description, timestamp, and optional thumbnail image.
7. Posts the embed to a Guilded webhook if the entry has not been processed before.

## Usage

Before running the script, you need to configure it using a `config.ini` file with the following parameters:

- `rss_feed_url`: The URL of the RSS feed you want to monitor.
- `webhook_url`: The URL of the Guilded webhook where updates will be posted.
- `rss_timezone`: The timezone of the RSS feed (e.g., "UTC").
- `local_timezone`: Your local timezone for converting timestamps (e.g., "America/New_York").

## Script Execution

To run the script, execute it as a Python script:

```bash
python script.py
```

Make sure you have the necessary Python packages installed, such as `feedparser`, `asyncio`, `guilded_webhook`, `bs4` (Beautiful Soup), and `pytz`.

## Version

Script Version: 1.0

## Skipping Keywords

The script will skip entries that contain any of the following keywords in their titles:

- (Tamil Dub)
- (Telugu Dub)
- (Hindi Dub)
- (Italian Dub)
- (Castilian Dub)
- (French Dub)
- (German Dub)
- (Spanish Dub)
- (Portuguese Dub)

## Error Handling

The script includes error handling to catch and log any exceptions that may occur during execution.

## Processed Entries

The script keeps track of processed entry links to avoid posting duplicate entries. Processed entry links are stored in a `processed_entries.txt` file.

---

Please ensure you have the necessary permissions and access rights for the Guilded webhook and the RSS feed. Modify the `skip_keywords` list and customize the script to meet your specific requirements.

For any questions or issues, please contact the script maintainers.

```
