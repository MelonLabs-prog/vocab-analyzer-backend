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
from deepgram import DeepgramClient
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
            deepgram = DeepgramClient(api_key=deepgram_api_key)

            with open(audio_file, "rb") as file:
                buffer_data = file.read()

            source = {"buffer": buffer_data}
            options = {
                "model": "nova-2",
                "smart_format": True,
                "language": "en",
            }

            response = deepgram.listen.prerecorded.transcribe_file(source, options)

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
        deepgram = DeepgramClient(api_key=deepgram_api_key)

        # Read file contents
        file_contents = await file.read()

        source = {"buffer": file_contents}
        options = {
            "model": "nova-2",
            "smart_format": True,
            "language": "en",
        }

        response = deepgram.listen.prerecorded.transcribe_file(source, options)
        transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]

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

    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')

        if is_url:
            # For URLs, use Google Search tool and request clean JSON
            prompt = f"""Analyze the content found at the following URL to identify unique vocabulary and grammar structures. Group them by their Common European Framework of Reference for Languages (CEFR) levels from A1 to C2.
If it's an article, use the main text content.

Your response MUST be a valid JSON object that adheres to the following structure. Do not include any text, explanations, or markdown formatting before or after the JSON object.

JSON Structure:
{{
  "vocabulary": {{
    "A1": ["word1", "word2"],
    "A2": [], "B1": [], "B2": [], "C1": [], "C2": []
  }},
  "grammarAnalysis": {{
    "A1": [{{"sentence": "Example sentence from the text.", "grammarPoint": "The grammar point name.", "explanation": "Explanation of the grammar point."}}],
    "A2": [], "B1": [], "B2": [], "C1": [], "C2": []
  }}
}}

For vocabulary, provide a list of unique words for each level. Do not include duplicates.
For grammar, provide example sentences from the text, identify the grammatical concept, and give a brief explanation for each, grouped by CEFR level. If no items are found for a level, return an empty array.

URL to analyze:
---
{content}"""

            generation_config = {
                "temperature": 0.2,
            }

            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                tools='google_search_retrieval'
            )

            json_text = response.text.strip()

            # Clean up potential markdown code block formatting
            if json_text.startswith('```json'):
                json_text = json_text[7:-3].strip()
            elif json_text.startswith('```'):
                json_text = json_text[3:-3].strip()

        else:
            # For text, use structured output with schema
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
