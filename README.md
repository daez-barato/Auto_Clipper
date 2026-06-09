# ClipFetcher
 
Fetch and download Twitch clips via the Helix API.
 
## Setup
 
```bash
pip install requests python-dotenv yt-dlp pyinstaller
```
 
Add a `.env` file with your [Twitch app](https://dev.twitch.tv/console/apps) credentials:
 
```env
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
```

## Build

pyinstaller --onefile --windowed app.py