class MaximoConnector(BaseConnector):
    def __init__(self, maximo_url, username, password):
        super().__init__("maximo", "http://api.kmrl.com")
        self.maximo_url = maximo_url
        self.username = username
        self.password = password
        
    def fetch_new_documents(self):
        """Fetch exported documents from Maximo"""
        # Maximo typically exports to FTP/SFTP or provides REST API
        documents = []
        
        # Method 1: FTP Export Folder
        ftp_host = "maximo-export.kmrl.com"
        ftp = FTP(ftp_host)
        ftp.login(self.username, self.password)
        ftp.cwd("/exports/documents")
        
        file_list = ftp.nlst()
        for filename in file_list:
            if self.is_document_file(filename):
                # Download file
                with open(f"/tmp/{filename}", 'wb') as f:
                    ftp.retrbinary(f'RETR {filename}', f.write)
                
                with open(f"/tmp/{filename}", 'rb') as f:
                    file_data = f.read()
                
                documents.append(Document(
                    file_data=file_data,
                    filename=filename,
                    metadata={
                        "export_date": datetime.now().isoformat(),
                        "source": "maximo",
                        "export_type": "maintenance_docs"
                    }
                ))
                
                # Clean up temp file
                os.remove(f"/tmp/{filename}")
        
        ftp.quit()
        return documents