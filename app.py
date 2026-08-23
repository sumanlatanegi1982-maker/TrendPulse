import os
import json
import time
import threading
import schedule
import copy
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict
import requests
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")

# ═════════════════════════════════════════════════════════════
#  BRIGHTDATA CONFIG
# ═════════════════════════════════════════════════════════════
API_KEY = os.getenv("BRIGHTDATA_API_KEY", "")
BASE_URL = "https://api.brightdata.com/datasets/v3"

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cached_data.json")
USE_CACHED_DATA = os.getenv("USE_CACHED_DATA", "false").lower() == "true"

DATASET_IDS = {
    "youtube_videos":   "gd_lk56epmy2i5g7lzu0k",
    "youtube_channels": "gd_lk538t2k2p1k3oos71",
    "youtube_comments":  "gd_lk9q0ew71spt1mxywf",
}

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

DEFAULT_LIMIT = 20
MAX_LIMIT = 1000

CACHE = {
    "videos": {},
    "last_updated": None,
}


# ════════════════════════════════════════════════════════════
#  SELF-HEALING BRIGHTDATA CLIENT
# ════════════════════════════════════════════════════════════
class BrightDataClient:

    MAX_HEAL_CYCLES = 3
    MAX_RETRIES = 3
    RETRY_DELAY = 5

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _trigger_async(self, dataset_id, input_data, extra_params=None):
        url = f"{BASE_URL}/trigger"
        params = {"dataset_id": dataset_id, "format": "json"}
        if extra_params:
            params.update(extra_params)
        resp = requests.post(url, params=params, headers=self.headers,
                             json=input_data, timeout=60)
        resp.raise_for_status()
        snapshot_data = resp.json()
        snapshot_id = snapshot_data.get("snapshot_id")
        if not snapshot_id:
            if isinstance(snapshot_data, list):
                return snapshot_data
            raise Exception(f"No snapshot_id: {snapshot_data}")
        return self._poll_and_download(snapshot_id)

    def _poll_and_download(self, snapshot_id):
        for attempt in range(120):
            resp = requests.get(f"{BASE_URL}/progress/{snapshot_id}",
                                headers=self.headers, timeout=30)
            resp.raise_for_status()
            progress = resp.json()
            status = progress.get("status")
            if status == "ready":
                resp2 = requests.get(f"{BASE_URL}/snapshot/{snapshot_id}",
                                    params={"format": "json"},
                                    headers=self.headers, timeout=120)
                resp2.raise_for_status()
                return resp2.json()
            if status == "failed":
                raise Exception(f"Snapshot failed: {progress.get('error')}")
            if attempt % 3 == 0:
                print(f"  [POLL] {snapshot_id}: {status} ({attempt+1})")
            time.sleep(10)
        raise Exception(f"Snapshot {snapshot_id} timed out")

    def _validate_record(self, record, required_fields):
        if not isinstance(record, dict):
            return False
        for field in required_fields:
            val = record.get(field)
            if val is None or val == "" or val == []:
                return False
        return True

    def _healed_scrape(self, dataset_id, input_data, required_fields,
                       mode="async", extra_params=None):
        good_records = []
        pending = list(input_data)

        for cycle in range(self.MAX_HEAL_CYCLES):
            if not pending:
                break

            records = []
            last_error = None
            for attempt in range(self.MAX_RETRIES):
                try:
                    records = self._trigger_async(dataset_id, pending, extra_params)
                    break
                except requests.exceptions.HTTPError as e:
                    last_error = e
                    status_code = e.response.status_code if e.response else 0
                    if status_code == 401:
                        raise Exception("AUTH FAILED: Check BRIGHTDATA_API_KEY in .env")
                    print(f"  [RETRY] HTTP {status_code}, attempt {attempt+1}")
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                except requests.exceptions.RequestException as e:
                    last_error = e
                    print(f"  [RETRY] Connection error, attempt {attempt+1}")
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
            else:
                if not good_records and not records:
                    raise Exception(f"All retries failed: {last_error}")
                break

            bad_inputs = []
            for i, record in enumerate(records):
                if self._validate_record(record, required_fields):
                    good_records.append(record)
                else:
                    if i < len(pending):
                        bad_inputs.append(pending[i])
                        print(f"  [HEAL] Broken record #{i}, will re-scrape")

            pending = bad_inputs
            if pending:
                print(f"  [HEAL] Cycle {cycle+1}: {len(pending)} broken, retrying...")
            else:
                print(f"  [HEAL] Cycle {cycle+1}: all {len(good_records)} records valid")

        return good_records

    def _normalize_yt(self, record):
        raw_duration = record.get("duration") or ""
        if not raw_duration and record.get("video_length"):
            try:
                secs = int(float(record["video_length"]))
                raw_duration = f"{secs // 60}:{secs % 60:02d}"
            except (ValueError, TypeError):
                raw_duration = str(record.get("video_length", ""))

        return {
            "url": record.get("url") or record.get("video_url") or "",
            "title": record.get("title") or "Untitled",
            "channel_name": record.get("channel_name") or record.get("youtuber")
                            or record.get("handle_name") or "Unknown",
            "views": record.get("views") or 0,
            "likes": record.get("likes") or 0,
            "num_comments": record.get("num_comments") or 0,
            "date_posted": record.get("date_posted") or "",
            "duration": raw_duration,
            "preview_image": record.get("preview_image") or record.get("thumbnail") or "",
            "tags": record.get("tags") or [],
            "channel_url": record.get("channel_url") or "",
        }

    def discover_by_keyword(self, keyword, num_posts=20, start_date=None):
        input_obj = {"keyword": keyword, "num_of_posts": num_posts}
        if start_date:
            input_obj["start_date"] = start_date
        input_data = [input_obj]
        required = ["url", "title", "views"]
        extra = {"type": "discover_new", "discover_by": "keyword"}
        raw = self._healed_scrape(DATASET_IDS["youtube_videos"], input_data,
                                   required, extra_params=extra)
        return [self._normalize_yt(r) for r in raw]


