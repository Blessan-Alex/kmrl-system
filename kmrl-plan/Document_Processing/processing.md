Excellent question! Based on the KMRL document types and requirements, let me design a comprehensive processing pipeline that handles all file types safely and intelligently.


[1 tool called]

# KMRL Document Processing Pipeline: Complete File Type Handling

Based on the KMRL document types from kmrl.md, here's a comprehensive processing pipeline:

## KMRL Document Types Analysis

From kmrl.md, KMRL handles:
- **Engineering drawings** (DWG, AutoCAD files)
- **Maintenance job cards** (PDF, scanned documents)
- **Incident reports** (PDF, Word, scanned)
- **Vendor invoices** (PDF, scanned)
- **Purchase-order correspondence** (Email, PDF)
- **Regulatory directives** (PDF, scanned)
- **Environmental-impact studies** (PDF, Word)
- **Safety circulars** (PDF, Word)
- **HR policies** (Word, PDF)
- **Legal opinions** (PDF, Word)
- **Board-meeting minutes** (PDF, Word, scanned)
- **Bilingual documents** (English + Malayalam)
- **Embedded tables, photos, signatures**

## Complete Processing Pipeline

### **Step 8: Enhanced Document Processing**

```python
def process_document_pipeline(document, file_url):
    """Complete KMRL document processing pipeline"""
    try:
        # Step 8.1: File Type Detection
        file_type = detect_file_type(document, file_url)
        
        # Step 8.2: Quality Assessment
        quality_result = assess_document_quality(document, file_url, file_type)
        
        if quality_result["status"] == "reject":
            return handle_poor_quality_document(document, quality_result)
        
        # Step 8.3: Route to appropriate processor
        if file_type["category"] == "text_document":
            result = process_text_document(document, file_url, file_type)
        elif file_type["category"] == "image":
            result = process_image_document(document, file_url, file_type)
        elif file_type["category"] == "technical_drawing":
            result = process_technical_drawing(document, file_url, file_type)
        elif file_type["category"] == "mixed_content":
            result = process_mixed_content_document(document, file_url, file_type)
        else:
            result = process_unknown_document(document, file_url, file_type)
        
        # Step 8.4: Quality validation
        if result["confidence"] < 0.7:
            result = flag_for_human_review(document, result)
        
        return result
        
    except Exception as error:
        return handle_processing_error(document, error)
```

### **Step 8.1: File Type Detection**

```python
def detect_file_type(document, file_url):
    """Detect file type and processing requirements"""
    file_extension = Path(file_url).suffix.lower()
    file_size = document.original_file.size
    
    # Technical drawings
    if file_extension in ['.dwg', '.dxf', '.step', '.stp', '.iges', '.igs']:
        return {
            "category": "technical_drawing",
            "type": "cad_file",
            "extension": file_extension,
            "size": file_size,
            "requires_special_processing": True,
            "ocr_required": False,
            "text_extraction": False
        }
    
    # Images
    elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp']:
        return {
            "category": "image",
            "type": "image_file",
            "extension": file_extension,
            "size": file_size,
            "requires_special_processing": False,
            "ocr_required": True,
            "text_extraction": True
        }
    
    # PDFs (could be text, images, or mixed)
    elif file_extension == '.pdf':
        pdf_type = analyze_pdf_content(file_url)
        return {
            "category": pdf_type["category"],  # "text_document", "image", or "mixed_content"
            "type": "pdf_file",
            "extension": file_extension,
            "size": file_size,
            "requires_special_processing": pdf_type["has_images"],
            "ocr_required": pdf_type["has_images"],
            "text_extraction": True,
            "page_count": pdf_type["page_count"],
            "has_images": pdf_type["has_images"],
            "has_text": pdf_type["has_text"]
        }
    
    # Office documents
    elif file_extension in ['.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt']:
        return {
            "category": "text_document",
            "type": "office_file",
            "extension": file_extension,
            "size": file_size,
            "requires_special_processing": False,
            "ocr_required": False,
            "text_extraction": True
        }
    
    # Text files
    elif file_extension in ['.txt', '.md', '.rst', '.html', '.xml', '.json', '.csv']:
        return {
            "category": "text_document",
            "type": "text_file",
            "extension": file_extension,
            "size": file_size,
            "requires_special_processing": False,
            "ocr_required": False,
            "text_extraction": True
        }
    
    else:
        return {
            "category": "unknown",
            "type": "unknown_file",
            "extension": file_extension,
            "size": file_size,
            "requires_special_processing": True,
            "ocr_required": True,
            "text_extraction": True
        }

def analyze_pdf_content(file_url):
    """Analyze PDF content to determine processing approach"""
    try:
        import fitz  # PyMuPDF
        
        doc = fitz.open(file_url)
        page_count = len(doc)
        has_text = False
        has_images = False
        
        for page_num in range(min(3, page_count)):  # Check first 3 pages
            page = doc[page_num]
            text = page.get_text().strip()
            images = page.get_images()
            
            if text:
                has_text = True
            if images:
                has_images = True
        
        doc.close()
        
        if has_text and has_images:
            category = "mixed_content"
        elif has_text:
            category = "text_document"
        elif has_images:
            category = "image"
        else:
            category = "unknown"
        
        return {
            "category": category,
            "page_count": page_count,
            "has_text": has_text,
            "has_images": has_images
        }
        
    except Exception as error:
        logging.error(f"PDF analysis failed: {error}")
        return {
            "category": "unknown",
            "page_count": 0,
            "has_text": False,
            "has_images": True  # Assume images if analysis fails
        }
```

