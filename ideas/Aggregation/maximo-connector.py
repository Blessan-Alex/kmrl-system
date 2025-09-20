class SharePointConnector(BaseConnector):
    def __init__(self, site_url, client_id, client_secret):
        super().__init__("sharepoint", "http://api.kmrl.com")
        self.site_url = site_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        
    def authenticate(self):
        """Get OAuth2 access token"""
        auth_url = f"{self.site_url}/_api/contextinfo"
        response = requests.post(auth_url, 
                               data={"client_id": self.client_id,
                                    "client_secret": self.client_secret})
        self.access_token = response.json()["access_token"]
    
    def fetch_new_documents(self):
        """Fetch documents modified since last sync"""
        if not self.access_token:
            self.authenticate()
            
        # Query SharePoint REST API
        query_url = f"{self.site_url}/_api/web/lists/getbytitle('Documents')/items"
        params = {
            "$filter": f"Modified gt datetime'{self.last_sync.isoformat()}'",
            "$select": "Title,Modified,FileRef,FileLeafRef"
        }
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        response = requests.get(query_url, params=params, headers=headers)
        documents = []
        
        for item in response.json()["value"]:
            # Download the actual file
            file_url = f"{self.site_url}/_api/web/GetFileByServerRelativeUrl('{item['FileRef']}')/$value"
            file_response = requests.get(file_url, headers=headers)
            
            documents.append(Document(
                file_data=file_response.content,
                filename=item["FileLeafRef"],
                metadata={
                    "title": item["Title"],
                    "modified": item["Modified"],
                    "file_path": item["FileRef"],
                    "source": "sharepoint"
                }
            ))
        
        return documents