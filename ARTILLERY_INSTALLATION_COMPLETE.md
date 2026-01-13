# Artillery Installation Complete ✅

## Installation Status

**Artillery Version**: 2.0.27  
**Installation Type**: Local (in `artillery/` directory)  
**Node.js Version**: v22.16.0  
**Status**: ✅ Installed and ready to use

## How to Use

### Option 1: Using npx (Recommended)

Since Artillery is installed locally, use `npx` to run it:

```bash
cd artillery
npx artillery run artillery-config.yml
```

### Option 2: Using npm scripts

```bash
cd artillery
npm run test          # Standard test
npm run test:stress   # Stress test
npm run test:spike    # Spike test
```

### Option 3: Using the shell scripts

The scripts have been updated to automatically detect the local installation:

```bash
# Quick test
./artillery/run-quick-test.sh

# All tests
./artillery/run-artillery-tests.sh
```

## Quick Start

### 1. Start Flask Application

```bash
export FLASK_PORT=5001
python app.py
```

### 2. Run Quick Test

```bash
cd artillery
npx artillery run artillery-quick.yml
```

Or use the script:
```bash
./artillery/run-quick-test.sh
```

### 3. Run Standard Test

```bash
cd artillery
npx artillery run artillery-config.yml
```

## Verify Installation

```bash
cd artillery
npx artillery --version
```

Expected output:
```
Artillery: 2.0.27
Node.js:   v22.16.0
OS:        darwin
```

## Installation Location

Artillery is installed in:
```
artillery/node_modules/artillery/
```

## Next Steps

1. **Start Flask app**: `export FLASK_PORT=5001 && python app.py`
2. **Run quick test**: `./artillery/run-quick-test.sh`
3. **Review results**: Check `artillery/results/` directory
4. **Run full suite**: `./artillery/run-artillery-tests.sh`

## Troubleshooting

### If scripts don't work

Use npx directly:
```bash
cd artillery
npx artillery run artillery-config.yml
```

### If you want global installation

Fix npm cache permissions first:
```bash
sudo chown -R $(whoami) ~/.npm
npm install -g artillery
```

Then use `artillery` command directly.

---

**Status**: ✅ Artillery installed and ready

**Quick Test**: `cd artillery && npx artillery run artillery-quick.yml`
