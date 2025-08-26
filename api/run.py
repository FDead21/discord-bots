# api/run.py

import os
import requests
import json
import feedparser
from http.server import BaseHTTPRequestHandler

# --- CONFIGURATION ---
RSS_FEED_URL = "https://www.espn.com/espn/rss/nba/news"
# You can set a custom color for the embed's sidebar (decimal value)
EMBED_COLOR = 3447003 # A nice blue color

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            feed = feedparser.parse(RSS_FEED_URL)
            if not feed.entries:
                # If the feed is empty, we can just stop.
                self.send_response(204) # 204 No Content
                self.end_headers()
                return

            latest_article = feed.entries[0]
            title = latest_article.title
            link = latest_article.link
            
            # --- NEW: Extract description and thumbnail ---
            # The summary from the RSS feed makes a great description.
            description = latest_article.summary
            
            # Try to find a thumbnail image. RSS feeds can hide this in a few places.
            thumbnail_url = ""
            if 'media_thumbnail' in latest_article and len(latest_article.media_thumbnail) > 0:
                thumbnail_url = latest_article.media_thumbnail[0]['url']
            elif 'links' in latest_article:
                for l in latest_article.links:
                    if 'image' in l.get('type', ''):
                        thumbnail_url = l.href
                        break

            # --- NEW: Create an embed object ---
            # Instead of a simple string, we build a dictionary that Discord understands.
            embed_data = {
                "title": title,
                "description": description,
                "url": link,
                "color": EMBED_COLOR,
                "thumbnail": {"url": thumbnail_url},
                "footer": {"text": "Source: ESPN"}
            }

        except Exception as e:
            print(f"ERROR: Failed to parse RSS feed: {e}")
            self.send_response(500)
            self.end_headers()
            return

        # Send the structured embed data to Discord
        self.send_to_discord(embed_data)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response_body = {"status": "success", "message": f"Posted embed: {title}"}
        self.wfile.write(json.dumps(response_body).encode('utf-8'))
        return

    def send_to_discord(self, embed_data):
        """
        Sends a rich embed to the Discord webhook instead of a simple message.
        """
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        if not webhook_url:
            print("ERROR: DISCORD_WEBHOOK_URL environment variable is not set.")
            return
            
        headers = {"Content-Type": "application/json"}
        
        # --- NEW: The JSON payload now contains an 'embeds' array ---
        # We send the embed_data dictionary inside this array.
        data = {
            "embeds": [embed_data]
        }
        
        try:
            response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error sending embed to Discord: {e}")