# ══════════════════════════════════════════════════════════
#  ANALYTICS ENGINE
# ═════════════════════════════════════════════════════════════
class AnalyticsEngine:

    @staticmethod
    def view_distribution(videos):
        buckets = [
            {"label": "0-1K", "min": 0, "max": 1000, "count": 0},
            {"label": "1K-10K", "min": 1000, "max": 10000, "count": 0},
            {"label": "10K-100K", "min": 10000, "max": 100000, "count": 0},
            {"label": "100K-1M", "min": 100000, "max": 1000000, "count": 0},
            {"label": "1M-10M", "min": 1000000, "max": 10000000, "count": 0},
            {"label": "10M+", "min": 10000000, "max": float("inf"), "count": 0},
        ]
        for v in videos:
            try:
                views = int(v.get("views", 0) or 0)
            except (ValueError, TypeError):
                views = 0
            for b in buckets:
                if b["min"] <= views < b["max"]:
                    b["count"] += 1
                    break
        return buckets

    @staticmethod
    def top_videos(videos, limit=5):
        try:
            sorted_videos = sorted(videos,
                key=lambda v: int(v.get("views", 0) or 0), reverse=True)
            return sorted_videos[:limit]
        except Exception:
            return videos[:limit]

    @staticmethod
    def separate_shorts(videos):
        shorts = []
        regular = []
        for v in videos:
            duration = v.get("duration", "")
            if not duration:
                regular.append(v)
                continue
            is_short = False
            parts = str(duration).split(":")
            try:
                if len(parts) == 2:
                    secs = int(parts[0]) * 60 + int(parts[1])
                    if secs <= 60:
                        is_short = True
                elif len(parts) == 1:
                    secs = int(float(parts[0]))
                    if secs <= 60:
                        is_short = True
            except (ValueError, TypeError):
                pass
            if is_short:
                shorts.append(v)
            else:
                regular.append(v)
        return regular, shorts


