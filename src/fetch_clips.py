from clip_fetcher import ClipFetcher

if __name__ == "__main__":
    clip_fetcher = ClipFetcher()
    clip_fetcher.update_broadcaster_ids(["marlon"])

    clips = clip_fetcher.fetch_clips("marlon", limit=1)
    clip_fetcher.download_clip(clips[0])
    
