import asyncio
import os
import edge_tts
from mutagen.mp3 import MP3

DEFAULT_VOICE = "en-US-JennyNeural"
DEFAULT_TEXT = "Hello! This is a test for TTS rate calibration."
OUTPUT_FILE = "output_test.mp3"


async def generate_speech(text: str, output_file: str, voice: str = DEFAULT_VOICE, rate: str = "+0%") -> str:
    """Generate audio using Edge TTS."""
    print(f"Generating audio with voice='{voice}', rate='{rate}'...")
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(output_file)
    print(f"Audio saved to {output_file}")
    return output_file


def inspect_audio(file_path: str):
    """Inspect generated audio file length and metadata with mutagen."""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    audio = MP3(file_path)
    print(f"\n--- Audio File Info ({file_path}) ---")
    print(f"Duration: {audio.info.length:.2f} seconds")
    print(f"Bitrate: {audio.info.bitrate // 1000} kbps")
    print(f"Sample Rate: {audio.info.sample_rate} Hz")
    print(f"Channels: {audio.info.channels}")


async def main():
    await generate_speech(DEFAULT_TEXT, OUTPUT_FILE, rate="+0%")
    inspect_audio(OUTPUT_FILE)


if __name__ == "__main__":
    asyncio.run(main())