### **Step 8.2: Quality Assessment**

```python
def assess_document_quality(document, file_url, file_type):
    """Assess document quality and determine processing approach"""
    quality_issues = []
    confidence_score = 1.0
    
    # File size check
    if file_type["size"] > 50 * 1024 * 1024:  # 50MB
        quality_issues.append("File too large for processing")
        confidence_score -= 0.3
    
    # Image quality check (for images and PDFs with images)
    if file_type["category"] in ["image", "mixed_content"]:
        image_quality = assess_image_quality(file_url, file_type)
        if image_quality["quality"] == "poor":
            quality_issues.append("Poor image quality detected")
            confidence_score -= 0.4
        elif image_quality["quality"] == "enhanceable":
            quality_issues.append("Image quality can be enhanced")
            confidence_score -= 0.2
    
    # Text density check (for PDFs)
    if file_type["extension"] == ".pdf":
        text_density = check_text_density(file_url)
        if text_density < 0.1:  # Less than 10% text
            quality_issues.append("Low text density - may be image-heavy")
            confidence_score -= 0.2
    
    # Determine processing approach
    if confidence_score < 0.3:
        return {
            "status": "reject",
            "reason": "Poor quality document",
            "issues": quality_issues,
            "confidence": confidence_score,
            "requires_human_review": True
        }
    elif confidence_score < 0.7:
        return {
            "status": "enhance",
            "reason": "Quality issues detected",
            "issues": quality_issues,
            "confidence": confidence_score,
            "requires_human_review": True
        }
    else:
        return {
            "status": "process",
            "reason": "Good quality document",
            "issues": quality_issues,
            "confidence": confidence_score,
            "requires_human_review": False
        }

def assess_image_quality(file_url, file_type):
    """Assess image quality for OCR processing"""
    try:
        from PIL import Image
        import cv2
        import numpy as np
        
        # Load image
        if file_type["extension"] == ".pdf":
            # Extract first page as image
            image = extract_pdf_page_as_image(file_url, 0)
        else:
            image = Image.open(file_url)
        
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Check resolution
        height, width = cv_image.shape[:2]
        if height < 300 or width < 300:
            return {"quality": "poor", "reason": "Low resolution"}
        
        # Check contrast
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        contrast = cv2.Laplacian(gray, cv2.CV_64F).var()
        if contrast < 100:
            return {"quality": "poor", "reason": "Low contrast"}
        elif contrast < 500:
            return {"quality": "enhanceable", "reason": "Moderate contrast"}
        
        # Check blur
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        if blur_score < 100:
            return {"quality": "poor", "reason": "Blurry image"}
        elif blur_score < 500:
            return {"quality": "enhanceable", "reason": "Slightly blurry"}
        
        return {"quality": "good", "reason": "High quality image"}
        
    except Exception as error:
        logging.error(f"Image quality assessment failed: {error}")
        return {"quality": "unknown", "reason": "Assessment failed"}
```

### **Step 8.3: Text Document Processing**

