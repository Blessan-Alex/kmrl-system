#!/usr/bin/env python3
"""
Upload Real Downloaded Files to KMRL Gateway
Reads files from connectors and uploads them to the gateway with proper metadata
"""

import os
import json
import requests
from pathlib import Path
from typing import List, Dict, Any
import structlog
from datetime import datetime

logger = structlog.get_logger()

class GatewayUploader:
    """Uploads real connector files to the KMRL Gateway"""
    
    def __init__(self, gateway_url: str = "http://localhost:3000"):
        self.gateway_url = gateway_url
        self.api_keys = {
            'gmail': 'connector-email',
            'google_drive': 'connector-google-drive', 
            'maximo': 'connector-maximo',
            'whatsapp': 'connector-whatsapp'
        }
        
        # Source mappings
        self.source_mappings = {
            'gmail': 'gmail',
            'google_drive': 'google-drive',
            'maximo': 'maximo',
            'whatsapp': 'whatsapp'
        }
        
        logger.info("Gateway uploader initialized", gateway_url=gateway_url)
    
    def check_gateway_health(self) -> bool:
        """Check if gateway is healthy"""
        try:
            response = requests.get(f"{self.gateway_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                logger.info("Gateway is healthy", status=health_data.get('overall_status'))
                return True
            else:
                logger.error("Gateway health check failed", status_code=response.status_code)
                return False
        except Exception as e:
            logger.error("Gateway not accessible", error=str(e))
            return False
    
    def get_downloaded_files(self) -> List[Dict[str, Any]]:
        """Get list of all downloaded files from connectors"""
        files_to_upload = []
        downloads_dir = Path('downloads')
        
        # Gmail files
        gmail_dir = downloads_dir / 'gmail'
        if gmail_dir.exists():
            for file_path in gmail_dir.glob('*'):
                if file_path.is_file():
                    files_to_upload.append({
                        'path': file_path,
                        'source': 'gmail',
                        'original_name': file_path.name,
                        'content_type': self._get_content_type(file_path),
                        'metadata': {
                            'department': 'operations',
                            'language': 'english',
                            'source_type': 'email_attachment',
                            'downloaded_at': datetime.now().isoformat()
                        }
                    })
        
        # Google Drive files
        gdrive_dir = downloads_dir / 'google_drive'
        if gdrive_dir.exists():
            for file_path in gdrive_dir.glob('*'):
                if file_path.is_file():
                    files_to_upload.append({
                        'path': file_path,
                        'source': 'google_drive',
                        'original_name': file_path.name,
                        'content_type': self._get_content_type(file_path),
                        'metadata': {
                            'department': 'engineering',
                            'language': 'english',
                            'source_type': 'google_drive',
                            'downloaded_at': datetime.now().isoformat()
                        }
                    })
        
        # Maximo files
        maximo_dir = downloads_dir / 'maximo'
        if maximo_dir.exists():
            for file_path in maximo_dir.glob('*.json'):
                if file_path.is_file():
                    files_to_upload.append({
                        'path': file_path,
                        'source': 'maximo',
                        'original_name': file_path.name,
                        'content_type': 'application/json',
                        'metadata': {
                            'department': 'maintenance',
                            'language': 'english',
                            'source_type': 'maximo_work_order',
                            'downloaded_at': datetime.now().isoformat()
                        }
                    })
        
        # WhatsApp files
        whatsapp_dir = downloads_dir / 'whatsapp'
        if whatsapp_dir.exists():
            for file_path in whatsapp_dir.glob('*.txt'):
                if file_path.is_file():
                    files_to_upload.append({
                        'path': file_path,
                        'source': 'whatsapp',
                        'original_name': file_path.name,
                        'content_type': 'text/plain',
                        'metadata': {
                            'department': 'operations',
                            'language': 'english',
                            'source_type': 'whatsapp_message',
                            'downloaded_at': datetime.now().isoformat()
                        }
                    })
        
        logger.info("Found downloaded files", count=len(files_to_upload))
        return files_to_upload
    
    def _get_content_type(self, file_path: Path) -> str:
        """Get content type based on file extension"""
        extension = file_path.suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.svg': 'image/svg+xml',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff',
            '.webp': 'image/webp'
        }
        return content_types.get(extension, 'application/octet-stream')
    
    def upload_file(self, file_info: Dict[str, Any]) -> bool:
        """Upload a single file to the gateway"""
        try:
            file_path = file_info['path']
            source = file_info['source']
            api_key = self.api_keys.get(source)
            
            if not api_key:
                logger.error("No API key found for source", source=source)
                return False
            
            # Prepare file for upload
            files = {
                'file': (
                    file_info['original_name'],
                    open(file_path, 'rb'),
                    file_info['content_type']
                )
            }
            
            # Prepare data
            data = {
                'source': self.source_mappings.get(source, source),
                'metadata': json.dumps(file_info['metadata'])
            }
            
            # Prepare headers
            headers = {
                'X-API-Key': api_key
            }
            
            # Upload to gateway
            response = requests.post(
                f"{self.gateway_url}/api/v1/documents/upload",
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                upload_data = response.json()
                logger.info(
                    "File uploaded successfully",
                    filename=file_info['original_name'],
                    source=source,
                    document_id=upload_data.get('document_id'),
                    status=upload_data.get('status')
                )
                return True
            else:
                logger.error(
                    "File upload failed",
                    filename=file_info['original_name'],
                    source=source,
                    status_code=response.status_code,
                    response=response.text
                )
                return False
                
        except Exception as e:
            logger.error(
                "File upload error",
                filename=file_info['original_name'],
                source=source,
                error=str(e)
            )
            return False
    
    def upload_all_files(self) -> Dict[str, Any]:
        """Upload all downloaded files to the gateway"""
        logger.info("Starting file upload process")
        
        # Check gateway health
        if not self.check_gateway_health():
            logger.error("Gateway is not healthy, aborting upload")
            return {'success': False, 'error': 'Gateway not healthy'}
        
        # Get all downloaded files
        files_to_upload = self.get_downloaded_files()
        
        if not files_to_upload:
            logger.warning("No files found to upload")
            return {'success': True, 'message': 'No files to upload', 'uploaded': 0}
        
        # Upload files
        results = {
            'total_files': len(files_to_upload),
            'uploaded_successfully': 0,
            'upload_failed': 0,
            'success': True,
            'details': []
        }
        
        for file_info in files_to_upload:
            success = self.upload_file(file_info)
            
            if success:
                results['uploaded_successfully'] += 1
                results['details'].append({
                    'filename': file_info['original_name'],
                    'source': file_info['source'],
                    'status': 'success'
                })
            else:
                results['upload_failed'] += 1
                results['details'].append({
                    'filename': file_info['original_name'],
                    'source': file_info['source'],
                    'status': 'failed'
                })
        
        logger.info(
            "Upload process completed",
            total=results['total_files'],
            successful=results['uploaded_successfully'],
            failed=results['upload_failed']
        )
        
        return results

def main():
    """Main function to upload files to gateway"""
    logger.info("Starting KMRL Gateway File Upload Process")
    
    uploader = GatewayUploader()
    results = uploader.upload_all_files()
    
    print("\n" + "="*60)
    print("KMRL GATEWAY FILE UPLOAD RESULTS")
    print("="*60)
    print(f"Total files found: {results['total_files']}")
    print(f"Successfully uploaded: {results['uploaded_successfully']}")
    print(f"Upload failed: {results['upload_failed']}")
    print(f"Success rate: {(results['uploaded_successfully']/results['total_files']*100):.1f}%" if results['total_files'] > 0 else "N/A")
    
    if results['details']:
        print("\nDetailed Results:")
        for detail in results['details']:
            status_icon = "✅" if detail['status'] == 'success' else "❌"
            print(f"  {status_icon} {detail['filename']} ({detail['source']}) - {detail['status']}")
    
    print("\n" + "="*60)
    print("Upload process completed!")
    
    return results

if __name__ == "__main__":
    main()
