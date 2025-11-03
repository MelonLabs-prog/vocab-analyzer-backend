# Setup Guide - Video Vocabulary Extractor

Follow these steps to get your application up and running.

## Step 1: Install Python

Make sure you have Python 3.8 or higher installed.

Check your Python version:
```bash
python --version
```

If you don't have Python, download it from: https://www.python.org/downloads/

## Step 2: Install FFmpeg

FFmpeg is required for audio processing.

### Windows

**Option A: Using Chocolatey (Recommended)**
```bash
choco install ffmpeg
```

**Option B: Manual Installation**
1. Download FFmpeg from: https://ffmpeg.org/download.html
2. Extract the zip file
3. Add the `bin` folder to your system PATH

**Verify installation:**
```bash
ffmpeg -version
```

### Mac

```bash
brew install ffmpeg
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install ffmpeg
```

## Step 3: Install Python Dependencies

Open a terminal in the project directory and run:

```bash
pip install -r requirements.txt
```

This will install:
- yt-dlp (video/audio downloading)
- openai-whisper (transcription)
- anthropic (Claude API)
- spacy (NLP processing)
- python-dotenv (environment variables)

## Step 4: Download spaCy Language Model

```bash
python -m spacy download en_core_web_sm
```

For other languages (optional):
```bash
# Spanish
python -m spacy download es_core_news_sm

# French
python -m spacy download fr_core_news_sm

# German
python -m spacy download de_core_news_sm
```

## Step 5: Get Anthropic API Key

1. Go to: https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (it starts with `sk-ant-...`)

## Step 6: Configure Environment Variables

1. Copy the example environment file:
```bash
cp .env.example .env
```

Or on Windows:
```bash
copy .env.example .env
```

2. Open `.env` in a text editor and add your API key:
```
ANTHROPIC_API_KEY=sk-ant-your-actual-api-key-here
```

**Important:** Never share your API key or commit the `.env` file to version control!

## Step 7: Test Your Setup

Run the test script to verify everything works:

```bash
python test_demo.py
```

Select option 4 to test CEFR classification (doesn't require video download).

## Step 8: Run the Application

```bash
python main.py
```

Enter a video URL when prompted and watch the magic happen!

## Recommended First Test

Use a short educational video from YouTube (1-3 minutes) for your first test:
- Faster processing
- Lower API costs
- Easy to verify results

Example URLs you can try:
- Short TED-Ed videos
- Language learning content
- News clips

## Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "spacy.cli.download failed"
Try downloading directly:
```bash
python -m spacy download en_core_web_sm
```

### "FFmpeg not found"
Make sure FFmpeg is installed and in your PATH. Test with:
```bash
ffmpeg -version
```

### "API key not found"
Make sure:
1. You created `.env` file (not `.env.txt`)
2. The API key is correct (starts with `sk-ant-`)
3. There are no spaces around the `=` sign

### "Video download failed"
Some platforms may block downloads:
- Try a different video
- Use a public/unlisted video
- Test with YouTube first (most reliable)

## API Usage & Costs

Claude API pricing (as of 2024):
- Haiku: ~$0.25 per million input tokens
- Sonnet: ~$3 per million input tokens

Typical costs per video:
- Short video (2-3 min): $0.05 - $0.15
- Medium video (5-10 min): $0.10 - $0.30
- Long video (20+ min): $0.30 - $1.00

You can monitor your usage at: https://console.anthropic.com/

## Performance Tips

### Faster Processing
- Use `whisper_model="tiny"` or `"base"` in main.py
- Process shorter videos first

### Better Accuracy
- Use `whisper_model="small"` or `"medium"`
- More accurate transcription = better vocabulary extraction

### Lower Costs
- The app already uses batching to minimize API calls
- Cache is automatically applied for repeated words
- Only unique words are sent to Claude

## Next Steps

1. ✅ Test with a short video
2. ✅ Review the JSON output in `results/` folder
3. ✅ Experiment with different video types
4. ✅ Try different Whisper models
5. ✅ Consider building a web interface or API

## Getting Help

- Check README.md for detailed documentation
- Review test_demo.py for component testing
- Check Anthropic docs: https://docs.anthropic.com/
- Check yt-dlp docs: https://github.com/yt-dlp/yt-dlp

---

🎉 **You're all set! Happy vocabulary extracting!**
