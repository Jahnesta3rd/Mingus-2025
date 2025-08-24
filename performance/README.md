# Mingus Performance & Load Testing

This suite covers load, stress, and endurance testing using Locust and pytest-based smoke checks.

## Quick Start (Locust)

Install deps:

```bash
pip install locust psutil requests
```

Run Locust locally against your app:

```bash
# In one terminal start your Flask app, ensure TEST_BASE_URL is reachable
export TEST_BASE_URL=http://localhost:5000

# In another terminal, run Locust headless for 500 users over 10 minutes
locust -f performance/locustfile.py \
  --host=$TEST_BASE_URL \
  --headless -u 500 -r 50 -t 10m \
  --csv=reports/locust_run
```

Key env vars:

- PCT_MOBILE (default 0.6): proportion of mobile user agents
- TARGET_P95_MS (default 800): fail build if overall p95 exceeds

## Scenarios

- Registration → Login → Dashboard fetches under load
- Profile update hot path under load
- Health/system endpoints for baselines

## Stress Testing

Increase users until failure to find breaking point:

```bash
locust -f performance/locustfile.py --host=$TEST_BASE_URL --headless -u 1200 -r 100 -t 15m
```

Monitor:
- p95/p99 response times
- Fail ratio
- Error distribution
- DB pool exhaustion
- Redis latency

## Endurance Testing

Run long duration (e.g., 24h):

```bash
locust -f performance/locustfile.py --host=$TEST_BASE_URL --headless -u 100 -r 5 -t 24h
```

Track memory growth, CPU, and error rates over time. Consider Prometheus/Grafana for continuous metrics.

## Pytest Smoke Performance

```bash
pytest -q tests/performance
```

Asserts p95 health endpoint, system health, and memory sanity.

## Data Generation

Locust generates realistic personas: names, metros (Atlanta, Houston, DC, Dallas, Chicago, LA), industries, titles, and incomes within $40k-$100k.

## Reporting & CI

- Locust CSV (--csv) and web UI stats
- Gate on p95 and fail ratio via TARGET_P95_MS
- Include runs in CI nightly for regression

## Optimization Tips

- Enable Redis caching on hot endpoints
- Review DB indexes for profile/dashboard queries
- Use connection pooling and tune pool size/max overflow
- Cache feature flags and subscription lookups
- Precompute heavy aggregates periodically


