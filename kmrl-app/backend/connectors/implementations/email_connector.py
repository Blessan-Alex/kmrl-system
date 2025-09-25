"""
Email Connector for KMRL Document Ingestion
Handles email attachments with Malayalam language detection and department classification
"""

import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any
import structlog
from datetime import datetime
from ..base.base_connector import BaseConnector, Document

logger = structlog.get_logger()

class EmailConnector(BaseConnector):
    """Email connector for KMRL document ingestion"""
    
    def __init__(self, imap_host: str, imap_port: int = 993):
        super().__init__("email", "http://localhost:3000")
        self.imap_host = imap_host
        self.imap_port = imap_port
    
    def fetch_documents(self, credentials: Dict[str, str], 
                       options: Dict[str, Any] = None) -> List[Document]:
        """Fetch email attachments since last sync"""
        options = options or {}
        
        try:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(self.imap_host, self.imap_port)
            mail.login(credentials["email"], credentials["password"])
            mail.select("INBOX")
            
            # Search for emails since last sync
            last_sync = self.get_last_sync_time()
            search_criteria = f'SINCE "{last_sync.strftime("%d-%b-%Y")}"'
            
            status, messages = mail.search(None, search_criteria)
            email_ids = messages[0].split()
            
            documents = []
            for email_id in email_ids:
                # Fetch email
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Extract attachments
                for part in email_message.walk():
                    if part.get_content_disposition() == 'attachment':
                        filename = part.get_filename()
                        if filename and self.is_kmrl_document(filename):
                            # Decode filename if needed
                            if filename.startswith('=?UTF-8?'):
                                filename = decode_header(filename)[0][0].decode()
                            
                            # Check if already processed
                            doc_id = f"{email_id.decode()}_{filename}"
                            if self.is_document_processed(doc_id):
                                continue
                            
                            content = part.get_payload(decode=True)
                            
                            # Detect language from email content
                            language = self.detect_language(email_message)
                            
                            document = Document(
                                source="email",
                                filename=filename,
                                content=content,
                                content_type=part.get_content_type(),
                                metadata={
                                    "from": email_message.get("From"),
                                    "subject": email_message.get("Subject"),
                                    "date": email_message.get("Date"),
                                    "message_id": email_id.decode(),
                                    "email_id": email_id.decode(),
                                    "department": self.classify_department(email_message.get("Subject", ""))
                                },
                                document_id=doc_id,
                                uploaded_at=datetime.now(),
                                language=language
                            )
                            
                            documents.append(document)
            
            mail.close()
            mail.logout()
            
            logger.info("Email documents fetched", count=len(documents))
            return documents
            
        except Exception as e:
            logger.error("Email connector error", error=str(e))
            raise Exception(f"Email connector failed: {str(e)}")
    
    def is_kmrl_document(self, filename: str) -> bool:
        """Check if file is a KMRL document type"""
        kmrl_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.pptx', 
                          '.jpg', '.jpeg', '.png', '.tiff', '.dwg', '.dxf',
                          '.step', '.stp', '.iges', '.igs']
        return any(filename.lower().endswith(ext) for ext in kmrl_extensions)
    
    def detect_language(self, email_message) -> str:
        """Detect if email contains Malayalam content"""
        subject = email_message.get("Subject", "")
        body = ""
        
        # Extract email body for better language detection
        # Handle both email message objects and simple text
        if hasattr(email_message, 'walk'):
            # Real email message object
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
        else:
            # Simple text or mock object
            body = str(email_message.get("Body", ""))
        
        # Malayalam Unicode range
        malayalam_chars = "അആഇഈഉഊഋഎഏഐഒഓഔകഖഗഘങചഛജഝഞടഠഡഢണതഥദധനപഫബഭമയരലവശഷസഹളഴറ"
        
        # Check for Malayalam characters in subject and body
        text_to_check = f"{subject} {body}"
        malayalam_count = sum(1 for char in text_to_check if char in malayalam_chars)
        english_count = sum(1 for char in text_to_check if char.isalpha() and char not in malayalam_chars)
        
        if malayalam_count > 0 and english_count > 0:
            return "mixed"
        elif malayalam_count > 0:
            return "malayalam"
        else:
            return "english"
    
    def classify_department(self, subject: str) -> str:
        """Classify email by department based on subject"""
        subject_lower = subject.lower()
        
        # Engineering keywords
        engineering_keywords = [
            "maintenance", "repair", "technical", "equipment", "machinery",
            "work order", "inspection", "calibration", "troubleshooting",
            "breakdown", "fault", "defect", "installation", "commissioning",
            "engineering", "mechanical", "electrical", "civil", "structural"
        ]
        
        # Finance keywords
        finance_keywords = [
            "finance", "invoice", "payment", "budget", "cost", "expense",
            "revenue", "accounting", "financial", "billing", "purchase",
            "procurement", "tender", "contract", "quotation", "price",
            "amount", "funds", "allocation", "disbursement"
        ]
        
        # Safety keywords
        safety_keywords = [
            "safety", "incident", "accident", "hazard", "risk", "emergency",
            "compliance", "regulatory", "audit", "inspection", "violation",
            "training", "procedure", "protocol", "standard", "ppe",
            "workplace", "occupational", "health", "environment"
        ]
        
        # HR keywords
        hr_keywords = [
            "hr", "personnel", "employee", "staff", "training", "recruitment",
            "attendance", "leave", "salary", "benefits", "performance",
            "appraisal", "disciplinary", "promotion", "transfer", "resignation"
        ]
        
        # Operations keywords
        operations_keywords = [
            "operations", "schedule", "timetable", "service", "passenger",
            "station", "train", "route", "depot", "control", "dispatch",
            "timetable", "service", "passenger", "commuter", "metro"
        ]
        
        # Executive keywords
        executive_keywords = [
            "board", "meeting", "minutes", "policy", "decision", "approval",
            "strategy", "planning", "review", "report", "presentation",
            "executive", "management", "director", "ceo", "md"
        ]
        
        # Check for department keywords
        if any(word in subject_lower for word in engineering_keywords):
            return "engineering"
        elif any(word in subject_lower for word in finance_keywords):
            return "finance"
        elif any(word in subject_lower for word in safety_keywords):
            return "safety"
        elif any(word in subject_lower for word in hr_keywords):
            return "hr"
        elif any(word in subject_lower for word in operations_keywords):
            return "operations"
        elif any(word in subject_lower for word in executive_keywords):
            return "executive"
        else:
            return "general"
