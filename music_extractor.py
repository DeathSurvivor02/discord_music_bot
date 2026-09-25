import asyncio
import re
from typing import List, Optional
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp as youtube_dl

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, YTDL_OPTIONS

# Initialize Spotify client if credentials are configured
sp = None
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET and "your_" not in SPOTIFY_CLIENT_ID:
    try:
        sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET
            )
        )
    except Exception as e:
        print(f"[Warning] Spotify client setup failed: {e}")

ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

class Song:
    """Represents a playable music track."""
    def __init__(
        self,
        title: str,
        source_url: str,
        stream_url: str,
        duration: int,
        thumbnail: Optional[str],
        requester: str
    ):
        self.title = title
        self.source_url = source_url
        self.stream_url = stream_url
        self.duration = duration
        self.thumbnail = thumbnail
        self.requester = requester

class MusicExtractor:
    @staticmethod
    def is_spotify_url(query: str) -> bool:
        """Checks whether the query is a Spotify URL."""
        return "open.spotify.com" in query

    @staticmethod
    async def get_spotify_queries(url: str) -> List[str]:
        """
        Parses Spotify tracks, albums, or playlists into YouTube search terms.
        """
        if not sp:
            raise ValueError(
                "Spotify is not configured! Please provide SPOTIFY_CLIENT_ID and "
                "SPOTIFY_CLIENT_SECRET in your .env file."
            )

        loop = asyncio.get_event_loop()
        queries: List[str] = []

        if "/track/" in url:
            track = await loop.run_in_executor(None, lambda: sp.track(url))
            artist_name = track['artists'][0]['name'] if track['artists'] else ""
            queries.append(f"{track['name']} {artist_name}")

        elif "/playlist/" in url:
            results = await loop.run_in_executor(None, lambda: sp.playlist_tracks(url))
            for item in results.get('items', []):
                track = item.get('track')
                if track:
                    artist_name = track['artists'][0]['name'] if track['artists'] else ""
                    queries.append(f"{track['name']} {artist_name}")

        elif "/album/" in url:
            results = await loop.run_in_executor(None, lambda: sp.album_tracks(url))
            album_artist = results.get('items', [{}])[0].get('artists', [{}])[0].get('name', '')
            for track in results.get('items', []):
                queries.append(f"{track['name']} {album_artist}")

        return queries

    @staticmethod
    async def extract_ytdl(query: str, requester: str) -> List[Song]:
        """
        Extracts stream URL and metadata using yt-dlp.
        Supports direct URLs and plain-text search terms.
        """
        loop = asyncio.get_event_loop()
        is_url = query.startswith("http://") or query.startswith("https://")
        search_target = query if is_url else f"ytsearch:{query}"

        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(search_target, download=False)
        )

        songs: List[Song] = []
        if 'entries' in data and data['entries']:
            # Either a playlist or a search query
            entries = data['entries'] if is_url else [data['entries'][0]]
            for entry in entries:
                if not entry:
                    continue
                songs.append(Song(
                    title=entry.get('title', 'Unknown Title'),
                    source_url=entry.get('webpage_url', query),
                    stream_url=entry.get('url', ''),
                    duration=entry.get('duration', 0),
                    thumbnail=entry.get('thumbnail', None),
                    requester=requester
                ))
        else:
            songs.append(Song(
                title=data.get('title', 'Unknown Title'),
                source_url=data.get('webpage_url', query),
                stream_url=data.get('url', ''),
                duration=data.get('duration', 0),
                thumbnail=data.get('thumbnail', None),
                requester=requester
            ))

        return songs
