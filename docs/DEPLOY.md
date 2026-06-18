# Deploying InfoShield for remote testers

Goal: hand testers **one link** — the social page, already activated — and let
them test the "extension" with the on-page **InfoShield Insights** toggle, no
install required.

How it works: a Chrome extension can't be shared as a link, so in the deployed
build the **website itself** renders the per-post InfoShield overlays (gated
behind `VITE_HOSTED=1`). Your **local** workflow is unchanged — without that flag
the real extension drives the overlays exactly as before.

Two pieces to host:
- **Backend** → Hugging Face Space (Docker). Serves `/feed` from the prebuilt
  cache and runs the live `/analyze-text` + `/rephrase`.
- **Frontend** → Vercel / Netlify / Cloudflare Pages (static). Points at the Space.

---

## 1. Backend → Hugging Face Space (Docker)

1. Create a Space: https://huggingface.co/new-space → **SDK: Docker** → blank.
2. In the Space's **README.md**, put this frontmatter at the very top (this is how
   HF knows the SDK + port):
   ```
   ---
   title: InfoShield Backend
   emoji: 🛡️
   colorFrom: purple
   colorTo: indigo
   sdk: docker
   app_port: 7860
   pinned: false
   ---
   ```
3. Add your key as a **secret** (Space → Settings → *Variables and secrets* →
   *New secret*): name `GEMINI_API_KEY`, value = your Gemini key. (Never commit
   it — `.env` is git-ignored.) If you use Groq instead, also add `GROQ_API_KEY`
   and set the variable `INFOSHIELD_LLM_PROVIDER=groq`.
4. Push this repo to the Space. The root `Dockerfile` + `.dockerignore` build a
   slim image that only ships `backend/` (incl. the committed `data/cache.json`):
   ```bash
   git remote add space https://huggingface.co/spaces/<user>/<space-name>
   git push space main
   ```
   (Authenticate with an HF token that has *write* access when prompted.)
5. Wait for the build, then the **first boot downloads the local ML models
   (~1–2 min)**. Verify:
   - `https://<user>-<space-name>.hf.space/health` → JSON with `"status":"ok"`
   - `https://<user>-<space-name>.hf.space/feed` → posts with `classification`

That `https://<user>-<space-name>.hf.space` URL is your **API base** for step 2.

> Free Spaces sleep after inactivity; the first request after a sleep takes
> ~1–2 min (models reload), then it's fast. The feed/analysis is instant
> regardless (prebuilt cache) — only the live draft "Check" needs the models.

---

## 2. Frontend → Vercel / Netlify / Cloudflare Pages (static)

Import this repo as a new project with:
- **Root directory:** `frontend`
- **Build command:** `npm run build`
- **Output directory:** `dist`
- **Environment variables:**
  - `VITE_HOSTED` = `1`
  - `VITE_API_BASE` = `https://<user>-<space-name>.hf.space`

Deploy. Then give testers:

```
https://<your-frontend-domain>/social
```

It loads pre-activated; testers flip the **InfoShield Insights** toggle to show/
hide the analysis, expand any flagged post for the explanation, and use
**Check with InfoShield** / **Suggest a respectful alternative** on the composer.

---

## Local development — unchanged

Don't set `VITE_HOSTED` / `VITE_API_BASE` locally. With them unset, `npm run dev`
+ `python backend/app.py` + the loaded extension behave exactly as before
(landing-page activation, extension-injected overlays). See `RUN.md`.
