"""
FastAPI server for video audio extraction and transcription
Provides API endpoint for React frontend to extract audio from video URLs
and transcribe using Deepgram
"""

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from pathlib import Path
import uuid
import yt_dlp
from deepgram import DeepgramClient, PrerecordedOptions

app = FastAPI(title="Video Audio Extraction API")

# Configure CORS for React app
# Get allowed origins from environment variable or use defaults
allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FFmpeg path configuration
# For local development on Windows, use full path
# For deployment (Railway/Render), FFmpeg is already in PATH
FFMPEG_PATH = os.getenv("FFMPEG_PATH", r"C:\ffmpeg\ffmpeg-8.0-essentials_build\bin")

class VideoURLRequest(BaseModel):
    url: str

class ExtractionResponse(BaseModel):
    message: str
    transcription: str

@app.get("/")
def read_root():
    return {
        "service": "Video Audio Extraction API",
        "status": "running",
        "endpoints": {
            "POST /extract-audio": "Extract audio from video URL",
            "GET /health": "Health check"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/extract-audio", response_model=ExtractionResponse)
async def extract_audio(request: VideoURLRequest):
    """
    Extract audio from video URL and transcribe using Deepgram

    Args:
        request: JSON body with 'url' field

    Returns:
        JSON with transcription text
    """
    url = request.url.strip()

    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    # Validate URL format
    if not (url.startswith('http://') or url.startswith('https://')):
        raise HTTPException(status_code=400, detail="Invalid URL format. Must start with http:// or https://")

    # Generate unique filename
    unique_id = str(uuid.uuid4())[:8]
    output_dir = Path("temp_audio")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"audio_{unique_id}"

    # yt-dlp options with headers to avoid bot detection
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(output_path),
        'quiet': True,
        'no_warnings': True,
        # Add headers to appear as a real browser
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }
    }

    # Only set ffmpeg_location if it exists (for local Windows development)
    if os.path.exists(FFMPEG_PATH):
        ydl_opts['ffmpeg_location'] = FFMPEG_PATH

    try:
        # Extract audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"Extracting audio from: {url}")
            ydl.download([url])

        # Get the actual filename with extension
        audio_file = str(output_path) + '.mp3'

        if not os.path.exists(audio_file):
            raise HTTPException(status_code=500, detail="Audio extraction failed")

        print(f"Audio extracted successfully: {audio_file}")

        # Transcribe using Deepgram
        deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
        if not deepgram_api_key:
            raise HTTPException(status_code=500, detail="DEEPGRAM_API_KEY not configured")

        try:
            print("Transcribing audio with Deepgram...")
            deepgram = DeepgramClient(deepgram_api_key)

            with open(audio_file, "rb") as audio:
                source = {"buffer": audio, "mimetype": "audio/mpeg"}
                options = PrerecordedOptions(
                    model="nova-2",
                    smart_format=True,
                    language="en",
                )

                response = deepgram.listen.prerecorded.v("1").transcribe_file(source, options)

                transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]

                if not transcript:
                    raise HTTPException(status_code=500, detail="No transcription returned")

                print(f"Transcription successful: {len(transcript)} characters")

                # Clean up audio file
                try:
                    os.remove(audio_file)
                    print(f"Cleaned up audio file: {audio_file}")
                except Exception as cleanup_error:
                    print(f"Warning: Could not delete audio file: {cleanup_error}")

                return ExtractionResponse(
                    message="Audio extracted and transcribed successfully",
                    transcription=transcript.strip()
                )

        except Exception as transcription_error:
            print(f"Error transcribing audio: {str(transcription_error)}")
            # Clean up audio file even if transcription fails
            try:
                os.remove(audio_file)
            except:
                pass
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(transcription_error)}")

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "Video unavailable" in error_msg:
            raise HTTPException(status_code=404, detail="Video not found or unavailable")
        elif "Private video" in error_msg:
            raise HTTPException(status_code=403, detail="Video is private")
        else:
            raise HTTPException(status_code=500, detail=f"Download failed: {error_msg}")

    except Exception as e:
        print(f"Error extracting audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/transcribe")
async def transcribe_uploaded_file(file: UploadFile = File(...)):
    """
    Transcribe an uploaded audio/video file using Deepgram

    Args:
        file: Audio/video file upload

    Returns:
        JSON with transcription text
    """
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
    if not deepgram_api_key:
        raise HTTPException(status_code=500, detail="DEEPGRAM_API_KEY not configured")

    try:
        print(f"Transcribing uploaded file: {file.filename} with Deepgram...")
        deepgram = DeepgramClient(deepgram_api_key)

        # Read file contents
        file_contents = await file.read()

        source = {"buffer": file_contents, "mimetype": file.content_type or "audio/mpeg"}
        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
            language="en",
        )

        response = deepgram.listen.prerecorded.v("1").transcribe_file(source, options)
        transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]

        if not transcript:
            raise HTTPException(status_code=500, detail="No transcription returned")

        print(f"Transcription successful: {len(transcript)} characters")

        return {"transcription": transcript.strip()}

    except Exception as e:
        print(f"Error transcribing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.delete("/cleanup/{filename}")
async def cleanup_audio(filename: str):
    """
    Clean up temporary audio file after use

    Args:
        filename: Name of the audio file to delete
    """
    try:
        file_path = Path("temp_audio") / filename
        if file_path.exists():
            os.remove(file_path)
            return {"message": "File deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("Starting Video Audio Extraction API server...")
    print("API will be available at: http://localhost:8000")
    print("Docs available at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
