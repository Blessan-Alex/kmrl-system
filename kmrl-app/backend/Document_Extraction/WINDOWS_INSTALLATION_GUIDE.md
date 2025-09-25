# KMRL Document Processing System - Windows Installation Guide

## 🖥️ Windows Setup Requirements

### **1. Python Installation**
```bash
# Download Python 3.10+ from https://python.org
# During installation, check "Add Python to PATH"
# Verify installation:
python --version
pip --version
```

### **2. System Dependencies**

#### **Tesseract OCR (Required)**
```bash
# Download from: https://github.com/UB-Mannheim/tesseract/wiki
# Install to: C:\Program Files\Tesseract-OCR\
# Add to PATH: C:\Program Files\Tesseract-OCR\

# Verify installation:
tesseract --version
```

#### **Malayalam Language Pack for Tesseract**
```bash
# Download mal.traineddata from: https://github.com/tesseract-ocr/tessdata
# Place in: C:\Program Files\Tesseract-OCR\tessdata\
# Or download directly:
# https://github.com/tesseract-ocr/tessdata/raw/main/mal.traineddata
```

#### **Redis Server (Optional - for Celery)**
```bash
# Option 1: Download from https://github.com/microsoftarchive/redis/releases
# Option 2: Use WSL2 with Ubuntu
# Option 3: Use Docker Desktop
# Option 4: Use Redis Cloud (free tier)
```

### **3. Python Dependencies**

#### **Core Requirements**
```bash
# Install from requirements.txt
pip install -r requirements.txt

# If requirements.txt is empty, install manually:
pip install celery
pip install redis
pip install opencv-python
pip install pytesseract
pip install python-magic-bin  # Windows version of python-magic
pip install pydantic
pip install loguru
pip install ezdxf
pip install markitdown
pip install langdetect
pip install pandas
pip install python-docx
pip install PyPDF2
pip install Pillow
pip install numpy
```

#### **Optional Dependencies**
```bash
# For enhanced CAD processing
pip install OCP  # or pythonocc-core

# For testing
pip install pytest

# For development
pip install jupyter
pip install black
pip install flake8
```

### **4. Windows-Specific Configuration**

#### **Environment Variables**
Create a `.env` file in the project root:
```env
# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Tesseract Configuration (Windows paths)
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
TESSERACT_LANGUAGES=mal+eng

# File Processing Limits
MAX_FILE_SIZE_MB=50
IMAGE_QUALITY_THRESHOLD=0.5
TEXT_DENSITY_THRESHOLD=0.3

# Logging
LOG_LEVEL=INFO
```

#### **Path Configuration**
Add to Windows PATH:
```
C:\Program Files\Tesseract-OCR\
C:\Program Files\Tesseract-OCR\tessdata\
```

### **5. Windows-Specific Issues & Solutions**

#### **Issue 1: python-magic not working**
```bash
# Solution: Use python-magic-bin instead
pip uninstall python-magic
pip install python-magic-bin
```

#### **Issue 2: Tesseract not found**
```bash
# Solution: Set explicit path in config.py
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

#### **Issue 3: OpenCV issues**
```bash
# Solution: Install specific version
pip install opencv-python==4.8.1.78
```

#### **Issue 4: Redis connection issues**
```bash
# Solution: Use Redis Cloud or Docker
# Or modify config.py to use different Redis URL
```

### **6. CAD Processing on Windows**

#### **DWG to DXF Conversion**
```bash
# Option 1: Install ODA File Converter (Free)
# Download from: https://www.opendesign.com/guestfiles/oda_file_converter
# Install and add to PATH

# Option 2: Use LibreCAD
# Download from: https://librecad.org/
# Open DWG → Export as DXF

# Option 3: Use FreeCAD
# Download from: https://freecad.org/
# Open DWG → Export as DXF
```

#### **IGES Processing**
```bash
# Install OCP for IGES processing
pip install OCP

# Alternative: pythonocc-core
pip install pythonocc-core
```

### **7. Testing Installation**

#### **Basic Test**
```bash
# Test Python imports
python -c "
import cv2
import pytesseract
import ezdxf
import magic
print('All imports successful!')
"

