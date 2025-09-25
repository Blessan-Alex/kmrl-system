#!/usr/bin/env python3
"""
Unified KMRL Document Downloader
Downloads documents from all connectors using the unified connector interface
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import structlog
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import unified connectors
from ..implementations.gmail_connector import GmailConnector
from ..implementations.gdrive_connector import GoogleDriveConnector
from ..implementations.maximo_connector import MaximoConnector
from ..implementations.whatsapp_connector import WhatsAppConnector

logger = structlog.get_logger()

class UnifiedDownloader:
    """Unified downloader using the new connector architecture"""
    
    def __init__(self, max_documents_per_source: int = 50):
        self.max_documents_per_source = max_documents_per_source
        
        # API endpoint (could be local file system for demo)
        self.api_endpoint = os.getenv('API_ENDPOINT', 'file://downloads')
        
        # Create download directories
        self.base_download_dir = Path('downloads')
        self.gmail_dir = self.base_download_dir / 'gmail'
        self.gdrive_dir = self.base_download_dir / 'google_drive'
        self.maximo_dir = self.base_download_dir / 'maximo'
        self.whatsapp_dir = self.base_download_dir / 'whatsapp'
        
        # Create directories
        for directory in [self.base_download_dir, self.gmail_dir, self.gdrive_dir, self.maximo_dir, self.whatsapp_dir]:
            directory.mkdir(exist_ok=True)
        
        # Initialize connectors
        self.connectors = {
            'gmail': GmailConnector(self.api_endpoint),
            'google_drive': GoogleDriveConnector(self.api_endpoint),
            'maximo': MaximoConnector(self.api_endpoint),
            'whatsapp': WhatsAppConnector(self.api_endpoint)
        }
        
        logger.info("Unified downloader initialized", 
                   max_documents=max_documents_per_source,
                   api_endpoint=self.api_endpoint)
    
    def get_connector_credentials(self, connector_name: str) -> Dict[str, Any]:
        """Get credentials for a specific connector"""
        credentials = {}
        
        if connector_name == 'gmail':
            credentials = {
                'credentials_file': self.connectors['gmail'].credentials_file,
                'token_file': self.connectors['gmail'].token_file
            }
        
        elif connector_name == 'google_drive':
            credentials = {
                'credentials_file': self.connectors['gdrive'].credentials_file,
                'token_file': self.connectors['gdrive'].token_file
            }
        
        elif connector_name == 'maximo':
            credentials = {
                'maximo_base_url': self.connectors['maximo'].maximo_base_url,
                'maximo_username': self.connectors['maximo'].maximo_username,
                'maximo_password': self.connectors['maximo'].maximo_password
            }
        
        elif connector_name == 'whatsapp':
            credentials = {
                'whatsapp_phone_number_id': self.connectors['whatsapp'].whatsapp_phone_number_id,
                'whatsapp_access_token': self.connectors['whatsapp'].whatsapp_access_token
            }
        
        return credentials
    
    def save_document_locally(self, document, connector_name: str) -> str:
        """Save document to local filesystem"""
        try:
            # Determine target directory
            if connector_name == 'gmail':
                target_dir = self.gmail_dir
            elif connector_name == 'google_drive':
                target_dir = self.gdrive_dir
            elif connector_name == 'maximo':
                target_dir = self.maximo_dir
            elif connector_name == 'whatsapp':
                target_dir = self.whatsapp_dir
            else:
                target_dir = self.base_download_dir
            
            # Create filename with timestamp
            timestamp = document.uploaded_at.strftime("%Y%m%d_%H%M%S")
            safe_filename = self.make_safe_filename(document.filename)
            filepath = target_dir / f"{timestamp}_{safe_filename}"
            
            # Handle duplicate filenames
            counter = 1
            original_path = filepath
            while filepath.exists():
                name, ext = os.path.splitext(original_path)
                filepath = Path(f"{name}_{counter}{ext}")
                counter += 1
            
            # Save file content
            with open(filepath, 'wb') as f:
                f.write(document.content)
            
            # Save metadata
            metadata_file = filepath.with_suffix(filepath.suffix + '.metadata.json')
            metadata = {
                'source': document.source,
                'filename': document.filename,
                'content_type': document.content_type,
                'language': document.language,
                'size': document.size,
                'checksum': document.checksum,
                'uploaded_at': document.uploaded_at.isoformat(),
                'metadata': document.metadata,
                'original_path': document.original_path,
                'connector': connector_name,
                'downloaded_at': datetime.now().isoformat()
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Saved document: {filepath.name}", 
                       source=connector_name,
                       size=document.size,
                       language=document.language)
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save document {document.filename}: {e}")
            return None
    
    def make_safe_filename(self, filename: str) -> str:
        """Make filename safe for filesystem"""
        import re
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        return safe_name[:100]  # Limit length
    
    def download_from_connector(self, connector_name: str, historical_days: int = None) -> Dict[str, Any]:
        """Download documents from a specific connector"""
        try:
            logger.info(f"Starting download from {connector_name}")
            
            connector = self.connectors[connector_name]
            credentials = self.get_connector_credentials(connector_name)
            
            downloaded_files = []
            total_documents = 0
            
            # Check if connector is properly configured
            if not credentials or all(not v for v in credentials.values()):
                logger.warning(f"{connector_name} connector not configured, skipping")
                return {
                    'connector': connector_name,
                    'status': 'skipped',
                    'reason': 'not_configured',
                    'documents': 0,
                    'files': []
                }
            
            # Perform sync
            if historical_days:
                # Historical sync
                result = connector.sync_historical(credentials, days_back=historical_days)
                sync_type = 'historical'
            else:
                # Incremental sync
                result = connector.sync_incremental(credentials)
                sync_type = 'incremental'
            
            if result.get('status') == 'completed':
                total_documents = result.get('total_documents', 0)
                
                # For demo purposes, we'll simulate document processing
                # In a real implementation, documents would be processed during sync
                logger.info(f"{connector_name} {sync_type} sync completed", 
                           documents=total_documents,
                           batches=result.get('batches_processed', 0))
                
                # Since we're not actually uploading to API, we'll create a summary
                summary_file = self.base_download_dir / f"{connector_name}_sync_summary.json"
                summary_data = {
                    'connector': connector_name,
                    'sync_type': sync_type,
                    'timestamp': datetime.now().isoformat(),
                    'result': result,
                    'status': 'completed'
                }
                
                with open(summary_file, 'w') as f:
                    json.dump(summary_data, f, indent=2)
                
                downloaded_files.append(str(summary_file))
            
            elif result.get('status') == 'skipped':
                logger.info(f"{connector_name} sync skipped: {result.get('reason', 'unknown')}")
            
            else:
                logger.warning(f"{connector_name} sync failed or returned unexpected status")
            
            return {
                'connector': connector_name,
                'status': result.get('status', 'unknown'),
                'documents': total_documents,
                'files': downloaded_files,
                'errors': result.get('errors', 0)
            }
            
        except Exception as e:
            logger.error(f"Download from {connector_name} failed: {e}")
            return {
                'connector': connector_name,
                'status': 'error',
                'error': str(e),
                'documents': 0,
                'files': []
            }
    
    def download_all_connectors(self, historical_days: int = None) -> Dict[str, Any]:
        """Download documents from all connectors"""
        logger.info("Starting unified download from all connectors")
        
        results = {}
        total_documents = 0
        total_files = 0
        
        for connector_name in self.connectors.keys():
            try:
                result = self.download_from_connector(connector_name, historical_days)
                results[connector_name] = result
                total_documents += result.get('documents', 0)
                total_files += len(result.get('files', []))
                
            except Exception as e:
                logger.error(f"Failed to download from {connector_name}: {e}")
                results[connector_name] = {
                    'connector': connector_name,
                    'status': 'error',
                    'error': str(e),
                    'documents': 0,
                    'files': []
                }
        
        # Create overall summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_connectors': len(self.connectors),
            'total_documents': total_documents,
            'total_files': total_files,
            'results': results,
            'download_directory': str(self.base_download_dir)
        }
        
        # Save summary
        summary_file = self.base_download_dir / 'unified_download_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info("Unified download completed", 
                   total_documents=total_documents,
                   total_files=total_files,
                   summary_file=str(summary_file))
        
        return summary
    
    def get_connector_status(self) -> Dict[str, Any]:
        """Get status of all connectors"""
        status = {}
        
        for connector_name, connector in self.connectors.items():
            try:
                connector_status = connector.get_sync_status()
                status[connector_name] = connector_status
            except Exception as e:
                status[connector_name] = {
                    'source': connector_name,
                    'status': 'error',
                    'error': str(e)
                }
        
        return status
    
    def check_connector_configuration(self) -> Dict[str, Any]:
        """Check configuration status of all connectors"""
        config_status = {}
        
        for connector_name in self.connectors.keys():
            credentials = self.get_connector_credentials(connector_name)
            configured = any(v for v in credentials.values() if v)
            
            config_status[connector_name] = {
                'configured': configured,
                'credentials': {k: bool(v) for k, v in credentials.items()}
            }
        
        return config_status

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified KMRL Document Downloader')
    parser.add_argument('--connector', choices=['gmail', 'google_drive', 'maximo', 'whatsapp', 'all'],
                       default='all', help='Connector to download from')
    parser.add_argument('--historical', type=int, help='Number of days for historical sync')
    parser.add_argument('--max-docs', type=int, default=50, help='Max documents per source')
    parser.add_argument('--status', action='store_true', help='Show connector status')
    parser.add_argument('--config', action='store_true', help='Show configuration status')
    
    args = parser.parse_args()
    
    # Initialize downloader
    downloader = UnifiedDownloader(max_documents_per_source=args.max_docs)
    
    if args.status:
        print("🔍 Connector Status:")
        print("=" * 50)
        status = downloader.get_connector_status()
        for connector_name, connector_status in status.items():
            print(f"\n📧 {connector_name.upper()}:")
            for key, value in connector_status.items():
                print(f"  {key}: {value}")
    
    elif args.config:
        print("⚙️  Connector Configuration:")
        print("=" * 50)
        config = downloader.check_connector_configuration()
        for connector_name, config_status in config.items():
            print(f"\n📧 {connector_name.upper()}:")
            print(f"  Configured: {config_status['configured']}")
            for cred_key, cred_value in config_status['credentials'].items():
                print(f"  {cred_key}: {'✅' if cred_value else '❌'}")
    
    else:
        print("🚀 Starting Unified KMRL Document Download")
        print("=" * 50)
        
        if args.connector == 'all':
            summary = downloader.download_all_connectors(historical_days=args.historical)
        else:
            result = downloader.download_from_connector(args.connector, historical_days=args.historical)
            summary = {
                'timestamp': datetime.now().isoformat(),
                'results': {args.connector: result}
            }
        
        print(f"\n🎉 Download Complete!")
        print(f"📊 Summary: {summary}")

if __name__ == "__main__":
    main()
