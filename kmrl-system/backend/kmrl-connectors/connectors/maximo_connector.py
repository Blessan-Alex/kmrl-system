"""
Maximo Connector for KMRL Maintenance Documents
Handles work order attachments and maintenance documentation
"""

import requests
from typing import List, Dict, Any
import structlog
from datetime import datetime
from base.base_connector import BaseConnector, Document

logger = structlog.get_logger()

class MaximoConnector(BaseConnector):
    """Maximo connector for KMRL maintenance work orders"""
    
    def __init__(self, base_url: str):
        super().__init__("maximo", "http://localhost:3000")
        self.base_url = base_url
        self.token = None
    
    def authenticate(self, credentials: Dict[str, str]) -> str:
        """Authenticate with Maximo and get token"""
        auth_response = requests.post(
            f"{self.base_url}/maximo/oslc/login",
            json={
                "username": credentials["username"],
                "password": credentials["password"]
            }
        )
        
        if auth_response.status_code == 200:
            self.token = auth_response.json()["token"]
            return self.token
        else:
            raise Exception(f"Maximo authentication failed: {auth_response.text}")
    
    def fetch_documents(self, credentials: Dict[str, str], 
                       options: Dict[str, Any] = None) -> List[Document]:
        """Fetch work order attachments since last sync"""
        options = options or {}
        
        try:
            # Authenticate if needed
            if not self.token:
                self.authenticate(credentials)
            
            # Get work orders modified since last sync
            last_sync = self.get_last_sync_time()
            headers = {"Authorization": f"Bearer {self.token}"}
            
            # Enhanced query parameters
            params = {
                "oslc.select": "wonum,description,status,attachments,changedate,location,assetnum,siteid,orgid,priority,worktype",
                "oslc.where": f"changedate>='{last_sync.strftime('%Y-%m-%dT%H:%M:%S')}'",
                "oslc.orderBy": "changedate desc"
            }
            
            response = requests.get(
                f"{self.base_url}/maximo/oslc/os/mxwo",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"Maximo API request failed: {response.status_code} - {response.text}")
            
            work_orders = response.json()
            documents = []
            
            for work_order in work_orders.get("data", []):
                if work_order.get("attachments"):
                    for attachment in work_order["attachments"]:
                        # Check if already processed
                        doc_id = f"{work_order['wonum']}_{attachment['id']}"
                        if self.is_document_processed(doc_id):
                            continue
                        
                        try:
                            # Download attachment with timeout
                            file_response = requests.get(
                                f"{self.base_url}/maximo/oslc/os/mxattachment/{attachment['id']}/content",
                                headers=headers,
                                timeout=60
                            )
                            
                            if file_response.status_code == 200:
                                # Classify department based on work type and description
                                department = self.classify_department(
                                    work_order.get("worktype", ""),
                                    work_order.get("description", "")
                                )
                                
                                document = Document(
                                    source="maximo",
                                    filename=attachment["filename"],
                                    content=file_response.content,
                                    content_type=attachment.get("contentType", "application/octet-stream"),
                                    metadata={
                                        "work_order_id": work_order["wonum"],
                                        "description": work_order["description"],
                                        "status": work_order["status"],
                                        "location": work_order.get("location", ""),
                                        "asset_number": work_order.get("assetnum", ""),
                                        "site_id": work_order.get("siteid", ""),
                                        "org_id": work_order.get("orgid", ""),
                                        "priority": work_order.get("priority", ""),
                                        "work_type": work_order.get("worktype", ""),
                                        "attachment_id": attachment["id"],
                                        "change_date": work_order["changedate"],
                                        "department": department
                                    },
                                    document_id=doc_id,
                                    uploaded_at=datetime.now(),
                                    language="english"  # Maximo typically in English
                                )
                                
                                documents.append(document)
                            else:
                                logger.warning(f"Failed to download attachment {attachment['id']}: {file_response.status_code}")
                                
                        except requests.exceptions.Timeout:
                            logger.warning(f"Timeout downloading attachment {attachment['id']}")
                        except Exception as e:
                            logger.warning(f"Error downloading attachment {attachment['id']}: {e}")
            
            logger.info("Maximo documents fetched", count=len(documents))
            return documents
            
        except Exception as e:
            logger.error("Maximo connector error", error=str(e))
            raise Exception(f"Maximo connector failed: {str(e)}")
    
    def classify_department(self, work_type: str, description: str) -> str:
        """Classify work order by department based on work type and description"""
        text_to_check = f"{work_type} {description}".lower()
        
        # Engineering keywords
        engineering_keywords = [
            "maintenance", "repair", "inspection", "calibration", "installation",
            "mechanical", "electrical", "pneumatic", "hydraulic", "lubrication"
        ]
        
        # Safety keywords
        safety_keywords = [
            "safety", "emergency", "hazard", "ppe", "compliance", "audit"
        ]
        
        # Operations keywords
        operations_keywords = [
            "operations", "service", "cleaning", "housekeeping", "logistics"
        ]
        
        if any(keyword in text_to_check for keyword in engineering_keywords):
            return "engineering"
        elif any(keyword in text_to_check for keyword in safety_keywords):
            return "safety"
        elif any(keyword in text_to_check for keyword in operations_keywords):
            return "operations"
        else:
            return "engineering"  # Default to engineering for Maximo
