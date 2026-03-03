# Milo — AI Physique & Health Coach

**Milo** is an AI-powered Telegram bot that coaches users to build their best physique and optimize their health through data-driven, progressive overload principles.

Named after **Milo of Croton**, the ancient Greek wrestler who built legendary strength by carrying a calf on his shoulders every single day. As the calf grew into a bull, so did Milo's strength. This is the principle of **progressive overload** — small, consistent effort that compounds into extraordinary results.

Milo connects to your **Whoop** and **Withings** devices, pulls your real health data, and delivers personalized coaching powered by **Claude AI** across four pillars.

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

- Conversational coaching powered by Claude — ask Milo anything about training, nutrition, sleep, or lifestyle
- Every recommendation is backed by your real Whoop and Withings data when available
- Context-aware responses that consider your recovery status, body composition trends, and workout history

### Proactive Check-ins

- Daily morning check-ins with training recommendations based on your Whoop recovery
- Weekly progress summaries with body composition trends, training volume, and sleep averages

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| AI Engine | Claude API (Anthropic) |
| Telegram | python-telegram-bot |
| Database | Supabase (PostgreSQL) |
| Scheduling | APScheduler |
| HTTP Client | httpx |
| Deployment | Railway |

## Getting Started

### Prerequisites

- Python 3.11+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- An Anthropic API key
- A Supabase project

### Installation

```bash
# Clone the repository
git clone https://github.com/gavinmichelsen/milo-bot.git
cd milo-bot

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your actual API keys
```

### Running Locally

```bash
python bot.py
```

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
- [x] Claude AI conversational coaching
- [x] Four pillar coaching framework
- [ ] Whoop OAuth integration and data sync
- [ ] Withings OAuth integration and data sync
- [ ] Supabase user profiles and workout logging
- [ ] Workout parsing and progressive overload tracking
- [ ] Daily morning check-in cron jobs
- [ ] Weekly progress summary reports
- [ ] Body composition trend visualization
- [ ] Training program templates
- [ ] Multi-user support with personalized coaching history
- [ ] Railway deployment with CI/CD

## Project Structure

```
milo-bot/
├── bot.py                  # Main entry point
├── agent.py                # Claude AI coaching brain
├── requirements.txt        # Python dependencies
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

This is an open source project. Contributions, issues, and feature requests are welcome.

---

*"The body adapts to the demands placed upon it. Place greater demands, and it will rise to meet them."*
*— The principle of Milo of Croton*
