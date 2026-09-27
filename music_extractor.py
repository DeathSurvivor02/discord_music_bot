import asyncio
from typing import Dict, List, Optional
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
    def is_youtube_url(query: str) -> bool:
        """Checks whether the query is a direct YouTube URL."""
        return "youtube.com" in query or "youtu.be" in query

    @staticmethod
    async def search_spotify_track(query: str) -> Optional[Dict]:
        """
        Searches Spotify's catalog for the top matching track and returns its metadata.
        """
        if not sp:
            return None

        loop = asyncio.get_event_loop()
        try:
            results = await loop.run_in_executor(
                None, lambda: sp.search(q=query, type='track', limit=1)
            )
            items = results.get('tracks', {}).get('items', [])
            if items:
                track = items[0]
                artists = ", ".join([a['name'] for a in track.get('artists', [])])
                album_art = None
                if track.get('album', {}).get('images'):
                    album_art = track['album']['images'][0]['url']

                return {
                    'title': f"{track['name']} - {artists}",
                    'search_query': f"{track['name']} {artists}",
                    'spotify_url': track['external_urls'].get('spotify', ''),
                    'thumbnail': album_art,
                    'duration': track.get('duration_ms', 0) // 1000
                }
        except Exception as e:
            print(f"[Spotify Search Warning] {e}")

        return None

    @staticmethod
    async def search_spotify_playlist(query: str, limit: int = 15) -> List[dict]:
        """
        Searches Spotify for a playlist or top tracks matching a genre/vibe and returns tracks.
        """
        if not sp:
            return []

        loop = asyncio.get_event_loop()
        try:
            # 1. Try finding a curated playlist first
            results = await loop.run_in_executor(
                None, lambda: sp.search(q=query, type='playlist', limit=3)
            )
            items = results.get('playlists', {}).get('items', [])
            # Filter out None items if any
            items = [p for p in items if p and p.get('id')]

            if items:
                playlist_id = items[0]['id']
                p_tracks = await loop.run_in_executor(
                    None, lambda: sp.playlist_tracks(playlist_id, limit=limit)
                )
                tracks_data: List[dict] = []
                for item in p_tracks.get('items', []):
                    track = item.get('track') if item else None
                    if track and track.get('name'):
                        artists = ", ".join([a['name'] for a in track.get('artists', [])])
                        album_art = track['album']['images'][0]['url'] if track.get('album', {}).get('images') else None
                        tracks_data.append({
                            'title': f"{track['name']} - {artists}",
                            'search_query': f"{track['name']} {artists}",
                            'spotify_url': track['external_urls'].get('spotify', ''),
                            'thumbnail': album_art,
                            'duration': track.get('duration_ms', 0) // 1000
                        })
                if tracks_data:
                    return tracks_data

            # 2. Fallback: Search for top tracks directly with that genre/vibe
            track_res = await loop.run_in_executor(
                None, lambda: sp.search(q=query, type='track', limit=limit)
            )
            tracks_data = []
            for track in track_res.get('tracks', {}).get('items', []):
                if track and track.get('name'):
                    artists = ", ".join([a['name'] for a in track.get('artists', [])])
                    album_art = track['album']['images'][0]['url'] if track.get('album', {}).get('images') else None
                    tracks_data.append({
                        'title': f"{track['name']} - {artists}",
                        'search_query': f"{track['name']} {artists}",
                        'spotify_url': track['external_urls'].get('spotify', ''),
                        'thumbnail': album_art,
                        'duration': track.get('duration_ms', 0) // 1000
                    })
            return tracks_data
        except Exception as e:
            print(f"[Spotify Playlist Search Warning] {e}")
            return []

    @staticmethod
    async def get_spotify_queries(url: str) -> List[dict]:
        """
        Parses Spotify tracks, albums, or playlists into metadata dictionaries.
        """
        if not sp:
            raise ValueError(
                "Spotify is not configured! Please provide SPOTIFY_CLIENT_ID and "
                "SPOTIFY_CLIENT_SECRET in your .env file."
            )

        loop = asyncio.get_event_loop()
        tracks_data: List[dict] = []

        if "/track/" in url:
            track = await loop.run_in_executor(None, lambda: sp.track(url))
            artists = ", ".join([a['name'] for a in track.get('artists', [])])
            album_art = track['album']['images'][0]['url'] if track.get('album', {}).get('images') else None
            tracks_data.append({
                'title': f"{track['name']} - {artists}",
                'search_query': f"{track['name']} {artists}",
                'spotify_url': track['external_urls'].get('spotify', url),
                'thumbnail': album_art,
                'duration': track.get('duration_ms', 0) // 1000
            })

        elif "/playlist/" in url:
            results = await loop.run_in_executor(None, lambda: sp.playlist_tracks(url))
            for item in results.get('items', []):
                track = item.get('track')
                if track:
                    artists = ", ".join([a['name'] for a in track.get('artists', [])])
                    album_art = track['album']['images'][0]['url'] if track.get('album', {}).get('images') else None
                    tracks_data.append({
                        'title': f"{track['name']} - {artists}",
                        'search_query': f"{track['name']} {artists}",
                        'spotify_url': track['external_urls'].get('spotify', ''),
                        'thumbnail': album_art,
                        'duration': track.get('duration_ms', 0) // 1000
                    })

        elif "/album/" in url:
            results = await loop.run_in_executor(None, lambda: sp.album_tracks(url))
            album_info = await loop.run_in_executor(None, lambda: sp.album(url))
            album_art = album_info['images'][0]['url'] if album_info.get('images') else None
            album_artist = album_info.get('artists', [{}])[0].get('name', '')

            for track in results.get('items', []):
                artists = ", ".join([a['name'] for a in track.get('artists', [])]) or album_artist
                tracks_data.append({
                    'title': f"{track['name']} - {artists}",
                    'search_query': f"{track['name']} {artists}",
                    'spotify_url': track['external_urls'].get('spotify', ''),
                    'thumbnail': album_art,
                    'duration': track.get('duration_ms', 0) // 1000
                })

        return tracks_data

    @staticmethod
    async def extract_ytdl(
        query: str,
        requester: str,
        override_title: Optional[str] = None,
        override_url: Optional[str] = None,
        override_thumbnail: Optional[str] = None
    ) -> List[Song]:
        """
        Extracts stream URL using yt-dlp.
        Supports direct URLs and plain-text search terms, with optional Spotify metadata override.
        """
        loop = asyncio.get_event_loop()
        is_url = query.startswith("http://") or query.startswith("https://")
        search_target = query if is_url else f"ytsearch:{query}"

        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(search_target, download=False)
        )

        songs: List[Song] = []
        if 'entries' in data and data['entries']:
            entries = data['entries'] if is_url else [data['entries'][0]]
            for entry in entries:
                if not entry:
                    continue
                songs.append(Song(
                    title=override_title or entry.get('title', 'Unknown Title'),
                    source_url=override_url or entry.get('webpage_url', query),
                    stream_url=entry.get('url', ''),
                    duration=entry.get('duration', 0),
                    thumbnail=override_thumbnail or entry.get('thumbnail', None),
                    requester=requester
                ))
        else:
            songs.append(Song(
                title=override_title or data.get('title', 'Unknown Title'),
                source_url=override_url or data.get('webpage_url', query),
                stream_url=data.get('url', ''),
                duration=data.get('duration', 0),
                thumbnail=override_thumbnail or data.get('thumbnail', None),
                requester=requester
            ))

        return songs
