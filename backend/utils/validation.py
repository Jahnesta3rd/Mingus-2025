from typing import Optional


def validate_user_tier(tier: Optional[str]) -> bool:
    if not tier:
        return False
    return tier in {"budget", "mid_tier", "professional"}


__all__ = ["validate_user_tier"]