```python
def process_text_document(document, file_url, file_type):
    """Process text-based documents using markitdown"""
    try:
        if file_type["extension"] in ['.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt']:
            # Use markitdown for Office documents
            text = extract_with_markitdown(file_url)
            
        elif file_type["extension"] == '.pdf':
            # Use markitdown for PDFs with text
            text = extract_with_markitdown(file_url)
            
        elif file_type["extension"] in ['.txt', '.md', '.rst', '.html', '.xml', '.json', '.csv']:
            # Direct text extraction
            text = extract_text_file(file_url)
            
        else:
            # Fallback to markitdown
            text = extract_with_markitdown(file_url)
        
        # Validate extracted text
        if not text or len(text.strip()) < 10:
            return {
                "status": "failed",
                "reason": "No text extracted",
                "confidence": 0.0,
                "requires_human_review": True
            }
        
        # Detect language
        language = detect_language(text)
        
        # Save results
        document.text = sanitise_string(text)
        document.token_count = len(tokeniser.encode(text))
        document.language = language
        document.processing_method = "markitdown"
        document.save()
        
        return {
            "status": "success",
            "text_length": len(text),
            "language": language,
            "confidence": 0.9,
            "requires_human_review": False
        }
        
    except Exception as error:
        logging.error(f"Text document processing failed: {error}")
        return {
            "status": "failed",
            "reason": str(error),
            "confidence": 0.0,
            "requires_human_review": True
        }
```

### **Step 8.4: Image Document Processing**

```python
def process_image_document(document, file_url, file_type):
    """Process image documents with OCR"""
    try:
        # Step 1: Image enhancement (if needed)
        enhanced_image = enhance_image_if_needed(file_url, file_type)
        
        # Step 2: Language detection
        language = detect_image_language(enhanced_image)
        
        # Step 3: OCR processing
        if language == "malayalam":
            text = extract_text_with_malayalam_ocr(enhanced_image)
        else:
            text = extract_text_with_english_ocr(enhanced_image)
        
        # Step 4: Quality validation
        if not text or len(text.strip()) < 5:
            return {
                "status": "failed",
                "reason": "No text extracted from image",
                "confidence": 0.0,
                "requires_human_review": True
            }
        
        # Step 5: Confidence assessment
        confidence = assess_ocr_confidence(text, language)
        
        # Save results
        document.text = sanitise_string(text)
        document.token_count = len(tokeniser.encode(text))
        document.language = language
        document.processing_method = "ocr"
        document.ocr_confidence = confidence
        document.save()
        
        return {
            "status": "success",
            "text_length": len(text),
            "language": language,
            "confidence": confidence,
            "requires_human_review": confidence < 0.7
        }
        
    except Exception as error:
        logging.error(f"Image document processing failed: {error}")
        return {
            "status": "failed",
            "reason": str(error),
            "confidence": 0.0,
            "requires_human_review": True
        }

def enhance_image_if_needed(file_url, file_type):
    """Enhance image quality for better OCR"""
    try:
        from PIL import Image, ImageEnhance, ImageFilter
        import cv2
        import numpy as np
        
        # Load image
        image = Image.open(file_url)
        
        # Convert to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Apply enhancements
        enhanced = cv_image.copy()
        
        # 1. Denoise
        enhanced = cv2.fastNlMeansDenoising(enhanced)
        
        # 2. Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
        lab[:,:,0] = clahe.apply(lab[:,:,0])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # 3. Sharpen
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        enhanced = cv2.filter2D(enhanced, -1, kernel)
        
        # 4. Convert back to PIL
        enhanced_pil = Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB))
        
        # Save enhanced image
        enhanced_path = f"/tmp/enhanced_{document.id}.png"
        enhanced_pil.save(enhanced_path)
        
        return enhanced_path
        
    except Exception as error:
        logging.error(f"Image enhancement failed: {error}")
        return file_url  # Return original if enhancement fails

def extract_text_with_malayalam_ocr(image_path):
    """Extract text using Malayalam OCR"""
    try:
        import pytesseract
        
        # Configure Tesseract for Malayalam
        custom_config = r'--oem 3 --psm 6 -l mal+eng'
        
        # Extract text
        text = pytesseract.image_to_string(
            Image.open(image_path),
            config=custom_config
        )
        
        return text
        
    except Exception as error:
        logging.error(f"Malayalam OCR failed: {error}")
        return ""

def extract_text_with_english_ocr(image_path):
    """Extract text using English OCR"""
    try:
        import pytesseract
        
        # Configure Tesseract for English
        custom_config = r'--oem 3 --psm 6 -l eng'
        
        # Extract text
        text = pytesseract.image_to_string(
            Image.open(image_path),
            config=custom_config
        )
        
        return text
        
    except Exception as error:
        logging.error(f"English OCR failed: {error}")
        return ""

def assess_ocr_confidence(text, language):
    """Assess OCR confidence based on text quality"""
    try:
        # Check for common OCR errors
        ocr_errors = 0
        total_chars = len(text)
        
        # Check for random characters
        random_chars = sum(1 for c in text if c in "!@#$%^&*()_+-=[]{}|;':\",./<>?")
        ocr_errors += random_chars
        
        # Check for repeated characters (OCR artifacts)
        repeated_chars = sum(1 for i in range(len(text)-1) if text[i] == text[i+1] and text[i].isalpha())
        ocr_errors += repeated_chars
        
        # Check for mixed case (OCR artifacts)
        mixed_case = sum(1 for i in range(len(text)-1) if text[i].islower() and text[i+1].isupper())
        ocr_errors += mixed_case
        
        # Calculate confidence
        if total_chars == 0:
            return 0.0
        
        confidence = max(0.0, 1.0 - (ocr_errors / total_chars))
        
        return confidence
        
    except Exception as error:
        logging.error(f"OCR confidence assessment failed: {error}")
        return 0.5  # Default confidence
```

