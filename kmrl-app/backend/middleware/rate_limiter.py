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
    
    async def check_rate_limit(self, request, endpoint: str, user_id: str = None) -> bool:
        """Check if service is within rate limits"""
        try:
            # Get client IP for rate limiting
            client_ip = request.client.host if request.client else "unknown"
            
            # Use user_id if provided, otherwise use IP
            rate_key = user_id if user_id else client_ip
            
            # Get rate limit config for endpoint
            endpoint_limits = {
                "document_upload": {"requests": 10, "window": 60},  # 10 requests per minute
                "document_status": {"requests": 100, "window": 60},  # 100 requests per minute
                "health_check": {"requests": 1000, "window": 60},  # 1000 requests per minute
            }
            
            limit_config = endpoint_limits.get(endpoint, {"requests": 50, "window": 60})
            key = f"rate_limit:{endpoint}:{rate_key}"
            current_time = int(time.time())
            window_start = current_time - limit_config["window"]
            
            # Remove old entries
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_requests = self.redis_client.zcard(key)
            
            if current_requests >= limit_config["requests"]:
                logger.warning(f"Rate limit exceeded for {endpoint}: {current_requests}/{limit_config['requests']}")
                return False
            
            # Add current request
            self.redis_client.zadd(key, {str(current_time): current_time})
            self.redis_client.expire(key, limit_config["window"])
            
            logger.info(f"Rate limit check passed for {endpoint}: {current_requests + 1}/{limit_config['requests']}")
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow request if rate limiting fails
