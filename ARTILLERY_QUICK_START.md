# Artillery Load Testing - Quick Start

## Installation

### Option 1: Install Globally (Recommended)

```bash
npm install -g artillery
```

Or use the installation script:
```bash
./artillery/install-artillery.sh
```

### Option 2: Use npx (No Installation)

```bash
npx artillery@latest run artillery/artillery-config.yml
```

### Verify Installation

```bash
artillery --version
```

## Quick Test (30 seconds)

```bash
# Start Flask app
export FLASK_PORT=5001
python app.py

# In another terminal, run quick test
./artillery/run-quick-test.sh
```

Or manually:
```bash
artillery run artillery/artillery-quick.yml
```

## Standard Test

```bash
artillery run artillery/artillery-config.yml
```

## All Tests

```bash
./artillery/run-artillery-tests.sh
```

## Test Scenarios

### 1. Quick Test (`artillery-quick.yml`)
- Duration: 30 seconds
- Rate: 10 req/s
- Endpoints: Health, Status, Metrics

### 2. Standard Test (`artillery-config.yml`)
- Duration: ~5 minutes
- Phases: Warm-up, Ramp-up, Sustained, Spike, Cool-down
- Multiple endpoints with weighted distribution

### 3. Stress Test (`artillery-stress.yml`)
- Duration: ~8 minutes
- High sustained load: 100 req/s
- Spike: 200 req/s

### 4. Spike Test (`artillery-spike.yml`)
- Duration: ~3 minutes
- Tests sudden traffic spikes

## Results

Results are saved to `artillery/results/`:
- JSON files for programmatic analysis
- HTML reports for visualization
- Text output for quick review

Generate HTML report:
```bash
artillery run --output results/test.json artillery/artillery-config.yml
artillery report results/test.json > results/test-report.html
open results/test-report.html
```

## Integration with Monitoring

While Artillery runs, monitor the application:

```bash
# Dashboard
open http://localhost:5001/dashboard

# Watch metrics
watch -n 2 'curl -s http://localhost:5001/api/metrics | jq'
```

## Next Steps

1. **Install Artillery**: `npm install -g artillery`
2. **Run Quick Test**: `./artillery/run-quick-test.sh`
3. **Review Results**: Check Artillery output and HTML reports
4. **Run Full Suite**: `./artillery/run-artillery-tests.sh`
5. **Customize**: Edit YAML files for your needs

---

**Status**: ✅ Artillery configured and ready

**Quick Test**: `./artillery/run-quick-test.sh`
