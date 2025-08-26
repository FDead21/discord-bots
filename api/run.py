# api/run.py

import os
import requests
import json
import feedparser
from http.server import BaseHTTPRequestHandler
from vercel_kv import KV

RSS_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=UCWJ2lWNubArHWmf3FIHbfcQ"
EMBED_COLOR = 16711680 # YouTube Red

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        last_posted_id = KV.get('last_posted_video_id')
        print(f"Last posted video ID from memory: {last_posted_id}")

        feed = feedparser.parse(RSS_FEED_URL)
        if not feed.entries:
            self.send_response(204) # No content
            self.end_headers()
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
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write("No new videos.".encode('utf-8'))
            return
        
        new_videos.reverse()
        print(f"Found {len(new_videos)} new videos to post.")
        
        for video in new_videos:
            thumbnail_url = video.media_thumbnail[0]['url'] if 'media_thumbnail' in video else ""
            
            embed_data = {
                "title": video.title,
                "url": video.link,
                "color": EMBED_COLOR,
                "image": {"url": thumbnail_url},
                "author": {"name": video.author},
                "footer": {"text": "Source: Official NBA YouTube Channel"}
            }
            self.send_to_discord(embed_data)

        newest_video_id = new_videos[-1].get('yt_videoid')
        KV.set('last_posted_video_id', newest_video_id)
        print(f"Successfully posted and updated last video ID to: {newest_video_id}")

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(f"Posted {len(new_videos)} new videos.".encode('utf-8'))
        return

    def send_to_discord(self, embed_data):
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        if not webhook_url: return
        headers = {"Content-Type": "application/json"}
        data = {
            "content": f"**{embed_data['author']['name']}** just uploaded a new video!",
            "embeds": [embed_data]
        }
        try:
            requests.post(webhook_url, data=json.dumps(data), headers=headers).raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error sending embed to Discord: {e}")