# Running InfoShield (demo)

Two terminals: **backend** (Flask, port 5050) + **frontend** (Vite, port 5173), plus the
Chrome extension. Do the one-time setup once; then follow "Every run" for each demo.

## One-time setup
1. **Key:** copy `.env.example` to `.env` and set `GEMINI_API_KEY=...`
   (analysis = `gemini-3.5-flash`, verifier = `gemini-3.1-pro-preview`).
2. **Backend deps:** `.venv/Scripts/python.exe -m pip install -r backend/requirements.txt`
3. **Frontend deps:** `cd frontend && npm install`
4. **Load the extension:** Chrome → `chrome://extensions` → enable **Developer mode** →
   **Load unpacked** → select the `extension/` folder.

## Every run

**Terminal 1 — backend**
```
.venv/Scripts/python.exe backend/app.py
```
- Serves http://localhost:5050.
- On the **first** run it downloads the two local models and **warms the analysis cache in
  the background** (~1 min) using Gemini. Later runs reuse `backend/data/cache.json` → instant.
- Activation is auto-reset on every start, so the landing page always shows **ACTIVATE**.

**Terminal 2 — frontend**
```
cd frontend
npm run dev
```
- Serves http://localhost:5173.

**Demo (browser)**
1. Open http://localhost:5173/ → click **ACTIVATE** (keep the localhost target) → save.
2. Open http://localhost:5173/social?bare=1 and refresh.
3. The mixed feed loads (normal / manipulation / hate / autoplaying video); the extension
   injects InfoShield overlays on the flagged posts.

## Check it's working
```
curl http://localhost:5050/health        # llm_provider=gemini, verifier_model, cached_posts
curl http://localhost:5050/feed           # posts with classification.kind = hate|manipulation
```
- Video plays at http://localhost:5050/media/video.mp4
- `/health` `cached_posts` should equal `posts` once the warm finishes.

## Refresh the analysis (only after you change prompts/models/posts)
The cache is reused for speed. To recompute from scratch:
```
curl -X POST http://localhost:5050/rebuild-cache
# or, offline:
.venv/Scripts/python.exe backend/scripts/build_cache.py
```
(Changing the post set or bumping `CACHE_VERSION` auto-invalidates the old cache on the next start.)
