# ClipFetcher

Fetch and download Twitch clips via the Helix API.

## Setup

```bash
pip install requests python-dotenv yt-dlp pyinstaller
```

Add a `.env` file in `src/` with your [Twitch app](https://dev.twitch.tv/console/apps) credentials:

```env
CLIENT_ID=your_client_id
CLIENT_SECRET=your_twitch_client_secret
JSON2VIDEO_SECRET=your_json2video_client_secret
INSTAGRAM_SECRET=your_meta_client_secret
INSTAGRAM_APP_ID=your_meta_app_id
```

## Running from source

From `src/`:

```bash
python -m app.clip_fetcher_app
```

## Build

To build the fetcher or editor into a standalone `.exe`, run from `src/`:

```bash
pyinstaller --name "ClipFetcher" --onefile --distpath ../build --workpath ../build/temp --specpath ../build run_fetcher.py
```

```bash
pyinstaller --name "ClipEditor" --onefile --distpath ../build --workpath ../build/temp --specpath ../build run_editor.py
```

The `.exe` will be in `../build`.

**Don't forget to copy `.env` into `build/` after building** — PyInstaller does not bundle it automatically.