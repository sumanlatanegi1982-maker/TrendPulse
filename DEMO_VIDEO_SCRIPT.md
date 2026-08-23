# Demo Video Script — TrendPulse
# Record a 2-3 minute video following this outline.

## 1. INTRO (15 seconds)
"Hi, I built TrendPulse — a YouTube trend analytics website that helps content creators find what's trending in their stream, powered by BrightData Scraper Studio."

## 2. SHOW THE WEBSITE (45 seconds)
- Open http://localhost:5000 in browser
- Show the homepage with red theme (YouTube branding)
- Click through stream filters: Gaming, Education, Tech
- Show that each stream shows DIFFERENT videos (not mixed)
- Click "Shorts" tab — show it filters to short videos only
- Click "Videos" tab — show long-form videos only
- Toggle dark/light theme (sun/moon button)

## 3. SHOW ANALYTICS (30 seconds)
- Scroll to analytics section
- Show View Distribution bar chart
- Show Top 5 Trending Videos list
- Show Stream Comparison chart
- Click a different stream — show analytics update

## 4. SHOW BRIGHTDATA INTEGRATION (45 seconds)
- Open terminal showing the app running
- Point out the console output:
  - "[SCHEDULED] Starting trend scrape"
  - "[HEAL] Cycle 1: all records valid ✓"
  - "[CACHE] Saved 23 videos to cached_data.json"
- Open BrightData dashboard (brightdata.com/cp/scrapers)
- Show the "Youtube - Videos posts - discover by keyword" scraper
- Show the free credits counter (3,167/5,000)

## 5. SHOW SELF-HEALING (20 seconds)
- In terminal, point out the [HEAL] log lines
- Explain: "If BrightData returns broken records with missing fields, the self-healing system re-scrapes only those broken records up to 3 times"

## 6. SHOW CREDIT-SAVING MODE (15 seconds)
- Open .env file
- Show USE_CACHED_DATA=true
- Explain: "I scraped once, saved the data, and now I develop without wasting credits"

## 7. CLOSING (10 seconds)
"TrendPulse — YouTube trend analytics with self-healing scrapers, scheduled auto-refresh, and credit-saving mode. Built with BrightData Scraper Studio for Into the Scrape-Verse."

## TOTAL: ~3 minutes

## Recording Tips
- Use OBS Studio or screen recording (Cmd+Shift+5 on Mac)
- Record in 1080p minimum
- Speak clearly, not too fast
- Show the terminal alongside the browser when explaining BrightData
- Keep it under 3 minutes
