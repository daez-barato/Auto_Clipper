import sys
import requests;
import os;
from dotenv import load_dotenv, find_dotenv;
from yt_dlp import YoutubeDL;


base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
load_dotenv(os.path.join(base_dir, ".env"))

_streamers = {}

class ClipFetcher:
    def __init__(self):
        base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
        self.download_path = os.path.join(base_dir, "extracted")
        os.makedirs(self.download_path, exist_ok=True)
        self.session = requests.Session()
        response = self.session.post("https://id.twitch.tv/oauth2/token", data={
            "client_id": os.getenv("CLIENT_ID"),
            "client_secret": os.getenv("CLIENT_SECRET"),
            "grant_type": "client_credentials"
        })
        if response.status_code == 200:
            self.access_token = response.json().get("access_token")
            self.session.headers.update({
                "Authorization": f"Bearer {self.access_token}",
                'Client-ID': os.getenv("CLIENT_ID"),
            })
        else:
            raise Exception(f"Failed to obtain access token: {response.status_code}")
    
    def update_broadcaster_ids(self, streamers):
        
        response = self.session.get("https://api.twitch.tv/helix/users", params={
            "login": streamers
        })

        if response.status_code == 200:
            data = response.json().get("data", [])
            for user in data:
                _streamers[user["login"]] = user["id"]
        else:
            raise Exception(f"Failed to fetch broadcaster ID: {response.status_code}")
    
    def get_trending_broadcasters(self, limit=5):
        
        response = self.session.get("https://api.twitch.tv/helix/streams", params={
            "first": limit
        })

        if response.status_code == 200:
            data = response.json().get("data", [])
            return [stream["user_login"] for stream in data]
        else:
            raise Exception(f"Failed to fetch trending broadcasters: {response.status_code}")

    def fetch_clips(self, streamer_name, limit=5):
        
        response = self.session.get("https://api.twitch.tv/helix/clips", params={
            "broadcaster_id": _streamers.get(streamer_name),
            "first": limit
        })
        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            raise Exception(f"Failed to fetch clips: {response.status_code}")
        
    def set_download_path(self, path):
        self.download_path = path
    
    def download_clip(self, clip):

        with YoutubeDL({"outtmpl": os.path.join(self.download_path, f"{clip['title'].replace(' ', '_')}.mp4")}) as ydl:
            ydl.download([clip["url"]])