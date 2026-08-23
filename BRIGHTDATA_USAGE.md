# How BrightData Scraper Studio Is Used in TrendPulse

This document explains exactly how TrendPulse uses BrightData Scraper Studio to scrape YouTube trending data.

---

## 1. Which Scraper We Use

TrendPulse uses BrightData's **pre-built YouTube scraper**, not a custom AI-built scraper. Pre-built scrapers are maintained by BrightData -- they handle proxy rotation, anti-bot bypassing, and parsing automatically. We never have to update parsing logic when YouTube changes their page structure.

**Scraper location in BrightData dashboard:**
- Go to Scrapers -> Scrapers Library -> search "youtube"
- Select "Youtube - Videos posts"
- Use the "Discover by keyword" endpoint

**Scraper details:**

| Property | Value |
|---|---|
| Scraper name | Youtube - Videos posts - discover by keyword |
| Dataset ID | `gd_lk56epmy2i5g7lzu0k` |
| API endpoint | `POST https://api.brightdata.com/datasets/v3/trigger` |
| Mode | Asynchronous (trigger + poll) |
| Cost | $1.50 per 1,000 records |
| Free credits used | 3,167 / 5,000 |

---

## 2. Authentication

Every API request includes a Bearer token in the Authorization header:

```
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

The API key is obtained from https://brightdata.com/cp/setting/users and stored in the `.env` file as `BRIGHTDATA_API_KEY`. The Python backend reads it using `python-dotenv` and never exposes it to the frontend.

---

## 3. Request Flow (Step by Step)

### Step 1: Trigger the scrape

When a user clicks a stream filter (e.g., "Gaming"), the backend sends a POST request to BrightData's `/trigger` endpoint:

```python
POST https://api.brightdata.com/datasets/v3/trigger
    ?dataset_id=gd_lk56epmy2i5g7lzu0k
    &format=json
    &type=discover_new
    &discover_by=keyword

Headers:
    Authorization: Bearer YOUR_API_KEY
    Content-Type: application/json

Body:
[
    {
        "keyword": "gaming highlights",
        "num_of_posts": 15,
        "start_date": "08-15-2026"
    }
]
```

The `start_date` parameter ensures only videos from the last 7 days are returned -- this is what makes TrendPulse show recent trends instead of old popular videos.

### Step 2: Receive snapshot_id

BrightData responds with a snapshot ID:

```json
{
    "snapshot_id": "s_m4x7enmven8djfqak"
}
```

### Step 3: Poll for completion

The backend polls the progress endpoint until the scrape is ready:

```python
GET https://api.brightdata.com/datasets/v3/progress/s_m4x7enmven8djfqak
Headers: Authorization: Bearer YOUR_API_KEY
```

Response when still running:
```json
{"snapshot_id": "s_m4x7enmven8djfqak", "status": "running"}
```

Response when ready:
```json
{"snapshot_id": "s_m4x7enmven8djfqak", "status": "ready", "records": 15}
```

### Step 4: Download results

Once ready, the backend downloads the structured JSON data:

```python
GET https://api.brightdata.com/datasets/v3/snapshot/s_m4x7enmven8djfqak
    ?format=json
Headers: Authorization: Bearer YOUR_API_KEY
```

---

## 4. Response Structure

BrightData returns clean, structured JSON -- no HTML parsing needed. Each video record contains:

```json
{
    "url": "https://www.youtube.com/watch?v=FuE6hPyNMCy",
    "title": "Insane 1v5 Clutch - Valorant Champions 2026",
    "channel_name": "ProGaming",
    "channel_url": "https://www.youtube.com/@ProGaming",
    "views": 2400000,
    "likes": 145000,
    "num_comments": 8200,
    "date_posted": "2026-08-21T14:00:00.000Z",
    "duration": "12:30",
    "video_length": 750,
    "description": "Watch this insane 1v5 clutch...",
    "preview_image": "https://i.ytimg.com/vi/FuE6hPyNMCy/maxresdefault.jpg",
    "tags": ["gaming", "valorant", "esports", "highlights"],
    "video_id": "FuE6hPyNMCy",
    "verified": true,
    "is_sponsored": false
}
```

Full example output: See `example_structured_output.json`

---

## 5. Self-Healing System

TrendPulse adds a self-healing layer on top of BrightData's scraper. The `BrightDataClient._healed_scrape()` method:

### Healing Cycle (repeats up to 3 times):

1. **Send request** to BrightData API
2. **Retry on failure** -- if the request fails (HTTP 429 rate limit, 500+ server error), wait and retry up to 3 times with increasing delay (5s, 10s, 15s)
3. **Sync-to-async fallback** -- if a synchronous request times out (>60s), BrightData returns a `snapshot_id`. The code detects this and automatically switches to async polling mode
4. **Validate each record** -- every returned record is checked for required fields (`url`, `title`, `views`). Records with missing/null fields are flagged as "broken"
5. **Re-scrape broken records** -- only the broken records' input URLs are collected and re-requested in the next cycle
6. **Return cleaned data** -- after all cycles, only valid records are returned

### Console output during healing:
```
[HEAL] Broken record #3, will re-scrape: {"keyword": "gaming highlights"}
[HEAL] Cycle 1: 1 broken records, retrying...
[HEAL] Cycle 2: all 15 records valid
```

### Auth error handling:
If the API key is invalid (HTTP 401), the code immediately raises a clear error:
```
AUTH FAILED: Check your BRIGHTDATA_API_KEY in .env file
```

---

## 6. Scheduled Scraping

The `ScheduledScraper` class runs automatically:

1. **On startup** -- scrapes all 10 streams immediately (or loads from `cached_data.json` if `USE_CACHED_DATA=true`)
2. **Every 4 hours** -- re-scrapes all streams to refresh trend data
3. **Old data replaced** -- each scrape overwrites the cache, so trends stay current
4. **Cache saved to file** -- after each scrape, data is saved to `cached_data.json` for credit-saving mode

### Streams scraped:
Each stream maps to a search keyword sent to BrightData:

| Stream | Keyword sent to BrightData |
|---|---|
| Gaming | "gaming highlights" |
| Education | "tutorial" |
| Tech | "tech review" |
| Music | "music video" |
| Comedy | "funny" |
| Fitness | "workout" |
| Cooking | "recipe" |
| Lifestyle | "vlog" |
| News | "breaking news" |
| Finance | "stock market" |

---

## 7. Credit-Saving Mode

To avoid wasting BrightData credits during development:

1. Set `USE_CACHED_DATA=false` in `.env`, run once with real API key
2. Data is saved to `cached_data.json`
3. Set `USE_CACHED_DATA=true`, restart
4. App loads from file -- zero API calls, zero credits used
5. Develop and debug freely
6. When ready for fresh data, set back to `false`

---

## 8. Data Processing Pipeline

```
User clicks "Gaming" filter
        |
Flask backend receives request
        |
Check cache for "gaming" stream
        |
If cache empty -> send keyword "gaming highlights" to BrightData API
        |
BrightData scrapes YouTube search results
        |
Self-healing: validate + re-scrape broken records
        |
Normalize field names (youtuber -> channel_name, etc.)
        |
Filter to last 7 days by date_posted
        |
Separate into videos (60s+) and shorts (<60s)
        |
Sort by views (highest first)
        |
Return JSON to frontend
        |
Frontend renders trend cards + analytics charts
```
