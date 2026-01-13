# Artillery Load Testing Configuration

## Quick Start

### 1. Install Artillery

```bash
npm install -g artillery
```

Or use npx (no installation):
```bash
npx artillery@latest run artillery-config.yml
```

### 2. Start Flask Application

```bash
export FLASK_PORT=5001
python app.py
```

### 3. Run Load Test

```bash
# Standard test
artillery run artillery-config.yml

# Stress test
artillery run artillery-stress.yml

# Spike test
artillery run artillery-spike.yml

# All tests
./run-artillery-tests.sh
```

## Test Files

- `artillery-config.yml` - Standard load test with multiple scenarios
- `artillery-stress.yml` - High load stress test
- `artillery-spike.yml` - Traffic spike test
- `artillery-processor.js` - Custom processor functions
- `run-artillery-tests.sh` - Automated test runner

## Results

Test results are saved to `results/` directory:
- JSON results: `results/*.json`
- HTML reports: `results/*-report.html`
- Text output: `results/*.txt`

## Configuration

Edit YAML files to customize:
- Load patterns (phases)
- Endpoints to test
- Request weights
- Response time expectations
- Error rate thresholds

## Documentation

See `ARTILLERY_LOAD_TESTING_GUIDE.md` for detailed documentation.
