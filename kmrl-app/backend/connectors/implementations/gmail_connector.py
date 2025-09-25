"""
Gmail Connector for KMRL Document Ingestion
Implements Gmail API-based email attachment processing with incremental sync
"""

import base64
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Generator, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import structlog

from ..base.enhanced_base_connector import EnhancedBaseConnector, Document, SyncState

logger = structlog.get_logger()

# Gmail API scopes
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/gmail.modify']

class GmailConnector(EnhancedBaseConnector):
    """Gmail connector for processing email attachments"""
    
    def __init__(self, api_endpoint: str, sync_interval_minutes: int = 2):
        super().__init__("gmail", api_endpoint, sync_interval_minutes)
        
        # Use hardcoded paths like reference implementation
        self.credentials_file = os.path.join(os.path.dirname(__file__), "..", "..", "credentials.json")
        self.token_file = os.path.join(os.path.dirname(__file__), "..", "..", "token.json")
        self.oauth2_port = int(os.getenv('OAUTH2_REDIRECT_PORT', '8080'))
        
        self._gmail_service = None
        
        logger.info("Gmail connector initialized")
    
    def _authenticate_gmail(self) -> bool:
        """Authenticate with Gmail API (from reference implementation)"""
        try:
            creds = None
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, GMAIL_SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        logger.error("Gmail credentials file not found", file=self.credentials_file)
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, GMAIL_SCOPES
                    )
                    creds = flow.run_local_server(port=self.oauth2_port)
                
                with open(self.token_file, "w") as token:
                    token.write(creds.to_json())
            
            self._gmail_service = build("gmail", "v1", credentials=creds)
            logger.info("Gmail authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {e}")
            return False
    
    def _get_gmail_service(self):
        """Get authenticated Gmail service"""
        if not self._gmail_service:
            if not self._authenticate_gmail():
                raise Exception("Failed to authenticate with Gmail")
        return self._gmail_service
    
    def _search_emails_with_attachments(self, query: str = "has:attachment", 
                                       max_results: int = 50) -> List[Dict[str, Any]]:
        """Search for emails with attachments"""
        try:
            service = self._get_gmail_service()
            results = service.users().messages().list(
                userId='me', 
                q=query, 
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} emails with attachments")
            return messages
            
        except HttpError as error:
            logger.error(f"Gmail search failed: {error}")
            raise
    
    def _get_email_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed email information"""
        try:
            service = self._get_gmail_service()
            message = service.users().messages().get(userId='me', id=message_id).execute()
            
            if not message or 'payload' not in message:
                logger.warning(f"Invalid email structure for {message_id}")
                return None
            
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            date_str = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            
            # Parse date with timezone handling
            try:
                from email.utils import parsedate_to_datetime
                date = parsedate_to_datetime(date_str)
                # Ensure timezone-aware datetime
                if date.tzinfo is None:
                    from datetime import timezone
                    date = date.replace(tzinfo=timezone.utc)
            except:
                from datetime import timezone
                date = datetime.now(timezone.utc)
            
            return {
                'message_id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'message': message
            }
            
        except HttpError as error:
            logger.error(f"Failed to get email details for {message_id}: {error}")
            return None
    
    def _extract_attachments(self, message_id: str, message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract attachments from email message"""
        attachments = []
        
        try:
            payload = message.get('payload', {})
            if not payload:
                return attachments
            
            def extract_from_parts(parts):
                for part in parts:
                    if part.get('filename'):
                        attachment_id = part['body'].get('attachmentId')
                        if attachment_id:
                            try:
                                service = self._get_gmail_service()
                                attachment = service.users().messages().attachments().get(
                                    userId='me', messageId=message_id, id=attachment_id
                                ).execute()
                                
                                data = attachment['data']
                                file_data = base64.urlsafe_b64decode(data)
                                
                                attachments.append({
                                    'filename': part['filename'],
                                    'mimeType': part['mimeType'],
                                    'data': file_data,
                                    'size': len(file_data)
                                })
                            except Exception as e:
                                logger.error(f"Failed to get attachment {part['filename']}: {e}")
                    
                    if 'parts' in part:
                        extract_from_parts(part['parts'])
            
            if 'parts' in payload:
                extract_from_parts(payload['parts'])
            elif payload.get('filename'):
                attachment_id = payload['body'].get('attachmentId')
                if attachment_id:
                    try:
                        service = self._get_gmail_service()
                        attachment = service.users().messages().attachments().get(
                            userId='me', messageId=message_id, id=attachment_id
                        ).execute()
                        
                        data = attachment['data']
                        file_data = base64.urlsafe_b64decode(data)
                        
                        attachments.append({
                            'filename': payload['filename'],
                            'mimeType': payload['mimeType'],
                            'data': file_data,
                            'size': len(file_data)
                        })
                    except Exception as e:
                        logger.error(f"Failed to get attachment {payload['filename']}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to extract attachments: {e}")
        
        return attachments
    
    def _create_document_from_attachment(self, attachment: Dict[str, Any], 
                                       email_info: Dict[str, Any]) -> Document:
        """Create Document object from email attachment"""
        metadata = {
            'email_subject': email_info['subject'],
            'email_sender': email_info['sender'],
            'email_date': email_info['date'].isoformat(),
            'email_message_id': email_info['message_id'],
            'attachment_size': attachment['size'],
            'attachment_mime_type': attachment['mimeType'],
            'source_type': 'email_attachment'
        }
        
        # Detect language from email content
        language = self._detect_language(email_info['subject'] + " " + str(email_info.get('sender', '')))
        
        return Document(
            source="gmail",
            filename=attachment['filename'],
            content=attachment['data'],
            content_type=attachment['mimeType'],
            metadata=metadata,
            uploaded_at=email_info['date'],
            language=language,
            original_path=f"gmail://{email_info['message_id']}/{attachment['filename']}"
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
        """Fetch new emails with attachments incrementally"""
        try:
            # Build query for incremental sync
            query_parts = ["has:attachment"]
            
            if state.last_sync_time > datetime.min:
                # Only get emails newer than last sync
                date_filter = state.last_sync_time.strftime("%Y/%m/%d")
                query_parts.append(f"after:{date_filter}")
            
            query = " ".join(query_parts)
            logger.info(f"Gmail incremental query: {query}")
            
            # Search for emails
            messages = self._search_emails_with_attachments(query, batch_size)
            
            if not messages:
                logger.info("No new emails with attachments found")
                return
            
            # Process emails in batches
            current_batch = []
            
            for message in messages:
                try:
                    email_info = self._get_email_details(message['id'])
                    if not email_info:
                        continue
                    
                    # Extract attachments
                    attachments = self._extract_attachments(message['id'], email_info['message'])
                    
                    for attachment in attachments:
                        document = self._create_document_from_attachment(attachment, email_info)
                        current_batch.append(document)
                        
                        if len(current_batch) >= batch_size:
                            yield current_batch
                            current_batch = []
                
                except Exception as e:
                    logger.error(f"Failed to process email {message['id']}: {e}")
                    continue
            
            # Yield remaining documents
            if current_batch:
                yield current_batch
                
        except Exception as e:
            logger.error(f"Gmail incremental fetch failed: {e}")
            raise
    
    def fetch_documents_historical(self, credentials: Dict[str, str], 
                                  start_date: datetime,
                                  batch_size: int = 100) -> Generator[List[Document], None, None]:
        """Fetch historical emails with attachments"""
        try:
            # Ensure start_date is timezone-aware
            if start_date.tzinfo is None:
                from datetime import timezone
                start_date = start_date.replace(tzinfo=timezone.utc)
            
            logger.info(f"Starting Gmail historical fetch from {start_date}")
            
            # Build query for historical sync - get ALL emails with attachments
            query = "has:attachment"
            
            # Process in smaller batches for historical data with better error handling
            processed_count = 0
            max_historical = 5000  # Increased limit for historical processing
            batch_count = 0
            
            while processed_count < max_historical:
                try:
                    batch_count += 1
                    logger.info(f"Processing Gmail batch {batch_count}, processed: {processed_count}/{max_historical}")
                    
                    messages = self._search_emails_with_attachments(query, batch_size)
                    
                    if not messages:
                        logger.info("No more historical emails found")
                        break
                    
                    current_batch = []
                    
                    for message in messages:
                        try:
                            email_info = self._get_email_details(message['id'])
                            if not email_info:
                                continue
                            
                            # For historical sync, get ALL emails regardless of date
                            # Only check timezone for consistency
                            email_date = email_info['date']
                            if email_date.tzinfo is None:
                                # Make email_date timezone-aware if it's naive
                                from datetime import timezone
                                email_date = email_date.replace(tzinfo=timezone.utc)
                            
                            attachments = self._extract_attachments(message['id'], email_info['message'])
                            
                            for attachment in attachments:
                                document = self._create_document_from_attachment(attachment, email_info)
                                current_batch.append(document)
                                processed_count += 1
                                
                                if processed_count >= max_historical:
                                    break
                        
                        except Exception as e:
                            logger.error(f"Failed to process historical email {message['id']}: {e}")
                            continue
                    
                    if current_batch:
                        logger.info(f"Gmail batch {batch_count} completed: {len(current_batch)} documents")
                        yield current_batch
                    
                    # Add small delay between batches to prevent rate limiting
                    if batch_count % 5 == 0:
                        import time
                        time.sleep(1)
                    
                    if processed_count >= max_historical:
                        logger.info(f"Reached historical processing limit: {max_historical}")
                        break
                    
                    # Add delay to prevent rate limiting
                    import time
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Gmail historical batch failed: {e}")
                    break
            
            logger.info(f"Gmail historical fetch completed: {processed_count} documents")
            
        except Exception as e:
            logger.error(f"Gmail historical fetch failed: {e}")
            raise
    
    def get_connector_info(self) -> Dict[str, Any]:
        """Get connector-specific information"""
        status = self.get_sync_status()
        
        # Add Gmail-specific info
        try:
            service = self._get_gmail_service()
            profile = service.users().getProfile(userId="me").execute()
            
            status.update({
                "gmail_email": profile.get('emailAddress'),
                "gmail_messages_total": profile.get('messagesTotal'),
                "gmail_threads_total": profile.get('threadsTotal'),
                "credentials_file": self.credentials_file,
                "token_file": self.token_file
            })
        except Exception as e:
            logger.warning(f"Failed to get Gmail profile info: {e}")
            status["gmail_error"] = str(e)
        
        return status
