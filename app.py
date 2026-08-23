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

# ════════════════════════════════════════════════════════════
#  BRIGHTDATA CONFIG
# ════════════════════════════════════════════════════════════
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
