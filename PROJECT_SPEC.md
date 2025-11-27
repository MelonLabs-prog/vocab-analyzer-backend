# AI Language Analyzer - Project Specification

## Project Overview

An AI-powered language learning tool that extracts vocabulary and grammar from various sources (YouTube videos, articles, text, audio files) and classifies them by CEFR levels (A1-C2).

**Live URLs:**
- Frontend: Deployed on Vercel
- Backend API: https://vocab-api-production.up.railway.app

---

## Architecture

### System Design
```
User Input (Frontend - Vercel)
    ↓
Backend API (Railway)
    ↓
External Services:
- Deepgram API (Audio Transcription)
- Google Gemini API (Text Analysis & CEFR Classification)
```

### Components

#### 1. Frontend (React/TypeScript)
- **Location:** `C:\Users\thewa\Downloads\ai-language-analyzer\`
- **Framework:** React 19 + TypeScript + Vite
- **Deployment:** Vercel (auto-deploys from GitHub)
- **Repository:** https://github.com/MelonLabs-prog/Demo-Vocab-Analyzer

**Key Files:**
- `App.tsx` - Main application logic, handles file processing and API calls
- `components/InputArea.tsx` - Input interface (text/file upload)
- `components/ResultsDisplay.tsx` - Displays vocabulary/grammar results with word details modal
- `components/Loader.tsx` - Loading animation

#### 2. Backend (Python/FastAPI)
- **Location:** `C:\Users\thewa\Documents\Projects\Vocab-Extraction\`
- **Framework:** FastAPI + Python 3.11
- **Deployment:** Railway (Docker)
- **Repository:** https://github.com/MelonLabs-prog/vocab-analyzer-backend

**Key Files:**
- `api_server.py` - Main API server with all endpoints
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration with FFmpeg
- `start.py` - Entry point for Railway deployment

---

## Features

### Input Types Supported

1. **YouTube URLs / Video Shorts**
   - Downloads audio using yt-dlp
   - Transcribes with Deepgram
   - Analyzes vocabulary/grammar

2. **Article URLs**
   - Fetches HTML content
   - Extracts text (up to 100K characters)
   - Analyzes content

3. **Text Input**
   - Direct text paste
   - Analyzes immediately

4. **File Uploads**
   - Audio files (.mp3, .mp4, .m4a, etc.)
   - Video files (.mp4)
   - Documents (.txt, .pdf, .docx, .csv)
   - Word lists (.csv with one word per line)

### Output

**Vocabulary Analysis:**
- Words grouped by CEFR levels (A1, A2, B1, B2, C1, C2)
- Click any word for definition and example sentence

**Grammar Analysis:**
- Example sentences from source text
- Grammar point identification
- Explanations for each grammar structure
- Grouped by CEFR levels

---

## Technology Stack

### Frontend
- React 19.2.0
- TypeScript 5.8.2
- Vite 6.2.0
- PDF.js (PDF reading)
- Mammoth.js (DOCX reading)

### Backend
- Python 3.11
- FastAPI 0.109.0+
- Uvicorn 0.27.0+
- yt-dlp (video/audio download)
- httpx (HTTP client)
- google-generativeai (Gemini API)
- FFmpeg (audio processing)

### External APIs
- **Deepgram API:** Speech-to-text transcription
- **Google Gemini 2.5 Flash:** CEFR classification and analysis

---

## API Endpoints

### Base URL
`https://vocab-api-production.up.railway.app`

### Endpoints

#### 1. Health Check
```
GET /
GET /health
```
Returns service status

#### 2. Extract & Transcribe YouTube Audio
```
POST /extract-audio
```
**Request Body:**
```json
{
  "url": "https://youtube.com/watch?v=..."
}
```

**Response:**
```json
{
  "message": "Audio extracted and transcribed successfully",
  "transcription": "Full transcript text..."
}
```

**Process:**
1. Downloads audio from YouTube using yt-dlp
2. Converts to MP3 using FFmpeg
3. Sends to Deepgram for transcription
4. Returns transcript text
5. Cleans up temp audio file

#### 3. Transcribe Uploaded Audio
```
POST /transcribe
```
**Request:** Multipart form-data with audio file

**Response:**
```json
{
  "transcription": "Transcript text..."
}
```

#### 4. Analyze Content
```
POST /analyze
```
**Request Body:**
```json
{
  "content": "Text to analyze or URL"
}
```

**Response:**
```json
{
  "vocabulary": {
    "A1": ["word1", "word2"],
    "A2": [...],
    "B1": [...],
    "B2": [...],
    "C1": [...],
    "C2": [...]
  },
  "grammarAnalysis": {
    "A1": [
      {
        "sentence": "Example sentence",
        "grammarPoint": "Present Simple",
        "explanation": "In easy words: ...\nPattern: Subject + verb (present simple)\nWhen to use: ...",
        "highlightedPart": "play football",
        "structurePattern": "Subject + verb (present simple)"
      }
    ],
    "A2": [...],
    ...
  }
}
```

**Process:**
- Detects content type (URL, word list, or text)
- **For URLs:** Fetches HTML, extracts text, analyzes
- **For word lists:** Classifies each word by CEFR level
- **For text:** Analyzes vocabulary and grammar in context

#### 5. Get Word Details
```
POST /word-details
```
**Request Body:**
```json
{
  "word": "example"
}
```

**Response:**
```json
{
  "definition": "A representative sample...",
  "example": "For example, this is how you use it."
}
```

---

## Environment Variables

### Backend (Railway)

**Required:**
```
GEMINI_API_KEY=<your-gemini-api-key>
DEEPGRAM_API_KEY=<your-deepgram-api-key>
PORT=8080 (set by Railway)
```

