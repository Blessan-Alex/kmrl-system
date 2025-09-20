"""
Rate Limiter for KMRL Gateway
Handles rate limiting for API endpoints
"""

import redis
import time
from typing import Dict, Any
import structlog

logger = structlog.get_logger()

class RateLimiter:
    """Rate limiter for KMRL API endpoints"""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url("redis://localhost:6379")
        self.rate_limits = {
            "system": {"requests": 1000, "window": 3600},  # 1000 requests per hour
            "email_connector": {"requests": 100, "window": 3600},  # 100 requests per hour
            "maximo_connector": {"requests": 200, "window": 3600},  # 200 requests per hour
            "sharepoint_connector": {"requests": 150, "window": 3600},  # 150 requests per hour
            "whatsapp_connector": {"requests": 300, "window": 3600},  # 300 requests per hour
        }
    
    async def check_rate_limit(self, service_type: str) -> bool:
        """Check if service is within rate limits"""
        try:
            if service_type not in self.rate_limits:
                logger.warning(f"Unknown service type: {service_type}")
                return True
            
            limit_config = self.rate_limits[service_type]
            key = f"rate_limit:{service_type}"
            current_time = int(time.time())
            window_start = current_time - limit_config["window"]
            
            # Remove old entries
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_requests = self.redis_client.zcard(key)
            
            if current_requests >= limit_config["requests"]:
                logger.warning(f"Rate limit exceeded for {service_type}: {current_requests}/{limit_config['requests']}")
                return False
            
            # Add current request
            self.redis_client.zadd(key, {str(current_time): current_time})
            self.redis_client.expire(key, limit_config["window"])
            
            logger.info(f"Rate limit check passed for {service_type}: {current_requests + 1}/{limit_config['requests']}")
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow request if rate limiting fails
