"""
Configuration settings for KMRL Document Processing System
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base configuration
BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/kmrl_docs")

# MinIO/S3 Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "documents")

# File Processing Limits
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
IMAGE_QUALITY_THRESHOLD = float(os.getenv("IMAGE_QUALITY_THRESHOLD", "0.7"))
TEXT_DENSITY_THRESHOLD = float(os.getenv("TEXT_DENSITY_THRESHOLD", "0.1"))

# OCR Configuration
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "/usr/bin/tesseract")
if os.name == "nt":
    # Try common Windows locations if not overridden
    candidates = [
        TESSERACT_CMD,
        r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
        r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
    ]
    for p in candidates:
        if Path(p).exists():
            TESSERACT_CMD = p
            break
# Prefer Malayalam first so Tesseract biases to mal when mixed content
TESSERACT_LANGUAGES = os.getenv("TESSERACT_LANGUAGES", "mal+eng")

# Tesseract traineddata directory (helps when mal.traineddata is missing)
if os.name == "nt":
    TESSDATA_PREFIX = os.getenv("TESSDATA_PREFIX", r"C:\\Program Files\\Tesseract-OCR")
else:
    TESSDATA_PREFIX = os.getenv("TESSDATA_PREFIX", "/usr/share/tesseract-ocr")

# Image enhancement configuration for OCR
# Options: auto, basic, contrast, scaled, denoised
IMAGE_ENHANCEMENT_METHOD = os.getenv("IMAGE_ENHANCEMENT_METHOD", "auto")
SAVE_ALL_ENHANCED_IMAGES = os.getenv("SAVE_ALL_ENHANCED_IMAGES", "true").lower() == "true"

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOG_DIR / "document_processor.log"

# Supported file types
SUPPORTED_EXTENSIONS = {
    # Technical drawings
    'cad': ['.dwg', '.dxf', '.step', '.stp', '.iges', '.igs'],
    # Images
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'],
    # PDFs
    'pdf': ['.pdf'],
    # Office documents
    'office': ['.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt'],
    # Text files
    'text': ['.txt', '.md', '.rst', '.html', '.xml', '.json', '.csv']
}

# File type priorities for detection
FILE_TYPE_PRIORITIES = ['cad', 'image', 'pdf', 'office', 'text']

