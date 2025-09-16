# Base Connector Class
class BaseConnector:
    def __init__(self, source_name, api_endpoint):
        self.source_name = source_name
        self.api_endpoint = api_endpoint
        self.last_sync = None
        
    def sync_documents(self):
        """Main sync method - runs every 5-15 minutes"""
        new_documents = self.fetch_new_documents()
        for doc in new_documents:
            self.upload_to_api(doc)
        self.update_last_sync()
    
    def upload_to_api(self, document):
        """Upload document to unified API"""
        payload = {
            "file": document.file_data,
            "filename": document.filename,
            "source": self.source_name,
            "metadata": document.metadata,
            "uploaded_by": document.user_id
        }
        response = requests.post(f"{self.api_endpoint}/documents/upload", 
                               files=payload)
        return response.json()