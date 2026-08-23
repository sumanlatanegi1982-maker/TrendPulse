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

https://youtu.be/xefEctUgBd0

The demo video walks through:
- Starting the app and loading trending videos
- Filtering by content stream (Gaming, Education, Tech, etc.)
- Switching between Videos and Shorts tabs
- Viewing analytics (view distribution, top 5 videos, stream comparison)
- Triggering a manual refresh (scrape new data via Bright Data API)
- Showing the self-healing mechanism when data is broken

> The video is hosted on YouTube (unlisted) and plays directly in the GitHub README.

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

### Where Each Piece Lives

| File | Purpose | Required for Submission? |
|---|---|---|
| `app.py` | Main backend server | ✅ Source code |
| `index.html` | Frontend UI | ✅ Source code |
| `requirements.txt` | Python dependencies | ✅ Reproducibility |
| `README.md` | Project documentation | ✅ Clear README |
| `example_structured_output.json` | Sample Bright Data output | ✅ Example structured output |
| `BRIGHTDATA_USAGE.md` | Bright Data explanation | ✅ Bright Data usage |
| `.env.example` | API key template | ✅ Setup guide |
| `.gitignore` | Git hygiene | ✅ Best practice |
| `cached_data.json` | Cached data | ❌ Auto-generated (in .gitignore) |
| `.env` | Real API key | ❌ Secret (in .gitignore) |

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
# Copy the template
cp .env.example .env

# Edit .env and add your Bright Data API key
# Replace the placeholder with your real key
echo 'BRIGHTDATA_API_KEY=your_real_api_key_here' > .env
```

Or open `.env` in any text editor and paste your key:
```
BRIGHTDATA_API_KEY=your_real_api_key_here
```

> 🔑 Get your API key from: https://brightdata.com/cp/setting/users

### Step 4: Run the App

**Option A — Live Mode (uses Bright Data API, costs credits):**
```bash
python app.py
```

**Option B — Cache Mode (uses cached_data.json, zero API calls):**
```bash
# First run in live mode to create cached_data.json
# Then set the environment variable
export USE_CACHED_DATA=true    # Linux/Mac
set USE_CACHED_DATA=true       # Windows
python app.py
```

**Option C — Demo Mode (no API key, uses built-in sample data):**
```bash
# Don't set any API key in .env, just run
python app.py
```
The app will detect no API key and automatically use sample data (23 videos across 10 streams, dated August 2026).

### Step 5: Open in Browser

```
http://localhost:5000
```

The app runs on port 5000 by default. You should see:
- Stream filter buttons at the top (All, Gaming, Education, Tech, Music, etc.)
- Video cards with thumbnails, titles, channel names, view counts
- Analytics section with view distribution chart, top 5 videos, stream comparison
- A "Refresh" button to trigger a new scrape

### How It Runs

```
User opens browser → Flask serves index.html
                   → Frontend calls /api/youtube/trending
                   → Backend checks cache (cached_data.json)
                      ├─ Cache exists → Return cached videos (0 API calls)
                      └─ No cache → Call Bright Data API
                                   → Trigger async scrape
                                   → Poll until ready
                                   → Download + validate results
                                   → Save to cached_data.json
                                   → Return videos to frontend
                   → Frontend renders video cards + analytics
```

The scheduler runs in a background thread:
```
Every 60 seconds → schedule.run_pending()
                 → At 2:00 AM daily → scrape_all_streams()
                 → New data replaces cached_data.json
```

---

## 🔌 Bright Data Scraper Studio Usage

### What We Used

TrendPulse uses **Bright Data Scraper Studio's pre-built YouTube scrapers** — no custom scraper code, no AI scrapers. We used the **dataset trigger API** to scrape YouTube video data by search keyword.

### Dataset IDs (Pre-Built by Bright Data)

| Dataset | ID | Purpose |
|---|---|---|
| YouTube Videos | `gd_lk56epmy2i5g7lzu0k` | Scrape video metadata by search keyword |
| YouTube Channels | `gd_lk538t2k2p1k3oos71` | Scrape channel-level stats (future use) |
| YouTube Comments | `gd_lk9q0ew71spt1mxywf` | Scrape video comments (future use) |

### API Flow (3 Steps)

```
Step 1: TRIGGER
   POST https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_lk56epmy2i5g7lzu0k&format=json
   Body: [{"url": "https://www.youtube.com/results?search_query=gaming+highlights"}]
   Headers: Authorization: Bearer <API_KEY>
   → Returns: {"snapshot_id": "snap_xxxxx"}

Step 2: POLL (repeat until status = "ready")
   GET https://api.brightdata.com/datasets/v3/progress/snap_xxxxx
   → Returns: {"status": "running"} or {"status": "ready"}

