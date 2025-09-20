class EmailConnector(BaseConnector):
    def __init__(self, imap_server, username, password):
        super().__init__("email", "http://api.kmrl.com")
        self.imap_server = imap_server
        self.username = username
        self.password = password
        
    def fetch_new_documents(self):
        """Fetch emails with attachments since last sync"""
        import imaplib
        import email
        
        mail = imaplib.IMAP4_SSL(self.imap_server)
        mail.login(self.username, self.password)
        mail.select('inbox')
        
        # Search for emails since last sync
        search_criteria = f'SINCE "{self.last_sync.strftime("%d-%b-%Y")}"'
        status, messages = mail.search(None, search_criteria)
        
        documents = []
        for msg_id in messages[0].split():
            status, msg_data = mail.fetch(msg_id, '(RFC822)')
            email_message = email.message_from_bytes(msg_data[0][1])
            
            # Extract attachments
            for part in email_message.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename and self.is_document_file(filename):
                        documents.append(Document(
                            file_data=part.get_payload(decode=True),
                            filename=filename,
                            metadata={
                                "sender": email_message.get("From"),
                                "subject": email_message.get("Subject"),
                                "date": email_message.get("Date"),
                                "source": "email"
                            }
                        ))
        
        mail.close()
        mail.logout()
        return documents
    
    def is_document_file(self, filename):
        """Check if file is a document type we process"""
        doc_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.pptx']
        return any(filename.lower().endswith(ext) for ext in doc_extensions)