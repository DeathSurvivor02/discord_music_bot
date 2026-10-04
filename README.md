# Discord Music Bot

A Discord music bot that plays songs from YouTube and Spotify, with an optional Spotify-style "AI DJ" that hops on the mic between tracks to introduce songs.

---

## What It Does

- **Plays Music:** Drop a YouTube link, Spotify link (song, album, or playlist), or just type song names to search and play.
- **AI DJ:** Talks in voice chat between songs like a radio DJ. Uses Edge TTS voices (Christopher, Eric, Guy, Jenny, Ryan, Sonia) and can use Google Gemini to write quick commentary about the artists.
- **On-Screen Buttons:** Skip, pause, resume, loop, and view the queue right from the embed buttons in chat without typing commands.
- **Autoplay:** Keeps the music going with recommendations when your queue runs out.
- **Web & Mobile Companion:** Includes a local FastAPI server and a lightweight web player if you want to listen outside Discord.

---

## Setup

### 1. Prerequisites
- **Python 3.10+**
- **FFmpeg** installed and added to your PATH:
  - Windows: `winget install Gyan.FFmpeg`
  - Mac: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

### 2. Install
```bash
git clone https://github.com/DeathSurvivor02/discord_music_bot.git
cd discord_music_bot

# Create and activate virtual environment
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# Mac / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Add Your Keys
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Open `.env` and fill in:
- `DISCORD_TOKEN`: From the [Discord Developer Portal](https://discord.com/developers/applications). Make sure to turn on **Message Content Intent** and **Server Members Intent** under your bot settings.
- `SPOTIFY_CLIENT_ID` & `SPOTIFY_CLIENT_SECRET`: Free from the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
- `GEMINI_API_KEY` *(Optional)*: Free from [Google AI Studio](https://aistudio.google.com/) if you want the DJ to write custom intro banter. If omitted, the DJ uses built-in radio lines.

---

## Running the Bot

```bash
python bot.py
```

### Discord Commands
- `/play <query>`: Play a song, playlist, or search term
- `/skip`: Skip to the next track
- `/stop`: Stop music and disconnect from voice
- `/nowplaying`: Shows what's currently playing with control buttons
- `/queue`: See what's coming up next
- `/loop`: Repeat the current song
- `/volume <1-100>`: Change volume
- `/dj toggle`: Turn the AI DJ on or off
- `/dj voice <name>`: Pick a DJ voice (`christopher`, `eric`, `guy`, `jenny`, `ryan`, `sonia`)
- `/dj drop`: Force the DJ to talk right before the next song

---

## License

[MIT](LICENSE)