# ════════════════════════════════════════════════════════════
#  SCHEDULED SCRAPER
# ═══════════════════════════════════════════════════════════
class ScheduledScraper:

    def __init__(self, bd_client):
        self.client = bd_client
        self.analytics = AnalyticsEngine()

    def save_cache_to_file(self):
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(CACHE, f, indent=2)
            total = sum(len(v) for v in CACHE.get("videos", {}).values())
            print(f"  [CACHE] Saved {total} videos to cached_data.json")
        except Exception as e:
            print(f"  [CACHE] Failed to save: {e}")

    def load_cache_from_file(self):
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r") as f:
                    loaded = json.load(f)
                CACHE["videos"] = loaded.get("videos", {})
                CACHE["last_updated"] = loaded.get("last_updated")
                # RE-TAG every video with its correct stream from the cache key
                # This fixes corrupted stream tags from old mutation bugs
                for stream_key, vids in CACHE["videos"].items():
                    for v in vids:
                        v["stream"] = stream_key
                total = sum(len(v) for v in CACHE["videos"].values())
                print(f"  [CACHE] Loaded {total} videos from cached_data.json")
                print(f"  [CACHE] Streams: {list(CACHE['videos'].keys())}")
                for s, vids in CACHE["videos"].items():
                    print(f"  [CACHE]   {s}: {len(vids)} videos")
                return True
            else:
                print(f"  [CACHE] No cached_data.json found")
                return False
        except Exception as e:
            print(f"  [CACHE] Failed to load: {e}")
            return False

    def _filter_recent(self, videos, cutoff_dt):
        result = []
        for v in videos:
            date_str = v.get("date_posted", "")
            if not date_str:
                result.append(v)
                continue
            try:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                if dt >= cutoff_dt:
                    result.append(v)
            except (ValueError, TypeError):
                result.append(v)
        return result

    def run_scrape(self):
        print(f"\n{'='*60}")
        print(f"  [SCHEDULED] Starting trend scrape at {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")

        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        start_date_str = week_ago.strftime("%m-%d-%Y")
        cutoff = week_ago
        all_videos = []

        for stream, keywords in STREAM_KEYWORDS.items():
            print(f"\n  [{stream}] Scraping (last 7 days)...")
            try:
                if self.client:
                    videos = self.client.discover_by_keyword(
                        keywords[0], num_posts=15, start_date=start_date_str
                    )
                else:
                    raw = SAMPLE_VIDEOS.get(stream, [])
                    videos = copy.deepcopy(raw)

                for v in videos:
                    v["stream"] = stream

                videos = self._filter_recent(videos, cutoff)
                CACHE["videos"][stream] = videos
                all_videos.extend(videos)
                print(f"  [{stream}] Got {len(videos)} recent videos")

            except Exception as e:
                print(f"  [{stream}] ERROR: {e}")
                raw = SAMPLE_VIDEOS.get(stream, [])
                fallback = copy.deepcopy(raw)
                for v in fallback:
                    v["stream"] = stream
                CACHE["videos"][stream] = fallback
                all_videos.extend(fallback)

        CACHE["last_updated"] = datetime.now().isoformat()
        self.save_cache_to_file()

        print(f"\n  [SCHEDULED] Done. {len(all_videos)} total videos cached.")

    def start(self, interval_hours=4):
        if USE_CACHED_DATA:
            print("\n  [MODE] Using cached data (no API calls, no credits used)")
            loaded = self.load_cache_from_file()
            if not loaded:
                print("  [MODE] No cache file found, using sample data")
                self.run_scrape()
        else:
            self.run_scrape()

        schedule.every(interval_hours).hours.do(self.run_scrape)

        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)

        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
        print(f"  [SCHEDULED] Auto-scraper running every {interval_hours} hours")


