"""
Audio extraction module using yt-dlp
Extracts audio from video URLs (YouTube, TikTok, Instagram, etc.)
"""

import yt_dlp
import os
from pathlib import Path


class AudioExtractor:
    def __init__(self, output_dir="temp_audio"):
        """
        Initialize AudioExtractor

        Args:
            output_dir: Directory to store temporary audio files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def extract_audio(self, url, output_filename=None):
        """
        Extract audio from video URL

        Args:
            url: Video URL (YouTube, TikTok, Instagram, Facebook, etc.)
            output_filename: Optional custom filename (without extension)

        Returns:
            str: Path to extracted audio file
        """
        if output_filename is None:
            output_filename = "extracted_audio"

        output_path = self.output_dir / output_filename

        ydl_opts = {
            'ffmpeg_location': 'C:/ffmpeg/ffmpeg-8.0-essentials_build/bin',
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': str(output_path),
            'quiet': False,
            'no_warnings': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"Extracting audio from: {url}")
                info = ydl.extract_info(url, download=True)

                # Get the actual filename with extension
                audio_file = str(output_path) + '.mp3'

                if os.path.exists(audio_file):
                    print(f"Audio extracted successfully: {audio_file}")
                    return audio_file
                else:
                    raise FileNotFoundError(f"Audio file not found: {audio_file}")

        except Exception as e:
            print(f"Error extracting audio: {str(e)}")
            raise

    def cleanup(self, audio_path):
        """
        Remove temporary audio file

        Args:
            audio_path: Path to audio file to delete
        """
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
                print(f"Cleaned up: {audio_path}")
        except Exception as e:
            print(f"Error cleaning up file: {str(e)}")


# Test function
if __name__ == "__main__":
    # Example usage
    extractor = AudioExtractor()

    # Test with a video URL (replace with actual URL)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    try:
        audio_path = extractor.extract_audio(test_url)
        print(f"Audio saved to: {audio_path}")

        # Cleanup
        # extractor.cleanup(audio_path)
    except Exception as e:
        print(f"Test failed: {e}")
