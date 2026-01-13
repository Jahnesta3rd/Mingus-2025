# Installation Instructions for Flask-Session and Redis

## Current Status

✅ **Redis** - Already installed (version 6.2.0)  
⚠️ **Flask-Session** - Needs to be installed

## Installation Options

### Option 1: User Installation (Recommended)

Run this command in your terminal:

```bash
pip install --user Flask-Session
```

This installs to your user directory and doesn't require sudo.

### Option 2: Using pip3

If you have multiple Python versions:

```bash
pip3 install Flask-Session
```

### Option 3: Using Anaconda/Conda

If you're using Anaconda:

```bash
conda install -c conda-forge flask-session
```

Or:

```bash
pip install Flask-Session
```

### Option 4: Virtual Environment (Best Practice)

If you're using a virtual environment:

```bash
# Activate your virtual environment first
source venv/bin/activate  # or: conda activate your_env_name

# Then install
pip install Flask-Session redis
```

### Option 5: With Trusted Hosts (If SSL Issues)

If you encounter SSL certificate errors:

```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org Flask-Session
```

## Verify Installation

After installation, verify it worked:

```bash
python -c "import flask_session; print('Flask-Session installed successfully')"
python -c "import redis; print('Redis installed successfully')"
```

## Dependencies

Flask-Session will automatically install:
- `flask>=2.2` (already installed)
- `msgspec>=0.18.6` (will be installed)
- `cachelib` (already installed)

## Next Steps

Once Flask-Session is installed:

1. ✅ Redis is already installed
2. ✅ Update `app.py` with session configuration
3. ✅ Update environment variables
4. ✅ Test Redis connection

## Troubleshooting

### Permission Errors
If you get permission errors, use `--user` flag:
```bash
pip install --user Flask-Session
```

### SSL Certificate Errors
Use trusted hosts:
```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org Flask-Session
```

### Multiple Python Versions
Make sure you're using the correct pip:
```bash
which pip
python --version
```

Use the pip that matches your Python version.
