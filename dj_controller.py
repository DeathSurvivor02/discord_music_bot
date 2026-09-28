import asyncio
import os
import random
import re
import tempfile
from typing import Optional, Tuple
import edge_tts

from config import GEMINI_API_KEY, DJ_NAME, DJ_VOICE

# Available voice options for user customization with studio broadcast modulation
DJ_VOICE_PRESETS = {
    "x": {
        "voice": "en-US-BrianMultilingualNeural",
        "pitch": "-4Hz",
        "rate": "+4%",
        "name": "DJ X (Spotify Style)",
        "desc": "Authentic Spotify DJ X: Charismatic, urban, modern cadence"
    },
    "christopher": {
        "voice": "en-US-ChristopherNeural",
        "pitch": "-5Hz",
        "rate": "+2%",
        "name": "Deep FM Broadcaster",
        "desc": "Bass-boosted studio microphone, late night radio presenter"
    },
    "andrew": {
        "voice": "en-US-AndrewMultilingualNeural",
        "pitch": "-3Hz",
        "rate": "+3%",
        "name": "Smooth Host",
        "desc": "Warm, engaging, contemporary podcast style"
    },
    "steffan": {
        "voice": "en-US-SteffanNeural",
        "pitch": "-4Hz",
        "rate": "+2%",
        "name": "Midnight Baritone",
        "desc": "Low-frequency, relaxed, deep baritone radio voice"
    },
    "roger": {
        "voice": "en-US-RogerNeural",
        "pitch": "-2Hz",
        "rate": "+6%",
        "name": "Hype Club DJ",
        "desc": "High energy, punchy and fast-paced"
    },
    "ryan": {
        "voice": "en-GB-RyanNeural",
        "pitch": "-3Hz",
        "rate": "+4%",
        "name": "UK 1Xtra",
        "desc": "Smooth British radio presenter"
    },
    "ava": {
        "voice": "en-US-AvaMultilingualNeural",
        "pitch": "-2Hz",
        "rate": "+3%",
        "name": "Ava (Female DJ)",
        "desc": "Crisp, modern, melodic female host"
    }
}


def clean_track_title(title: str) -> str:
    """Cleans YouTube noise like '(Official Video)', '[4K]', 'feat.' for natural speech."""
    # Remove contents in brackets/parentheses like (Official Video), [HD], etc.
    cleaned = re.sub(r'[\(\[][^\)\]]*(?:official|video|audio|lyrics|hd|4k|remaster|visualizer)[^\)\]]*[\)\]]', '', title, flags=re.IGNORECASE)
    # Remove multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else title

