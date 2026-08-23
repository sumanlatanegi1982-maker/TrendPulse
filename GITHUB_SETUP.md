# 🚀 GitHub Setup Guide — Step-by-Step

Follow these exact steps to push TrendPulse to GitHub for your hackathon submission.

---

## Step 1: Create a GitHub Account (if you don't have one)

1. Go to https://github.com/signup
2. Create an account with your email
3. Verify your email address

---

## Step 2: Create a New Repository

1. Go to https://github.com/new
2. Fill in the details:
   - **Repository name:** `TrendPulse`
   - **Description:** `YouTube Trend Analytics — powered by Bright Data Scraper Studio | Into the Scrape-Verse Hackathon`
   - **Visibility:** ⬜ **Public** (MUST be public for hackathon submission)
   - **Initialize this repository with:**
     - ✅ Add a README file (uncheck — we already have one)
     - ⬜ .gitignore (uncheck — we already have one)
     - ⬜ license (uncheck — we already have MIT)
3. Click **"Create repository"**

---

## Step 3: Install Git on Your Computer

### Windows:
1. Download from https://git-scm.com/download/win
2. Run the installer (keep default settings)
3. Open **Git Bash** (search in Start menu)

### Mac:
```bash
# If you have Homebrew:
brew install git

# Or download from:
# https://git-scm.com/download/mac
```

### Linux:
```bash
sudo apt install git    # Ubuntu/Debian
sudo dnf install git    # Fedora
```

### Verify installation:
```bash
git --version
```

---

## Step 4: Configure Git (one-time setup)

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

Use the same email you used for GitHub.

---

## Step 5: Authenticate with GitHub

### Option A: Personal Access Token (recommended)

1. Go to https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Set:
   - **Note:** `TrendPulse`
   - **Expiration:** 30 days
   - **Scopes:** ✅ `repo` (full repository access)
4. Click **"Generate token"**
5. **COPY the token** — you won't see it again!

### Option B: GitHub CLI

```bash
# Install GitHub CLI
# Windows: winget install GitHub.cli
# Mac: brew install gh
# Linux: sudo apt install gh

gh auth login
# Follow the prompts
```

---

## Step 6: Create Your Local Project Folder

```bash
# Create the project folder
mkdir TrendPulse
cd TrendPulse

# Initialize git
git init
```

---

## Step 7: Copy All Project Files

Copy ALL the following files into the `TrendPulse` folder:

```
TrendPulse/
├── app.py                          ← Flask backend
├── index.html                      ← Frontend UI
├── requirements.txt                ← Python dependencies
├── README.md                       ← Main documentation
├── BRIGHTDATA_USAGE.md             ← Bright Data usage explanation
├── DEMO_VIDEO_SCRIPT.md            ← Demo video script
├── demo_voice_narration.txt        ← Voice narration for demo
├── example_structured_output.json  ← Example Bright Data output
├── ARCHITECTURE.html               ← Visual architecture diagram
├── .env.example                    ← API key template
└── .gitignore                      ← Git ignore rules
```

### Important files to NOT upload:
- `.env` — Contains your real API key (the .gitignore will block it)
- `cached_data.json` — Contains scraped data (auto-generated, .gitignore blocks it)
- `__pycache__/` — Python cache (auto-generated, .gitignore blocks it)

---

## Step 8: Verify .gitignore Is Correct

Open the `.gitignore` file and make sure it contains:

```gitignore
# Environment variables (SECRETS!)
.env

# Cached data (auto-generated)
cached_data.json

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Virtual environments
venv/
env/
.venv/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

---

## Step 9: Add and Commit Files

```bash
# Check what files will be uploaded
git status

# Add all files (respecting .gitignore)
git add .

# Verify .env is NOT included
git status
# You should NOT see .env in the list!
# If you see .env, STOP — your .gitignore is wrong

# Commit
git commit -m "Initial commit: TrendPulse YouTube Trend Analytics

