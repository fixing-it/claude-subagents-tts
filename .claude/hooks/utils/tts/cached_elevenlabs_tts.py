#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "elevenlabs",
#     "python-dotenv",
# ]
# ///

import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv

# Standard phrases that should have nice filenames
STANDARD_PHRASES = {
    "Work complete!": "work-complete.mp3",
    "Task finished!": "task-finished.mp3", 
    "All done!": "all-done.mp3",
    "Job complete!": "job-complete.mp3",
    "Ready for next task!": "ready-for-next-task.mp3",
    "Subagent complete!": "subagent-complete.mp3",
    "Setup completed successfully!": "setup-completed-successfully.mp3",
    "Test passed!": "test-passed.mp3",
    "Build successful!": "build-successful.mp3",
    "Deployment complete!": "deployment-complete.mp3",
    "Analysis finished!": "analysis-finished.mp3",
    "Processing complete!": "processing-complete.mp3"
}

def text_to_filename(text: str) -> str:
    """Convert text to a clean filename."""
    # Check if it's a standard phrase first
    if text in STANDARD_PHRASES:
        return STANDARD_PHRASES[text]
    
    # Otherwise create filename from text
    # Remove special characters, lowercase, replace spaces with dashes
    clean = re.sub(r'[^\w\s-]', '', text.lower())
    clean = re.sub(r'\s+', '-', clean.strip())
    # Limit length to reasonable filename
    if len(clean) > 50:
        clean = clean[:50]
    return f"{clean}.mp3"

def main():
    """
    Cached ElevenLabs TTS Script with Smart Audio Reuse
    
    Features:
    - Caches common phrases like "Work complete!", "Task finished!"
    - MD5 hash-based file naming for efficient lookup
    - Falls back to live generation for new text
    - Saves audio files in ./output/tts-cache/
    
    Usage:
    - ./cached_elevenlabs_tts.py "Text to speak"
    """
    
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("❌ Error: ELEVENLABS_API_KEY not found in environment variables")
        sys.exit(1)
    
    # Get text from command line
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = "The first move is what sets everything in motion."
    
    # Setup cache directory
    cache_dir = Path("./output/tts-cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Create smart filename
    filename = text_to_filename(text)
    cache_file = cache_dir / filename
    
    print(f"🎯 Text: {text}")
    
    # Check if cached version exists
    if cache_file.exists():
        print(f"🔄 Using cached audio: {filename}")
        try:
            from elevenlabs import play
            with open(cache_file, 'rb') as f:
                audio_data = f.read()
            play(audio_data)
            print("✅ Cached playback complete!")
            return
        except Exception as e:
            print(f"⚠️  Cache playback failed: {e}, generating new...")
    
    # Generate new audio
    try:
        from elevenlabs.client import ElevenLabs
        from elevenlabs import play
        
        # Initialize client
        elevenlabs = ElevenLabs(api_key=api_key)
        
        print("🔊 Generating new audio...")
        
        # Generate audio
        audio = elevenlabs.text_to_speech.convert(
            text=text,
            voice_id="pNInz6obpgDQGcFmaJgB",  # Adam voice
            model_id="eleven_turbo_v2_5",
            output_format="mp3_44100_128",
        )
        
        # Save to cache
        try:
            with open(cache_file, 'wb') as f:
                # Convert audio generator to bytes if needed
                if hasattr(audio, '__iter__'):
                    audio_bytes = b''.join(audio)
                else:
                    audio_bytes = audio
                f.write(audio_bytes)
            print(f"💾 Cached audio as: {filename}")
        except Exception as e:
            print(f"⚠️  Caching failed: {e}")
            audio_bytes = audio
        
        # Play audio
        play(audio_bytes if 'audio_bytes' in locals() else audio)
        print("✅ Playback complete!")
        
    except ImportError:
        print("❌ Error: elevenlabs package not installed")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()