Step 3: DOWNLOAD
   GET https://api.brightdata.com/datasets/v3/snapshot/snap_xxxxx?format=json
   → Returns: [{"url": "...", "title": "...", "views": 12345, ...}, ...]
```

### How Each Stream Is Scraped

Each content stream has 3 search keywords defined in `STREAM_KEYWORDS`:

```python
STREAM_KEYWORDS = {
    "gaming":    ["gaming highlights", "gameplay", "walkthrough"],
    "education": ["tutorial", "explained", "course"],
    "tech":      ["tech review", "gadgets", "technology"],
    "music":     ["music video", "new song", "cover"],
    "comedy":    ["funny", "comedy sketch", "meme"],
    "fitness":   ["workout", "fitness", "gym"],
    "cooking":   ["recipe", "cooking", "food"],
    "lifestyle": ["vlog", "daily routine", "lifestyle"],
    "news":      ["breaking news", "news today", "current events"],
    "finance":   ["stock market", "crypto", "personal finance"],
}
```

For each keyword, the app sends a YouTube search URL to Bright Data:
```
https://www.youtube.com/results?search_query=gaming+highlights
```

Bright Data's pre-built scraper visits that URL, extracts all video results, and returns structured JSON.

### Self-Healing Mechanism

When Bright Data returns data, some records may have missing or broken fields (empty titles, null view counts, etc.). The self-healing system:

1. **Validates** each record against required fields (`url`, `title`)
2. **Separates** good records from broken ones
3. **Re-scrapes** only the broken records (up to 3 cycles)
4. **Merges** healed records back with good ones
5. **Skips** records that still fail after 3 attempts (logs a warning)

```python
def _healed_scrape(self, dataset_id, input_data, required_fields, ...):
    good_records = []
    pending = list(input_data)

    for cycle in range(self.MAX_HEAL_CYCLES):  # 3 cycles
        results = self._trigger_async(dataset_id, pending)
        good, broken = self._split_valid_invalid(results, required_fields)
        good_records.extend(good)
        pending = broken  # Retry only broken records
        if not pending:
            break  # All healed!
```

### Credit-Saving Cache

To minimize Bright Data API credit usage:

1. **First run** — Scrape all streams → save to `cached_data.json`
2. **Subsequent runs** — Set `USE_CACHED_DATA=true` → loads from file → zero API calls
3. **Scheduled refresh** — Daily at 2:00 AM, the scheduler re-scrapes and overwrites the cache

This means you can demo the app unlimited times on a single scrape's worth of credits.

For the full Bright Data usage guide, see [BRIGHTDATA_USAGE.md](BRIGHTDATA_USAGE.md).

---

## 📊 Example Structured Output

Bright Data's YouTube Videos dataset returns this structure (example with real field names):

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "title": "Video Title Here",
  "description": "Full video description...",
  "channel_name": "Channel Name",
  "channel_url": "https://www.youtube.com/@channelname",
  "date_posted": "2026-08-21T14:00:00Z",
  "views": 2400000,
  "likes": 145000,
  "num_comments": 8200,
  "duration": "12:30",
  "preview_image": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
  "tags": ["gaming", "highlights"]
}
```

TrendPulse normalizes this into its internal format:

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "title": "Video Title Here",
  "channel_name": "Channel Name",
  "views": 2400000,
  "likes": 145000,
  "comments": 8200,
  "date_posted": "2026-08-21T14:00:00Z",
  "duration": "12:30",
  "preview_image": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
  "stream": "gaming",
  "is_short": false
}
```

See [example_structured_output.json](example_structured_output.json) for a full example with multiple videos.

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3 (custom, no framework), Vanilla JavaScript |
| **Backend** | Python 3.12, Flask |
| **Data Source** | Bright Data Scraper Studio (pre-built YouTube datasets) |
| **Scheduling** | `schedule` Python library (background thread) |
| **Caching** | JSON file (`cached_data.json`) |
| **API** | Bright Data REST API (`/datasets/v3/trigger`, `/progress`, `/snapshot`) |
| **Env Management** | python-dotenv |
| **HTTP Client** | requests |

---

## 📸 Codebase Screenshots

> Add screenshots of your running app here:

1. **Main Dashboard** — Shows stream filters + video cards
2. **Stream Filter Active** — e.g., Gaming selected, only gaming videos visible
3. **Analytics View** — View distribution chart + Top 5 videos + Stream comparison
4. **Shorts Tab** — Shows only YouTube Shorts (≤60s duration)
5. **Terminal Output** — Shows self-healing logs and cache loading

---

## 🏆 Hackathon Compliance Checklist

| Requirement | Status | File |
|---|---|---|
| Demo video showing working project | Done | https://youtu.be/xefEctUgBd0 |
| Public source-code repository | Done | https://github.com/sumanlatanegi1982-maker/TrendPulse |
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