# Test Tesseract
python -c "
import pytesseract
print(pytesseract.get_tesseract_version())
"

# Test Malayalam
python -c "
import pytesseract
from PIL import Image
import numpy as np
# Create test image with Malayalam text
img = Image.new('RGB', (100, 50), color='white')
print('Malayalam test:', pytesseract.image_to_string(img, lang='mal'))
"
```

#### **Run System Test**
```bash
# Test batch processing
python batch_process_folder.py --input ./tests --output ./outputs/windows_test

# Check outputs
dir outputs\windows_test
```

### **8. Windows-Specific File Paths**

#### **Configuration Updates**
Update `config.py` for Windows paths:
```python
# Windows-specific paths
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT_LANGUAGES = "mal+eng"

# Windows file paths
SUPPORTED_EXTENSIONS = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp'],
    'pdf': ['.pdf'],
    'office': ['.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt'],
    'text': ['.txt', '.md', '.rst', '.html', '.xml', '.json', '.csv'],
    'cad': ['.dwg', '.dxf', '.step', '.stp', '.iges', '.igs']
}
```

### **9. Performance Optimization for Windows**

#### **Memory Management**
```python
# Add to config.py
MAX_FILE_SIZE_MB = 50
IMAGE_QUALITY_THRESHOLD = 0.5
TEXT_DENSITY_THRESHOLD = 0.3

# For large files
import gc
gc.collect()
```

#### **Multiprocessing**
```python
# Windows multiprocessing fix
if __name__ == '__main__':
    # Your code here
    pass
```

### **10. Troubleshooting Windows Issues**

#### **Common Problems & Solutions**

1. **"tesseract is not installed"**
   ```bash
   # Solution: Install Tesseract and add to PATH
   # Or set explicit path in config.py
   ```

2. **"magic library not found"**
   ```bash
   # Solution: Use python-magic-bin
   pip install python-magic-bin
   ```

3. **"Redis connection refused"**
   ```bash
   # Solution: Install Redis or use Redis Cloud
   # Or modify REDIS_URL in config.py
   ```

4. **"OpenCV import error"**
   ```bash
   # Solution: Reinstall OpenCV
   pip uninstall opencv-python
   pip install opencv-python==4.8.1.78
   ```

5. **"DWG conversion failed"**
   ```bash
   # Solution: Install ODA File Converter
   # Or use LibreCAD/FreeCAD for manual conversion
   ```

### **11. Windows Service Setup (Optional)**

#### **Run as Windows Service**
```bash
# Install pywin32
pip install pywin32

# Create service script
python -c "
import win32serviceutil
import win32service
import win32event

class KMRLService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'KMRLDocumentProcessor'
    _svc_display_name_ = 'KMRL Document Processing Service'
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
    
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
    
    def SvcDoRun(self):
        # Start your document processing worker here
        pass

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(KMRLService)
"
```

### **12. Quick Start Commands**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Test installation
python example_usage.py

# 3. Run batch processing
python batch_process_folder.py --input ./tests --output ./outputs/windows_test

# 4. Check results
dir outputs\windows_test
type outputs\windows_test\index.json
```

### **13. Windows-Specific Notes**

- **File Paths**: Use forward slashes or raw strings (`r"C:\path"`)
- **Permissions**: Run as Administrator if needed for system-wide installations
- **Antivirus**: May need to whitelist Python and Tesseract directories
- **Firewall**: Allow Redis connections if using local Redis server
- **Performance**: Consider using SSD for better I/O performance

### **14. Verification Checklist**

- [ ] Python 3.10+ installed and in PATH
- [ ] Tesseract OCR installed and in PATH
- [ ] Malayalam language pack installed
- [ ] All Python dependencies installed
- [ ] Redis server running (if using Celery)
- [ ] DWG conversion tools installed (optional)
- [ ] Test run successful
- [ ] Output files generated correctly

---

**Note**: This guide covers the essential Windows setup. For production deployment, consider using Docker containers or virtual environments for better isolation and management.
