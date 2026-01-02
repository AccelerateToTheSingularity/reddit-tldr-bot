# Reddit TLDR Bot

Automatic TLDR generation for long posts on r/accelerate.

## How It Works

This bot runs on GitHub Actions every 3 minutes, 24/7:

1. Checks r/accelerate for new posts with 500+ words
2. Generates a TLDR summary using Google Gemini AI
3. Posts the TLDR as a pinned moderator comment

## Setup

### 1. Fork this repository

### 2. Add GitHub Secrets

Go to Settings → Secrets and variables → Actions → New repository secret:

| Secret Name | Description |
|-------------|-------------|
| `REDDIT_CLIENT_ID` | Your Reddit app client ID |
| `REDDIT_CLIENT_SECRET` | Your Reddit app client secret |
| `REDDIT_USERNAME` | Bot Reddit username |
| `REDDIT_PASSWORD` | Bot Reddit password |
| `GEMINI_API_KEY` | Google Gemini API key |
| `EMAIL_USERNAME` | Gmail for notifications (optional) |
| `EMAIL_PASSWORD` | Gmail app password (optional) |

### 3. Enable Actions

Go to the Actions tab and enable workflows.

## Stats Dashboard

View live stats at: **https://YOUR-USERNAME.github.io/reddit-tldr-bot/**

## Configuration

Edit `tldr_runner.py` to customize:
- `WORD_THRESHOLD` - Minimum words to trigger TLDR (default: 500)
- `MAX_TLDR_PER_RUN` - Max TLDRs per 3-minute cycle (default: 5)

## Costs

- **GitHub Actions**: Free for public repos (unlimited minutes)
- **Gemini API**: ~$0.0001 per TLDR (very cheap)

## License

MIT
