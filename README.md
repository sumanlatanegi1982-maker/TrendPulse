# 🔴 TrendPulse — YouTube Trend Analytics

> **Into the Scrape-Verse Hackathon Submission**
>
> TrendPulse helps content creators discover trending YouTube videos and Shorts across 10 content streams (Gaming, Education, Tech, Music, Comedy, Fitness, Cooking, Lifestyle, News, Finance) — powered by **Bright Data Scraper Studio** pre-built YouTube scrapers, with self-healing data pipelines, scheduled auto-scraping, and credit-saving cache mode.

---

## 📋 Table of Contents

1. [Demo Video](#-demo-video)
2. [Features](#-features)
3. [Architecture](#-architecture)
4. [File Structure](#-file-structure)
5. [How It Works](#-how-it-works)
6. [Bright Data Scraper Studio Usage](#-bright-data-scraper-studio-usage)
7. [How to Run](#-how-to-run)
8. [Example Structured Output](#-example-structured-output)
9. [Tech Stack](#-tech-stack)

---

## 🎥 Demo Video

**Link:** `[Add your YouTube/demo video link here]`

The demo video walks through:
- Starting the app and loading trending videos
- Filtering by content stream (Gaming, Education, Tech, etc.)
- Switching between Videos and Shorts tabs
- Viewing analytics (view distribution, top 5 videos, stream comparison)
- Triggering a manual refresh (scrape new data via Bright Data API)
- Showing the self-healing mechanism when data is broken

> **Recording tip:** Use [OBS Studio](https://obsproject.com/) or [Loom](https://www.loom.com/) to record your screen. Keep it under 3 minutes.

---

## ✨ Features

### Core Features

| Feature | Description |
|---|---|
| **10 Content Streams** | Gaming, Education, Tech, Music, Comedy, Fitness, Cooking, Lifestyle, News, Finance |
| **Videos + Shorts Separation** | Automatically separates Shorts (≤60s) from regular videos via duration parsing |
| **7-Day Recency Filter** | Only shows videos from the last 7 days — fresh trends only, regardless of view count |
| **View Distribution Chart** | Bar chart showing how many videos fall in each view bucket (0-1K, 1K-10K, 10K-100K, 100K-1M, 1M-10M, 10M+) |
| **Top 5 Trending Videos** | Ranked by view count with channel name, thumbnail, and stats |
| **Stream Comparison** | Side-by-side comparison of average views per stream — find which stream is hottest |
| **Red Theme UI** | White-red light mode / black-red dark mode — clean, no glossy effects |

### Bright Data Integration Features

| Feature | Description |
|---|---|
| **Pre-built YouTube Scrapers** | Uses Bright Data's dataset `gd_lk56epmy2i5g7lzu0k` (YouTube Videos) — no custom scraper code |
| **Self-Healing Scraper** | If scraped data has missing/broken fields, the system automatically retries with field-level validation up to 3 cycles |
| **Scheduled Auto-Scraping** | Background scheduler runs daily at 2:00 AM — new trends replace old data automatically |
| **Credit-Saving Cache Mode** | Scrape once → save to `cached_data.json` → reuse without API calls. Set `USE_CACHED_DATA=true` to skip API entirely |
| **Async Polling** | Uses Bright Data's async trigger → poll → snapshot flow for large scrapes without timeouts |
| **Data Normalization** | `_normalize_yt()` handles field name variations from Bright Data (e.g., `num_comments` vs `comments_count`) |

---

## 🏗 Architecture

### System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER (Content Creator)                        │
│                              Browser                                 │
│                                                                     │
│   ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐   │
│   │ Stream Filter│  │ Videos/Shorts │  │ Analytics Dashboard     │   │
│   │ (10 streams) │  │   Tabs       │  │ (charts, top 5, compare)│   │
│   └──────┬──────┘  └──────┬───────┘  └───────────┬─────────────┘   │
│          │                │                       │                  │
└──────────┼────────────────┼───────────────────────┼──────────────────┘
           │                │                       │
           ▼                ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FLASK BACKEND (app.py)                       │
│                                                                     │
│   /api/youtube/trending     /api/youtube/analytics    /api/refresh  │
│          │                          │                      │        │
│          ▼                          ▼                      │        │
│   ┌──────────────────────────────────────────────────┐   │        │
│   │        get_videos_for_stream() / get_all()        │   │        │
│   │  Re-tags corrupted cache · deepcopy prevents bugs  │   │        │
│   └──────────────────────┬───────────────────────────┘   │        │
│                          │                               │        │
│              ┌───────────┴───────────┐                   │        │
│              ▼                       ▼                   │        │
│   ┌─────────────────┐    ┌────────────────────┐          │        │
│   │  CACHE LAYER     │    │  BRIGHTDATA CLIENT  │◄─────────┘        │
│   │                  │    │                    │                   │
│   │ cached_data.json│    │ Self-Healing:      │                   │
│   │ (credit-saving) │    │  - validates fields │                   │
│   │                  │    │  - retries broken   │                   │
│   │ If cache exists │    │    records          │                   │
│   │ → zero API calls│    │  - up to 3 cycles   │                   │
│   └─────────────────┘    └─────────┬──────────┘                   │
│                                    │                               │
│   ┌────────────────────────────────┐│                              │
│   │  SCHEDULED SCRAPING (schedule) ││                              │
│   │  Daily 2:00 AM auto-refresh   ││                              │
│   │  New trends replace old data   ││                              │
│   └────────────────────────────────┘│                              │
└─────────────────────────────────────┼───────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   BRIGHT DATA SCRAPER STUDIO                        │
│                                                                     │
│   POST /datasets/v3/trigger   →  Start async scrape                │
│   GET  /datasets/v3/progress/ →  Poll status                       │
│   GET  /datasets/v3/snapshot/ →  Download results                  │
│                                                                     │
│   Dataset IDs (pre-built, no custom code):                          │
│   ├── YouTube Videos:   gd_lk56epmy2i5g7lzu0k                     │
│   ├── YouTube Channels: gd_lk538t2k2p1k3oos71                     │
│   └── YouTube Comments: gd_lk9q0ew71spt1mxywf                     │
└─────────────────────────────────────────────────────────────────────┘
```

### How the Pieces Connect

1. **Frontend (`index.html`)** — Single-page app with stream filter buttons, Videos/Shorts tabs, and analytics dashboard. Makes fetch calls to Flask API endpoints.

2. **Backend (`app.py`)** — Flask server with 3 API routes:
   - `/api/youtube/trending?stream=gaming` — Returns filtered video list
   - `/api/youtube/analytics?stream=gaming` — Returns charts + top videos
   - `/api/youtube/refresh` — Triggers a fresh Bright Data scrape

3. **Cache Layer** — `cached_data.json` stores scraped data on disk. When `USE_CACHED_DATA=true`, the app loads from this file and makes zero API calls — saving Bright Data credits.

4. **Bright Data Client** — Self-healing wrapper around Bright Data's REST API. Triggers async scrapes, polls for completion, validates each record's required fields, and retries broken records up to 3 times.

5. **Scheduler** — Background thread runs `schedule.run_pending()` every 60 seconds. At 2:00 AM daily, it triggers a full re-scrape across all 10 streams. New data replaces old cache automatically.

6. **Self-Healing Flow:**
   ```
   Scrape → Validate each record → Good? Add to results
                               → Broken? Retry just that record (up to 3 cycles)
                               → Still broken? Skip, log warning, continue
   ```

---

## 📁 File Structure

```
TrendPulse/
│
├── app.py                      # Flask backend — API routes, BrightData client, self-healing, scheduler
├── index.html                  # Frontend — single-page UI with stream filters, analytics, charts
├── cached_data.json            # Cached scrape data (credit-saving mode) — created on first scrape
├── .env                        # Environment variables (BRIGHTDATA_API_KEY) — NOT in git
├── .env.example                # Template for .env — safe to commit
├── .gitignore                  # Git ignore rules
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── BRIGHTDATA_USAGE.md         # Detailed Bright Data usage explanation
├── DEMO_VIDEO_SCRIPT.md       # Script for recording the demo video
├── demo_voice_narration.txt    # Voice narration for demo video
└── example_structured_output.json  # Example of Bright Data's output format
```

---

## 🔧 How to Run

### Prerequisites

- Python 3.10 or higher
- A Bright Data account with API access (get your API key from [Bright Data Dashboard](https://brightdata.com/cp/setting/users))
- Git (for cloning)

### Step 1: Clone the Repository

```bash
git clone https://github.com/sumanlatanegi1982-maker/TrendPulse.git
cd TrendPulse
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `flask` — Web framework
- `requests` — HTTP client for Bright Data API
- `python-dotenv` — Load `.env` file
- `schedule` — Background task scheduling

### Step 3: Set Up Your API Key

```bash
cp .env.example .env
# Edit .env and add your Bright Data API key
```

> 🔑 Get your API key from: https://brightdata.com/cp/setting/users

### Step 4: Run the App

**Option A — Live Mode (uses Bright Data API, costs credits):**
```bash
python app.py
```

**Option B — Cache Mode (uses cached_data.json, zero API calls):**
```bash
export USE_CACHED_DATA=true    # Linux/Mac
set USE_CACHED_DATA=true       # Windows
python app.py
```

**Option C — Demo Mode (no API key, uses built-in sample data):**
```bash
python app.py
```
The app will detect no API key and automatically use sample data (23 videos across 10 streams, dated August 2026).

### Step 5: Open in Browser

```
http://localhost:5000
```

---

## 🔌 Bright Data Scraper Studio Usage

### Dataset IDs (Pre-Built by Bright Data)

| Dataset | ID | Purpose |
|---|---|---|
| YouTube Videos | `gd_lk56epmy2i5g7lzu0k` | Scrape video metadata by search keyword |
| YouTube Channels | `gd_lk538t2k2p1k3oos71` | Scrape channel-level stats |
| YouTube Comments | `gd_lk9q0ew71spt1mxywf` | Scrape video comments |

### API Flow (3 Steps)

```
Step 1: TRIGGER
   POST https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_lk56epmy2i5g7lzu0k&format=json
   → Returns: {"snapshot_id": "snap_xxxxx"}

Step 2: POLL (repeat until status = "ready")
   GET https://api.brightdata.com/datasets/v3/progress/snap_xxxxx
   → Returns: {"status": "running"} or {"status": "ready"}

Step 3: DOWNLOAD
   GET https://api.brightdata.com/datasets/v3/snapshot/snap_xxxxx?format=json
   → Returns: [{"url": "...", "title": "...", "views": 12345, ...}, ...]
```

### Self-Healing Mechanism

1. **Validates** each record against required fields (`url`, `title`)
2. **Separates** good records from broken ones
3. **Re-scrapes** only the broken records (up to 3 cycles)
4. **Merges** healed records back with good ones
5. **Skips** records that still fail after 3 attempts (logs a warning)

### Credit-Saving Cache

1. **First run** — Scrape all streams → save to `cached_data.json`
2. **Subsequent runs** — Set `USE_CACHED_DATA=true` → loads from file → zero API calls
3. **Scheduled refresh** — Daily at 2:00 AM, the scheduler re-scrapes and overwrites the cache

For the full Bright Data usage guide, see [BRIGHTDATA_USAGE.md](BRIGHTDATA_USAGE.md).

---

## 📊 Example Structured Output

See [example_structured_output.json](example_structured_output.json) for a full example with multiple videos.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Backend** | Python 3.12, Flask |
| **Data Source** | Bright Data Scraper Studio (pre-built YouTube datasets) |
| **Scheduling** | `schedule` Python library (background thread) |
| **Caching** | JSON file (`cached_data.json`) |
| **API** | Bright Data REST API |

---

## 🏆 Hackathon Compliance Checklist

| Requirement | Status | File |
|---|---|---|
| Demo video showing working project | ⬜ Record & add link | See `DEMO_VIDEO_SCRIPT.md` |
| Public source-code repository | ✅ | GitHub |
| Clear README | ✅ | `README.md` (this file) |
| Example structured output | ✅ | `example_structured_output.json` |
| Bright Data usage explanation | ✅ | `BRIGHTDATA_USAGE.md` + this README |

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

## 👥 Author

Built for **Into the Scrape-Verse** hackathon.

**YouTube-only** — no Instagram, no TikTok. Just YouTube trends, powered by Bright Data.
