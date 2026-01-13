# Running Artillery Load Tests

## Quick Start

### Option 1: Automated Script (Recommended)

```bash
./start-and-test.sh
```

This script will:
1. Start the Flask app on port 5001
2. Wait for it to be ready
3. Run Artillery quick test
4. Run Artillery standard test
5. Stop the Flask app

### Option 2: Manual Steps

#### Step 1: Start Flask App

**Terminal 1:**
```bash
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"
export FLASK_PORT=5001
python app.py
```

Wait for: `* Running on http://0.0.0.0:5001`

#### Step 2: Run Artillery Tests

**Terminal 2:**
```bash
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor/artillery"

# Quick test (30 seconds)
npx artillery run artillery-quick.yml

# Standard test (~5 minutes)
npx artillery run artillery-config.yml

# Stress test (~8 minutes)
npx artillery run artillery-stress.yml

# Spike test (~3 minutes)
npx artillery run artillery-spike.yml
```

#### Step 3: View Results

Results are saved to `artillery/results/`:
- JSON files for analysis
- HTML reports for visualization

Generate HTML report:
```bash
cd artillery
npx artillery run --output results/test.json artillery-config.yml
npx artillery report results/test.json > results/test-report.html
open results/test-report.html
```

## Test Scenarios

### Quick Test (`artillery-quick.yml`)
- **Duration**: 30 seconds
- **Rate**: 10 req/s
- **Endpoints**: Health, Status, Metrics

### Standard Test (`artillery-config.yml`)
- **Duration**: ~5 minutes
- **Phases**: Warm-up, Ramp-up, Sustained, Spike, Cool-down
- **Endpoints**: Multiple with weighted distribution

### Stress Test (`artillery-stress.yml`)
- **Duration**: ~8 minutes
- **Load**: 100 req/s sustained, 200 req/s spike

### Spike Test (`artillery-spike.yml`)
- **Duration**: ~3 minutes
- **Pattern**: Normal → Spike → Normal

## Troubleshooting

### Flask App Won't Start

1. **Check if port is in use:**
   ```bash
   lsof -ti:5001
   ```

2. **Check Redis (optional):**
   ```bash
   redis-cli ping
   # If not running, app will use filesystem sessions
   ```

3. **Check logs:**
   ```bash
   tail -f flask.log
   ```

### Artillery Tests Fail

1. **Verify server is running:**
   ```bash
   curl http://localhost:5001/health
   ```

2. **Check Artillery installation:**
   ```bash
   cd artillery
   npx artillery --version
   ```

3. **Run with verbose output:**
   ```bash
   npx artillery run --verbose artillery-quick.yml
   ```

## Expected Results

### Quick Test
- **Requests**: ~300
- **Response Time (p95)**: < 500ms
- **Error Rate**: < 1%

### Standard Test
- **Requests**: ~3,000-5,000
- **Response Time (p95)**: < 1000ms
- **Error Rate**: < 1%

## Monitoring During Tests

While Artillery runs, monitor the application:

```bash
# Dashboard
open http://localhost:5001/dashboard

# Metrics API
watch -n 2 'curl -s http://localhost:5001/api/metrics | jq'

# Error statistics
watch -n 2 'curl -s http://localhost:5001/api/errors/stats?hours=1 | jq'
```

---

**Status**: ✅ Ready to run

**Quick Start**: `./start-and-test.sh`
