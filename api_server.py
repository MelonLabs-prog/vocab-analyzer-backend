"""
FastAPI server for video audio extraction and transcription
Provides API endpoint for React frontend to extract audio from video URLs
and transcribe using Deepgram
"""

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Any
import os
from pathlib import Path
import uuid
import yt_dlp
import httpx
import google.generativeai as genai
import json

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

# YouTube cookies file path (to bypass bot detection)
# Export cookies from your browser using a browser extension like "Get cookies.txt LOCALLY"
# Place the file in the project root or specify a custom path via environment variable
YOUTUBE_COOKIES_PATH = os.getenv("YOUTUBE_COOKIES_PATH", "youtube_cookies.txt")

class VideoURLRequest(BaseModel):
    url: str

class ExtractionResponse(BaseModel):
    message: str
    transcription: str

class AnalyzeRequest(BaseModel):
    content: str

class GrammarItem(BaseModel):
    sentence: str
    grammarPoint: str
    explanation: str

class AnalysisResult(BaseModel):
    vocabulary: Dict[str, List[str]]
    grammarAnalysis: Dict[str, List[GrammarItem]]

class WordDetailsRequest(BaseModel):
    word: str

class WordDetailsResponse(BaseModel):
    definition: str
    example: str

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

    # yt-dlp options with headers and cookies to avoid bot detection
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
        # Add enhanced headers to appear as a real browser
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        },
        # Add rate limiting to avoid triggering bot detection
        'sleep_interval': 1,
        'max_sleep_interval': 3,
    }

    # Cookie management for YouTube bot detection bypass
    # Note: This uses server-side cookies, not user cookies (for security/privacy)

    # Option 1: Use cookie file if available (production deployment)
    if os.path.exists(YOUTUBE_COOKIES_PATH):
        ydl_opts['cookiefile'] = YOUTUBE_COOKIES_PATH
        print(f"Using cookie file: {YOUTUBE_COOKIES_PATH}")
    # Option 2: Try browser cookies (local development only)
    elif os.path.exists(os.path.expanduser('~/.config/google-chrome')) or \
         os.path.exists(os.path.expanduser('~/Library/Application Support/Google/Chrome')) or \
         os.path.exists(os.path.expanduser(r'~\AppData\Local\Google\Chrome')):
        try:
            ydl_opts['cookiesfrombrowser'] = ('chrome',)
            print("Using cookies from Chrome browser (local development)")
        except Exception as e:
            print(f"Could not load cookies from browser: {e}")
            print("No cookies available - may encounter bot detection for some videos")
    else:
        print("No cookies available - may encounter bot detection for some videos")

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
            print("Transcribing audio with Deepgram REST API...")

            with open(audio_file, "rb") as file:
                audio_data = file.read()

            # Use Deepgram REST API directly
            headers = {
                "Authorization": f"Token {deepgram_api_key}",
                "Content-Type": "audio/mpeg"
            }
            params = {
                "model": "nova-2",
                "smart_format": "true",
                "language": "en"
            }

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.deepgram.com/v1/listen",
                    headers=headers,
                    params=params,
                    content=audio_data
                )
                response.raise_for_status()
                result = response.json()

            transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]

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
        # Log full error for debugging
        print(f"YouTube download error: {error_msg}")
        
        if "Sign in to confirm you're not a bot" in error_msg or "HTTP Error 429" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="YouTube is blocking this video download due to bot detection. This happens periodically with YouTube's anti-bot measures.\n\nSuggestions:\n• Try a different YouTube video\n• Wait a few minutes and try again\n• If this persists, the server administrator may need to configure YouTube authentication cookies\n\nNote: This is a YouTube limitation, not an issue with our service."
            )
        elif "Video unavailable" in error_msg:
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
        print(f"Transcribing uploaded file: {file.filename} with Deepgram REST API...")

        # Read file contents
        file_contents = await file.read()

        # Use Deepgram REST API directly
        headers = {
            "Authorization": f"Token {deepgram_api_key}",
            "Content-Type": file.content_type or "audio/mpeg"
        }
        params = {
            "model": "nova-2",
            "smart_format": "true",
            "language": "en"
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.deepgram.com/v1/listen",
                headers=headers,
                params=params,
                content=file_contents
            )
            response.raise_for_status()
            result = response.json()

        transcript = result["results"]["channels"][0]["alternatives"][0]["transcript"]

        if not transcript:
            raise HTTPException(status_code=500, detail="No transcription returned")

        print(f"Transcription successful: {len(transcript)} characters")

        return {"transcription": transcript.strip()}

    except Exception as e:
        print(f"Error transcribing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/analyze", response_model=AnalysisResult)
