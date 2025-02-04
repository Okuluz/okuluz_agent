from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio
import logging

class RateLimiter:
    """Rate limiting for Twitter API calls"""
    
    def __init__(self):
        self.limits: Dict[str, Dict[str, Any]] = {
            "tweets": {
                "window": timedelta(minutes=15),
                "max_requests": 300,
                "remaining": 300,
                "reset_time": datetime.utcnow()
            },
            "likes": {
                "window": timedelta(minutes=15),
                "max_requests": 1000,
                "remaining": 1000,
                "reset_time": datetime.utcnow()
            },
            "follows": {
                "window": timedelta(minutes=15),
                "max_requests": 400,
                "remaining": 400,
                "reset_time": datetime.utcnow()
            },
            "dms": {
                "window": timedelta(minutes=15),
                "max_requests": 1000,
                "remaining": 1000,
                "reset_time": datetime.utcnow()
            }
        }
        self.logger = logging.getLogger(__name__)

    async def check_limit(self, action_type: str) -> bool:
        """Check if action is within rate limits"""
        if action_type not in self.limits:
            return True
            
        limit = self.limits[action_type]
        now = datetime.utcnow()
        
        # Reset if window has passed
        if now >= limit["reset_time"]:
            limit["remaining"] = limit["max_requests"]
            limit["reset_time"] = now + limit["window"]
            
        # Check remaining requests
        if limit["remaining"] <= 0:
            wait_time = (limit["reset_time"] - now).total_seconds()
            self.logger.warning(f"Rate limit exceeded for {action_type}. "
                              f"Reset in {wait_time:.0f} seconds")
            return False
            
        return True

    async def use_limit(self, action_type: str):
        """Use one request from the limit"""
        if action_type in self.limits:
            self.limits[action_type]["remaining"] -= 1

    async def update_limits(self, headers: Dict[str, str]):
        """Update limits from Twitter API response headers"""
        for key, value in headers.items():
            if "x-rate-limit-remaining" in key:
                action_type = key.split("-")[0]
                if action_type in self.limits:
                    self.limits[action_type]["remaining"] = int(value)
                    
            elif "x-rate-limit-reset" in key:
                action_type = key.split("-")[0]
                if action_type in self.limits:
                    self.limits[action_type]["reset_time"] = datetime.fromtimestamp(int(value)) 