# ══════════════════════════════════════════════════════════════════
#  SAMPLE DATA
# ═══════════════════════════════════════════════════════════
SAMPLE_VIDEOS = {
    "gaming": [
        {"url": "https://youtube.com/watch?v=g1", "title": "Insane 1v5 Clutch - Valorant Champions",
         "channel_name": "ProGaming", "views": 2400000, "likes": 145000,
         "date_posted": "2026-08-21T14:00:00Z", "duration": "12:30",
         "preview_image": "https://i.ytimg.com/vi/dQw4w9VgXcQ/maxresdefault.jpg",
         "num_comments": 8200, "tags": ["gaming", "valorant", "esports"]},
        {"url": "https://youtube.com/watch?v=g2", "title": "Best Gaming Setup 2026 - Budget Build",
         "channel_name": "TechGamer", "views": 890000, "likes": 45000,
         "date_posted": "2026-08-20T09:00:00Z", "duration": "0:45",
         "preview_image": "https://i.ytimg.com/vi/kqtD5dpn9C8/maxresdefault.jpg",
         "num_comments": 2100, "tags": ["gaming", "setup", "budget"]},
        {"url": "https://youtube.com/watch?v=g3", "title": "Top 10 Gaming Moments This Week",
         "channel_name": "GameHighlights", "views": 1500000, "likes": 89000,
         "date_posted": "2026-08-19T18:00:00Z", "duration": "15:22",
         "preview_image": "https://i.ytimg.com/vi/9bZkp7q19f0/maxresdefault.jpg",
         "num_comments": 5400, "tags": ["gaming", "highlights", "top10"]},
    ],
    "education": [
        {"url": "https://youtube.com/watch?v=e1", "title": "Python Full Course - Learn in 10 Hours",
         "channel_name": "CodeWithMe", "views": 5100000, "likes": 230000,
         "date_posted": "2026-08-18T08:00:00Z", "duration": "58:42",
         "preview_image": "https://i.ytimg.com/vi/kqtD5dpn9C8/maxresdefault.jpg",
         "num_comments": 15000, "tags": ["python", "tutorial", "coding"]},
        {"url": "https://youtube.com/watch?v=e2", "title": "Math Made Easy - Algebra Basics",
         "channel_name": "MathMaster", "views": 1200000, "likes": 56000,
         "date_posted": "2026-08-17T10:00:00Z", "duration": "0:55",
         "preview_image": "https://i.ytimg.com/vi/JGwWNGJdvx8/maxresdefault.jpg",
         "num_comments": 3200, "tags": ["math", "education", "algebra"]},
        {"url": "https://youtube.com/watch?v=e3", "title": "Physics Explained - Quantum Mechanics",
         "channel_name": "SciEdu", "views": 890000, "likes": 42000,
         "date_posted": "2026-08-16T15:00:00Z", "duration": "22:10",
         "preview_image": "https://i.ytimg.com/vi/60ItHLz5WEA/maxresdefault.jpg",
         "num_comments": 2800, "tags": ["physics", "science", "education"]},
    ],
    "tech": [
        {"url": "https://youtube.com/watch?v=t1", "title": "iPhone 17 Pro Review - Worth It?",
         "channel_name": "TechReview", "views": 3200000, "likes": 98000,
         "date_posted": "2026-08-21T16:00:00Z", "duration": "15:20",
         "preview_image": "https://i.ytimg.com/vi/9bZkp7q19f0/maxresdefault.jpg",
         "num_comments": 5400, "tags": ["tech", "iphone", "review"]},
        {"url": "https://youtube.com/watch?v=t2", "title": "Best Budget Laptops 2026",
         "channel_name": "TechBudget", "views": 670000, "likes": 34000,
         "date_posted": "2026-08-20T11:00:00Z", "duration": "0:58",
         "preview_image": "https://i.ytimg.com/vi/OPf0YbXqDm0/maxresdefault.jpg",
         "num_comments": 1800, "tags": ["tech", "laptop", "budget"]},
        {"url": "https://youtube.com/watch?v=t3", "title": "AI Tools That Will Replace Developers",
         "channel_name": "AIWeekly", "views": 2100000, "likes": 87000,
         "date_posted": "2026-08-21T13:00:00Z", "duration": "18:45",
         "preview_image": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
         "num_comments": 6700, "tags": ["ai", "tech", "programming"]},
    ],
    "fitness": [
        {"url": "https://youtube.com/watch?v=f1", "title": "Full Body Workout - No Equipment",
         "channel_name": "FitLife", "views": 1800000, "likes": 67000,
         "date_posted": "2026-08-21T06:00:00Z", "duration": "0:48",
         "preview_image": "https://i.ytimg.com/vi/OPf0YbXqDm0/maxresdefault.jpg",
         "num_comments": 3200, "tags": ["fitness", "workout", "home"]},
        {"url": "https://youtube.com/watch?v=f2", "title": "30 Day Transformation Challenge",
         "channel_name": "GymPro", "views": 950000, "likes": 45000,
         "date_posted": "2026-08-19T17:00:00Z", "duration": "12:30",
         "preview_image": "https://i.ytimg.com/vi/JGwWNGJdvx8/maxresdefault.jpg",
         "num_comments": 2100, "tags": ["fitness", "challenge", "transformation"]},
    ],
    "cooking": [
        {"url": "https://youtube.com/watch?v=c1", "title": "15 Minute Pasta Recipe",
         "channel_name": "FoodLab", "views": 950000, "likes": 45000,
         "date_posted": "2026-08-20T12:00:00Z", "duration": "0:45",
         "preview_image": "https://i.ytimg.com/vi/JGwWNGJdvx8/maxresdefault.jpg",
         "num_comments": 2100, "tags": ["cooking", "pasta", "recipe"]},
        {"url": "https://youtube.com/watch?v=c2", "title": "Street Food Tour - Mumbai",
         "channel_name": "FoodTravel", "views": 1400000, "likes": 78000,
         "date_posted": "2026-08-21T19:00:00Z", "duration": "20:15",
         "preview_image": "https://i.ytimg.com/vi/60ItHLz5WEA/maxresdefault.jpg",
         "num_comments": 3400, "tags": ["cooking", "streetfood", "india"]},
    ],
    "finance": [
        {"url": "https://youtube.com/watch?v=fi1", "title": "Stock Market Today - What to Buy",
         "channel_name": "FinancePro", "views": 1200000, "likes": 34000,
         "date_posted": "2026-08-22T09:00:00Z", "duration": "22:10",
         "preview_image": "https://i.ytimg.com/vi/60ItHLz5WEA/maxresdefault.jpg",
         "num_comments": 4100, "tags": ["finance", "stocks", "investing"]},
        {"url": "https://youtube.com/watch?v=fi2", "title": "How to Save $10K This Year",
         "channel_name": "MoneyTips", "views": 780000, "likes": 39000,
         "date_posted": "2026-08-18T14:00:00Z", "duration": "0:52",
         "preview_image": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
         "num_comments": 1900, "tags": ["finance", "savings", "money"]},
    ],
    "music": [
        {"url": "https://youtube.com/watch?v=m1", "title": "Best Music Mix 2026 - Top Hits",
         "channel_name": "MusicMix", "views": 3400000, "likes": 125000,
         "date_posted": "2026-08-21T20:00:00Z", "duration": "1:02:30",
         "preview_image": "https://i.ytimg.com/vi/9bZkp7q19f0/maxresdefault.jpg",
         "num_comments": 8900, "tags": ["music", "mix", "hits"]},
        {"url": "https://youtube.com/watch?v=m2", "title": "Acoustic Cover - Popular Songs",
         "channel_name": "AcousticVibes", "views": 670000, "likes": 34000,
         "date_posted": "2026-08-20T16:00:00Z", "duration": "0:58",
         "preview_image": "https://i.ytimg.com/vi/JGwWNGJdvx8/maxresdefault.jpg",
         "num_comments": 1500, "tags": ["music", "cover", "acoustic"]},
    ],
    "comedy": [
        {"url": "https://youtube.com/watch?v=co1", "title": "Funniest Gaming Fails #5",
         "channel_name": "ComedyGaming", "views": 2200000, "likes": 110000,
         "date_posted": "2026-08-21T17:00:00Z", "duration": "10:15",
         "preview_image": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
         "num_comments": 7600, "tags": ["comedy", "gaming", "funny"]},
        {"url": "https://youtube.com/watch?v=co2", "title": "Stand Up Comedy Special",
         "channel_name": "ComedyCentral", "views": 890000, "likes": 42000,
         "date_posted": "2026-08-18T21:00:00Z", "duration": "0:55",
         "preview_image": "https://i.ytimg.com/vi/OPf0YbXqDm0/maxresdefault.jpg",
         "num_comments": 2300, "tags": ["comedy", "standup", "funny"]},
    ],
    "lifestyle": [
        {"url": "https://youtube.com/watch?v=l1", "title": "Day in My Life - Productivity Routine",
         "channel_name": "LifeWithMe", "views": 560000, "likes": 28000,
         "date_posted": "2026-08-21T08:00:00Z", "duration": "14:30",
         "preview_image": "https://i.ytimg.com/vi/kqtD5dpn9C8/maxresdefault.jpg",
         "num_comments": 1800, "tags": ["lifestyle", "vlog", "routine"]},
        {"url": "https://youtube.com/watch?v=l2", "title": "Morning Routine That Changed My Life",
         "channel_name": "BetterDays", "views": 1200000, "likes": 67000,
         "date_posted": "2026-08-20T07:00:00Z", "duration": "0:50",
         "preview_image": "https://i.ytimg.com/vi/60ItHLz5WEA/maxresdefault.jpg",
         "num_comments": 3400, "tags": ["lifestyle", "morning", "routine"]},
    ],
    "news": [
        {"url": "https://youtube.com/watch?v=n1", "title": "Breaking: Major Tech Announcement Today",
         "channel_name": "NewsNow", "views": 1800000, "likes": 45000,
         "date_posted": "2026-08-22T10:00:00Z", "duration": "8:20",
         "preview_image": "https://i.ytimg.com/vi/9bZkp7q19f0/maxresdefault.jpg",
         "num_comments": 5600, "tags": ["news", "tech", "breaking"]},
        {"url": "https://youtube.com/watch?v=n2", "title": "World News Summary - August 2026",
         "channel_name": "WorldNews", "views": 670000, "likes": 23000,
         "date_posted": "2026-08-21T22:00:00Z", "duration": "0:58",
         "preview_image": "https://i.ytimg.com/vi/JGwWNGJdvx8/maxresdefault.jpg",
         "num_comments": 1200, "tags": ["news", "world", "summary"]},
    ],
}


