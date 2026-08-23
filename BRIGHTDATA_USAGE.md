# How BrightData Scraper Studio Is Used in TrendPulse

This document explains exactly how TrendPulse uses BrightData Scraper Studio to scrape YouTube trending data.

---

## 1. Which Scraper We Use

TrendPulse uses BrightData's **pre-built YouTube scraper**, not a custom AI-built scraper. Pre-built scrapers are maintained by BrightData â€” they handle proxy rotation, anti-bot bypassing, and parsing automatically. We never have to update parsing logic when YouTube changes their page structure.

**Scraper location in BrightData dashboard:**
- Go to Scrapers â†’ Scrapers Library â†’ search "youtube"
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

The `start_date` parameter ensures only videos from the last 7 days are returned â€” this is what makes TrendPulse show recent trends instead of old popular videos.

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

BrightData returns clean, structured JSON â€” no HTML parsing needed. Each video record contains:

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
2. **Retry on failure** â€” if the request fails (HTTP 429 rate limit, 500+ server error), wait and retry up to 3 times with increasing delay (5s, 10s, 15s)
3. **Sync-to-async fallback** â€” if a synchronous request times out (>60s), BrightData returns a `snapshot_id`. The code detects this and automatically switches to async polling mode
4. **Validate each record** â€”]™\žH™]\›™Y™XÛÜ™\ÈÚXÚÙY›Üˆ™\]Z\™YšY[È
\›]XšY]ÜØ
Kˆ™XÛÜ™ÈÚ]Z\ÜÚ[™ËÛ[šY[È\™H›YÙÙY\È˜œ›ÚÙ[ˆ‚Kˆ
Š”™K\ØÜ˜\Hœ›ÚÙ[ˆ™XÛÜ™ÊŠˆ8 %Û›HHœ›ÚÙ[ˆ™XÛÜ™ÉÈ[œ]T“È\™HÛÛXÝY[™™K\™\]Y\ÝY[ˆH™^ÞXÛB‹ˆ
Š”™]\›ˆÛX[™Y]JŠˆ8 %Y\ˆ[ÞXÛ\ËÛ›H˜[Y™XÛÜ™È\™H™]\›™Y‚ˆÈÈÈÛÛœÛÛHÝ]]\š[™ÈX[[™Î‚˜–ÒPSHœ›ÚÙ[ˆ™XÛÜ™ÌËÚ[™K\ØÜ˜\NˆÈšÙ^]ÛÜ™Žˆ™Ø[Z[™ÈYÚYÚÈŸB–ÒPSHÞXÛHNˆHœ›ÚÙ[ˆ™XÛÜ™Ë™]žZ[™Ë‹‹‚–ÒPSHÞXÛHŽˆ[MH™XÛÜ™È˜[Y8§$‚˜‚ˆÈÈÈ]]\œ›Üˆ[™[™Î‚’YˆHTHÙ^H\È[˜[Y
JKHÛÙH[[YYX][H˜Z\Ù\ÈHÛX\ˆ\œ›ÜŽ‚˜UURSQˆÚXÚÈ[Ý\ˆ”’QÒUWÐTWÒÑVH[ˆ™[ˆš[B˜‚‹KKB‚ˆÈÈ‹ˆØÚY[YØÜ˜\[™Â‚•HØÚY[YØÜ˜\\˜Û\ÜÈ[œÈ]]ÛX]XØ[N‚‚ŒKˆ
Š“ÛˆÝ\\
Šˆ8 %ØÜ˜\\È[LÝ™X[\È[[YYX][H
ÜˆØYÈœ›ÛHØXÚYÙ]KšœÛÛ˜YˆTÑWÐÐPÒQÑUO]YX
BŒ‹ˆ
Š‘]™\žHÝ\œÊŠˆ8 %™K\ØÜ˜\\È[Ý™X[\ÈÈ™Yœ™\Ú™[™]BŒËˆ
Š“Û]H™\XÙY
Šˆ8 %XXÚØÜ˜\HÝ™\Üš]\ÈHØXÚKÛÈ™[™ÈÝ^HÝ\œ™[ˆ
ŠØXÚHØ]™YÈš[JŠˆ8 %Y\ˆXXÚØÜ˜\K]H\ÈØ]™YÈØXÚYÙ]KšœÛÛ˜›ÜˆÜ™Y]\Ø]š[™È[ÙB‚ˆÈÈÝ™X[\ÈØÜ˜\Y‚‘XXÚÝ™X[HX\ÈÈHÙX\˜ÚÙ^]ÛÜ™Ù[ÈœšYÚ]N‚‚ŸÝ™X[HÙ^]ÛÜ™Ù[ÈœšYÚ]HŸKK_KK_ŸØ[Z[™È™Ø[Z[™ÈYÚYÚÈˆŸYXØ][Ûˆ]ÜšX[ˆŸXÚXÚ™]šY]ÈˆŸ]\ÚXÈ›]\ÚXÈšY[ÈˆŸÛÛYYH™[›žHˆŸš]™\ÜÈÛÜšÛÝ]ˆŸÛÛÚÚ[™Èœ™XÚ\HˆŸY™\Ý[H›ÙÈˆŸ™]ÜÈ˜œ™XZÚ[™È™]ÜÈˆŸš[˜[˜ÙHœÝØÚÈX\šÙ]ˆ‚‹KKB‚ˆÈÈËˆÜ™Y]TØ]š[™È[ÙB‚•È]›ÚYØ\Ý[™ÈœšYÚ]HÜ™Y]È\š[™È]™[ÜY[‚‚ŒKˆÙ]TÑWÐÐPÒQÑUOY˜[ÙX[ˆ™[˜[ˆÛ˜ÙHÚ]™X[THÙ^BŒ‹ˆ]H\ÈØ]™YÈØXÚYÙ]KšœÛÛ˜ŒËˆÙ]TÑWÐÐPÒQÑUO]YX™\Ý\ˆ\ØYÈœ›ÛHš[H8 %™\›ÈTHØ[Ë™\›ÈÜ™Y]È\ÙYKˆ]™[Ü[™XYÈœ™Y[B‹ˆÚ[ˆ™XYH›Üˆœ™\Ú]KÙ]˜XÚÈÈ˜[ÙX‚‹KKB‚ˆÈÈˆ]H›ØÙ\ÜÚ[™È\[[™B‚˜•\Ù\ˆÛXÚÜÈ‘Ø[Z[™Èˆš[\‚ˆ8¡¤Â‘›\ÚÈ˜XÚÙ[™™XÙZ]™\È™\]Y\Ýˆ8¡¤ÂÚXÚÈØXÚH›Üˆ™Ø[Z[™ÈˆÝ™X[Bˆ8¡¤Â’YˆØXÚH[\H8¡¤ˆÙ[™Ù^]ÛÜ™™Ø[Z[™ÈYÚYÚÈˆÈœšYÚ]HTBˆ8¡¤ÂœšYÚ]HØÜ˜\\È[ÝUX™HÙX\˜Ú™\Ý[Âˆ8¡¤Â”Ù[‹ZX[[™Îˆ˜[Y]H
È™K\ØÜ˜\Hœ›ÚÙ[ˆ™XÛÜ™Âˆ8¡¤Â“›Ü›X[^™HšY[˜[Y\È
[Ý]X™\ˆ8¡¤ˆÚ[›™[Û˜[YK]ËŠBˆ8¡¤Â‘š[\ˆÈ\ÝÈ^\ÈžH]WÜÜÝYˆ8¡¤Â”Ù\\˜]H[ÈšY[ÜÈ
ŒÊÊH[™ÚÜÈ
ŒÊBˆ8¡¤Â”ÛÜžHšY]ÜÈ
YÚ\Ýš\œÝ
Bˆ8¡¤Â”™]\›ˆ”ÓÓˆÈœ›Û[™ˆ8¡¤Â‘œ›Û[™™[™\œÈ™[™Ø\™È
È[˜[]XÜÈÚ\Â˜