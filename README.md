# Milo — AI Physique & Health Coach

**Milo** is an AI-powered Telegram bot I built to coach users toward their best physique and optimal health through data-driven, progressive overload principles.

Named after **Milo of Croton**, the ancient Greek wrestler who built legendary strength by carrying a calf on his shoulders every single day. As the calf grew into a bull, so did Milo's strength. This is the principle of **progressive overload** — small, consistent effort that compounds into extraordinary results.

Milo connects to **Whoop** and **Withings** devices, pulls real health data, and delivers personalized AI coaching across four pillars.

## Features

### Four Pillar Coaching System

- **Resistance Training** — Progressive overload tracking, program design, exercise selection, sets/reps/load management, and deload recommendations based on recovery
- **Sleep** — Recovery optimization using Whoop sleep data (duration, efficiency, sleep stages), sleep hygiene guidance, and training adjustments based on sleep quality
- **Nutrition** — Body composition focused nutrition coaching, protein targets, calorie awareness, and meal timing around training sessions
- **Lifestyle** — Stress management through HRV trend analysis, daily habit optimization, hydration, sunlight exposure, and longevity-focused recommendations

### Integrations

- **Whoop** — Recovery scores, HRV, resting heart rate, strain, and sleep metrics via OAuth
- **Withings** — Body weight, body fat percentage, and muscle mass via OAuth

### AI Coaching

- Conversational coaching powered by AI — ask Milo anything about training, nutrition, sleep, or lifestyle
- Every recommendation is backed by real Whoop and Withings data when available
- Context-aware responses that consider recovery status, body composition trends, and workout history

### Proactive Check-ins

- Daily morning check-ins with training recommendations based on Whoop recovery
- Weekly progress summaries with body composition trends, training volume, and sleep averages

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| AI | Anthropic API |
| Telegram | python-telegram-bot |
| Database | Supabase (PostgreSQL) |
| Scheduling | APScheduler |
| HTTP Client | httpx |
| Deployment | Railway |

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Meet Milo and get started |
| `/connect` | Connect Whoop and Withings devices |
| `/stats` | View your latest health and body metrics |
| `/progress` | See your progress over time |
| `/log` | Log a workout (e.g. `bench press 3x5 185lbs`) |
| `/help` | Show all available commands |

You can also send any message to chat with Milo naturally about training, nutrition, sleep, or lifestyle.

## Roadmap

- [x] Telegram bot with command handlers
- [x] AI conversational coaching
- [x] Four pillar coaching framework
- [x] Supabase user profiles
- [x] Railway deployment
- [ ] Whoop OAuth integration and data sync
- [ ] Withings OAuth integration and data sync
- [ ] Workout parsing and progressive overload tracking
- [ ] Daily morning check-in cron jobs
- [ ] Weekly progress summary reports
- [ ] Body composition trend visualization
- [ ] Training program templates
- [ ] Personalized coaching history per user

## Project Structure

```
milo-bot/
├── bot.py                  # Main entry point
├── agent.py                # AI coaching brain
├── requirements.txt        # Python dependencies
├── Procfile                # Railway deployment
├── .env.example            # Environment variable template
│
├── integrations/           # Third-party API connections
│   ├── whoop.py            # Whoop OAuth + data fetching
│   └── withings.py         # Withings OAuth + data fetching
│
├── core/                   # Core bot logic
│   ├── database.py         # Supabase database layer
│   ├── scheduler.py        # Cron jobs for check-ins
│   └── handlers.py         # Telegram command handlers
│
├── coaching/               # Coaching intelligence
│   ├── prompts.py          # System prompts and templates
│   ├── nutrition.py        # Nutrition coaching logic
│   ├── training.py         # Resistance training logic
│   ├── sleep.py            # Sleep coaching logic
│   └── lifestyle.py        # Lifestyle coaching logic
│
└── utils/                  # Helper functions
    ├── logger.py           # Logging configuration
    └── helpers.py          # Shared utilities
```

## License

This project is licensed under [CC BY-NC 4.0](LICENSE). You can view, fork, and learn from the code — but commercial use is not permitted without permission.

---

*"The body adapts to the demands placed upon it. Place greater demands, and it will rise to meet them."*
*— The principle of Milo of Croton*
