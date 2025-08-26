# api/run.py

import os
import redis
import json
import requests
import feedparser
from http.server import BaseHTTPRequestHandler

# --- CONFIGURATION ---
RSS_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UCWJ2lWNubArHWmf3FIHbfcQ"

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        redis_url = os.environ.get('REDIS_URL')
        if not redis_url:
            self.send_response(500)
            self.wfile.write("Redis URL not configured.".encode('utf-8'))
            return
        
        r = redis.from_url(redis_url)

        last_posted_id_bytes = r.get('last_posted_video_id')
        last_posted_id = last_posted_id_bytes.decode('utf-8') if last_posted_id_bytes else None
        print(f"Last posted video ID from memory: {last_posted_id}")

        try:
            feed = feedparser.parse(RSS_FEED_URL)
            if not feed.entries:
                self.send_response(204) # No content
                return

            new_videos = []
            for video in feed.entries:
                video_id = video.get('yt_videoid')
                if video_id == last_posted_id:
                    break
                new_videos.append(video)

            if not new_videos:
                print("No new videos to post.")
                self.send_response(200)
                self.wfile.write("No new videos.".encode('utf-8'))
                return
            
            new_videos.reverse()
            print(f"Found {len(new_videos)} new videos to post.")
            
            for video in new_videos:
                self.send_to_discord(video.link)

            newest_video_id = new_videos[-1].get('yt_videoid')
            r.set('last_posted_video_id', newest_video_id)
            print(f"Successfully posted and updated last video ID to: {newest_video_id}")

            self.send_response(200)
            self.wfile.write(f"Posted {len(new_videos)} new videos.".encode('utf-8'))
            return

        except Exception as e:
            # If anything in the 'try' block fails, this code will run instead of crashing
            print(f"CRITICAL ERROR: Failed to process RSS feed. Error: {e}")
            self.send_response(500)
            self.wfile.write(f"An error occurred: {e}".encode('utf-8'))
            return
        # --- END of new try...except block ---

    def send_to_discord(self, video_url):
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        if not webhook_url: return
        headers = {"Content-Type": "application/json"}
        data = {"content": video_url}
        try:
            requests.post(webhook_url, data=json.dumps(data), headers=headers).raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error sending video link to Discord: {e}")