def format_number(n):
    if n is None:
        return "0"
    try:
        n = int(n)
    except (ValueError, TypeError):
        return str(n)
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def get_videos_for_stream(stream):
    """Get videos for a specific stream from cache, with sample data fallback.
    ALWAYS returns a non-empty list if the stream exists.
    Re-tags every video with the correct stream name to fix corrupted cache data."""
    # Try cache first
    cached = CACHE["videos"].get(stream, [])
    if cached:
        videos = copy.deepcopy(cached)
        # FORCE re-tag with correct stream — fixes corrupted cache from old mutation bug
        for v in videos:
            v["stream"] = stream
        return videos

    # Fallback to sample data
    sample = SAMPLE_VIDEOS.get(stream, [])
    if sample:
        videos = copy.deepcopy(sample)
        for v in videos:
            v["stream"] = stream
        return videos

    return []


def get_all_videos():
    """Get all videos from all streams, with sample data fallback.
    Re-tags every video with its correct stream from the cache key."""
    videos = []
    # Try cache first
    for s, vids in CACHE["videos"].items():
        for v in vids:
            v_copy = copy.deepcopy(v)
            v_copy["stream"] = s  # Force correct stream tag
            videos.append(v_copy)

    # If cache is empty, use sample data
    if not videos:
        for s, vids in SAMPLE_VIDEOS.items():
            for v in vids:
                v_copy = copy.deepcopy(v)
                v_copy["stream"] = s
                videos.append(v_copy)

    return videos


