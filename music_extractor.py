import asyncio
import random
import re
from typing import Dict, List, Optional
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp as youtube_dl

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, YTDL_OPTIONS

try:
    from ytmusicapi import YTMusic
    ytmusic = YTMusic()
except Exception as e:
    ytmusic = None
    print(f"[Warning] ytmusicapi initialization failed: {e}")

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
    async def search_spotify_playlist(query: str, limit: int = 10) -> List[dict]:
        """
        Searches Spotify for top tracks matching a genre, vibe, or artist and returns tracks.
        """
        if not sp:
            return []

        safe_limit = min(limit, 10)
        loop = asyncio.get_event_loop()
        try:
            # Query with 'hits' or plain query
            q_clean = query.strip()
            search_query = q_clean if any(w in q_clean.lower() for w in ["hit", "top", "best", "radio"]) else f"{q_clean} hits"
            results = await loop.run_in_executor(
                None, lambda: sp.search(q=search_query, type='track', limit=safe_limit)
            )
            items = results.get('tracks', {}).get('items', [])
            if not items:
                # Fallback to plain query
                results = await loop.run_in_executor(
                    None, lambda: sp.search(q=q_clean, type='track', limit=safe_limit)
                )
                items = results.get('tracks', {}).get('items', [])

            tracks_data: List[dict] = []
            for track in items:
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
            print(f"[Spotify Track Search Warning] {e}")
            return []

    @staticmethod
    async def get_autoplay_recommendations(last_song_title: str, history: Optional[List[str]] = None, limit: int = 5) -> List[dict]:
        """
        Finds recommended tracks matching the genre, vibe, and energy of the last played song
        across diverse artists (Spotify/YouTube Radio style).
        """
        history_lower = [h.lower() for h in (history or [])]
        # Clean title noise
        clean_title = re.sub(r'[\(\[][^\)\]]*(?:official|video|audio|lyrics|hd|4k|remaster|visualizer)[^\)\]]*[\)\]]', '', last_song_title, flags=re.IGNORECASE)
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        loop = asyncio.get_event_loop()

        # 1. Primary: Use YouTube Music Radio algorithm (returns true 'songs like this' by varied artists)
        if ytmusic:
            try:
                def _fetch_ytm_radio():
                    results = ytmusic.search(clean_title, filter="songs")
                    if not results:
                        return []
                    seed = results[0]
                    seed_video_id = seed.get('videoId')
                    seed_artist = seed.get('artists', [{}])[0].get('name', '').lower()
                    seed_name = seed.get('title', '').lower()

                    watch = ytmusic.get_watch_playlist(videoId=seed_video_id, limit=35)
                    tracks_data = []
                    same_artist_count = 0

                    for t in watch.get('tracks', []):
                        t_name = t.get('title', '')
                        t_artists_list = [a.get('name', '') for a in t.get('artists', [])]
                        t_artists = ", ".join(t_artists_list)
                        full_title = f"{t_name} - {t_artists}"
                        t_artist_main = t_artists_list[0].lower() if t_artists_list else ""

                        # Skip if in history or matches seed
                        if any(h in full_title.lower() or full_title.lower() in h for h in history_lower):
                            continue
                        if seed_name and (seed_name in t_name.lower() or t_name.lower() in seed_name):
                            continue
                        if clean_title.lower() in t_name.lower() or t_name.lower() in clean_title.lower():
                            continue

                        # Diversity filter: allow at most 1 track by original artist to prioritize 'songs like this'
                        if seed_artist and seed_artist in t_artist_main:
                            if same_artist_count >= 1:
                                continue
                            same_artist_count += 1

                        thumb = None
                        thumbs = t.get('thumbnail', [])
                        if isinstance(thumbs, list) and len(thumbs) > 0:
                            thumb = thumbs[-1].get('url')

                        # Parse duration string "MM:SS"
                        dur_sec = 0
                        length_str = t.get('length')
                        if isinstance(length_str, str) and ":" in length_str:
                            parts = length_str.split(":")
                            try:
                                dur_sec = int(parts[0]) * 60 + int(parts[1]) if len(parts) == 2 else int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                            except Exception:
                                dur_sec = 0

                        tracks_data.append({
                            'title': full_title,
                            'search_query': f"{t_name} {t_artists}",
                            'spotify_url': f"https://music.youtube.com/watch?v={t.get('videoId')}",
                            'thumbnail': thumb,
                            'duration': dur_sec
                        })
                        if len(tracks_data) >= limit:
                            break
                    return tracks_data

                recs = await loop.run_in_executor(None, _fetch_ytm_radio)
                if recs:
                    return recs
            except Exception as e:
                print(f"[Autoplay YTM Warning] {e}")

        # 2. Secondary: Spotify playlist/track search
        if sp:
            try:
                # Search for vibe playlist
                vibe_query = f"{clean_title} radio"
                rec_res = await loop.run_in_executor(
                    None, lambda: sp.search(q=vibe_query, type='track', limit=10)
                )
                tracks_data = []
                for t in rec_res.get('tracks', {}).get('items', []):
                    t_name = t.get('name', '')
                    t_artists = ", ".join([a['name'] for a in t.get('artists', [])])
                    full_title = f"{t_name} - {t_artists}"

                    if any(h in full_title.lower() or full_title.lower() in h for h in history_lower):
                        continue
                    if clean_title.lower() in t_name.lower():
                        continue

                    album_art = t['album']['images'][0]['url'] if t.get('album', {}).get('images') else None
                    tracks_data.append({
                        'title': full_title,
                        'search_query': f"{t_name} {t_artists}",
                        'spotify_url': t['external_urls'].get('spotify', ''),
                        'thumbnail': album_art,
                        'duration': t.get('duration_ms', 0) // 1000
                    })
                    if len(tracks_data) >= limit:
                        break

                if tracks_data:
                    return tracks_data
            except Exception as e:
                print(f"[Autoplay Spotify Warning] {e}")

        # 3. Fallback: search YouTube for radio mix
        try:
            yt_res = await loop.run_in_executor(
                None, lambda: ytdl.extract_info(f"ytsearch{limit + 5}:{clean_title} radio mix", download=False)
            )
            entries = yt_res.get('entries', []) if yt_res else []
            tracks = []
            for entry in entries:
                if not entry:
                    continue
                e_title = entry.get('title', '')
                if any(h in e_title.lower() for h in history_lower):
                    continue
                tracks.append({
                    'title': e_title,
                    'search_query': e_title,
                    'spotify_url': entry.get('webpage_url', ''),
                    'thumbnail': entry.get('thumbnail'),
                    'duration': entry.get('duration', 0)
                })
                if len(tracks) >= limit:
                    break
            return tracks
        except Exception as e:
            print(f"[Autoplay YouTube Warning] {e}")
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