**Optional:**
```
ALLOWED_ORIGINS=* (for CORS, comma-separated)
FFMPEG_PATH=/usr/bin/ffmpeg (auto-detected in Docker)
```

### Frontend (Vercel)

**Required:**
```
VITE_API_URL=https://vocab-api-production.up.railway.app
```

**Note:** No API keys in frontend - all keys are secure on backend

---

## Deployment Setup

### Backend (Railway)

1. Connect GitHub repo to Railway
2. Select Dockerfile deployment
3. Add environment variables (GEMINI_API_KEY, DEEPGRAM_API_KEY)
4. Railway auto-deploys on git push to main

**Docker Configuration:**
- Base image: Python 3.11-slim
- Installs FFmpeg for audio processing
- Exposes port 8080
- Runs via `start.py` to handle PORT env var

### Frontend (Vercel)

1. Connect GitHub repo to Vercel
2. Framework preset: Vite
3. Add VITE_API_URL environment variable
4. Vercel auto-deploys on git push to main

---

## File Structure

### Backend
```
Vocab-Extraction/
├── api_server.py         # Main FastAPI application
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
├── start.py            # Entry point for Railway
├── temp_audio/         # Temp folder for audio files
└── PROJECT_SPEC.md     # This file
```

### Frontend
```
ai-language-analyzer/
├── App.tsx                    # Main app component
├── components/
│   ├── InputArea.tsx         # Input interface
│   ├── ResultsDisplay.tsx    # Results display
│   └── Loader.tsx            # Loading animation
├── services/
│   └── (removed - all API calls now in App.tsx)
├── types.ts                  # TypeScript types
├── constants.ts              # Constants (CEFR levels)
├── package.json              # Dependencies
└── vite.config.ts           # Vite configuration
```

---

## Common Development Tasks

### Adding a New Input Type

**Frontend (App.tsx):**
1. Add file type check in `handleAnalyze` function
2. Add processing logic to extract text
3. Send text to backend `/analyze` endpoint

**Backend (api_server.py):**
- Usually no changes needed - `/analyze` handles text

### Adding a New Analysis Feature

**Backend (api_server.py):**
1. Update prompt in `/analyze` endpoint
2. Modify `response_schema` to include new fields
3. Update `AnalysisResult` Pydantic model

**Frontend:**
1. Update `AnalysisResult` type in `types.ts`
2. Update `ResultsDisplay.tsx` to show new fields

### Changing CEFR Classification Logic

**Backend (api_server.py):**
- Modify prompts in `/analyze` endpoint
- Adjust instructions for Gemini model

### Adding API Rate Limiting

**Backend:**
1. Install `slowapi`: Add to `requirements.txt`
2. Import and configure in `api_server.py`
3. Add rate limit decorators to endpoints

### Improving Text Extraction from URLs

**Backend (api_server.py):**
1. Install BeautifulSoup4: Add to `requirements.txt`
2. Replace HTMLParser with BeautifulSoup in URL fetching
3. Use `.get_text()` for better extraction

---

## Troubleshooting

### YouTube Downloads Failing
- Check yt-dlp is up to date
- Verify URL format (YouTube, TikTok, Instagram supported)
- Check Railway logs for bot detection errors

### Transcription Errors
- Verify DEEPGRAM_API_KEY is set correctly
- Check Deepgram account has credits
- Audio file size limit: ~50MB

### Analysis Taking Too Long
- Check content length (limit to 100K chars)
- Gemini 2.5 Flash should respond in 5-10 seconds
- Check Railway memory usage

### CORS Errors
- Verify ALLOWED_ORIGINS in Railway includes frontend URL
- Use `*` for development/testing

---

## API Keys & Costs

### Deepgram
- Free tier: $200 credit + 45,000 minutes
- Pay-as-you-go after free tier
- Get key: https://console.deepgram.com/signup

### Google Gemini
- Free tier: 1,500 requests/day
- Gemini 2.5 Flash is the cheapest model
- Get key: https://aistudio.google.com/apikey

### Cost Optimization
- Use Gemini Flash (not Pro) - cheaper and faster
- Implement caching for repeated queries
- Set daily request limits

---

## Security Notes

1. **All API keys stored on backend only** - never exposed to browser
2. CORS configured to limit frontend access
3. No authentication required (public tool)
4. Rate limiting recommended for production
5. Temp audio files auto-cleaned after transcription

---

## Future Enhancements

### Potential Features
- [ ] User accounts and history
- [ ] Export results (PDF, CSV)
- [ ] Multiple language support
- [ ] Custom CEFR word lists
- [ ] Batch processing multiple files
- [ ] API authentication
- [ ] Sentence-level difficulty scoring
- [ ] Study flashcard generation
- [ ] Progress tracking for learners

### Technical Improvements
- [ ] Add Redis caching for repeated analyses
- [ ] Implement request queuing for large files
- [ ] Add comprehensive error logging (Sentry)
- [ ] Create automated tests
- [ ] Add API documentation (Swagger UI)
- [ ] Implement WebSocket for real-time progress

---

## Support & Maintenance

**GitHub Issues:**
- Frontend: https://github.com/MelonLabs-prog/Demo-Vocab-Analyzer/issues
- Backend: https://github.com/MelonLabs-prog/vocab-analyzer-backend/issues

**Monitoring:**
- Railway dashboard for backend logs and metrics
- Vercel dashboard for frontend deployment status

**Regular Maintenance:**
1. Update dependencies monthly (security patches)
2. Monitor API usage/costs
3. Check for yt-dlp updates (YouTube changes frequently)
4. Verify Deepgram/Gemini API compatibility

---

## Version History

- **v1.0** - Initial release with all core features
  - YouTube video transcription
  - Article URL analysis
  - Multiple file format support
  - CEFR classification
  - Word definitions
  - Secure backend architecture