### **Step 8.5: Technical Drawing Processing**

```python
def process_technical_drawing(document, file_url, file_type):
    """Process technical drawings and CAD files"""
    try:
        # Technical drawings require special handling
        if file_type["extension"] in ['.dwg', '.dxf']:
            result = process_cad_file(document, file_url, file_type)
        elif file_type["extension"] in ['.step', '.stp', '.iges', '.igs']:
            result = process_step_file(document, file_url, file_type)
        else:
            result = process_unknown_cad_file(document, file_url, file_type)
        
        return result
        
    except Exception as error:
        logging.error(f"Technical drawing processing failed: {error}")
        return {
            "status": "failed",
            "reason": str(error),
            "confidence": 0.0,
            "requires_human_review": True
        }

def process_cad_file(document, file_url, file_type):
    """Process CAD files (DWG, DXF)"""
    try:
        # CAD files cannot be processed automatically
        # They require specialized software and human interpretation
        
        # Extract metadata if possible
        metadata = extract_cad_metadata(file_url)
        
        # Create placeholder text
        text = f"Technical Drawing: {document.file_name}\n"
        text += f"File Type: {file_type['extension'].upper()}\n"
        text += f"File Size: {file_type['size']} bytes\n"
        
        if metadata:
            text += f"Metadata: {metadata}\n"
        
        text += "\nThis is a technical drawing that requires specialized software to view and interpret. "
        text += "Please use appropriate CAD software to open this file."
        
        # Save results
        document.text = text
        document.token_count = len(tokeniser.encode(text))
        document.processing_method = "cad_metadata"
        document.requires_specialized_viewer = True
        document.save()
        
        return {
            "status": "partial",
            "reason": "CAD file requires specialized viewer",
            "confidence": 0.3,
            "requires_human_review": True,
            "requires_specialized_viewer": True
        }
        
    except Exception as error:
        logging.error(f"CAD file processing failed: {error}")
        return {
            "status": "failed",
            "reason": str(error),
            "confidence": 0.0,
            "requires_human_review": True
        }
```

### **Step 8.6: Mixed Content Processing**

```python
def process_mixed_content_document(document, file_url, file_type):
    """Process documents with both text and images"""
    try:
        # Extract text first
        text = extract_with_markitdown(file_url)
        
        # Extract images from PDF
        images = extract_images_from_pdf(file_url)
        
        # Process each image with OCR
        ocr_texts = []
        for i, image_path in enumerate(images):
            try:
                # Enhance image if needed
                enhanced_image = enhance_image_if_needed(image_path, {"extension": ".png"})
                
                # Detect language
                language = detect_image_language(enhanced_image)
                
                # Extract text
                if language == "malayalam":
                    ocr_text = extract_text_with_malayalam_ocr(enhanced_image)
                else:
                    ocr_text = extract_text_with_english_ocr(enhanced_image)
                
                if ocr_text:
                    ocr_texts.append(f"Image {i+1}: {ocr_text}")
                
            except Exception as error:
                logging.error(f"OCR failed for image {i+1}: {error}")
                ocr_texts.append(f"Image {i+1}: [OCR failed]")
        
        # Combine text and OCR results
        combined_text = text
        if ocr_texts:
            combined_text += "\n\n--- Extracted from Images ---\n"
            combined_text += "\n".join(ocr_texts)
        
        # Save results
        document.text = sanitise_string(combined_text)
        document.token_count = len(tokeniser.encode(combined_text))
        document.processing_method = "mixed_content"
        document.save()
        
        return {
            "status": "success",
            "text_length": len(combined_text),
            "images_processed": len(images),
            "confidence": 0.8,
            "requires_human_review": False
        }
        
    except Exception as error:
        logging.error(f"Mixed content processing failed: {error}")
        return {
            "status": "failed",
            "reason": str(error),
            "confidence": 0.0,
            "requires_human_review": True
        }
```

