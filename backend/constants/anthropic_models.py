"""Anthropic Messages API model IDs for the Mingus backend.

Single source of truth: dated snapshot model IDs are retired by Anthropic and
the API returns 404 for them. Prefer importing from this module instead of
hard-coding model strings in routes.
"""

# Default Sonnet for conversational and short-copy calls (April 2026).
CLAUDE_SONNET_MODEL = "claude-sonnet-4-6"
