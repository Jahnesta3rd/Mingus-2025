# Mingus Reddit Engine

A unified pipeline that discovers high-value communities, listens for pain signals, and converts validated organic leads into Reddit Ads targeting briefs.

## Pipeline

1. **Heat Map Intelligence** (`intelligence/`) — discovers, ranks, and monitors Reddit and Facebook communities by activity level.
2. **Community Lead Finder** (`listeners/`) — listens to ranked communities for pain signals that Mingus solves.
3. **Ads Brief Generator** (`pipeline/`) — converts validated organic signals into structured briefs for Reddit Ads activation.

Supporting modules:

| Directory     | Purpose                                      |
|---------------|----------------------------------------------|
| `config/`     | Signal libraries, domain configs, thresholds |
| `storage/`    | PostgreSQL schema and data access layer      |
| `scheduler/`  | Cron-style job orchestration                 |
| `reporting/`  | Notifications and performance reports        |
| `dashboard/`  | Flask dashboard for leads and briefs           |
| `tests/`      | Unit and integration tests                   |

## Setup

```bash
cd mingus-reddit-engine
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

### Database

Requires PostgreSQL with the `pgcrypto` extension (for `gen_random_uuid()`). Initialize the schema:

```python
from dotenv import load_dotenv
load_dotenv()

from storage.db import init_db
init_db()
```

Or run `storage/schema.sql` directly against your database.

Connection parameters are read from environment variables:

- `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`
- `PGSSLMODE` — set to `require` for DigitalOcean managed databases

## Environment Variables

See `.env.example` for the full list. Key thresholds:

- `HOT_LEAD_THRESHOLD` — score that triggers immediate notification (default `9.0`)
- `COMPOSITE_THRESHOLD` — minimum composite score for lead inclusion (default `6.5`)

## Schema Overview

- **communities** — ranked community targets with heat scores and priority tiers
- **leads** — ingested posts with pain/readiness scoring and reply tracking
- **ad_briefs** — generated Reddit Ads targeting briefs from lead patterns
- **ad_performance** — campaign performance linked to briefs
- **signal_library_updates** — audit log for keyword library changes
