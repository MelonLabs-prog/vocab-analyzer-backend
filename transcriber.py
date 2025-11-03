"""
Transcription module using OpenAI Whisper
Converts audio to text with high accuracy
"""

import whisper
import warnings
import os
warnings.filterwarnings("ignore")

# Add FFmpeg to PATH for Whisper
FFMPEG_PATH = r"C:\ffmpeg\ffmpeg-8.0-essentials_build\bin"
if FFMPEG_PATH not in os.environ['PATH']:
    os.environ['PATH'] = FFMPEG_PATH + os.pathsep + os.environ['PATH']


class AudioTranscriber:
    def __init__(self, model_size="base"):
        """
        Initialize AudioTranscriber

        Args:
            model_size: Whisper model size
                - tiny: Fastest, least accurate (~1GB RAM)
                - base: Good balance (default, ~1GB RAM)
                - small: Better accuracy (~2GB RAM)
                - medium: High accuracy (~5GB RAM)
                - large: Best accuracy (~10GB RAM)
        """
        self.model_size = model_size
        self.model = None
        print(f"Initializing Whisper model: {model_size}")

    def load_model(self):
        """Load the Whisper model"""
        if self.model is None:
            print(f"Loading Whisper {self.model_size} model (first run may take a few minutes)...")
            self.model = whisper.load_model(self.model_size)
            print("Model loaded successfully")

    def transcribe(self, audio_path, language=None):
        """
        Transcribe audio file to text

        Args:
            audio_path: Path to audio file
            language: Optional language code (e.g., 'en', 'es', 'fr')
                     If None, Whisper will auto-detect

        Returns:
            dict: Transcription result with text, segments, and language
        """
        self.load_model()

        print(f"Transcribing audio: {audio_path}")

        # Transcribe options
        options = {
            "language": language,
            "task": "transcribe",
            "verbose": False
        }

        # Remove None values
        options = {k: v for k, v in options.items() if v is not None}

        try:
            result = self.model.transcribe(audio_path, **options)

            print(f"Transcription completed")
            print(f"Detected language: {result.get('language', 'unknown')}")
            print(f"Text length: {len(result['text'])} characters")

            return {
                'text': result['text'],
                'language': result.get('language'),
                'segments': result.get('segments', []),
            }

        except Exception as e:
            print(f"Error during transcription: {str(e)}")
            raise

    def transcribe_with_timestamps(self, audio_path, language=None):
        """
        Transcribe with word-level timestamps

        Args:
            audio_path: Path to audio file
            language: Optional language code

        Returns:
            dict: Transcription with detailed segment information
        """
        result = self.transcribe(audio_path, language)

        # Extract segments with timestamps
        segments_with_time = []
        for segment in result['segments']:
            segments_with_time.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text'],
            })

        return {
            'full_text': result['text'],
            'language': result['language'],
            'segments': segments_with_time
        }


# Test function
if __name__ == "__main__":
    # Example usage
    transcriber = AudioTranscriber(model_size="base")

    # Test with an audio file (replace with actual path)
    test_audio = "temp_audio/extracted_audio.mp3"

    try:
        result = transcriber.transcribe(test_audio)
        print("\n--- Transcription Result ---")
        print(result['text'][:500])  # Print first 500 characters
    except Exception as e:
        print(f"Test failed: {e}")
