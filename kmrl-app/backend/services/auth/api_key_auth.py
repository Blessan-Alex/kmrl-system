"""
API Key Authentication for KMRL Gateway
Handles authentication for connector services
"""

import os
from fastapi import HTTPException, Depends, Header
import structlog

logger = structlog.get_logger()

class APIKeyAuth:
    """API Key authentication for KMRL connectors"""
    
    def __init__(self):
        self.valid_api_keys = {
            os.getenv("API_KEY", "kmrl-api-key-2024"): "system",
            "connector-email": "email_connector",
            "connector-maximo": "maximo_connector", 
            "connector-google-drive": "google_drive_connector",
            "connector-whatsapp": "whatsapp_connector"
        }
    
    def verify_api_key(self, x_api_key: str = Header(None)) -> str:
        """Verify API key and return service type with improved error handling"""
        try:
            if not x_api_key:
                logger.warning("API key missing from request")
                raise HTTPException(
                    status_code=401, 
                    detail="API key required in X-API-Key header"
                )
            
            if x_api_key not in self.valid_api_keys:
                logger.warning(f"Invalid API key attempt: {x_api_key[:8]}...")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid API key"
                )
            
            service_type = self.valid_api_keys[x_api_key]
            logger.info(f"API key verified for service: {service_type}")
            return service_type
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"API key verification failed: {e}")
            raise HTTPException(
                status_code=500,
                detail="Authentication service error"
            )