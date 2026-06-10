import os
import sys
import time
import requests
from dotenv import load_dotenv

base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
load_dotenv(os.path.join(base_dir, ".env"))

class ClipEditor:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "x-api-key": os.getenv("JSON2VIDEO_SECRET"),
            "Content-Type": "application/json",
        })
        
    def edit_clip(self, clip):
        response = self.session.post("https://api.json2video.com/v2/movies", 
            json={
                "template": "dMdY8aBnmrOFINmB2wej",
                "variables": {
                    "video_url": clip["unedited_download_url"],
                    "caption": f"{clip['title']} 😭🔥"
                }
            }
        )
        if response.status_code == 200:
            return response.json()["project"]
        else:
            raise Exception(f"Failed to edit clip: {response.status_code} - {response.text}")

    def wait_for_movie(self, project_id):
        while True:
            res = self.session.get("https://api.json2video.com/v2/movies",
                params={"project": project_id},
            )
            if res.status_code != 200:
                raise Exception(f"Failed to check movie status: {res.status_code} - {res.text}")
            
            movie = res.json()["movie"]
            if movie["status"] == "done":
                return movie["url"]
            if movie["status"] == "error":
                raise RuntimeError(movie.get("message"))
            time.sleep(3)