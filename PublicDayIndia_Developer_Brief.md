# PUBLIC DAY INDIA — News Video Automation System
## Developer Requirements Brief

**Client:** Public Day India (News Channel)
**Location:** Devbhumi Dwarka, Gujarat, India
**Primary language of content:** Gujarati
**Date:** July 2026

---

## 1. WHAT WE WANT BUILT

A self-hosted web application where our reporters enter a news script and upload a video or photo, and the system automatically:

1. Generates a Gujarati voice-over from the script
2. Renders a news-style video (logo, lower-third headline, synced subtitles, scrolling ticker)
3. Generates caption and hashtags
4. Publishes to Instagram, Facebook, and YouTube Shorts
5. Shows status and results on a dashboard

**Non-negotiable:** The system must be delivered complete and tested end-to-end. No partially working modules.

---

## 2. OPERATING CONTEXT (confirmed by client)

| Item | Detail |
|---|---|
| Server | Single Windows PC at our office (high-spec machine) |
| Network | Static public IP available |
| Access method | Direct IP address in browser, protected by login ID + password. **No domain purchase required.** |
| Daily volume | 8–10 posts per day maximum |
| Concurrent users | 2–3 reporters |
| Social accounts | Instagram and Facebook pages already created (small follower base, ~50–60) |
| Cloud/VPS | Not required — everything runs on the office PC |

---

## 3. TECH STACK (suggested — developer may propose alternatives with reasoning)

- **Backend:** Python 3.11+ with Flask
- **Video rendering:** FFmpeg via Python subprocess
- **Text-to-Speech:** Edge TTS (free, supports Gujarati). Build with a provider abstraction so ElevenLabs or another paid TTS can be swapped in later via config.
- **Subtitle timing:** Prefer TTS-provided word/character timestamps. Whisper as fallback.
- **Caption/hashtag generation:** LLM API (Claude or equivalent), with manual edit option in UI
- **Social publishing:** Meta Graph API, YouTube Data API v3
- **Database:** SQLite (adequate for this volume)
- **Frontend:** HTML + Tailwind CSS, must be mobile-responsive (reporters will post from phones in the field)
- **Font:** Noto Sans Gujarati must be bundled and verified for correct rendering

---

## 4. WEB APPLICATION — REQUIRED FEATURES

### 4.1 Authentication
- Login with username and password
- Two roles: **Admin** (owner) and **Reporter**
- Reporters can create posts; only Admin can approve and publish
- Passwords hashed (bcrypt or equivalent) — never stored in plain text
- Session timeout
- Rate limiting on login endpoint (brute-force protection)

### 4.2 Create Post Form
- Headline field (Gujarati)
- Full script / news text (Gujarati)
- Media upload: video or photo, multiple files supported
- Voice selection dropdown
- Platform checkboxes: Instagram / Facebook / YouTube Shorts
- Separate field for ticker text
- Publish immediately OR schedule for a specific time

### 4.3 Preview and Approval — MANDATORY
- After rendering, the video preview appears on the dashboard
- Post publishes **only** after Admin clicks Approve
- Reject option that returns the item for re-rendering with edits
- This step must not be skipped or made optional. A wrong post reaching the public damages channel credibility.

### 4.4 Dashboard
- List of all posts: date, headline, status
- Status values: Draft / Rendering / Ready for Approval / Posted / Failed
- Per-platform success or failure indicator
- Direct links to published posts
- Retry button for failed publishes
- Basic engagement metrics (views, likes) pulled from platform APIs where available

---

## 5. VIDEO RENDER ENGINE — DETAILED SPECIFICATION

### Input
Gujarati script text, raw video or photo (any resolution or orientation), headline text, ticker text.

### Processing pipeline

**Step 1 — Voice-over**
Generate Gujarati voice-over as MP3. Measure exact duration.

**Step 2 — Match media duration to voice-over**
- Video shorter than voice-over → loop it
- Video longer → trim to voice-over length
- Photo input → generate video with slow zoom (Ken Burns effect) for voice-over duration

**Step 3 — Aspect ratio handling**
- Reels/Shorts output: 1080×1920 vertical
- Feed output: 1080×1080 square
- Horizontal source video must be fitted over a blurred background — do not center-crop in a way that cuts off heads or key subjects

**Step 4 — Overlay layers**

| Layer | Position | Notes |
|---|---|---|
| Channel logo | Top left | Transparent PNG |
| Date / LIVE badge | Top right | |
| Lower-third headline | Lower area | Gujarati, must render correctly |
| Subtitles | Lower-center | Synced to voice-over, Gujarati |
| Scrolling ticker | Bottom edge | |

**Step 5 — Audio mix**
Original ambient audio from source video at approximately 15% volume, voice-over at full volume on top. Normalize final output.

**Step 6 — Export**
- `reel.mp4` — 1080×1920 for Instagram Reels, Facebook Reels, YouTube Shorts
- `feed.mp4` — 1080×1080 for Instagram and Facebook feed
- H.264 video, AAC audio, encoded to current Instagram specifications

