import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text
from sqlalchemy.sql import func
from .database import Base

class DocumentStatus(enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
 

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, index=True)  # was filename
    s3_key = Column(String, index=True)             # was s3_path
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.QUEUED)
    extracted_text = Column(Text)