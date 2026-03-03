# Milo — AI Physique & Health Coach

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Anthropic](https://img.shields.io/badge/Claude_AI-Anthropic-191919?style=flat-square&logo=anthropic&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot_API-26A5E4?style=flat-square&logo=telegram&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3FCF8E?style=flat-square&logo=supabase&logoColor=white)
![Railway](https://img.shields.io/badge/Railway-Live-0B0D0E?style=flat-square&logo=railway&logoColor=white)
![Whoop](https://img.shields.io/badge/Whoop-OAuth_2.0-44D62C?style=flat-square)
![Withings](https://img.shields.io/badge/Withings-OAuth_2.0-00B2A9?style=flat-square)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat-square)

Milo is an AI health coaching agent that lives inside Telegram. It connects to your Whoop strap and Withings scale, pulls real biometric data, and delivers personalized coaching across training, sleep, nutrition, and lifestyle — all through natural conversation powered by Claude.

The name comes from **Milo of Croton**, an ancient Greek wrestler who built legendary strength by carrying a calf on his shoulders every single day. As the calf grew into a bull, so did Milo's strength. That's progressive overload — small, consistent effort compounding into extraordinary results. It's the core philosophy behind everything this bot does.

I built Milo because I wanted a coach that actually knows my numbers. Not a chatbot that gives generic advice, but an agent that wakes up, checks my recovery score, looks at my sleep data, sees what I weigh this morning, and tells me exactly how to train today. That's what this is.

## Why It's an Agent, Not a Chatbot

There's a meaningful distinction between a chatbot and an agent, and Milo sits firmly on the agent side.

A chatbot responds when you talk to it. Milo does that too — you can ask it anything about training, nutrition, sleep, or lifestyle and it'll coach you with real data backing every recommendation. But what makes it an agent is everything it does when you're *not* talking to it.

Milo runs scheduled jobs that proactively reach out. It refreshes your Whoop and Withings tokens in the background so your data is always fresh. It has a morning check-in system that pulls your overnight recovery, looks at your HRV trend, checks your body weight from this morning's weigh-in, and generates a personalized training recommendation before you've even opened the app. It sends weekly progress summaries that aggregate your data across the entire week — sleep averages, body composition trends, training volume — and tells you what's working and what needs to change.

The architecture is built around an **agent harness** pattern: a system prompt that defines Milo's coaching philosophy and boundaries, a context injection layer that assembles real-time data from multiple APIs into structured blocks, and a security layer that enforces topic scope, blocks prompt injection attempts, and rate-limits abuse. Claude doesn't just answer questions — it reasons over your actual biometric data to produce coaching that's specific to *you*, right now, today.

## The Four Coaching Pillars

Milo coaches across four domains, and every recommendation ties back to your real data when it's available:

**Resistance Training** — Progressive overload is the foundation. Milo tracks your lifts, monitors volume and intensity trends, recommends when to push and when to deload based on your Whoop recovery, and designs programming around exercise selection, sets, reps, and load management. If your recovery is in the red, it'll tell you to back off. If you're green-lit with a 90% recovery, it'll push you.

**Sleep** — Sleep is the single most important recovery tool, and Milo treats it that way. It pulls Whoop sleep data — duration, efficiency, disturbances, sleep stages — and uses it to guide recommendations on sleep hygiene, schedule consistency, temperature, light exposure, and pre-bed routines. It connects sleep quality directly to training performance so you can see the relationship between a bad night and a bad session.

**Nutrition** — Body composition focused coaching. Protein is the priority (0.8-1g per pound of bodyweight minimum), with calorie awareness without obsessive tracking, and meal timing guidance around training sessions. Milo uses your Withings weight and body fat trends to adjust recommendations — if you're cutting and weight is stalling, it'll have something to say about that.

**Lifestyle** — The connective tissue between training and results. HRV trend analysis reveals how stress, travel, alcohol, and daily habits affect your recovery. Milo coaches on hydration, sunlight exposure, movement outside of training, and the balance between training intensity and life demands.

## Tech Stack and Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Telegram User                      │
│              (commands + free-form chat)              │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│                    bot.py                             │
│         Telegram polling + aiohttp web server         │
│         (runs concurrently via asyncio)               │
└──────┬───────────┬────────────┬──────────────────────┘
       │           │            │
       ▼           ▼            ▼
┌──────────┐ ┌──────────┐ ┌───────────────────────────┐
│ handlers │ │ OAuth    │ │ scheduler.py               │
│ .py      │ │ server   │ │ APScheduler cron jobs      │
│          │ │ (aiohttp)│ │ - morning check-in (7 AM)  │
│ /start   │ │          │ │ - weekly summary (Sun 6 PM)│
│ /connect │ │ /auth/   │ │ - Whoop refresh (50 min)   │
│ /stats   │ │  whoop/  │ │ - Withings refresh (2.5hr) │
│ /log     │ │  callback│ │ - startup token refresh    │
│ /help    │ │ /auth/   │ │                            │
│ /progress│ │  withings│ │                            │
│ chat msg │ │  /callback│ │                            │
└──────┬───┘ └─────┬────┘ └───────────────────────────┘
       │           │
       ▼           ▼
┌──────────────────────────────────────────────────────┐
│                   core/database.py                    │
│            Supabase (PostgreSQL) via REST API         │
│                                                      │
│  users │ whoop_tokens │ withings_tokens │ workouts   │
└──────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│                     agent.py                          │
│              Claude AI Coaching Brain                 │
│                                                      │
│  System prompt (coaching/prompts.py)                 │
│  + User context injection (Whoop + Withings data)    │
│  + Security layer (rate limit, topic scope, anti-PII)│
│  → Claude Sonnet 4.6 API call                        │
│  → Personalized coaching response                    │
└──────────────────────────────────────────────────────┘
```

| Component | Technology | Why |
|-----------|-----------|-----|
| Runtime | Python 3.11+ | Async-native, rich ecosystem for API integrations |
| AI Engine | Claude Sonnet 4.6 (Anthropic API) | Best reasoning for nuanced coaching with structured data context |
| Chat Interface | Telegram (python-telegram-bot) | Ubiquitous, great bot API, inline keyboards for OAuth flows |
| Database | Supabase (PostgreSQL) | Managed Postgres with REST API, auth, and real-time — free tier is generous |
| Deployment | Railway | Git-push deploys, persistent containers, built-in health checks |
| Wearable Data | Whoop API v2 (OAuth 2.0) | Recovery, HRV, resting HR, sleep metrics, strain |
| Body Composition | Withings API (OAuth 2.0 + HMAC-SHA256) | Weight, body fat %, fat mass from smart scales |
| Scheduling | APScheduler | Async-native cron jobs for proactive coaching and token refresh |
| HTTP | httpx + aiohttp | httpx for external API calls with retry/transport, aiohttp for the OAuth callback server |

## Key Engineering Decisions

**Concurrent polling + web server.** Telegram bots typically use either polling or webhooks. Milo uses polling for simplicity (no SSL cert management, works locally for development) but also needs to receive OAuth callbacks from Whoop and Withings. The solution: run the Telegram polling loop and an aiohttp web server concurrently in the same asyncio event loop. One process, two interfaces.

**Raw HTTP for Supabase token storage.** The supabase-py client works well for reads, but during the OAuth callback flow I hit intermittent DNS resolution failures on Railway's internal network. Rather than fight the client library, I wrote `store_whoop_tokens()` and `store_withings_tokens()` using raw httpx with `HTTPTransport(retries=3)` and the Supabase REST API directly. More control, more reliable.

**In-memory OAuth state store.** OAuth state tokens are stored in a Python dict with 10-minute expiry instead of a database table. This eliminates a Supabase round-trip during the most latency-sensitive part of the flow (the redirect). The tradeoff is that states are lost on redeploy, but since tokens are short-lived and users can just tap /connect again, this is acceptable for a single-instance deployment.

**HMAC-SHA256 request signing for Withings.** Unlike most OAuth providers, Withings requires every API request to be signed with an HMAC-SHA256 signature over specific parameter values. The signing only covers `action, client_id, nonce` (not all params) — getting this wrong produces a generic "Invalid Params" error that's hard to debug. Each signed request also requires a fresh nonce from Withings' signature endpoint.

**Token refresh on startup.** Whoop tokens expire after 60 minutes and Withings after 3 hours. When Railway redeploys (which happens on every git push), the container restarts and any tokens stored in Supabase may be stale. The scheduler runs both refresh jobs immediately on startup before the first interval tick, so tokens are always fresh after a deploy.

**401 auto-retry in /stats.** If a Whoop API call returns 401 (expired token), the stats handler automatically refreshes the token, stores the new one, and retries the request once before telling the user to reconnect. This makes the user experience seamless — they never see a "please reconnect" message unless the refresh token itself is truly dead.

**Security layer with three-pass validation.** Every user message passes through rate limiting (10 msg/min per user), regex-based prompt injection detection (blocks "ignore your instructions" and similar patterns), and keyword-based topic relevance checking before it ever reaches the Claude API. This keeps costs predictable and the bot on-topic.

## Project Structure

```
milo-bot/
├── bot.py                  # Entry point — Telegram polling + aiohttp server
├── agent.py                # Claude AI coaching brain with context injection
├── requirements.txt
├── Procfile                # Railway deployment (web process)
├── railway.toml            # Health checks, restart policy
│
├── core/
│   ├── handlers.py         # Telegram command handlers (/start, /connect, /stats, etc.)
│   ├── database.py         # Supabase layer — users, tokens, workouts
│   ├── oauth_server.py     # aiohttp routes for Whoop + Withings OAuth callbacks
│   ├── oauth_state.py      # In-memory OAuth state store with TTL
│   └── scheduler.py        # APScheduler jobs — check-ins, summaries, token refresh
│
├── integrations/
│   ├── whoop.py            # Whoop OAuth 2.0 + v2 API (recovery, sleep, strain)
│   └── withings.py         # Withings OAuth 2.0 + HMAC signing + measurements API
│
├── coaching/
│   ├── prompts.py          # System prompt + morning/weekly templates
│   ├── security.py         # Rate limiting, prompt injection blocking, topic scope
│   ├── training.py         # Resistance training coaching logic
│   ├── nutrition.py        # Nutrition coaching logic
│   ├── sleep.py            # Sleep coaching logic
│   └── lifestyle.py        # Lifestyle coaching logic
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
| `/stats` | Pulls live data — recovery score, HRV, resting HR, weight, body fat % |
| `/log` | Log a workout (e.g. `bench press 3x5 185lbs`) for progressive overload tracking |
| `/progress` | View your trends over time |
| `/help` | List all commands |

Or just send a message. Ask Milo anything about training, nutrition, sleep, or lifestyle and it'll coach you using your real data.

## Roadmap

**Built and deployed:**
- [x] Telegram bot with full command handler system
- [x] Claude-powered conversational coaching with system prompt engineering
- [x] Four pillar coaching framework (training, sleep, nutrition, lifestyle)
- [x] Whoop OAuth 2.0 integration — connect, token exchange, token refresh
- [x] Withings OAuth 2.0 integration — HMAC-SHA256 signed requests, token refresh
- [x] Live `/stats` pulling real Whoop recovery + Withings body composition
- [x] Supabase database layer with user profiles and device token storage
- [x] Automatic token refresh (Whoop every 50 min, Withings every 2.5 hr)
- [x] Startup token refresh so data is fresh after every deploy
- [x] 401 auto-retry with transparent token refresh in /stats
- [x] Security layer — rate limiting, prompt injection detection, topic scope enforcement
- [x] Railway deployment with health checks and auto-deploy on push

**Coming next:**
- [ ] Workout parsing and progressive overload tracking from `/log` entries
- [ ] Daily morning check-in cron job — personalized training recommendations based on overnight recovery
- [ ] Weekly progress summary — aggregated sleep, body comp trends, training volume
- [ ] Inject real Whoop + Withings data into every conversational coaching response (not just /stats)
- [ ] Body composition trend visualization
- [ ] Training program templates with auto-regulation based on recovery
- [ ] Multi-turn conversation memory per user
- [ ] Personalized coaching history stored in Supabase

## License

This project is licensed under the [MIT License](LICENSE).

---

*"The body adapts to the demands placed upon it. Place greater demands, and it will rise to meet them."*
