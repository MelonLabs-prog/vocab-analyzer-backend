"""
FastAPI server for video audio extraction
Provides API endpoint for React frontend to extract audio from video URLs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from pathlib import Path
import uuid
import yt_dlp

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
    audio_url: str

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

@app.post("/extract-audio")
async def extract_audio(request: VideoURLRequest):
    """
    Extract audio from video URL (YouTube, TikTok, Instagram, etc.)

    Args:
        request: JSON body with 'url' field

    Returns:
        Audio file in MP3 format
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

    # yt-dlp options
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

        # Return the audio file
        return FileResponse(
            audio_file,
            media_type="audio/mpeg",
            filename=f"audio_{unique_id}.mp3",
            headers={
                "Content-Disposition": f"attachment; filename=audio_{unique_id}.mp3"
            }
        )

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
