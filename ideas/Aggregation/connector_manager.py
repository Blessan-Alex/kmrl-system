class WhatsAppConnector(BaseConnector):
    def __init__(self, whatsapp_api_token, phone_number_id):
        super().__init__("whatsapp", "http://api.kmrl.com")
        self.api_token = whatsapp_api_token
        self.phone_number_id = phone_number_id
        
    def fetch_new_documents(self):
        """Fetch documents from WhatsApp Business API"""
        url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        response = requests.get(url, headers=headers)
        documents = []
        
        for message in response.json()["data"]:
            if message.get("type") == "document":
                # Download document
                media_id = message["document"]["id"]
                media_url = f"https://graph.facebook.com/v17.0/{media_id}"
                media_response = requests.get(media_url, headers=headers)
                
                documents.append(Document(
                    file_data=media_response.content,
                    filename=message["document"]["filename"],
                    metadata={
                        "from": message["from"],
                        "timestamp": message["timestamp"],
                        "source": "whatsapp",
                        "message_id": message["id"]
                    }
                ))
        
        return documents