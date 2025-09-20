"""
JWT Handler for KMRL Gateway
Handles JWT token generation and validation
"""

import os
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any

class JWTHandler:
    """JWT handler for KMRL authentication"""
    
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "kmrl-jwt-secret-2024")
        self.algorithm = "HS256"
        self.expiration_hours = 24
    
    def generate_token(self, user_data: Dict[str, Any]) -> str:
        """Generate JWT token for user"""
        payload = {
            "user_id": user_data.get("user_id"),
            "username": user_data.get("username"),
            "department": user_data.get("department"),
            "exp": datetime.utcnow() + timedelta(hours=self.expiration_hours),
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return payload"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")
