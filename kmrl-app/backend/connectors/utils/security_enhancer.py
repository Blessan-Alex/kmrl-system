"""
Security Enhancer for KMRL Connectors
Advanced security measures and threat protection
"""

import os
import hashlib
import hmac
import time
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import structlog
import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import secrets

logger = structlog.get_logger()

class ConnectorSecurityEnhancer:
    """Enhanced security for KMRL connector system"""
    
    def __init__(self):
        self.redis_client = self._connect_redis()
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Security configuration
        self.security_config = {
            'max_failed_attempts': 5,
            'lockout_duration': 300,  # 5 minutes
            'rate_limit_requests': 100,  # per minute
            'rate_limit_window': 60,  # seconds
            'session_timeout': 3600,  # 1 hour
            'encryption_algorithm': 'AES-256-GCM',
            'hash_algorithm': 'SHA-256'
        }
    
    def _connect_redis(self) -> redis.Redis:
        """Connect to Redis with security settings"""
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        return redis.Redis.from_url(redis_url, decode_responses=True)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key"""
        try:
            # Try to get existing key from Redis
            key = self.redis_client.get('kmrl_encryption_key')
            if key:
                return base64.b64decode(key)
        except Exception:
            pass
        
        # Generate new key
        key = Fernet.generate_key()
        
        # Store in Redis (in production, use secure key management)
        try:
            self.redis_client.set('kmrl_encryption_key', base64.b64encode(key).decode())
        except Exception as e:
            logger.warning(f"Failed to store encryption key in Redis: {e}")
        
        return key
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise
    
    def hash_password(self, password: str, salt: str = None) -> Tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )
        key = base64.b64encode(kdf.derive(password.encode())).decode()
        
        return key, salt
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            computed_hash, _ = self.hash_password(password, salt)
            return hmac.compare_digest(computed_hash, hashed_password)
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    def generate_api_key(self, user_id: str, permissions: List[str] = None) -> str:
        """Generate secure API key"""
        try:
            # Create key data
            key_data = {
                'user_id': user_id,
                'permissions': permissions or ['read', 'write'],
                'created_at': datetime.now().isoformat(),
                'nonce': secrets.token_hex(16)
            }
            
            # Create HMAC signature
            message = json.dumps(key_data, sort_keys=True)
            signature = hmac.new(
                self.encryption_key,
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Combine data and signature
            api_key_data = {
                'data': key_data,
                'signature': signature
            }
            
            # Encode as base64
            api_key = base64.b64encode(
                json.dumps(api_key_data).encode()
            ).decode()
            
            # Store in Redis with expiration
            self.redis_client.setex(
                f'api_key:{api_key}',
                self.security_config['session_timeout'],
                json.dumps(key_data)
            )
            
            return api_key
            
        except Exception as e:
            logger.error(f"Failed to generate API key: {e}")
            raise
    
    def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Validate API key"""
        try:
            # Decode API key
            api_key_data = json.loads(base64.b64decode(api_key).decode())
            
            # Verify signature
            message = json.dumps(api_key_data['data'], sort_keys=True)
            expected_signature = hmac.new(
                self.encryption_key,
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(api_key_data['signature'], expected_signature):
                return {'valid': False, 'error': 'Invalid signature'}
            
            # Check if key exists in Redis
            stored_data = self.redis_client.get(f'api_key:{api_key}')
            if not stored_data:
                return {'valid': False, 'error': 'API key expired or invalid'}
            
            # Parse stored data
            key_data = json.loads(stored_data)
            
            return {
                'valid': True,
                'user_id': key_data['user_id'],
                'permissions': key_data['permissions'],
                'created_at': key_data['created_at']
            }
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return {'valid': False, 'error': 'Invalid API key format'}
    
    def check_rate_limit(self, identifier: str, operation: str = 'default') -> Dict[str, Any]:
        """Check rate limiting"""
        try:
            key = f'rate_limit:{identifier}:{operation}'
            current_time = int(time.time())
            window_start = current_time - self.security_config['rate_limit_window']
            
            # Clean old entries
            self.redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_requests = self.redis_client.zcard(key)
            
            if current_requests >= self.security_config['rate_limit_requests']:
                return {
                    'allowed': False,
                    'remaining': 0,
                    'reset_time': self.security_config['rate_limit_window']
                }
            
            # Add current request
            self.redis_client.zadd(key, {str(current_time): current_time})
            self.redis_client.expire(key, self.security_config['rate_limit_window'])
            
            return {
                'allowed': True,
                'remaining': self.security_config['rate_limit_requests'] - current_requests - 1,
                'reset_time': self.security_config['rate_limit_window']
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return {'allowed': True, 'error': str(e)}
    
    def check_failed_attempts(self, identifier: str) -> Dict[str, Any]:
        """Check failed login attempts"""
        try:
            key = f'failed_attempts:{identifier}'
            attempts = self.redis_client.get(key)
            
            if attempts:
                attempt_count = int(attempts)
                if attempt_count >= self.security_config['max_failed_attempts']:
                    # Check if still locked out
                    lockout_key = f'lockout:{identifier}'
                    lockout_time = self.redis_client.get(lockout_key)
                    
                    if lockout_time:
                        remaining_time = int(lockout_time) - int(time.time())
                        if remaining_time > 0:
                            return {
                                'locked': True,
                                'remaining_time': remaining_time,
                                'attempts': attempt_count
                            }
                        else:
                            # Lockout expired, reset
                            self.redis_client.delete(key)
                            self.redis_client.delete(lockout_key)
            
            return {
                'locked': False,
                'attempts': int(attempts) if attempts else 0
            }
            
        except Exception as e:
            logger.error(f"Failed attempts check failed: {e}")
            return {'locked': False, 'error': str(e)}
    
    def record_failed_attempt(self, identifier: str) -> None:
        """Record failed attempt"""
        try:
            key = f'failed_attempts:{identifier}'
            attempts = self.redis_client.incr(key)
            self.redis_client.expire(key, self.security_config['lockout_duration'])
            
            # Check if should lockout
            if attempts >= self.security_config['max_failed_attempts']:
                lockout_key = f'lockout:{identifier}'
                self.redis_client.setex(
                    lockout_key,
                    self.security_config['lockout_duration'],
                    int(time.time())
                )
                logger.warning(f"Account locked due to failed attempts: {identifier}")
                
        except Exception as e:
            logger.error(f"Failed to record failed attempt: {e}")
    
    def reset_failed_attempts(self, identifier: str) -> None:
        """Reset failed attempts counter"""
        try:
            self.redis_client.delete(f'failed_attempts:{identifier}')
            self.redis_client.delete(f'lockout:{identifier}')
        except Exception as e:
            logger.error(f"Failed to reset failed attempts: {e}")
    
    def validate_input(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data against schema"""
        try:
            errors = []
            
            for field, rules in schema.items():
                value = data.get(field)
                
                # Check required fields
                if rules.get('required', False) and value is None:
                    errors.append(f"Field '{field}' is required")
                    continue
                
                if value is None:
                    continue
                
                # Check type
                expected_type = rules.get('type')
                if expected_type and not isinstance(value, expected_type):
                    errors.append(f"Field '{field}' must be of type {expected_type.__name__}")
                    continue
                
                # Check string length
                if expected_type == str and 'max_length' in rules:
                    if len(value) > rules['max_length']:
                        errors.append(f"Field '{field}' exceeds maximum length of {rules['max_length']}")
                
                # Check numeric range
                if expected_type in (int, float) and 'min' in rules:
                    if value < rules['min']:
                        errors.append(f"Field '{field}' must be at least {rules['min']}")
                
                if expected_type in (int, float) and 'max' in rules:
                    if value > rules['max']:
                        errors.append(f"Field '{field}' must be at most {rules['max']}")
                
                # Check allowed values
                if 'allowed_values' in rules:
                    if value not in rules['allowed_values']:
                        errors.append(f"Field '{field}' must be one of {rules['allowed_values']}")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            return {'valid': False, 'errors': [str(e)]}
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for security"""
        try:
            # Remove path traversal attempts
            filename = os.path.basename(filename)
            
            # Remove dangerous characters
            dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
            for char in dangerous_chars:
                filename = filename.replace(char, '_')
            
            # Limit length
            if len(filename) > 255:
                name, ext = os.path.splitext(filename)
                filename = name[:250] + ext
            
            return filename
            
        except Exception as e:
            logger.error(f"Filename sanitization failed: {e}")
            return "sanitized_filename"
    
    def detect_suspicious_activity(self, identifier: str, activity: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Detect suspicious activity patterns"""
        try:
            # Store activity
            activity_key = f'activity:{identifier}'
            activity_data = {
                'activity': activity,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            self.redis_client.lpush(activity_key, json.dumps(activity_data))
            self.redis_client.ltrim(activity_key, 0, 99)  # Keep last 100 activities
            self.redis_client.expire(activity_key, 3600)  # Expire after 1 hour
            
            # Analyze patterns
            recent_activities = self.redis_client.lrange(activity_key, 0, 9)  # Last 10 activities
            
            suspicious_patterns = []
            
            # Check for rapid requests
            if len(recent_activities) >= 10:
                timestamps = []
                for activity_json in recent_activities:
                    activity_obj = json.loads(activity_json)
                    timestamps.append(datetime.fromisoformat(activity_obj['timestamp']))
                
                # Check if requests are too frequent
                if len(timestamps) >= 5:
                    time_diff = (timestamps[0] - timestamps[-1]).total_seconds()
                    if time_diff < 10:  # 10 requests in less than 10 seconds
                        suspicious_patterns.append('rapid_requests')
            
            # Check for unusual patterns
            activity_types = [json.loads(a)['activity'] for a in recent_activities]
            if len(set(activity_types)) == 1 and len(activity_types) >= 5:
                suspicious_patterns.append('repetitive_activity')
            
            return {
                'suspicious': len(suspicious_patterns) > 0,
                'patterns': suspicious_patterns,
                'activity_count': len(recent_activities)
            }
            
        except Exception as e:
            logger.error(f"Suspicious activity detection failed: {e}")
            return {'suspicious': False, 'error': str(e)}
    
    def create_audit_log(self, user_id: str, action: str, resource: str, 
                        success: bool, metadata: Dict[str, Any] = None) -> None:
        """Create audit log entry"""
        try:
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'action': action,
                'resource': resource,
                'success': success,
                'metadata': metadata or {},
                'ip_address': metadata.get('ip_address', 'unknown') if metadata else 'unknown'
            }
            
            # Store in Redis
            audit_key = f'audit_log:{datetime.now().strftime("%Y-%m-%d")}'
            self.redis_client.lpush(audit_key, json.dumps(audit_entry))
            self.redis_client.ltrim(audit_key, 0, 9999)  # Keep last 10000 entries
            self.redis_client.expire(audit_key, 86400 * 30)  # Keep for 30 days
            
            logger.info(f"Audit log created: {action} by {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
    
    def get_security_report(self) -> Dict[str, Any]:
        """Generate security report"""
        try:
            # Get failed attempts
            failed_attempts = 0
            for key in self.redis_client.scan_iter(match='failed_attempts:*'):
                attempts = self.redis_client.get(key)
                if attempts:
                    failed_attempts += int(attempts)
            
            # Get active API keys
            active_keys = 0
            for key in self.redis_client.scan_iter(match='api_key:*'):
                active_keys += 1
            
            # Get recent audit logs
            today = datetime.now().strftime("%Y-%m-%d")
            audit_key = f'audit_log:{today}'
            recent_logs = self.redis_client.lrange(audit_key, 0, 99)
            
            # Analyze logs
            successful_actions = 0
            failed_actions = 0
            for log_json in recent_logs:
                log = json.loads(log_json)
                if log.get('success', False):
                    successful_actions += 1
                else:
                    failed_actions += 1
            
            return {
                'timestamp': datetime.now().isoformat(),
                'failed_attempts': failed_attempts,
                'active_api_keys': active_keys,
                'recent_actions': {
                    'successful': successful_actions,
                    'failed': failed_actions,
                    'total': len(recent_logs)
                },
                'security_status': 'healthy' if failed_attempts < 10 else 'warning'
            }
            
        except Exception as e:
            logger.error(f"Failed to generate security report: {e}")
            return {'error': str(e)}

if __name__ == '__main__':
    # Test security enhancer
    security = ConnectorSecurityEnhancer()
    
    # Test encryption
    test_data = "sensitive information"
    encrypted = security.encrypt_sensitive_data(test_data)
    decrypted = security.decrypt_sensitive_data(encrypted)
    print(f"Encryption test: {test_data == decrypted}")
    
    # Test API key generation
    api_key = security.generate_api_key("test_user", ["read", "write"])
    validation = security.validate_api_key(api_key)
    print(f"API key validation: {validation}")
    
    # Test rate limiting
    rate_limit = security.check_rate_limit("test_user", "upload")
    print(f"Rate limit check: {rate_limit}")
    
    # Generate security report
    report = security.get_security_report()
    print(f"Security report: {json.dumps(report, indent=2)}")
