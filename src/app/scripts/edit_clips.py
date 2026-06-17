import requests

from app.classes.clip_fetcher import ClipFetcher
from app.classes.clip_editor import ClipEditor
import os
import sys

base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
_clips = []

if __name__ == "__main__":
    clip_fetcher = ClipFetcher()
    clip_fetcher.update_broadcaster_ids(["jasontheween"])

    clips = clip_fetcher.fetch_clips("jasontheween", limit=1)
    _clips.extend(clips)

    clip_editor = ClipEditor()
    for clip in _clips:
        clip_url = clip_fetcher.clip_download_http(clip)

        clip["unedited_download_url"] = clip_url
        edit_id = clip_editor.edit_clip(clip)
        clip["edit_id"] = edit_id
        download_url = clip_editor.wait_for_movie(clip["edit_id"])
        clip["download_url"] = download_url

        filename = clip["title"].replace(" ", "_") + ".mp4"
        filepath = os.path.join(base_dir,"..", "edited", filename)
        os.makedirs(os.path.join(base_dir,"..", "edited"), exist_ok=True)

        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
