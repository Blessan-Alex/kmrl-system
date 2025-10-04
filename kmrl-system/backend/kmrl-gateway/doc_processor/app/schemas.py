from pydantic import BaseModel
try:
    # Pydantic v2
    from pydantic import ConfigDict
    V2 = True
except Exception:
    V2 = False
from datetime import datetime
from typing import Optional
from .models import DocumentStatus

class DocumentBase(BaseModel):
    original_filename: str

class DocumentCreate(DocumentBase):
    s3_key: str

class Document(DocumentBase):
    id: int
    s3_key: str
    upload_time: datetime
    status: DocumentStatus
    extracted_text: Optional[str] = None

    if V2:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True