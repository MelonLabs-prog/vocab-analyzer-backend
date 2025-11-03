# Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.8+
- FFmpeg installed
- Anthropic API key

## Installation (5 steps)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download spaCy model
python -m spacy download en_core_web_sm

# 3. Create .env file
copy .env.example .env   # Windows
# cp .env.example .env   # Mac/Linux

# 4. Add your API key to .env
# Edit .env and add: ANTHROPIC_API_KEY=your_key_here

# 5. Test it!
python test_demo.py
```

## Usage

### Simple Command Line

```bash
python main.py
```

Then paste any video URL (YouTube, TikTok, Instagram, etc.).

### Python Script

```python
from main import VocabExtractorApp

app = VocabExtractorApp()
results = app.process_video("https://youtube.com/watch?v=...")

print(results['vocabulary']['difficulty_analysis'])
```

## Example Output

```
📊 Statistics:
  - Total unique words: 342
  - Overall level: B1 (Intermediate)

📚 Distribution:
  A1:   45 words (13.2%)
  A2:   78 words (22.8%)
  B1:  112 words (32.7%) ← Most common
  B2:   67 words (19.6%)
  C1:   32 words ( 9.4%)
  C2:    8 words ( 2.3%)
```

## Common Issues

| Issue | Solution |
|-------|----------|
| "FFmpeg not found" | Install FFmpeg (see setup_guide.md) |
| "API key not found" | Add key to .env file |
| "spaCy model not found" | Run: `python -m spacy download en_core_web_sm` |

## What's Next?

- Read `README.md` for detailed documentation
- Check `setup_guide.md` for troubleshooting
- Run `test_demo.py` to test individual components
- Explore the `results/` folder for JSON outputs

## Cost & Performance

- **Typical video (5-10 min)**: $0.10 - $0.30, ~3-5 minutes processing
- **Whisper model "base"**: Good balance of speed/accuracy
- **Results**: Saved to `results/` folder as JSON

## Tips

1. Start with short videos (2-3 minutes)
2. Use educational content for best results
3. Check the JSON output for detailed word-by-word analysis
4. Try different Whisper models in main.py if needed

---

Need help? Check the README.md or setup_guide.md
