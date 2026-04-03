# Oeconomia Twitter Agent

Automated Twitter/X posting agent for the Oeconomia DeFi ecosystem. Uses Claude (Anthropic) for content generation and optionally DALL-E 3 for image generation.

## Features

- **AI Content Generation** — Claude claude-sonnet-4-5 generates on-brand tweets with configurable post types (technical, hype, educational, philosophical)
- **DALL-E 3 Integration** — Optional auto-generated images with Oeconomia brand styling (dark cinematic, neon teal/amber)
- **Smart Scheduling** — APScheduler posts at random times between 8 AM–10 PM, with configurable daily frequency
- **Dedup Protection** — 50-character prefix matching against post log prevents repeating content within 30 days
- **DRY_RUN Mode** — Safe by default; logs everything without posting
- **Telegram Notifications** — Optional alerts to a Telegram channel
- **Image Prompt Logging** — CSV tracking of all image prompts for manual workflows

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Anthropic API key
- Twitter/X API v2 credentials (free tier: ~1,500 tweets/month)
- OpenAI API key (optional, for DALL-E 3 — ~$10/month at standard quality)

### 2. Install

```bash
cd oeconomia-twitter-agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
# Edit .env with your API keys and preferences
```

### 4. Run

```bash
# Default: DRY_RUN=true, IMAGE_MODE=manual (safe mode)
python -m agent.main
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | — | Claude API key |
| `OPENAI_API_KEY` | For dalle mode | — | OpenAI API key for DALL-E 3 |
| `TWITTER_API_KEY` | For live posting | — | Twitter API consumer key |
| `TWITTER_API_SECRET` | For live posting | — | Twitter API consumer secret |
| `TWITTER_ACCESS_TOKEN` | For live posting | — | Twitter OAuth access token |
| `TWITTER_ACCESS_TOKEN_SECRET` | For live posting | — | Twitter OAuth access token secret |
| `TWITTER_BEARER_TOKEN` | For live posting | — | Twitter bearer token |
| `TELEGRAM_BOT_TOKEN` | No | — | Telegram bot token (optional) |
| `TELEGRAM_CHAT_ID` | No | — | Telegram chat ID (optional) |
| `DRY_RUN` | No | `true` | Log tweets without posting |
| `IMAGE_MODE` | No | `manual` | Image generation mode |
| `POST_FREQUENCY_MIN` | No | `2` | Min posts per day |
| `POST_FREQUENCY_MAX` | No | `4` | Max posts per day |
| `TIMEZONE` | No | `America/Los_Angeles` | Scheduling timezone |
| `CLAUDE_MODEL` | No | `claude-sonnet-4-5` | Claude model ID |

### IMAGE_MODE Options

| Mode | Behavior | Cost |
|---|---|---|
| `dalle` | Auto-generates images via DALL-E 3 and attaches to tweets | ~$0.04/image |
| `manual` | Generates image prompts and logs them to CSV — you supply the images | Free |
| `none` | Text-only tweets, no image prompts generated | Free |

**Switching modes:**

```bash
# In your .env file:
IMAGE_MODE=dalle    # Full auto — generates and attaches images
IMAGE_MODE=manual   # Prompts logged to data/image_prompts.csv for manual creation
IMAGE_MODE=none     # Text-only tweets
```

When using `manual` mode, check `data/image_prompts.csv` for prompts you can use with any image tool (DALL-E playground, Midjourney, etc.).

## Project Structure

```
oeconomia-twitter-agent/
├── agent/
│   ├── __init__.py
│   ├── main.py              # Entry point, run_post_cycle() wiring
│   ├── content_generator.py # Claude API + dedup logic
│   ├── dalle_client.py      # DALL-E 3 image generation
│   ├── image_prompt_logger.py # CSV logging for image prompts
│   ├── twitter_client.py    # Tweepy v2/v1.1 posting
│   ├── telegram_client.py   # Telegram notifications (optional)
│   └── scheduler.py         # APScheduler random-time scheduling
├── config/
│   ├── __init__.py
│   ├── settings.py          # All env var loading
│   └── brand_voice.py       # System prompt + DALL-E style anchor
├── data/
│   ├── generated_images/    # DALL-E output (gitignored)
│   ├── post_log.json        # Tweet history for dedup
│   └── image_prompts.csv    # Image prompt tracking
├── tests/
│   ├── __init__.py
│   └── test_generator.py    # Unit tests
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Testing

```bash
python -m pytest tests/ -v
```

## Going Live

1. Set `DRY_RUN=false` in `.env`
2. Set `IMAGE_MODE=dalle` if you want auto-generated images
3. Ensure all Twitter API credentials are configured
4. Run: `python -m agent.main`

The agent will schedule random posts throughout the day (8 AM–10 PM in your timezone) and automatically re-plan at midnight.

## Cost Estimates

| Component | Monthly Cost |
|---|---|
| Claude API (claude-sonnet-4-5, ~4 tweets/day) | ~$2–5 |
| DALL-E 3 (standard quality, ~4 images/day) | ~$5–10 |
| Twitter API (free tier) | Free |
| **Total** | **~$7–15/month** |

## Safety

- **DRY_RUN=true by default** — nothing posts until you explicitly enable it
- **IMAGE_MODE=manual by default** — no DALL-E costs until you switch to `dalle`
- All credentials loaded from `.env`, never hardcoded
- Exponential backoff on Twitter rate limits (3 retries)
- Content policy blocks from DALL-E handled gracefully (tweet posts without image)
