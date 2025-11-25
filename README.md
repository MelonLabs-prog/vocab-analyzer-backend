# Video Vocabulary Extractor with CEFR Classification

An educational tool that extracts vocabulary from videos and classifies words by CEFR (Common European Framework of Reference for Languages) levels using AI.

## Features

- 🎥 **Universal Video Support**: Works with YouTube, TikTok, Instagram, Facebook, and 1000+ other platforms
- 🎯 **Accurate Transcription**: Uses OpenAI Whisper for high-quality speech-to-text
- 📚 **CEFR Classification**: Automatically classifies vocabulary into A1-C2 levels using Claude AI
- 📊 **Detailed Analysis**: Provides word frequency, context, and difficulty analysis
- 💾 **Export Results**: Saves detailed JSON reports for further analysis

## How It Works

```
Video URL → Audio Extraction → Transcription → Vocabulary Extraction → CEFR Classification → Results
```

1. **Audio Extraction**: Downloads audio from video using yt-dlp
2. **Transcription**: Converts audio to text using Whisper
3. **Vocabulary Extraction**: Identifies unique words and their context
4. **CEFR Classification**: Claude AI analyzes each word and assigns CEFR level
5. **Results**: Displays and saves comprehensive analysis

## Installation

### Prerequisites

- Python 3.8 or higher
- FFmpeg (required for audio processing)
- Anthropic API key (for Claude)

### Install FFmpeg

**Windows:**
```bash
# Using Chocolatey
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
```

**Mac:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

### Install Python Dependencies

1. Clone or download this repository
2. Install required packages:

```bash
pip install -r requirements.txt
```

3. Download spaCy English model:

```bash
python -m spacy download en_core_web_sm
```

### Setup API Key

1. Get your Anthropic API key from: https://console.anthropic.com/
2. Create a `.env` file in the project directory:

```bash
cp .env.example .env
```

3. Edit `.env` and add your API key:

```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

## Usage

### Basic Usage

Run the main application:

```bash
python main.py
```

Then enter a video URL when prompted.

### Programmatic Usage

```python
from main import VocabExtractorApp

# Initialize
app = VocabExtractorApp(whisper_model="base")

# Process a video
url = "https://www.youtube.com/watch?v=example"
results = app.process_video(url)

# Access results
print(results['vocabulary']['difficulty_analysis'])
```

### Whisper Model Options

You can choose different Whisper models for transcription accuracy vs. speed:

```python
app = VocabExtractorApp(whisper_model="small")  # Options: tiny, base, small, medium, large
```

| Model  | Speed | Accuracy | RAM Usage |
|--------|-------|----------|-----------|
| tiny   | ⚡⚡⚡ | ⭐⭐   | ~1GB      |
| base   | ⚡⚡   | ⭐⭐⭐ | ~1GB      |
| small  | ⚡     | ⭐⭐⭐⭐ | ~2GB     |
| medium | 🐢     | ⭐⭐⭐⭐⭐ | ~5GB    |
| large  | 🐢🐢   | ⭐⭐⭐⭐⭐⭐ | ~10GB  |

## Output

The application provides:

1. **Console Output**: Real-time progress and summary
2. **JSON Report**: Detailed results saved to `results/` folder

### Sample Output

```
📊 Statistics:
  - Total unique words: 342
  - Total word occurrences: 1,523
  - Average word length: 5.8 characters

🎯 Difficulty Analysis:
  - Overall level: B1
  - Recommendation: Suitable for intermediate learners
  - Average score: 3.2/6

📚 Distribution by CEFR Level:
  A1:   45 words (13.2%) ██████
  A2:   78 words (22.8%) ███████████
  B1:  112 words (32.7%) ████████████████
  B2:   67 words (19.6%) █████████
  C1:   32 words ( 9.4%) ████
  C2:    8 words ( 2.3%) █
```

## CEFR Level Guidelines

- **A1 (Beginner)**: Basic everyday words - cat, dog, eat, happy
- **A2 (Elementary)**: Common descriptive words - because, travel, expensive
- **B1 (Intermediate)**: Work/school vocabulary - although, environment, budget
- **B2 (Upper-Intermediate)**: Abstract concepts - comprehensive, sustainability
- **C1 (Advanced)**: Sophisticated vocabulary - paradigm, infrastructure
- **C2 (Proficiency)**: Rare/specialized terms - ubiquitous, juxtaposition

## Cost Estimation

Using Claude API (Haiku or Sonnet):
- ~100 words: $0.01 - $0.02
- ~500 words: $0.05 - $0.10
- Typical 10-minute video: $0.10 - $0.30

## Accuracy

Expected CEFR classification accuracy:
- **A1-B1 words**: ~90% accuracy
- **B2-C1 words**: ~75% accuracy
- **Overall**: ~80-85% accuracy

The AI considers context and usage, providing more nuanced classifications than static word lists.

## Project Structure

```
Vocab Extraction/
├── audio_extractor.py     # Audio extraction from videos
├── transcriber.py         # Speech-to-text transcription
├── vocab_extractor.py     # Vocabulary extraction
├── cefr_classifier.py     # CEFR classification with Claude
├── main.py               # Main application
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

## Troubleshooting

### "FFmpeg not found"
Install FFmpeg (see installation section above)

### "spaCy model not found"
Run: `python -m spacy download en_core_web_sm`

### "API key not found"
Make sure you created `.env` file with your Anthropic API key

### "Video download failed"
Some platforms may block downloads. Try a different video or platform.

### "Sign in to confirm you're not a bot" (YouTube)
YouTube periodically blocks automated downloads. **Solution: Use browser cookies**

The application now automatically uses cookies from your Chrome browser. To ensure this works:

1. **Make sure you're logged into YouTube in Chrome**
2. **Keep Chrome installed** (yt-dlp will extract cookies automatically)

**Alternative: Use a cookie file**

If automatic cookie extraction doesn't work, manually export cookies:

1. Install a browser extension:
   - **Chrome/Edge**: [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - **Firefox**: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. While logged into YouTube, click the extension icon and export cookies

3. Save the file as `youtube_cookies.txt` in the project root directory

4. (Optional) Set custom path via environment variable:
   ```
   YOUTUBE_COOKIES_PATH=/path/to/your/cookies.txt
   ```

**Note**: Cookies may expire. If you encounter this error again, repeat the export process.

## Legal & Privacy

This tool is designed for **educational purposes**:
- ✅ Extracting vocabulary for language learning
- ✅ Analyzing content difficulty
- ✅ Personal study and research

Please note:
- Audio/video files are automatically deleted after processing
- Only vocabulary data is retained
- Respect copyright and platform Terms of Service
- Don't redistribute copyrighted content

## Future Enhancements

- [ ] Support for multiple languages
- [ ] Web interface (Flask/FastAPI)
- [ ] Batch processing of multiple videos
- [ ] Export to Anki flashcards
- [ ] Phrasal verbs and idioms detection
- [ ] Custom word list filtering

## License

MIT License - Feel free to use and modify for educational purposes.

## Support

For issues or questions, please check:
1. The troubleshooting section above
2. API documentation: https://docs.anthropic.com/
3. yt-dlp documentation: https://github.com/yt-dlp/yt-dlp

---

**Note**: This tool requires an internet connection for video downloading and Claude API access.
