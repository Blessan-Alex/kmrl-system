"""
Maximo Connector for KMRL Document Ingestion
Implements Maximo API-based work order and document processing with incremental sync
"""

import json
import os
import base64
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Generator, Optional
import structlog
from urllib.parse import urljoin

from ..base.enhanced_base_connector import EnhancedBaseConnector, Document, SyncState

logger = structlog.get_logger()

class MaximoConnector(EnhancedBaseConnector):
    """Maximo connector for processing work orders and associated documents"""
    
    def __init__(self, api_endpoint: str, sync_interval_minutes: int = 2):
        super().__init__("maximo", api_endpoint, sync_interval_minutes)
        
        # Maximo configuration
        self.maximo_base_url = os.getenv('MAXIMO_BASE_URL')
        self.maximo_username = os.getenv('MAXIMO_USERNAME')
        self.maximo_password = os.getenv('MAXIMO_PASSWORD')
        
        # Maximo API settings
        self.maximo_api_version = os.getenv('MAXIMO_API_VERSION', 'v1')
        self.work_order_endpoint = f"/maxrest/rest/os/{self.maximo_api_version}/mxwo"
        self.document_endpoint = f"/maxrest/rest/os/{self.maximo_api_version}/mxdoclinks"
        
        # Sync settings
        self.work_order_statuses = os.getenv('MAXIMO_WO_STATUSES', 'WAPPR,INPRG,COMP').split(',')
        self.include_attachments = os.getenv('MAXIMO_INCLUDE_ATTACHMENTS', 'true').lower() == 'true'
        
        self._session = None
        
        logger.info("Maximo connector initialized", 
                   base_url=self.maximo_base_url,
                   api_version=self.maximo_api_version)
    
    def _authenticate_maximo(self) -> bool:
        """Authenticate with Maximo API"""
        try:
            if not all([self.maximo_base_url, self.maximo_username, self.maximo_password]):
                logger.error("Maximo credentials not configured")
                return False
            
            # Create session for authentication
            self._session = requests.Session()
            
            # Maximo uses basic authentication
            self._session.auth = (self.maximo_username, self.maximo_password)
            
            # Test authentication
            test_url = urljoin(self.maximo_base_url, "/maxrest/rest/os/current/mxperson")
            response = self._session.get(test_url, timeout=10)
            
            if response.status_code == 200:
                logger.info("Maximo authentication successful")
                return True
            else:
                logger.error(f"Maximo authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Maximo authentication failed: {e}")
            return False
    
    def _get_maximo_session(self):
        """Get authenticated Maximo session"""
        if not self._session:
            if not self._authenticate_maximo():
                raise Exception("Failed to authenticate with Maximo")
        return self._session
    
    def _query_work_orders(self, query_params: Dict[str, Any] = None, 
                          page_size: int = 100, page_start: int = 0) -> Dict[str, Any]:
        """Query work orders from Maximo"""
        try:
            session = self._get_maximo_session()
            url = urljoin(self.maximo_base_url, self.work_order_endpoint)
            
            params = {
                '_lid': self.maximo_username,
                '_lpwd': self.maximo_password,
                '_format': 'json',
                '_compact': 'true',
                'oslc.pageSize': page_size,
                'oslc.select': 'wonum,description,status,createdate,changeby,location,assetnum,worktype'
            }
            
            if query_params:
                params.update(query_params)
            
            # Add pagination
            if page_start > 0:
                params['oslc.pageStart'] = page_start
            
            response = session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            work_orders = data.get('member', [])
            
            logger.debug(f"Retrieved {len(work_orders)} work orders from Maximo")
            return {
                'work_orders': work_orders,
                'total_count': data.get('totalCount', len(work_orders))
            }
            
        except Exception as e:
            logger.error(f"Maximo work order query failed: {e}")
            raise
    
    def _get_work_order_details(self, wo_num: str) -> Optional[Dict[str, Any]]:
        """Get detailed work order information"""
        try:
            session = self._get_maximo_session()
            url = urljoin(self.maximo_base_url, f"{self.work_order_endpoint}/{wo_num}")
            
            params = {
                '_lid': self.maximo_username,
                '_lpwd': self.maximo_password,
                '_format': 'json'
            }
            
            response = session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('member', [{}])[0] if data.get('member') else None
            
        except Exception as e:
            logger.error(f"Failed to get work order details for {wo_num}: {e}")
            return None
    
    def _create_document_from_work_order(self, wo_info: Dict[str, Any], 
                                        wo_details: Dict[str, Any] = None) -> Document:
        """Create Document object from work order information"""
        # Use detailed info if available, otherwise use basic info
        details = wo_details or wo_info
        
        metadata = {
            'work_order_num': details.get('wonum', ''),
            'work_order_description': details.get('description', ''),
            'work_order_status': details.get('status', ''),
            'work_order_type': details.get('worktype', ''),
            'location': details.get('location', ''),
            'asset_number': details.get('assetnum', ''),
            'created_date': details.get('createdate', ''),
            'created_by': details.get('changeby', ''),
            'source_type': 'maximo_work_order'
        }
        
        # Create filename from work order info
        wo_num = details.get('wonum', 'UNKNOWN')
        filename = f"WO_{wo_num}_details.json"
        
        # Create content as JSON
        content = json.dumps({
            'work_order': details,
            'metadata': metadata
        }, indent=2).encode('utf-8')
        
        # Detect language
        language = self._detect_language(details.get('description', ''))
        
        return Document(
            source="maximo",
            filename=filename,
            content=content,
            content_type="application/json",
            metadata=metadata,
            uploaded_at=datetime.now(),
            language=language,
            original_path=f"maximo://workorder/{wo_num}"
        )
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection for Malayalam/English"""
        # Basic Malayalam Unicode range detection
        malayalam_chars = sum(1 for char in text if '\u0D00' <= char <= '\u0D7F')
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars > 0 and malayalam_chars / total_chars > 0.1:
            return "mal"
        return "eng"
    
    def fetch_documents_incremental(self, credentials: Dict[str, str], 
                                   state: SyncState,
                                   batch_size: int = 50) -> Generator[List[Document], None, None]:
        """Fetch new/modified work orders from Maximo incrementally"""
        try:
            # Build query for incremental sync
            query_params = {}
            if state.last_sync_time > datetime.min:
                date_filter = state.last_sync_time.strftime('%Y-%m-%d')
                query_params['oslc.where'] = f"createdate >= '{date_filter}'"
            
            logger.info(f"Maximo incremental query: {query_params}")
            
            current_batch = []
            page_start = 0
            
            while True:
                # Get work orders from Maximo
                result = self._query_work_orders(query_params, batch_size, page_start)
                work_orders = result['work_orders']
                
                if not work_orders:
                    logger.info("No new/modified work orders found in Maximo")
                    break
                
                for wo_info in work_orders:
                    try:
                        wo_num = wo_info.get('wonum', '')
                        if not wo_num:
                            continue
                        
                        # Get detailed work order information
                        wo_details = self._get_work_order_details(wo_num)
                        
                        # Create document from work order
                        wo_document = self._create_document_from_work_order(wo_info, wo_details)
                        current_batch.append(wo_document)
                        
                        if len(current_batch) >= batch_size:
                            yield current_batch
                            current_batch = []
                    
                    except Exception as e:
                        logger.error(f"Failed to process work order {wo_info.get('wonum', 'unknown')}: {e}")
                        continue
                
                # Yield remaining documents
                if current_batch:
                    yield current_batch
                    current_batch = []
                
                # Check if we should continue
                page_start += batch_size
                if page_start >= result['total_count']:
                    break
                
                # Small delay to prevent overwhelming the system
                import time
                time.sleep(0.1)
            
            logger.info("Maximo incremental fetch completed")
                
        except Exception as e:
            logger.error(f"Maximo incremental fetch failed: {e}")
            raise
    
    def fetch_documents_historical(self, credentials: Dict[str, str], 
                                  start_date: datetime,
                                  batch_size: int = 100) -> Generator[List[Document], None, None]:
        """Fetch historical work orders from Maximo"""
        try:
            logger.info(f"Starting Maximo historical fetch from {start_date}")
            
            # Build query for historical sync
            date_filter = start_date.strftime('%Y-%m-%d')
            query_params = {
                'oslc.where': f"createdate >= '{date_filter}'"
            }
            
            current_batch = []
            page_start = 0
            processed_count = 0
            max_historical = 500  # Limit historical processing
            
            while processed_count < max_historical:
                try:
                    # Get work orders from Maximo
                    result = self._query_work_orders(query_params, batch_size, page_start)
                    work_orders = result['work_orders']
                    
                    if not work_orders:
                        logger.info("No more historical work orders found")
                        break
                    
                    for wo_info in work_orders:
                        try:
                            wo_num = wo_info.get('wonum', '')
                            if not wo_num:
                                continue
                            
                            # Get detailed work order information
                            wo_details = self._get_work_order_details(wo_num)
                            
                            # Create document from work order
                            wo_document = self._create_document_from_work_order(wo_info, wo_details)
                            current_batch.append(wo_document)
                            processed_count += 1
                            
                            if processed_count >= max_historical:
                                break
                            
                            if len(current_batch) >= batch_size:
                                yield current_batch
                                current_batch = []
                        
                        except Exception as e:
                            logger.error(f"Failed to process historical work order {wo_info.get('wonum', 'unknown')}: {e}")
                            continue
                    
                    # Yield remaining documents
                    if current_batch:
                        yield current_batch
                        current_batch = []
                    
                    # Check if we should continue
                    page_start += batch_size
                    if page_start >= result['total_count'] or processed_count >= max_historical:
                        break
                    
                    # Add delay to prevent overwhelming the system
                    import time
                    time.sleep(0.1)
                
                except Exception as e:
                    logger.error(f"Maximo historical batch failed: {e}")
                    break
            
            logger.info(f"Maximo historical fetch completed: {processed_count} documents")
            
        except Exception as e:
            logger.error(f"Maximo historical fetch failed: {e}")
            raise
    
    def get_connector_info(self) -> Dict[str, Any]:
        """Get connector-specific information"""
        status = self.get_sync_status()
        
        # Add Maximo-specific info
        status.update({
            "maximo_base_url": self.maximo_base_url,
            "maximo_username": self.maximo_username,
            "maximo_api_version": self.maximo_api_version,
            "work_order_statuses": self.work_order_statuses,
            "include_attachments": self.include_attachments
        })
        
        return status