async def analyze_content(request: AnalyzeRequest):
    """
    Analyze text content for vocabulary and grammar using Gemini

    Args:
        request: JSON body with 'content' field (text or URL)

    Returns:
        JSON with vocabulary and grammar analysis by CEFR levels
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    content = request.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")

    # Check if it's a URL
    is_url = content.startswith('http://') or content.startswith('https://')

    # Check if it's a word list (many single words with minimal other text)
    words = [w.strip() for w in content.replace(',', '\n').split('\n') if w.strip()]
    avg_word_length = sum(len(w.split()) for w in words) / len(words) if words else 0
    is_word_list = len(words) > 20 and avg_word_length < 2.0  # If many lines with 1-2 words each

    if is_word_list:
        print(f"Detected word list with {len(words)} words")

    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        # If word list, use special prompt for classification
        if is_word_list:
            word_list = '\n'.join(words)
            prompt = f"""You are given a list of English words. Classify each word according to its CEFR (Common European Framework of Reference for Languages) level from A1 to C2.

For each word, determine its appropriate CEFR level based on:
- Frequency of use in everyday English
- Complexity and abstractness
- Typical learning progression

Provide the output as a JSON object with words grouped by CEFR level. Include ALL words from the list.

Word list to classify:
---
{word_list}

Return ONLY the JSON object with this structure (no markdown formatting):
{{
  "vocabulary": {{
    "A1": ["word1", "word2", ...],
    "A2": [...],
    "B1": [...],
    "B2": [...],
    "C1": [...],
    "C2": [...]
  }},
  "grammarAnalysis": {{
    "A1": [], "A2": [], "B1": [], "B2": [], "C1": [], "C2": []
  }}
}}"""

            generation_config = {
                "temperature": 0.2,
                "response_mime_type": "application/json",
            }

            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )

            json_text = response.text.strip()
            result = json.loads(json_text)
            print(f"Classified {len(words)} words into CEFR levels")
            return result

        # If URL, fetch content first and treat as text
        elif is_url:
            try:
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    url_response = await client.get(content)
                    url_response.raise_for_status()
                    url_content = url_response.text

                    # Extract text from HTML
                    from html.parser import HTMLParser

                    class TextExtractor(HTMLParser):
                        def __init__(self):
                            super().__init__()
                            self.text = []

                        def handle_data(self, data):
                            if data.strip():
                                self.text.append(data.strip())

                    extractor = TextExtractor()
                    extractor.feed(url_content)
                    extracted_text = ' '.join(extractor.text)

                    # Limit to avoid token limits (Gemini 2.5 Flash supports up to 1M tokens)
                    # 100K characters is roughly 25K tokens, well within limits
                    if len(extracted_text) > 100000:
                        extracted_text = extracted_text[:100000]

                    print(f"Extracted {len(extracted_text)} characters from URL")
                    content = extracted_text
                    is_url = False  # Treat as text from now on

            except Exception as url_error:
                print(f"Error fetching URL: {str(url_error)}")
                raise HTTPException(status_code=500, detail=f"Failed to fetch URL content: {str(url_error)}")

        # Analyze content as text (works for both plain text and extracted URL content)
        prompt = f"""Analyze the following text to identify unique vocabulary and grammar structures. Group them by their Common European Framework of Reference for Languages (CEFR) levels from A1 to C2.
For vocabulary, provide a list of unique words for each level. Do not include duplicates.
For grammar, provide example sentences from the text, identify the grammatical concept, and give a brief explanation for each, grouped by CEFR level.
Provide the output in a JSON format that adheres to the provided schema. Do not include words or grammar points if they do not fit into any CEFR level.

