# Milo - AI Physique & Health Coach

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Anthropic](https://img.shields.io/badge/Claude_AI-Anthropic-191919?style=flat-square&logo=anthropic&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot_API-26A5E4?style=flat-square&logo=telegram&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3FCF8E?style=flat-square&logo=supabase&logoColor=white)
![Railway](https://img.shields.io/badge/Railway-Live-0B0D0E?style=flat-square&logo=railway&logoColor=white)
![Whoop](https://img.shields.io/badge/Whoop-OAuth_2.0-44D62C?style=flat-square)
![Withings](https://img.shields.io/badge/Withings-OAuth_2.0-00B2A9?style=flat-square)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat-square)

Milo is an AI health coaching agent that lives inside Telegram. It connects to your Whoop strap and Withings scale, pulls real biometric data, and delivers personalized coaching across training, sleep, nutrition, and lifestyle through natural conversation powered by Claude.

The name comes from **Milo of Croton**, an ancient Greek wrestler who built legendary strength by carrying a calf on his shoulders every single day. As the calf grew into a bull, so did Milo's strength. That's progressive overload. Small, consistent effort compounding into extraordinary results. It's the core philosophy behind everything this bot does.

I built Milo because I wanted a coach that actually knows my numbers. Not a chatbot that gives generic advice, but an agent that wakes up, checks my recovery score, looks at my sleep data, sees what I weigh this morning, and tells me exactly how to train today. That's what this is.

## Why It's an Agent, Not a Chatbot

There's a real difference between a chatbot and an agent, and Milo sits firmly on the agent side.

A chatbot responds when you talk to it. Milo does that too. You can ask it anything about training, nutrition, sleep, or lifestyle and it'll coach you with real data backing every recommendation. But what makes it an agent is everything it does when you're *not* talking to it.

Milo runs scheduled jobs that proactively reach out. It refreshes your Whoop and Withings tokens in the background so your data is always fresh. It has a morning check-in system that pulls your overnight recovery, looks at your HRV trend, checks your body weight from this morning's weigh-in, and generates a personalized training recommendation before you've even opened the app. It sends weekly progress summaries that aggregate your data across the entire week (sleep averages, body composition trends, training volume) and tells you what's working and what needs to change.

Under the hood, it's built around an **agent harness** pattern. There's a system prompt that defines Milo's coaching philosophy and boundaries, a context injection layer that assembles real-time data from multiple APIs into structured blocks, and a security layer that enforces topic scope, blocks prompt injection attempts, and rate-limits abuse. Claude doesn't just answer questions. It reasons over your actual biometric data to produce coaching that's specific to *you*, right now, today.

## Hybrid Coaching Engine (v1)

Milo uses a **hybrid deterministic + AI** architecture for coaching decisions. This is the core of what makes it reliable.

**Deterministic state layer.** Recovery status, nutrition targets, and training guidance are computed from raw biometric data using evidence-based thresholds and formulas. Recovery evaluation pulls 7-30 days of Whoop snapshots and scores HRV trend, resting heart rate trend, sleep duration, and sleep efficiency into a composite tier (green/yellow/red). Nutrition state computes TDEE, calorie targets, and protein targets from user profile and body composition using Mifflin-St Jeor + activity multipliers. Training guidance adjusts volume and intensity based on recovery tier and workout history.

**AI reasoning layer.** Claude receives the deterministic state as constraints and reasons flexibly within those bounds. It won't contradict calorie targets or suggest hard training on a red recovery day. But it can explain *why* you should deload, connect your poor sleep to your elevated resting heart rate, and adapt its tone to how you're feeling. The deterministic layer ensures consistency; the AI layer ensures the coaching feels human.

**Research-backed logic.** The coaching rules are grounded in ~12,000 lines of research documentation covering TDEE and calorie cycling, volume progression and periodization, autoregulation and deload protocols, recovery science and nocebo effects, ad libitum dietary approaches, sleep hygiene, protein phasing, and programming principles.

## The Four Coaching Pillars

Milo coaches across four domains, and every recommendation ties back to your real data when it's available.

**Resistance Training.** Progressive overload is the foundation. Milo tracks your lifts, monitors volume and intensity trends, recommends when to push and when to deload based on your Whoop recovery, and designs programming around exercise selection, sets, reps, and load management. If your recovery is in the red, it'll tell you to back off. If you're green-lit with a 90% recovery, it'll push you.

**Sleep.** Sleep is the single most important recovery tool, and Milo treats it that way. It pulls Whoop sleep data (duration, efficiency, disturbances, sleep stages) and uses it to guide recommendations on sleep hygiene, schedule consistency, temperature, light exposure, and pre-bed routines. It connects sleep quality directly to training performance so you can see the relationship between a bad night and a bad session.

**Nutrition.** Body composition focused coaching. Protein is the priority (0.8-1g per pound of bodyweight minimum), with calorie awareness without obsessive tracking, and meal timing guidance around training sessions. Milo uses your Withings weight and body fat trends to adjust recommendations. If you're cutting and weight is stalling, it'll have something to say about that.

**Lifestyle.** This is the connective tissue between training and results. HRV trend analysis reveals how stress, travel, alcohol, and daily habits affect your recovery. Milo coaches on hydration, sunlight exposure, movement outside of training, and finding the right balance between training intensity and life demands.

## Tech Stack and Architecture

```
+-----------------------------------------------------+
|                   Telegram User                      |
|              (commands + free-form chat)              |
+------------------------+----------------------------+
                         |
                         v
+------------------------------------------------------+
|                    bot.py                             |
|         Telegram polling + aiohttp web server        |
|         (runs concurrently via asyncio)              |
+------+----------+----------+------------------------+
       |          |          |
       v          v          v
+----------+ +----------+ +---------------------------+
| handlers | | OAuth    | | scheduler.py              |
| .py      | | server   | | APScheduler cron jobs     |
|          | | (aiohttp)| | - morning check-in (7 AM) |
| /start   | |          | | - weekly summary (Sun 6PM)|
| /connect | | /auth/   | | - Whoop refresh (50 min)  |
| /stats   | |  whoop/  | | - Withings refresh (2.5hr)|
| /sleep   | |  callback| | - startup token refresh   |
| /strain  | | /auth/   | |                           |
| /workout | |  withings| |                           |
| /body    | |  /callback|                            |
| /log     | +----------+ +---------------------------+
| /profile |
| /progress|
| /help    |
| chat msg |
+------+---+
       |
       v
+------------------------------------------------------+
|              Coaching State Engine                    |
|                                                      |
|  coaching/recovery.py  - HRV/RHR/sleep -> tier       |
|  coaching/nutrition.py - TDEE/macros -> targets       |
|  coaching/training.py  - volume/intensity guidance    |
|  coaching/progress.py  - trend tracking               |
+------+-----------------------------------------------+
       |
       v
+------------------------------------------------------+
|                   core/database.py                   |
|            Supabase (PostgreSQL) via REST API         |
|                                                      |
|  users | whoop_tokens | withings_tokens | workouts   |
|  whoop_snapshots | body_metrics | user_profiles      |
|  nutrition_states | recovery_daily_status             |
+------+-----------------------------------------------+
       |
       v
+------------------------------------------------------+
|                     agent.py                         |
|              Claude AI Coaching Brain                 |
|                                                      |
|  System prompt (coaching/prompts.py)                 |
|  + Deterministic state constraints                   |
|  + User context injection (Whoop + Withings + lifts) |
|  + Security layer (rate limit, topic scope, anti-PII)|
|  -> Claude API call (model configurable via MILO_MODEL)|
|  -> Personalized coaching response                   |
+------------------------------------------------------+
```

| Component | Technology | Why |
|-----------|-----------|-----|
| Runtime | Python 3.11+ | Async-native with a rich ecosystem for API integrations |
| AI Engine | Anthropic Claude (configurable model via `MILO_MODEL`) | Flexible model selection while keeping coaching quality |
| Chat Interface | Telegram (python-telegram-bot) | Ubiquitous, solid bot API, inline keyboards work great for OAuth flows |
| Database | Supabase (PostgreSQL) | Managed Postgres with a REST API and a generous free tier |
| Deployment | Railway | Git-push deploys, persistent containers, built-in health checks |
| Wearable Data | Whoop API v2 (OAuth 2.0) | Recovery, HRV, resting HR, sleep metrics, strain |
| Body Composition | Withings API (OAuth 2.0 + HMAC-SHA256) | Weight, body fat %, fat mass from smart scales |
| Scheduling | APScheduler | Async-native cron jobs for proactive coaching and token refresh |
| HTTP | httpx + aiohttp | httpx for external API calls with retry/transport, aiohttp for the OAuth callback server |

## Key Engineering Decisions

**Hybrid deterministic + AI coaching.** Rather than letting Claude make all coaching decisions freeform, Milo computes recovery tiers, nutrition targets, and training guidance deterministically from raw data. Claude receives these as constraints it must respect. This gives you reproducible, evidence-based coaching with the conversational flexibility of an LLM.

**Concurrent polling + web server.** Telegram bots typically use either polling or webhooks. Milo uses polling for simplicity (no SSL cert management, works locally for development) but also needs to receive OAuth callbacks from Whoop and Withings. So I run the Telegram polling loop and an aiohttp web server concurrently in the same asyncio event loop. One process, two interfaces.

**Raw HTTP for Supabase token storage.** The supabase-py client works well for reads, but during the OAuth callback flow I hit intermittent DNS resolution failures on Railway's internal network. Rather than fight the client library, I wrote `store_whoop_tokens()` and `store_withings_tokens()` using raw httpx with `HTTPTransport(retries=3)` against the Supabase REST API directly. More control, more reliable.

**In-memory OAuth state store.** OAuth state tokens live in a Python dict with 10-minute expiry instead of a database table. This eliminates a Supabase round-trip during the most latency-sensitive part of the flow (the redirect). The tradeoff is that states are lost on redeploy, but since tokens are short-lived and users can just tap /connect again, it's fine for a single-instance deployment.

**HMAC-SHA256 request signing for Withings.** Unlike most OAuth providers, Withings requires every API request to be signed with an HMAC-SHA256 signature over specific parameter values. The signing only covers `action, client_id, nonce` (not all params). Getting this wrong gives you a generic "Invalid Params" error that's a pain to debug. Each signed request also requires a fresh nonce from Withings' signature endpoint.

**Token refresh on startup.** Whoop tokens expire after 60 minutes, Withings after 3 hours. When Railway redeploys (which happens on every git push), the container restarts and any tokens stored in Supabase may be stale. The scheduler runs both refresh jobs immediately on startup before the first interval tick, so tokens are always fresh after a deploy.

**401 auto-retry in /stats.** If a Whoop API call returns 401 (expired token), the stats handler automatically refreshes the token, stores the new one, and retries the request once before telling the user to reconnect. Users never see a "please reconnect" message unless the refresh token itself is truly dead.

**Security layer with three-pass validation.** Every user message passes through rate limiting (10 msg/min per user), regex-based prompt injection detection (blocks "ignore your instructions" and similar patterns), and keyword-based topic relevance checking before it ever reaches the Claude API. This keeps costs predictable and the bot on-topic.

## Project Structure

```
milo-bot/
├── bot.py                  # Entry point: Telegram polling + aiohttp server
├── agent.py                # Claude AI coaching brain with context injection
├── requirements.txt
├── Procfile                # Railway deployment (web process)
├── railway.toml            # Health checks, restart policy
│
├── core/
│   ├── handlers.py         # Telegram command handlers (/start, /connect, /stats, etc.)
│   ├── database.py         # Supabase layer for users, tokens, workouts, snapshots, state
│   ├── user_context.py     # Builds live coaching context from all data sources
│   ├── oauth_server.py     # aiohttp routes for Whoop + Withings OAuth callbacks
│   ├── oauth_state.py      # In-memory OAuth state store with TTL
│   └── scheduler.py        # APScheduler jobs for check-ins, summaries, token refresh
│
├── integrations/
│   ├── whoop.py            # Whoop OAuth 2.0 + v2 API (recovery, sleep, strain)
│   └── withings.py         # Withings OAuth 2.0 + HMAC signing + measurements API
│
├── coaching/
│   ├── prompts.py          # System prompt + morning/weekly templates
│   ├── security.py         # Rate limiting, prompt injection blocking, topic scope
│   ├── recovery.py         # Deterministic recovery evaluation (HRV, RHR, sleep -> tier)
│   ├── training.py         # Training guidance (volume, intensity, overload tracking)
│   ├── nutrition.py        # Nutrition state (TDEE, calories, protein targets)
│   ├── progress.py         # Trend tracking and progress analysis
│   ├── sleep.py            # Sleep coaching logic
│   └── lifestyle.py        # Lifestyle coaching logic
│
├── coaching-logic/         # Research documentation (~12,000 lines)
│   ├── milo_master_research.md
│   ├── track1_tdee_calories.md
│   ├── track2_volume_progression.md
│   ├── track3_autoregulation_deloads.md
│   ├── track4_recovery_nocebo.md
│   ├── track5_ad_libitum.md
│   ├── track6_sleep_hygiene.md
│   ├── track7_protein_phases.md
│   └── track8_programming.md
│
├── supabase/
│   └── migrations/         # PostgreSQL schema migrations
│
└── utils/
    ├── logger.py           # Structured logging setup
    └── helpers.py          # Shared utilities
```

## Bot Commands

| Command | What it does |
|---------|-------------|
| `/start` | Saves your profile and introduces Milo with the Milo of Croton story |
| `/connect` | Shows inline buttons to connect Whoop and Withings via OAuth |
| `/stats` | Full coaching dashboard: recovery tier, training guidance, nutrition targets, live biometrics |
| `/sleep` | Detailed sleep breakdown from Whoop (duration, efficiency, stages, disturbances) |
| `/strain` | Daily strain score and cardiovascular load from Whoop |
| `/workout` | Recent workout details from Whoop (activity type, strain, duration) |
| `/body` | Body composition from Withings (weight, body fat %) |
| `/log` | Log a workout (e.g. `bench press 3x5 185lbs`) for progressive overload tracking |
| `/profile` | View or set coaching profile (sex, age, height, weight, goal, experience, training days) |
| `/progress` | View your trends over time |
| `/help` | List all commands |

Or just send a message. Ask Milo anything about training, nutrition, sleep, or lifestyle and it'll coach you using your real data.

## Roadmap

**Built and deployed:**
- [x] Telegram bot with full command handler system
- [x] Claude-powered conversational coaching with system prompt engineering
- [x] Four pillar coaching framework (training, sleep, nutrition, lifestyle)
- [x] Whoop OAuth 2.0 integration: connect, token exchange, token refresh
- [x] Withings OAuth 2.0 integration: HMAC-SHA256 signed requests, token refresh
- [x] Live `/stats` dashboard pulling Whoop recovery + Withings body composition
- [x] Supabase database layer with user profiles, device tokens, and coaching state
- [x] Automatic token refresh (Whoop every 50 min, Withings every 2.5 hr)
- [x] Startup token refresh so data is fresh after every deploy
- [x] 401 auto-retry with transparent token refresh
- [x] Security layer: rate limiting, prompt injection detection, topic scope enforcement
- [x] Railway deployment with health checks and auto-deploy on push
- [x] Hybrid coaching engine: deterministic recovery/nutrition/training state + Claude AI overlay
- [x] Recovery evaluation from 7-30 day Whoop snapshots (HRV, RHR, sleep duration, sleep efficiency)
- [x] Nutrition state computation (TDEE, calorie targets, protein targets from profile + body comp)
- [x] Training guidance with progressive overload suggestions
- [x] Morning check-in cron job with personalized training recommendations based on overnight recovery
- [x] Weekly progress summary with aggregated sleep, body comp trends, training volume
- [x] `/sleep`, `/strain`, `/workout`, `/body` commands for detailed biometric views
- [x] `/profile` command for setting coaching parameters (goal, experience, training days)
- [x] Real biometric data injected into every conversational coaching response
- [x] ~12,000 lines of evidence-based coaching research documentation
- [x] Foreign key constraints and schema integrity across all tables

**Coming next:**
- [ ] Body composition trend visualization
- [ ] Time-based deload recommendations (proactive, not just reactive to red recovery)
- [ ] Training program templates with auto-regulation based on recovery
- [ ] Extended conversation memory beyond 6-message window
- [ ] Coaching history analysis and long-term pattern recognition

## License

This project is licensed under the [MIT License](LICENSE).

---

*"The body adapts to the demands placed upon it. Place greater demands, and it will rise to meet them."*
