"""Redis-backed token denylist — production only."""
from __future__ import annotations

from datetime import datetime, timezone
import redis

from src.domains.auth.repositories.base_denylist import BaseTokenDenylist


class RedisTokenDenylist(BaseTokenDenylist):
    """Repository for managing revoked tokens using Redis."""
    
    def __init__(self, client: redis.Redis) -> None:
        self._client = client
        self._prefix = "denylist:"

    def add(self, jti: str, exp: datetime | int) -> None:
        """
        Adds a token's JTI to the denylist.
        Sets the TTL of the redis key to match the token's expiration.
        """
        key = f"{self._prefix}{jti}"
        
        if isinstance(exp, int):
            # If exp is already a unix timestamp integer
            ttl = exp - int(datetime.now(timezone.utc).timestamp())
        else:
            # If exp is a datetime object
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            ttl = int((exp - datetime.now(timezone.utc)).total_seconds())
            
        # If the token is already expired or about to expire, we can use a very short TTL
        if ttl <= 0:
            ttl = 1
            
        self._client.setex(key, ttl, "revoked")

    def is_revoked(self, jti: str) -> bool:
        """Checks if a given JTI exists in the denylist."""
        key = f"{self._prefix}{jti}"
        return self._client.exists(key) == 1
