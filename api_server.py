import asyncio
import os
import socket
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from config import DJ_NAME, DJ_VOICE
from music_extractor import MusicExtractor
from dj_controller import dj_controller, DJ_VOICE_PRESETS

def get_local_ip() -> str:
    """Attempts to find the machine's local Wi-Fi / LAN IP for phone connection."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't need to be reachable, just used to detect the default outgoing interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

app = FastAPI(title="Spotify AI DJ Mobile API", version="1.0.0")

# Enable CORS for mobile development & Web preview
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount DJ audio cache so mobile app can stream generated voice drops
os.makedirs(dj_controller.cache_dir, exist_ok=True)
app.mount("/dj_audio", StaticFiles(directory=dj_controller.cache_dir), name="dj_audio")

# Models
class VibeSessionRequest(BaseModel):
    vibe: Optional[str] = "Today's Top Hits"
    voice: Optional[str] = None

class DJIntroRequest(BaseModel):
    next_track: str
    prev_track: Optional[str] = None
    vibe: Optional[str] = None
    voice: Optional[str] = None
    is_first: bool = False

class ResolveStreamRequest(BaseModel):
    search_query: str
    title: Optional[str] = None

class AutoplayRequest(BaseModel):
    last_track: str
    history: Optional[List[str]] = []
    limit: Optional[int] = 5

@app.get("/api/health")
async def health_check():
    """Healthcheck endpoint returning local connection info and DJ settings."""
    return {
        "status": "online",
        "dj_name": DJ_NAME,
        "default_voice": DJ_VOICE,
        "local_ip": get_local_ip(),
        "api_port": 8000,
        "voice_presets": list(DJ_VOICE_PRESETS.keys())
    }

@app.get("/api/search")
async def search_tracks(q: str = Query(..., description="Song name or artist")):
    """Searches Spotify catalog first, falling back to YouTube."""
    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    query = q.strip()
    spotify_track = await MusicExtractor.search_spotify_track(query)
    if spotify_track:
        return {"source": "spotify", "tracks": [spotify_track]}

    # Fallback to direct extraction query
    songs = await MusicExtractor.extract_ytdl(query, requester="Mobile User")
    if not songs:
        return {"source": "none", "tracks": []}

    return {
        "source": "youtube",
        "tracks": [{
            "title": s.title,
            "search_query": s.title,
            "spotify_url": s.source_url,
            "stream_url": s.stream_url,
            "thumbnail": s.thumbnail,
            "duration": s.duration
        } for s in songs]
    }

@app.post("/api/resolve")
async def resolve_stream(req: ResolveStreamRequest):
    """Resolves a playable stream URL for a track using yt-dlp."""
    songs = await MusicExtractor.extract_ytdl(req.search_query, requester="Mobile User", override_title=req.title)
    if not songs:
        raise HTTPException(status_code=404, detail="Could not extract stream for track")

    song = songs[0]
    return {
        "title": song.title,
        "stream_url": song.stream_url,
        "source_url": song.source_url,
        "thumbnail": song.thumbnail,
        "duration": song.duration
    }

@app.post("/api/dj/session")
async def start_vibe_session(req: VibeSessionRequest):
    """
    Launches an entire curated music session by vibe (e.g. 'Hip Hop', 'Chill', 'Today's Top Hits')
    Returns the track list and DJ X's synthesized opening speech clip.
    """
    vibe = req.vibe.strip() if req.vibe and req.vibe.strip() else "Today's Top Hits"
    tracks_data = await MusicExtractor.search_spotify_playlist(vibe, limit=15)

    if not tracks_data:
        raise HTTPException(status_code=404, detail=f"No tracks found for vibe: {vibe}")

    first_track = tracks_data[0]
    # Synthesize opening DJ intro
    audio_path, speech_text = await dj_controller.get_dj_audio_clip(
        guild_id=99999,  # mobile session id
        next_song_title=first_track['title'],
        requester="You",
        previous_song_title=None,
        is_first=True,
        voice=req.voice,
        vibe=vibe
    )

    audio_url = None
    if audio_path:
        filename = os.path.basename(audio_path)
        audio_url = f"/dj_audio/{filename}"

    return {
        "vibe": vibe,
        "dj_intro": {
            "text": speech_text,
            "audio_url": audio_url
        },
        "tracks": tracks_data
    }

@app.post("/api/dj/intro")
async def generate_dj_intro(req: DJIntroRequest):
    """Generates DJ X commentary audio for a specific track transition."""
    audio_path, speech_text = await dj_controller.get_dj_audio_clip(
        guild_id=99999,
        next_song_title=req.next_track,
        requester="You",
        previous_song_title=req.prev_track,
        is_first=req.is_first,
        voice=req.voice,
        vibe=req.vibe
    )

    audio_url = None
    if audio_path:
        filename = os.path.basename(audio_path)
        audio_url = f"/dj_audio/{filename}"

    return {
        "speech_text": speech_text,
        "audio_url": audio_url
    }

@app.post("/api/autoplay")
async def get_autoplay(req: AutoplayRequest):
    """Fetches recommended tracks based on listening history when the queue ends."""
    tracks = await MusicExtractor.get_autoplay_recommendations(
        last_song_title=req.last_track,
        history=req.history,
        limit=req.limit or 5
    )
    return {"tracks": tracks}

if __name__ == "__main__":
    local_ip = get_local_ip()
    print("=" * 60)
    print("Spotify AI DJ Mobile API Server")
    print(f"Local LAN Address: http://{local_ip}:8000")
    print(f"Localhost Address: http://127.0.0.1:8000")
    print(f"Interactive Docs: http://127.0.0.1:8000/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)