# ════════════════════════════════════════════════════════════
#  INIT
# ════════════════════════════════════════════════════════════
client = None
if API_KEY and API_KEY != "YOUR_API_KEY_HERE":
    client = BrightDataClient(API_KEY)
    print("[TrendPulse] BrightData client initialised")
else:
    print("[TrendPulse] No API key - DEMO mode with sample data")

analytics = AnalyticsEngine()
scraper = ScheduledScraper(client)

SCRAPER_INTERVAL = int(os.getenv("SCRAPER_INTERVAL_HOURS", "4"))
scraper.start(interval_hours=SCRAPER_INTERVAL)


# ═══════════════════════════════════════════════════════════
#  ROUTES
# ════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    stream_counts = {}
    for s, vids in CACHE.get("videos", {}).items():
        stream_counts[s] = len(vids)
    return jsonify({
        "status": "ok",
        "mode": "live" if client else "demo",
        "use_cached_data": USE_CACHED_DATA,
        "api_key_configured": bool(client),
        "cache_last_updated": CACHE.get("last_updated"),
        "cached_streams": stream_counts,
        "scraper_interval_hours": SCRAPER_INTERVAL,
    })


@app.route("/api/streams")
def streams():
    return jsonify({"streams": list(STREAM_KEYWORDS.keys())})


