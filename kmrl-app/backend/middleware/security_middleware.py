"""
Security Middleware for KMRL Gateway
Advanced security headers and protection
"""

import os
import time
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import structlog
import redis

logger = structlog.get_logger()

class SecurityMiddleware:
    """Enhanced security middleware for KMRL gateway"""
    
    def __init__(self):
        self.redis_client = self._connect_redis()
        self.security_config = {
            'max_request_size': 200 * 1024 * 1024,  # 200MB
            'rate_limit_requests': 100,  # per minute
            'rate_limit_window': 60,  # seconds
            'blocked_ips': set(),
            'suspicious_patterns': [
                'sql injection',
                'xss',
                'script',
                'javascript:',
                'data:text/html',
                '../',
                '..\\',
                '<script',
                'eval(',
                'exec('
            ]
        }
    
    def _connect_redis(self) -> redis.Redis:
        """Connect to Redis"""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        return redis.Redis.from_url(redis_url, decode_responses=True)
    
    async def __call__(self, request: Request, call_next):
        """Security middleware implementation"""
        start_time = time.time()
        
        try:
            # Get client IP
            client_ip = self._get_client_ip(request)
            
            # Check if IP is blocked
            if await self._is_ip_blocked(client_ip):
                return JSONResponse(
                    status_code=403,
                    content={"error": "IP address blocked"}
                )
            
            # Check request size
            if await self._check_request_size(request):
                return JSONResponse(
                    status_code=413,
                    content={"error": "Request too large"}
                )
            
            # Check for suspicious patterns
            if await self._check_suspicious_patterns(request):
                await self._log_suspicious_activity(client_ip, request)
                return JSONResponse(
                    status_code=400,
                    content={"error": "Suspicious request detected"}
                )
            
            # Rate limiting
            if await self._check_rate_limit(client_ip, request):
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded"}
                )
            
            # Process request
            response = await call_next(request)
            
            # Add security headers
            response = await self._add_security_headers(response)
            
            # Log request
            duration = time.time() - start_time
            await self._log_request(client_ip, request, response, duration)
            
            return response
            
        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error"}
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    async def _is_ip_blocked(self, client_ip: str) -> bool:
        """Check if IP is blocked"""
        try:
            blocked_key = f"blocked_ip:{client_ip}"
            return self.redis_client.exists(blocked_key) > 0
        except Exception:
            return False
    
    async def _check_request_size(self, request: Request) -> bool:
        """Check if request size exceeds limit"""
        content_length = request.headers.get("Content-Length")
        if content_length:
            size = int(content_length)
            return size > self.security_config['max_request_size']
        return False
    
    async def _check_suspicious_patterns(self, request: Request) -> bool:
        """Check for suspicious patterns in request"""
        try:
            # Check URL
            url = str(request.url).lower()
            for pattern in self.security_config['suspicious_patterns']:
                if pattern in url:
                    return True
            
            # Check headers
            for header_name, header_value in request.headers.items():
                header_str = f"{header_name}: {header_value}".lower()
                for pattern in self.security_config['suspicious_patterns']:
                    if pattern in header_str:
                        return True
            
            # Check query parameters
            for param_name, param_value in request.query_params.items():
                param_str = f"{param_name}={param_value}".lower()
                for pattern in self.security_config['suspicious_patterns']:
                    if pattern in param_str:
                        return True
            
            return False
            
        except Exception:
            return False
    
    async def _check_rate_limit(self, client_ip: str, request: Request) -> bool:
        """Check rate limiting"""
        try:
            rate_key = f"rate_limit:{client_ip}"
            current_time = int(time.time())
            window_start = current_time - self.security_config['rate_limit_window']
            
            # Clean old entries
            self.redis_client.zremrangebyscore(rate_key, 0, window_start)
            
            # Count current requests
            current_requests = self.redis_client.zcard(rate_key)
            
            if current_requests >= self.security_config['rate_limit_requests']:
                return True
            
            # Add current request
            self.redis_client.zadd(rate_key, {str(current_time): current_time})
            self.redis_client.expire(rate_key, self.security_config['rate_limit_window'])
            
            return False
            
        except Exception:
            return False
    
    async def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to response"""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            "X-Permitted-Cross-Domain-Policies": "none",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response
    
    async def _log_suspicious_activity(self, client_ip: str, request: Request):
        """Log suspicious activity"""
        try:
            activity_data = {
                'timestamp': datetime.now().isoformat(),
                'client_ip': client_ip,
                'method': request.method,
                'url': str(request.url),
                'headers': dict(request.headers),
                'user_agent': request.headers.get('User-Agent', ''),
                'type': 'suspicious_activity'
            }
            
            # Store in Redis
            self.redis_client.lpush('security_log', str(activity_data))
            self.redis_client.ltrim('security_log', 0, 9999)  # Keep last 10000 entries
            self.redis_client.expire('security_log', 86400 * 30)  # Keep for 30 days
            
            logger.warning(f"Suspicious activity detected from {client_ip}: {request.url}")
            
        except Exception as e:
            logger.error(f"Failed to log suspicious activity: {e}")
    
    async def _log_request(self, client_ip: str, request: Request, response: Response, duration: float):
        """Log request for security analysis"""
        try:
            request_data = {
                'timestamp': datetime.now().isoformat(),
                'client_ip': client_ip,
                'method': request.method,
                'url': str(request.url),
                'status_code': response.status_code,
                'duration': duration,
                'user_agent': request.headers.get('User-Agent', ''),
                'content_type': request.headers.get('Content-Type', ''),
                'content_length': request.headers.get('Content-Length', '0')
            }
            
            # Store in Redis
            self.redis_client.lpush('request_log', str(request_data))
            self.redis_client.ltrim('request_log', 0, 9999)  # Keep last 10000 entries
            self.redis_client.expire('request_log', 86400 * 7)  # Keep for 7 days
            
        except Exception as e:
            logger.error(f"Failed to log request: {e}")
    
    async def block_ip(self, client_ip: str, reason: str, duration_hours: int = 24):
        """Block an IP address"""
        try:
            block_data = {
                'ip': client_ip,
                'reason': reason,
                'blocked_at': datetime.now().isoformat(),
                'duration_hours': duration_hours
            }
            
            # Store block information
            block_key = f"blocked_ip:{client_ip}"
            self.redis_client.hset(block_key, mapping=block_data)
            self.redis_client.expire(block_key, duration_hours * 3600)
            
            logger.warning(f"IP {client_ip} blocked for {duration_hours} hours: {reason}")
            
        except Exception as e:
            logger.error(f"Failed to block IP {client_ip}: {e}")
    
    async def unblock_ip(self, client_ip: str):
        """Unblock an IP address"""
        try:
            block_key = f"blocked_ip:{client_ip}"
            self.redis_client.delete(block_key)
            
            logger.info(f"IP {client_ip} unblocked")
            
        except Exception as e:
            logger.error(f"Failed to unblock IP {client_ip}: {e}")
    
    async def get_security_logs(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get security logs for the last N hours"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            logs = []
            
            # Get security logs
            security_logs = self.redis_client.lrange('security_log', 0, 9999)
            for log_entry in security_logs:
                try:
                    log_data = eval(log_entry)  # Convert string back to dict
                    log_time = datetime.fromisoformat(log_data['timestamp'])
                    if log_time >= cutoff_time:
                        logs.append(log_data)
                except Exception:
                    continue
            
            return logs
            
        except Exception as e:
            logger.error(f"Failed to get security logs: {e}")
            return []
    
    async def get_blocked_ips(self) -> List[Dict[str, Any]]:
        """Get list of blocked IPs"""
        try:
            blocked_ips = []
            pattern = "blocked_ip:*"
            keys = self.redis_client.keys(pattern)
            
            for key in keys:
                try:
                    ip_data = self.redis_client.hgetall(key)
                    if ip_data:
                        blocked_ips.append(ip_data)
                except Exception:
                    continue
            
            return blocked_ips
            
        except Exception as e:
            logger.error(f"Failed to get blocked IPs: {e}")
            return []
    
    async def get_security_statistics(self) -> Dict[str, Any]:
        """Get security statistics"""
        try:
            stats = {
                'total_requests': 0,
                'blocked_requests': 0,
                'suspicious_activities': 0,
                'blocked_ips': 0,
                'top_ips': {},
                'top_user_agents': {},
                'error_rates': {}
            }
            
            # Get request logs
            request_logs = self.redis_client.lrange('request_log', 0, 9999)
            security_logs = self.redis_client.lrange('security_log', 0, 9999)
            blocked_ips = self.redis_client.keys('blocked_ip:*')
            
            stats['blocked_ips'] = len(blocked_ips)
            stats['suspicious_activities'] = len(security_logs)
            
            # Analyze request logs
            for log_entry in request_logs:
                try:
                    log_data = eval(log_entry)
                    stats['total_requests'] += 1
                    
                    # Count by IP
                    ip = log_data.get('client_ip', 'unknown')
                    stats['top_ips'][ip] = stats['top_ips'].get(ip, 0) + 1
                    
                    # Count by user agent
                    user_agent = log_data.get('user_agent', 'unknown')
                    stats['top_user_agents'][user_agent] = stats['top_user_agents'].get(user_agent, 0) + 1
                    
                    # Count errors
                    status_code = log_data.get('status_code', 200)
                    if status_code >= 400:
                        stats['error_rates'][str(status_code)] = stats['error_rates'].get(str(status_code), 0) + 1
                    
                except Exception:
                    continue
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get security statistics: {e}")
            return {}

if __name__ == '__main__':
    # Test security middleware
    middleware = SecurityMiddleware()
    
    # Test blocking an IP
    import asyncio
    
    async def test_security():
        await middleware.block_ip("192.168.1.100", "Suspicious activity", 1)
        
        # Get security statistics
        stats = await middleware.get_security_statistics()
        print(f"Security statistics: {stats}")
    
    asyncio.run(test_security())
