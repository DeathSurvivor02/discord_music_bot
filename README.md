# Discord Music Bot 🎵

A feature-rich Discord music bot built with **discord.py (v2.x)**, **yt-dlp**, and **spotipy**. Supports audio streaming from **YouTube** and metadata conversion from **Spotify** (tracks, playlists, and albums), with full **interactive Discord UI button controls**.

---

## ✨ Features

- 🎙️ **Spotify-Style AI DJ ("DJ X")**: Dynamic radio commentary spoken directly into your voice channel before tracks! Powered by neural text-to-speech with optional Google Gemini banter generation and customizable voice presets.
- 🎧 **YouTube Streaming**: Stream any YouTube video, playlist, or plain-text search query.
- 🟢 **Spotify Integration**: Resolves Spotify tracks, playlists, and albums into high-quality YouTube audio streams.
- 🎛️ **Interactive Controls**: Buttons directly on the "Now Playing" embed:
  - ⏯️ **Play / Pause**
  - ⏭️ **Skip**
  - ⏹️ **Stop & Disconnect**
  - 🔁 **Repeat / Loop**
  - 📜 **Queue Preview**
  - 🎧 **DJ: ON / OFF Toggle**
- ⚡ **Slash Commands**: Modern Discord commands (`/play`, `/skip`, `/stop`, `/nowplaying`, `/queue`, `/loop`, `/volume`, `/dj`).
- 🔊 **Volume Control**: Dynamic volume transformer (`/volume <1-100>`).

---

## 🚀 Setup & Installation

### Prerequisites
1. **Python 3.10+** (Tested on Python 3.11).
2. **FFmpeg** on system PATH:
   - **Windows**: `winget install Gyan.FFmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

### 1. Clone the Repository
```bash
git clone https://github.com/DeathSurvivor02/discord_music_bot.git
cd discord_music_bot
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure Credentials
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your API credentials in `.env`:
- **DISCORD_TOKEN**: From [Discord Developer Portal](https://discord.com/developers/applications)
  - Ensure **Message Content Intent** and **Server Members Intent** are enabled under Privileged Gateway Intents.
- **SPOTIFY_CLIENT_ID** & **SPOTIFY_CLIENT_SECRET**: From [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- **GEMINI_API_KEY** *(Optional)*: From [Google AI Studio](https://aistudio.google.com/) for dynamic AI DJ commentary scriptwriting.

---

## 🎮 Running the Bot

```bash
python bot.py
```

### Commands in Discord
- `/play <query>`: Play a song from YouTube, Spotify, or a search term.
- `/skip`: Skip the current song.
- `/stop`: Clear the queue and leave voice.
- `/nowplaying`: Display the current track with control buttons.
- `/queue`: View upcoming songs in queue.
- `/loop`: Toggle repeating the active song.
- `/volume <1-100>`: Set playback volume.
- `/dj <action>`: Manage AI DJ commentary (`toggle`, `drop`, `frequency`, `voice`, `status`).
  - *Voices available*: `christopher` (default radio host), `eric` (energetic), `guy` (conversational), `jenny` (warm female), `ryan` (British radio host), `sonia` (British female).

---

## 🛡️ License
MIT License.