class DJController:
    """Manages AI radio script generation and neural voice synthesis."""

    def __init__(self):
        self.dj_name = DJ_NAME or "DJ X"
        self.cache_dir = os.path.join(tempfile.gettempdir(), "discord_bot_dj_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self._gemini_client = None
        self._init_gemini()

    def _init_gemini(self):
        if GEMINI_API_KEY and GEMINI_API_KEY.strip() and "your_" not in GEMINI_API_KEY:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=GEMINI_API_KEY.strip())
            except Exception as e:
                print(f"[DJ Controller] Failed to initialize Gemini client: {e}")
                self._gemini_client = None

    async def generate_speech_text(
        self,
        next_song_title: str,
        requester: str,
        previous_song_title: Optional[str] = None,
        is_first: bool = False,
        vibe: Optional[str] = None
    ) -> str:
        """Generates radio DJ commentary using Gemini or dynamic fallback templates."""
        cleaned_next = clean_track_title(next_song_title)
        cleaned_prev = clean_track_title(previous_song_title) if previous_song_title else None

        # 1. Try generating with Gemini if available
        if self._gemini_client:
            try:
                return await self._generate_with_gemini(cleaned_next, requester, cleaned_prev, is_first, vibe=vibe)
            except Exception as e:
                print(f"[DJ Controller] Gemini script generation error: {e}. Using fallback template.")

        # 2. Dynamic high-quality fallback templates
        return self._generate_fallback(cleaned_next, requester, cleaned_prev, is_first, vibe=vibe)

    async def _generate_with_gemini(
        self,
        next_title: str,
        requester: str,
        prev_title: Optional[str],
        is_first: bool,
        vibe: Optional[str] = None
    ) -> str:
        """Uses Google Gemini 3.8 Flash to write authentic radio DJ banter."""
        prompt = (
            f"You are {self.dj_name}, the charismatic, smooth, culturally savvy radio AI DJ (modeled after Spotify DJ Xavier 'X').\n"
            f"Introduce the upcoming song in 1 to 2 punchy, conversational sentences (maximum 20-25 words).\n"
            f"- Next song: '{next_title}' requested by {requester}.\n"
        )
        if vibe:
            prompt += f"- Music vibe or genre requested: '{vibe}'. Mention you're locking into this vibe.\n"
        if prev_title and not is_first:
            prompt += f"- Previous song that just finished: '{prev_title}'. Smoothly bridge from it.\n"
        else:
            prompt += "- This is the start of the music session. Give a warm, hype welcome.\n"

        prompt += (
            "\nRules:\n"
            "1. Output ONLY the spoken words. No quotation marks, asterisks, brackets, or stage directions.\n"
            "2. Sound authentic, rhythmic, and natural for audio text-to-speech.\n"
            "3. Keep it brief and high energy.\n"
        )

        loop = asyncio.get_running_loop()
        # Run synchronous SDK call in thread pool with a quick timeout
        def call_gemini():
            response = self._gemini_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )
            return response.text.strip() if response and response.text else None

        text = await asyncio.wait_for(loop.run_in_executor(None, call_gemini), timeout=3.5)
        if text:
            # Clean any remaining markdown formatting
            text = text.replace('"', '').replace('*', '').replace('_', '').strip()
            return text

        raise RuntimeError("Empty response from Gemini")

    def _generate_fallback(
        self,
        next_title: str,
        requester: str,
        prev_title: Optional[str],
        is_first: bool,
        vibe: Optional[str] = None
    ) -> str:
        """Dynamic fallback radio drops when Gemini is offline or not configured."""
        if vibe:
            vibe_templates = [
                f"What's good everybody, it's {self.dj_name}! Setting the mood with some {vibe} for {requester}. First track up is {next_title}—let's get into it!",
                f"Welcome to the session, it's your boy {self.dj_name}! Locking into that {vibe} energy, starting off hot with {next_title} for {requester}. Turn it up!",
                f"{self.dj_name} in the mix! {requester} asked for that {vibe} feel, so we're kicking off with {next_title}. Let's ride the wave!",
                f"Aight y'all, {self.dj_name} right here. Turning on that {vibe} rotation for {requester}. Up first, {next_title}!"
            ]
            return random.choice(vibe_templates)

        if is_first or not prev_title:
            templates = [
                f"What's good everybody, it's {self.dj_name}! Kicking things off with {next_title}, lined up by {requester}. Let's get into it!",
                f"Welcome back to the vibe, it's your boy {self.dj_name}. Starting off strong with {next_title} for {requester}. Turn it up!",
                f"{self.dj_name} in the mix! We're rolling into {next_title}, shoutout to {requester} for the pick!",
                f"Alright y'all, {self.dj_name} right here. Let's set the mood with {next_title}, selected by {requester}!"
            ]
        else:
            templates = [
                f"That was {prev_title}. Next up, keeping the momentum going, here's {next_title} for {requester}!",
                f"And that wraps up {prev_title}. Sliding right into something fresh, check out {next_title} picked by {requester}!",
                f"Loving that energy from {prev_title}. Now, {requester} wanted to hear {next_title}, so let's ride the wave!",
                f"Smooth sounds right there with {prev_title}. Next in rotation, we got {next_title} queued up for {requester}!",
                f"Big vibes on that last track. Let's switch gears and roll right into {next_title} for {requester}!",
                f"That was {prev_title}. Staying locked in, here comes {next_title} courtesy of {requester}!"
            ]
        return random.choice(templates)

    async def synthesize_speech(self, text: str, output_path: str, voice: Optional[str] = None) -> bool:
        """Converts text to speech using edge-tts with radio broadcast pitch & rate tuning."""
        voice_key = (voice or DJ_VOICE or "x").lower()
        preset = DJ_VOICE_PRESETS.get(voice_key)

        if preset:
            selected_voice = preset["voice"]
            pitch = preset.get("pitch", "-4Hz")
            rate = preset.get("rate", "+3%")
        else:
            selected_voice = voice_key if "neural" in voice_key else "en-US-BrianMultilingualNeural"
            pitch = "-4Hz"
            rate = "+3%"

        try:
            communicate = edge_tts.Communicate(text, selected_voice, pitch=pitch, rate=rate)
            await communicate.save(output_path)
            return os.path.exists(output_path) and os.path.getsize(output_path) > 0
        except Exception as e:
            print(f"[DJ Controller] TTS synthesis failed: {e}")
            return False


    async def get_dj_audio_clip(
        self,
        guild_id: int,
        next_song_title: str,
        requester: str,
        previous_song_title: Optional[str] = None,
        is_first: bool = False,
        voice: Optional[str] = None,
        vibe: Optional[str] = None
    ) -> Tuple[Optional[str], str]:
        """
        Generates the script and synthesizes the audio clip.
        Returns a tuple: (audio_file_path, speech_text).
        If synthesis fails, audio_file_path is None.
        """
        speech_text = await self.generate_speech_text(
            next_song_title=next_song_title,
            requester=requester,
            previous_song_title=previous_song_title,
            is_first=is_first,
            vibe=vibe
        )

        output_file = os.path.join(self.cache_dir, f"dj_{guild_id}_{random.randint(1000, 9999)}.mp3")
        success = await self.synthesize_speech(speech_text, output_file, voice=voice)

        if success:
            return output_file, speech_text
        return None, speech_text

    def cleanup_file(self, file_path: Optional[str]):
        """Safely removes temporary DJ audio clip."""
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

dj_controller = DJController()
