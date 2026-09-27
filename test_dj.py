import asyncio
import os
from dj_controller import dj_controller

async def main():
    print("Testing DJ text generation...")
    text1 = await dj_controller.generate_speech_text(
        next_song_title="Blinding Lights (Official Audio)",
        requester="Ean",
        is_first=True
    )
    print(f"Intro text: {text1}")

    text2 = await dj_controller.generate_speech_text(
        next_song_title="Starboy",
        requester="Alex",
        previous_song_title="Blinding Lights",
        is_first=False
    )
    print(f"Transition text: {text2}")

    print("Testing edge-tts synthesis...")
    audio_path, speech_text = await dj_controller.get_dj_audio_clip(
        guild_id=12345,
        next_song_title="Blinding Lights",
        requester="Ean",
        is_first=True
    )
    print(f"Generated audio: {audio_path}")
    print(f"Speech: {speech_text}")
    if audio_path and os.path.exists(audio_path):
        size = os.path.getsize(audio_path)
        print(f"Audio file size: {size} bytes")
        dj_controller.cleanup_file(audio_path)
        print(f"Cleaned up audio file: {not os.path.exists(audio_path)}")
        print("DJ test PASSED!")
    else:
        print("DJ test FAILED to generate audio!")

if __name__ == "__main__":
    asyncio.run(main())
