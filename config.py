import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
BOT_PREFIX = os.getenv("BOT_PREFIX", "!")

# Gemini API & AI DJ Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DJ_ENABLED_BY_DEFAULT = os.getenv("DJ_ENABLED", "true").lower() in ("true", "1", "yes")
DJ_NAME = os.getenv("DJ_NAME", "DJ X")
DJ_VOICE = os.getenv("DJ_VOICE", "en-US-ChristopherNeural")
DJ_DEFAULT_FREQUENCY = int(os.getenv("DJ_FREQUENCY", "2"))

# Locate FFmpeg binary automatically on Windows / Linux / macOS
import shutil
import glob

def find_ffmpeg() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    # Check WinGet installation on Windows
    pattern = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\*ffmpeg*\*build\bin\ffmpeg.exe")
    matches = glob.glob(pattern)
    if matches and os.path.exists(matches[0]):
        return matches[0]
    pattern2 = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\**\ffmpeg.exe")
    matches2 = glob.glob(pattern2, recursive=True)
    if matches2 and os.path.exists(matches2[0]):
        return matches2[0]
    prog_files = glob.glob(r"C:\Program Files\*ffmpeg*\bin\ffmpeg.exe")
    if prog_files and os.path.exists(prog_files[0]):
        return prog_files[0]
    return "ffmpeg"

FFMPEG_EXECUTABLE = find_ffmpeg()

# Ensure FFmpeg directory is in current process PATH
if os.path.isabs(FFMPEG_EXECUTABLE) and os.path.exists(FFMPEG_EXECUTABLE):
    ffmpeg_dir = os.path.dirname(FFMPEG_EXECUTABLE)
    if ffmpeg_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

# FFmpeg streaming options: prevents stream aborts on packet drops
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# yt-dlp configuration
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'ios']
        }
    }
}