Text to analyze:
---
{content}"""

        generation_config = {
            "temperature": 0.2,
            "response_mime_type": "application/json",
            "response_schema": {
                    "type": "object",
                    "properties": {
                        "vocabulary": {
                            "type": "object",
                            "description": "A dictionary of vocabulary words grouped by CEFR level.",
                            "properties": {
                                "A1": {"type": "array", "items": {"type": "string"}},
                                "A2": {"type": "array", "items": {"type": "string"}},
                                "B1": {"type": "array", "items": {"type": "string"}},
                                "B2": {"type": "array", "items": {"type": "string"}},
                                "C1": {"type": "array", "items": {"type": "string"}},
                                "C2": {"type": "array", "items": {"type": "string"}},
                            }
                        },
                        "grammarAnalysis": {
                            "type": "object",
                            "description": "Grammar points found in the text, grouped by CEFR level.",
                            "properties": {
                                "A1": {"type": "array", "items": {
                                    "type": "object",
                                    "properties": {
                                        "sentence": {"type": "string"},
                                        "grammarPoint": {"type": "string"},
                                        "explanation": {"type": "string"}
                                    }
                                }},
                                "A2": {"type": "array", "items": {
                                    "type": "object",
                                    "properties": {
                                        "sentence": {"type": "string"},
                                        "grammarPoint": {"type": "string"},
                                        "explanation": {"type": "string"}
                                    }
                                }},
                                "B1": {"type": "array", "items": {
                                    "type": "object",
                                    "properties": {
                                        "sentence": {"type": "string"},
                                        "grammarPoint": {"type": "string"},
                                        "explanation": {"type": "string"}
                                    }
                                }},
                                "B2": {"type": "array", "items": {
                                    "type": "object",
                                    "properties": {
                                        "sentence": {"type": "string"},
                                        "grammarPoint": {"type": "string"},
                                        "explanation": {"type": "string"}
                                    }
                                }},
                                "C1": {"type": "array", "items": {
                                    "type": "object",
                                    "properties": {
                                        "sentence": {"type": "string"},
                                        "grammarPoint": {"type": "string"},
                                        "explanation": {"type": "string"}
                                    }
                                }},
                                "C2": {"type": "array", "items": {
                                    "type": "object",
                                    "properties": {
                                        "sentence": {"type": "string"},
                                        "grammarPoint": {"type": "string"},
                                        "explanation": {"type": "string"}
                                    }
                                }},
                            }
                        }
                    },
                    "required": ["vocabulary", "grammarAnalysis"]
                }
        }

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        json_text = response.text.strip()

        # Parse and return
        result = json.loads(json_text)
        print(f"Analysis successful for content length: {len(content)}")
        return result

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}")
        raise HTTPException(status_code=500, detail="AI returned invalid response format. Please try again.")
    except Exception as e:
        print(f"Error analyzing content: {str(e)}")
        if is_url:
            raise HTTPException(status_code=500, detail="Failed to analyze URL. The URL may be inaccessible or content not analyzable.")
        raise HTTPException(status_code=500, detail="Failed to analyze content. It might be too long or format is invalid.")

@app.post("/word-details", response_model=WordDetailsResponse)
async def get_word_details(request: WordDetailsRequest):
    """
    Get definition and example for a word using Gemini

    Args:
        request: JSON body with 'word' field

    Returns:
        JSON with definition and example
    """
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    word = request.word.strip()
    if not word:
        raise HTTPException(status_code=400, detail="Word is required")

    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        prompt = f'Provide a clear definition and an example sentence for the English word: "{word}". Your response should be a JSON object adhering to the specified schema. Do not include any markdown formatting or other text outside of the JSON object.'

        generation_config = {
            "temperature": 0.2,
            "response_mime_type": "application/json",
            "response_schema": {
                "type": "object",
                "properties": {
                    "definition": {"type": "string"},
                    "example": {"type": "string"}
                },
                "required": ["definition", "example"]
            }
        }

        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        result = json.loads(response.text.strip())
        print(f"Word details fetched for: {word}")
        return result

    except Exception as e:
        print(f"Error fetching word details for '{word}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get details for '{word}'. Please try again.")

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