### Performance target
Under 3 minutes from submission to preview-ready video. Progress indicator visible in the UI during rendering.

---

## 6. BRANDING ASSETS

Client will provide: logo PNG (transparent), lower-third template, intro clip, outro clip, color scheme.

Developer must structure these in a clearly documented `assets/` folder so the client can replace any of them later without code changes.

---

## 7. SOCIAL MEDIA INTEGRATION

### 7.1 Meta (Instagram + Facebook)
- Instagram account must be Business type and linked to the Facebook Page
- Meta Developer App creation and configuration
- Required permissions: `instagram_content_publish`, `pages_manage_posts`, `pages_read_engagement`
- Long-lived Page Access Token with **automatic refresh logic** — the system must not silently stop working when a token expires
- **Important:** Meta App Review typically takes 1–2 weeks. Begin this process on day one, in parallel with development.

### 7.2 YouTube Shorts
- YouTube Data API v3 with OAuth
- Auto-populate title, description, and tags

### 7.3 Caption and Hashtags
- Generated from the script automatically
- Platform-appropriate length for each network
- Include local hashtags: #દ્વારકા #દેવભૂમિદ્વારકા #ગુજરાત #PublicDayIndia plus story-relevant tags
- Caption must be editable in the UI before approval

---

## 8. SECURITY REQUIREMENTS

The application will be exposed on a public static IP. The following are mandatory:

1. **HTTPS.** Self-signed is not acceptable for daily use — use a free certificate. If the client prefers not to buy a domain, propose the simplest workable option and explain the tradeoff clearly.
2. Windows Firewall configured to expose only the required port
3. Password hashing (bcrypt or equivalent)
4. Rate limiting on authentication endpoints
5. All API keys and secrets in a `.env` file — never hardcoded in source
6. Upload validation: file type whitelist and size limits
7. Basic access logging (who posted what, when)

---

## 9. ERROR HANDLING

- FFmpeg failure → clear error message on dashboard plus entry in log file
- Social API failure → automatic retry (3 attempts with backoff), then flag on dashboard
- Token expiry → auto-refresh; if refresh fails, alert the Admin
- Power loss or PC restart → queued jobs resume automatically on startup
- Disk space management → auto-cleanup of rendered files older than 30 days
- All errors written to a timestamped log file

---

## 10. DELIVERABLES

### Code
- Complete, commented source code
- `requirements.txt`
- `.env.example` with all required variables documented

### Installation
- Step-by-step Windows setup guide (plain English)
- Automated installer or batch script strongly preferred
- Instructions covering Python, FFmpeg, and font installation
- Windows Task Scheduler configuration so the system starts automatically on boot

### Configuration guides
- Meta App setup, step by step, with screenshots
- YouTube API setup, step by step
- Token generation and renewal procedure

### Testing — delivery is not complete without this
Minimum 10 end-to-end test posts covering:
- Long script with short source video
- Short script with long source video
- Photo-only input
- Horizontal source video
- Vertical source video

For each, provide evidence of successful publication to each platform. Additionally verify:
- Subtitle timing accuracy on Gujarati audio
- Gujarati font renders correctly with no broken or clipped characters
- Failure paths behave as specified in section 9

### Documentation
- Reporter user manual (Gujarati preferred)
- Admin manual
- Troubleshooting guide covering common failures and fixes

### Handover

- Live demo and training session over screen share
- Minimum 30 days of bug-fix support after delivery
- Full code ownership transfers to the client

---

## 11. SUGGESTED PHASING

**Phase 1 — Render engine.** Script in, finished video out. No social integration required. *Milestone: reel.mp4 generated locally from a script and source clip.*

**Phase 2 — Web application.** Login, upload form, database, dashboard, preview, approval workflow. *Milestone: a post can be created in the browser and previewed.*

**Phase 3 — Social publishing.** Meta and YouTube integration. Run Meta App Review in parallel starting from Phase 1. *Milestone: clicking Approve publishes to all three platforms.*

**Phase 4 — Hardening.** Scheduling, analytics, error handling, security, full test suite, documentation. *Milestone: 10 test posts passed, documentation complete.*

Demo required at the end of each phase.

---

## 12. QUESTIONS FOR THE DEVELOPER TO ANSWER IN THEIR PROPOSAL

1. Total cost, broken down by phase
2. Timeline per phase
3. Any recurring monthly costs (APIs, services) — itemized, with free alternatives noted where they exist
4. Which TTS option you recommend for Gujarati and why
5. Your recommended approach for HTTPS given the client's preference to avoid buying a domain
6. Payment schedule and what triggers each milestone payment
7. What is covered under the 30-day support period and what would be billed separately

---

## 13. CLIENT EXPECTATIONS

- Delivered complete and tested — not partially working
- Demo at each phase completion
- Gujarati text rendering verified everywhere it appears
- Code written to be readable and maintainable by another developer later
- Any paid service must be flagged and approved by the client before it is used
