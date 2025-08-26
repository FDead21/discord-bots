# api/run.py

import os
import requests
import json
from http.server import BaseHTTPRequestHandler

# This is the main handler class for the Vercel serverless function.
class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        """
        This method is called when a GET request is made to the function's URL.
        This is where our main logic will live.
        """

        # --- 1. Fetch the data you want to post ---
        # For now, we'll use a static message.
        # In the future, you would replace this section with code to call a real API
        # (e.g., fetch top post from r/nba, get scores from a sports API).
        message_to_send = "🏀 This is an automated test message from my Vercel Python bot!"

        # --- 2. Send the data to Discord ---
        self.send_to_discord(message_to_send)

        # --- 3. Send a success response back to the caller (the cron job) ---
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response_body = {"status": "success", "message": "Message sent to Discord."}
        self.wfile.write(json.dumps(response_body).encode('utf-8'))
        return

    def send_to_discord(self, message_content):
        """Sends the provided message to the Discord webhook."""

        # Get the webhook URL from an environment variable for security
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")

        if not webhook_url:
            print("ERROR: DISCORD_WEBHOOK_URL environment variable is not set.")
            return

        headers = { "Content-Type": "application/json" }
        data = { "content": message_content }

        try:
            response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
            response.raise_for_status() # Raises an exception for 4xx/5xx errors
            print(f"Message sent successfully, status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending message to Discord: {e}")