### **Step 8.7: Quality Control and Human Review**

```python
def flag_for_human_review(document, result):
    """Flag document for human review"""
    try:
        # Create human review task
        review_task = HumanReviewTask.objects.create(
            document=document,
            reason=result["reason"],
            confidence=result["confidence"],
            status="pending",
            priority="normal"
        )
        
        # Update document status
        document.status = Document.Status.pending_review
        document.human_review_required = True
        document.save()
        
        # Notify human reviewers
        notify_human_reviewers(review_task)
        
        return {
            "status": "pending_review",
            "reason": "Flagged for human review",
            "confidence": result["confidence"],
            "requires_human_review": True,
            "review_task_id": review_task.id
        }
        
    except Exception as error:
        logging.error(f"Human review flagging failed: {error}")
        return result

def handle_poor_quality_document(document, quality_result):
    """Handle documents that cannot be processed"""
    try:
        # Create rejection record
        rejection = DocumentRejection.objects.create(
            document=document,
            reason=quality_result["reason"],
            issues=quality_result["issues"],
            confidence=quality_result["confidence"]
        )
        
        # Update document status
        document.status = Document.Status.rejected
        document.rejection_reason = quality_result["reason"]
        document.save()
        
        # Notify user
        notify_document_rejection(document, quality_result)
        
        return {
            "status": "rejected",
            "reason": quality_result["reason"],
            "issues": quality_result["issues"],
            "confidence": quality_result["confidence"],
            "requires_human_review": True
        }
        
    except Exception as error:
        logging.error(f"Poor quality document handling failed: {error}")
        return {
            "status": "error",
            "reason": str(error),
            "confidence": 0.0,
            "requires_human_review": True
        }
```

## Error Handling and Fallback Mechanisms

### **1. OCR Error Handling**

```python
def handle_ocr_errors(document, error):
    """Handle OCR processing errors"""
    try:
        # Log error
        logging.error(f"OCR failed for {document.file_name}: {error}")
        
        # Try alternative OCR engines
        alternative_results = []
        
        # Try different OCR configurations
        for config in ["--oem 1 --psm 6", "--oem 2 --psm 6", "--oem 3 --psm 3"]:
            try:
                text = pytesseract.image_to_string(
                    Image.open(document.original_file.url),
                    config=config
                )
                if text and len(text.strip()) > 5:
                    alternative_results.append({
                        "text": text,
                        "config": config,
                        "confidence": 0.5
                    })
            except:
                continue
        
        # If alternatives work, use best result
        if alternative_results:
            best_result = max(alternative_results, key=lambda x: len(x["text"]))
            document.text = sanitise_string(best_result["text"])
            document.processing_method = f"ocr_alternative_{best_result['config']}"
            document.save()
            
            return {
                "status": "success",
                "text_length": len(best_result["text"]),
                "confidence": best_result["confidence"],
                "requires_human_review": True
            }
        
        # If all OCR fails, flag for human review
        return flag_for_human_review(document, {
            "reason": "OCR processing failed",
            "confidence": 0.0
        })
        
    except Exception as error:
        logging.error(f"OCR error handling failed: {error}")
        return {
            "status": "failed",
            "reason": str(error),
            "confidence": 0.0,
            "requires_human_review": True
        }
```

### **2. Quality Control Dashboard**

```python
def create_quality_control_dashboard():
    """Create dashboard for quality control"""
    return {
        "pending_review": Document.objects.filter(
            status=Document.Status.pending_review
        ).count(),
        "rejected_documents": Document.objects.filter(
            status=Document.Status.rejected
        ).count(),
        "low_confidence_documents": Document.objects.filter(
            ocr_confidence__lt=0.7
        ).count(),
        "processing_errors": Document.objects.filter(
            status=Document.Status.errored
        ).count()
    }
```

## Summary

This comprehensive processing pipeline handles all KMRL document types:

✅ **Text Documents**: Markitdown extraction
✅ **Images**: OCR with enhancement and quality control
✅ **PDFs**: Mixed content processing (text + OCR)
✅ **Technical Drawings**: Specialized handling with metadata
✅ **Bilingual Documents**: Malayalam + English OCR
✅ **Quality Control**: Automatic assessment and human review
✅ **Error Handling**: Fallback mechanisms and alternative processing
✅ **Human Review**: Flagging system for problematic documents

The system ensures that **crucial mistakes are minimized** through:
- Quality assessment before processing
- Confidence scoring for all results
- Human review for low-confidence results
- Multiple fallback mechanisms
- Clear error reporting and handling