- Flask backend with Bright Data Scraper Studio integration
- Self-healing scraper with field validation
- Scheduled auto-scraping (daily 2 AM)
- Credit-saving cache mode
- 10 content streams, 7-day recency filter
- Analytics dashboard with view distribution, top 5, stream comparison
- YouTube-only (videos + shorts)"
```

---

## Step 10: Connect to GitHub and Push

```bash
# Replace YOUR_USERNAME with your actual GitHub username
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/TrendPulse.git
git push -u origin main
```

When prompted:
- **Username:** Your GitHub username
- **Password:** Paste your Personal Access Token (from Step 5A) — NOT your GitHub password!

If you used GitHub CLI (Step 5B), authentication is automatic.

---

## Step 11: Verify on GitHub

1. Go to https://github.com/YOUR_USERNAME/TrendPulse
2. You should see all your files listed
3. Click on `README.md` — it should render with full formatting
4. Click on `app.py` — you should see the code with syntax highlighting
5. Verify `.env` is NOT visible in the repository (check file list)

---

## Step 12: Record Your Demo Video

1. Run the app:
   ```bash
   cd TrendPulse
   pip install -r requirements.txt
   python app.py
   ```

2. Open http://localhost:5000

3. Record your screen using:
   - **OBS Studio** (free, powerful): https://obsproject.com/
   - **Loom** (easy, free tier): https://www.loom.com/
   - **Windows Game Bar** (Win + G): built into Windows
   - **QuickTime** (Mac): File → New Screen Recording

4. Follow the script in `DEMO_VIDEO_SCRIPT.md`

5. Upload the video to:
   - YouTube (unlisted is fine)
   - Google Drive (shareable link)
   - Loom (auto-hosted)

6. Get the video link and add it to your README.md:
   ```bash
   # Edit README.md
   # Find the "Demo Video" section
   # Replace [Add your YouTube/demo video link here] with your actual link
   ```

---

## Step 13: Update README with Demo Video Link

```bash
# Edit README.md and add your demo video link
# Then commit and push the update:
git add README.md
git commit -m "Add demo video link"
git push
```

---

## Step 14: Final Checklist

Before submitting, verify ALL of these:

- [ ] Repository is **PUBLIC** (not private)
- [ ] `app.py` is uploaded
- [ ] `index.html` is uploaded
- [ ] `requirements.txt` is uploaded
- [ ] `README.md` is uploaded and renders correctly
- [ ] `example_structured_output.json` is uploaded
- [ ] `BRIGHTDATA_USAGE.md` is uploaded
- [ ] `.env.example` is uploaded
- [ ] `.gitignore` is uploaded
- [ ] `ARCHITECTURE.html` is uploaded
- [ ] Demo video is recorded and link is in README
- [ ] `.env` file is NOT in the repository (check!)
- [ ] `cached_data.json` is NOT in the repository

---

## Troubleshooting

### "Permission denied" or "Authentication failed"
```bash
# Check your remote URL
git remote -v

# If wrong, remove and re-add:
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/TrendPulse.git

# Push again — use your Personal Access Token as password
git push -u origin main
```

### "fatal: not a git repository"
```bash
# You forgot to run git init — make sure you're in the right folder:
cd TrendPulse
git init
```

### "README.md is not rendering"
- Make sure it's named exactly `README.md` (uppercase, .md extension)
- GitHub auto-renders any file named README.md

### ".env file got uploaded!"
```bash
# Remove it from git tracking (keeps local copy):
git rm --cached .env
git commit -m "Remove .env from tracking"
git push

# Verify it's in .gitignore
echo ".env" >> .gitignore
```

### Large file errors
```bash
# If cached_data.json is too large:
# Make sure it's in .gitignore and remove from tracking:
git rm --cached cached_data.json
git commit -m "Remove cached data from repo"
git push
```

---

## Quick Command Summary (Copy & Paste)

```bash
# 1. Create folder and init
mkdir TrendPulse && cd TrendPulse
git init

# 2. Copy all files into this folder manually

# 3. Add and commit
git add .
git commit -m "Initial commit: TrendPulse YouTube Trend Analytics"

# 4. Connect to GitHub (replace YOUR_USERNAME!)
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/TrendPulse.git
git push -u origin main
```

---

## What Your GitHub Repo Should Look Like

When you're done, your repository at `https://github.com/YOUR_USERNAME/TrendPulse` should have:

```
📁 TrendPulse/
   📄 app.py                          — Flask backend (main code)
   📄 index.html                      — Frontend UI
   📄 requirements.txt                — Python dependencies
   📄 README.md                       — Full documentation (renders on GitHub)
   📄 BRIGHTDATA_USAGE.md             — Bright Data explanation
   📄 ARCHITECTURE.html               — Visual architecture diagram
   📄 DEMO_VIDEO_SCRIPT.md            — Demo video script
   📄 demo_voice_narration.txt        — Voice narration
   📄 example_structured_output.json  — Example Bright Data output
   📄 .env.example                    — API key template
   📄 .gitignore                      — Git ignore rules
```

That's it! Your repo is ready for hackathon submission. 🎉