@app.route("/api/youtube/trending")
def youtube_trending():
    stream = request.args.get("stream", "").strip()
    content_type = request.args.get("type", "all").strip()

    print(f"  [API] trending: stream='{stream}', type='{content_type}'")

    # Get videos for this stream (or all)
    if stream:
        videos = get_videos_for_stream(stream)
    else:
        videos = get_all_videos()

    print(f"  [API] Found {len(videos)} videos for stream='{stream}'")

    # Separate shorts and videos
    regular, shorts = analytics.separate_shorts(videos)

    if content_type == "shorts":
        result = shorts
    elif content_type == "videos":
        result = regular
    else:
        result = videos

    # Sort by views (highest first)
    result = sorted(result, key=lambda v: int(v.get("views", 0) or 0), reverse=True)

    print(f"  [API] Returning {len(result)} items (regular={len(regular)}, shorts={len(shorts)})")

    return jsonify({
        "status": "ok",
        "data": result,
        "source": "live" if client else "demo",
        "count": len(result),
        "total_videos": len(regular),
        "total_shorts": len(shorts),
        "stream_filter": stream or "all",
        "cache_updated": CACHE.get("last_updated"),
    })


@app.route("/api/youtube/analytics")
def youtube_analytics():
    stream = request.args.get("stream", "").strip()

    print(f"  [API] analytics: stream='{stream}'")

    try:
        # Get videos for this stream (or all)
        if stream:
            videos = get_videos_for_stream(stream)
        else:
            videos = get_all_videos()

        print(f"  [API] Analytics for {len(videos)} videos")

        view_dist = analytics.view_distribution(videos)
        top_vids = analytics.top_videos(videos, limit=5)

        # Stream comparison (only when viewing All)
        stream_stats = []
        if not stream:
            for s in STREAM_KEYWORDS.keys():
                vids = CACHE["videos"].get(s, [])
                if not vids:
                    vids = SAMPLE_VIDEOS.get(s, [])
                if vids:
                    try:
                        total_views = 0
                        for v in vids:
                            try:
                                total_views += int(v.get("views", 0) or 0)
                            except (ValueError, TypeError):
                                pass
                        avg_views = total_views // len(vids) if vids else 0
                    except (ValueError, TypeError, ZeroDivisionError):
                        avg_views = 0
                    stream_stats.append({"stream": s, "avg_views": avg_views, "count": len(vids)})
            stream_stats.sort(key=lambda x: x["avg_views"], reverse=True)

        regular, shorts = analytics.separate_shorts(videos)

        result = {
            "status": "ok",
            "source": "live" if client else "demo",
            "stream": stream or "all",
            "total_videos": len(videos),
            "total_regular": len(regular),
            "total_shorts": len(shorts),
            "view_distribution": view_dist,
            "top_videos": top_vids,
            "stream_comparison": stream_stats,
            "cache_updated": CACHE.get("last_updated"),
        }
        print(f"  [API] Analytics OK: view_dist={[(d['label'],d['count']) for d in view_dist]}, top={len(top_vids)}")
        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"  [API] Analytics ERROR: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "view_distribution": [],
            "top_videos": [],
            "stream_comparison": [],
            "total_videos": 0,
            "total_regular": 0,
            "total_shorts": 0,
        }), 200  # Return 200 so frontend doesn't crash


@app.route("/api/youtube/refresh")
def manual_refresh():
    thread = threading.Thread(target=scraper.run_scrape, daemon=True)
    thread.start()
    return jsonify({
        "status": "ok",
        "message": "Refresh started in background. Check /api/health for updates."
    })


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    print(f"\n{'='*60}")
    print(f"  TrendPulse starting on http://localhost:{port}")
    print(f"  Mode: {'LIVE (BrightData)' if client else 'DEMO (sample data)'}")
    print(f"  Cached data: {'YES' if USE_CACHED_DATA else 'NO'}")
    print(f"  Scheduled scraper: every {SCRAPER_INTERVAL} hours")
    print(f"{'='*60}\n")
    app.run(host="0.0.0.0", port=port, debug=True)
