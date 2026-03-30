#!/usr/bin/env python3
"""Shared Flask-Limiter instance — initialized via init_app in app.py."""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
