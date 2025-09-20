# Enhanced Data Preprocessing for KMRL RAG Worker

## Data Preprocessing Workflow Diagram

**Complete Data Preprocessing Pipeline for KMRL Documents:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT: Raw Document Data                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Document from kmrl-document-worker                    │   │
│  │ • text: "Raw extracted text with OCR errors"          │   │
│  │ • document_id: "doc_12345"                           │   │
│  │ • document_type: "maintenance/incident/financial/     │   │
│  │   technical_drawing/general"                         │   │
│  │ • metadata: {source, department, confidence_score}    │   │
│  │ • language: "english/malayalam/mixed"                │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 1: Confidence Assessment               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Confidence Checker                                    │   │
│  │ • High confidence (≥0.7) → Standard processing        │   │
│  │ • Low confidence (<0.7) → Enhanced error correction   │   │
│  │ • Failed processing → Flag for human review           │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 2: Language Processing                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Language Processor                                     │   │
│  │ • Malayalam → Translate to English + Keep original    │   │
│  │ • Mixed language → Process sentence by sentence       │   │
│  │ • English → Standard processing                       │   │
│  │ • Technical drawings → Extract metadata + placeholder │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 3: Document-Type Processing            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Document Type Processor                                │   │
│  │ • Maintenance docs → Section-based cleaning           │   │
│  │ • Incident reports → Event-based cleaning             │   │
│  │ • Financial docs → Table-based cleaning                │   │
│  │ • Technical drawings → Metadata extraction            │   │
│  │ • General docs → Paragraph-based cleaning              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 4: KMRL-Specific Cleaning             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ KMRL Text Cleaner                                     │   │
│  │ • Standardize KMRL terms (Metro, Train, KMRL)         │   │
│  │ • Fix OCR errors specific to Malayalam/English        │   │
│  │ • Remove duplicates and noise                          │   │
│  │ • Preserve technical terminology                       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 5: Quality Validation                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Quality Validator                                      │   │
│  │ • Text length validation (≥10 characters)             │   │
│  │ • OCR error ratio check (<30% single characters)      │   │
│  │ • Meaningful content validation (≥5 words)            │   │
│  │ • Technical drawing metadata validation                │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT: Preprocessed Document               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Clean, standardized text ready for chunking          │   │
│  │ • Language information preserved                        │   │
│  │ • Translation metadata included                         │   │
│  │ • Quality scores and confidence levels                 │   │
│  │ • Technical drawing metadata extracted                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Enhanced Data Preprocessing Implementation

### **Step 1: Comprehensive Text Preprocessor**

```python
# utils/text_processing.py
import re
from typing import List, Dict, Any, Tuple
import logging
from googletrans import Translator
import langdetect
import json

logger = logging.getLogger(__name__)

class TextPreprocessor:
    """Enhanced RAG-specific text preprocessing for KMRL documents"""
    
    def __init__(self):
        # OCR error patterns specific to Malayalam/English KMRL documents
        self.ocr_error_patterns = {
            # Malayalam OCR errors
            r'[|]': 'I',  # Common Malayalam OCR confusion
            r'[0]': 'O',  # Number vs letter confusion
            r'[1]': 'l',  # Number vs letter confusion
            r'[5]': 'S',  # Number vs letter confusion
            # KMRL-specific patterns
            r'[Tt]rain': 'Train',  # Standardize train references
            r'[Mm]etro': 'Metro',  # Standardize metro references
            r'[Kk]mrl': 'KMRL',   # Standardize organization name
        }
        
        # Technical drawing metadata patterns
        self.technical_patterns = {
            'drawing_number': r'Drawing\s*No[.:]\s*([A-Z0-9-]+)',
            'revision': r'Rev[.:]\s*([A-Z0-9]+)',
            'scale': r'Scale[.:]\s*([0-9:]+)',
            'title': r'Title[.:]\s*([^\n]+)',
            'date': r'Date[.:]\s*([0-9/-]+)',
        }
        
        # Initialize translator for Malayalam → English
        self.translator = Translator()
    
    def preprocess_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main preprocessing function for KMRL documents
        Handles all document types including technical drawings
        """
        text = document_data['text']
        metadata = document_data['metadata']
        document_type = document_data.get('document_type', 'general')
        confidence_score = metadata.get('confidence_score', 1.0)
        
        logger.info(f"Processing document {document_data['document_id']} of type {document_type}")
        
        # Step 1: Handle confidence-based processing
        if confidence_score < 0.7:
            logger.warning(f"Low confidence document {document_data['document_id']}: {confidence_score}")
            text = self._enhance_low_confidence_text(text, metadata)
        
        # Step 2: Document-type specific processing
        if document_type == 'technical_drawing':
            text, technical_metadata = self._process_technical_drawing(text, metadata)
            metadata['technical_metadata'] = technical_metadata
        else:
            # Step 3: Language-specific preprocessing
            language = metadata.get('language', 'english')
            if language == 'malayalam' or self._detect_malayalam_content(text):
                text, translation_info = self._process_malayalam_text(text)
                metadata['translation_info'] = translation_info
            elif language == 'mixed':
                text, translation_info = self._process_mixed_language_text(text)
                metadata['translation_info'] = translation_info
        
        # Step 4: KMRL-specific cleaning
        text = self._clean_kmrl_text(text, metadata, document_type)
        
        # Step 5: Quality validation
        if not self._validate_text_quality(text, document_type):
            logger.error(f"Text quality validation failed for {document_data['document_id']}")
            raise ValueError("Text quality too low for RAG processing")
        
        return {
            'text': text,
            'metadata': metadata,
            'preprocessing_applied': True,
            'document_type': document_type
        }
    
    def _process_technical_drawing(self, text: str, metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Process technical drawings (CAD files, engineering drawings)
        Extract metadata and create searchable placeholder text
        """
        logger.info("Processing technical drawing")
        
        technical_metadata = {}
        
        # Extract technical drawing metadata
        for field, pattern in self.technical_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                technical_metadata[field] = match.group(1).strip()
        
        # Create searchable placeholder text
        placeholder_text = self._create_technical_placeholder(technical_metadata, metadata)
        
        # Combine original text with placeholder
        combined_text = f"{text}\n\n[Technical Drawing Metadata: {placeholder_text}]"
        
        return combined_text, technical_metadata
    
    def _create_technical_placeholder(self, technical_metadata: Dict[str, Any], 
                                     metadata: Dict[str, Any]) -> str:
        """Create searchable placeholder text for technical drawings"""
        placeholder_parts = []
        
        # Add drawing information
        if 'drawing_number' in technical_metadata:
            placeholder_parts.append(f"Drawing Number: {technical_metadata['drawing_number']}")
        
        if 'title' in technical_metadata:
            placeholder_parts.append(f"Title: {technical_metadata['title']}")
        
        if 'revision' in technical_metadata:
            placeholder_parts.append(f"Revision: {technical_metadata['revision']}")
        
        if 'scale' in technical_metadata:
            placeholder_parts.append(f"Scale: {technical_metadata['scale']}")
        
        if 'date' in technical_metadata:
            placeholder_parts.append(f"Date: {technical_metadata['date']}")
        
        # Add source and department information
        placeholder_parts.append(f"Source: {metadata.get('source', 'unknown')}")
        placeholder_parts.append(f"Department: {metadata.get('department', 'engineering')}")
        
        # Add document type
        placeholder_parts.append("Document Type: Technical Drawing")
        placeholder_parts.append("Content: Engineering drawing, CAD file, or technical specification")
        
        return " | ".join(placeholder_parts)
    
    def _enhance_low_confidence_text(self, text: str, metadata: Dict[str, Any]) -> str:
        """Enhance low-confidence OCR extractions"""
        logger.info("Applying low-confidence text enhancement")
        
        # Apply aggressive OCR error correction
        for pattern, replacement in self.ocr_error_patterns.items():
            text = re.sub(pattern, replacement, text)
        
        # Remove excessive whitespace and line breaks
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        
        # Try to fix common Malayalam OCR issues
        text = self._fix_malayalam_ocr_errors(text)
        
        return text.strip()
    
    def _process_malayalam_text(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Process Malayalam text: Keep original + Add English translation
        Based on KMRL requirement: 'If mal we need to trans to english'
        """
        logger.info("Processing Malayalam text with translation")
        
        # Detect Malayalam content percentage
        malayalam_chars = re.findall(r'[\u0D00-\u0D7F]', text)
        malayalam_ratio = len(malayalam_chars) / len(text) if text else 0
        
        translation_info = {
            'original_language': 'malayalam',
            'malayalam_ratio': malayalam_ratio,
            'translation_confidence': 0.0
        }
        
        if malayalam_ratio > 0.3:  # Significant Malayalam content
            try:
                # Translate to English for better embedding generation
                translated = self.translator.translate(text, src='ml', dest='en')
                translation_info['translation_confidence'] = translated.confidence
                
                # Combine original Malayalam + English translation
                combined_text = f"{text}\n\n[English Translation: {translated.text}]"
                
                logger.info(f"Translated Malayalam text (confidence: {translated.confidence})")
                return combined_text, translation_info
                
            except Exception as e:
                logger.warning(f"Translation failed: {e}, using original text")
                return text, translation_info
        
        return text, translation_info
    
    def _process_mixed_language_text(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Process mixed Malayalam-English text"""
        logger.info("Processing mixed language text")
        
        # Split by sentences and process each
        sentences = re.split(r'[.!?]+', text)
        processed_sentences = []
        
        for sentence in sentences:
            if self._detect_malayalam_content(sentence):
                # Translate Malayalam sentences
                try:
                    translated = self.translator.translate(sentence, src='ml', dest='en')
                    processed_sentences.append(f"{sentence} ({translated.text})")
                except:
                    processed_sentences.append(sentence)
            else:
                processed_sentences.append(sentence)
        
        return ' '.join(processed_sentences), {
            'original_language': 'mixed',
            'processing_method': 'sentence_by_sentence'
        }
    
    def _detect_malayalam_content(self, text: str) -> bool:
        """Detect if text contains significant Malayalam content"""
        malayalam_chars = re.findall(r'[\u0D00-\u0D7F]', text)
        return len(malayalam_chars) > 5  # Threshold for Malayalam detection
    
    def _fix_malayalam_ocr_errors(self, text: str) -> str:
        """Fix common Malayalam OCR errors"""
        # Common Malayalam OCR error patterns
        malayalam_fixes = {
            r'[|]': 'I',  # Malayalam character confusion
            r'[0]': 'O',  # Number vs Malayalam character
            r'[1]': 'l',  # Number vs Malayalam character
        }
        
        for pattern, replacement in malayalam_fixes.items():
            text = re.sub(pattern, replacement, text)
        
        return text
    
    def _clean_kmrl_text(self, text: str, metadata: Dict[str, Any], 
                        document_type: str) -> str:
        """KMRL-specific text cleaning based on document type"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Standardize KMRL-specific terms
        text = re.sub(r'\bkmrl\b', 'KMRL', text, flags=re.IGNORECASE)
        text = re.sub(r'\bmetro\b', 'Metro', text, flags=re.IGNORECASE)
        text = re.sub(r'\btrain\b', 'Train', text, flags=re.IGNORECASE)
        
        # Document-type specific cleaning
        if document_type == 'maintenance':
            text = self._clean_maintenance_text(text)
        elif document_type == 'incident':
            text = self._clean_incident_text(text)
        elif document_type == 'financial':
            text = self._clean_financial_text(text)
        elif document_type == 'technical_drawing':
            text = self._clean_technical_text(text)
        
        # Remove special characters but preserve Malayalam
        text = re.sub(r'[^\w\s\u0D00-\u0D7F.,!?;:()]', '', text)
        
        # Standardize line breaks
        text = re.sub(r'\n+', '\n', text)
        
        return text.strip()
    
    def _clean_maintenance_text(self, text: str) -> str:
        """Clean maintenance document text"""
        # Standardize maintenance terms
        text = re.sub(r'\bmaintenance\b', 'Maintenance', text, flags=re.IGNORECASE)
        text = re.sub(r'\binspection\b', 'Inspection', text, flags=re.IGNORECASE)
        text = re.sub(r'\bschedule\b', 'Schedule', text, flags=re.IGNORECASE)
        return text
    
    def _clean_incident_text(self, text: str) -> str:
        """Clean incident report text"""
        # Standardize incident terms
        text = re.sub(r'\bincident\b', 'Incident', text, flags=re.IGNORECASE)
        text = re.sub(r'\baccident\b', 'Accident', text, flags=re.IGNORECASE)
        text = re.sub(r'\bsafety\b', 'Safety', text, flags=re.IGNORECASE)
        return text
    
    def _clean_financial_text(self, text: str) -> str:
        """Clean financial document text"""
        # Standardize financial terms
        text = re.sub(r'\bbudget\b', 'Budget', text, flags=re.IGNORECASE)
        text = re.sub(r'\bcost\b', 'Cost', text, flags=re.IGNORECASE)
        text = re.sub(r'\binvoice\b', 'Invoice', text, flags=re.IGNORECASE)
        return text
    
    def _clean_technical_text(self, text: str) -> str:
        """Clean technical drawing text"""
        # Standardize technical terms
        text = re.sub(r'\bdrawing\b', 'Drawing', text, flags=re.IGNORECASE)
        text = re.sub(r'\bengineering\b', 'Engineering', text, flags=re.IGNORECASE)
        text = re.sub(r'\bspecification\b', 'Specification', text, flags=re.IGNORECASE)
        return text
    
    def _validate_text_quality(self, text: str, document_type: str) -> bool:
        """Validate text quality for RAG processing"""
        if not text or len(text.strip()) < 10:
            return False
        
        # Check for excessive OCR errors (too many single characters)
        single_chars = len(re.findall(r'\b\w\b', text))
        if single_chars > len(text) * 0.3:  # More than 30% single characters
            return False
        
        # Check for meaningful content
        words = text.split()
        if len(words) < 5:  # Too few words
            return False
        
        # Special validation for technical drawings
        if document_type == 'technical_drawing':
            # Check if we have at least some metadata
            has_metadata = any(keyword in text.lower() for keyword in 
                             ['drawing', 'technical', 'engineering', 'cad'])
            if not has_metadata:
                return False
        
        return True
    
    def remove_duplicates(self, texts: List[str]) -> List[str]:
        """Remove duplicate text chunks"""
        seen = set()
        unique_texts = []
        
        for text in texts:
            text_hash = hash(text.strip().lower())
            if text_hash not in seen:
                seen.add(text_hash)
                unique_texts.append(text)
        
        logger.info(f"Removed {len(texts) - len(unique_texts)} duplicate chunks")
        return unique_texts
```

### **Step 2: Updated Dependencies**

```bash
# requirements.txt - Enhanced dependencies for KMRL preprocessing
celery==5.3.4
redis==5.0.1
sentence-transformers==2.2.2
faiss-cpu==1.7.4
opensearch-py==2.4.0
numpy==1.24.3
pydantic==2.5.0
python-dotenv==1.0.0

# Enhanced KMRL-specific preprocessing dependencies
googletrans==4.0.0rc1  # For Malayalam → English translation
langdetect==1.0.9      # For language detection
tesseract-ocr==0.3.13  # For Malayalam OCR support
scikit-learn==1.3.0   # For similarity calculations
regex==2023.10.3       # For advanced text processing
```

### **Step 3: Integration with Document Processing Layer**

**From detailed_flow.md Steps 9-17:**
- ✅ **Quality Assessment** (Step 9-10)
- ✅ **OCR Processing** with confidence scoring (Step 11)
- ✅ **Language Detection** (Malayalam/English) (Step 11)
- ✅ **Quality Validation** with confidence thresholds (Step 12-13)
- ✅ **Technical Drawing Processing** (Step 11)

**Standard Input Format:**
```python
document_data = {
    'document_id': 'doc_12345',
    'text': 'Pre-processed, cleaned text',  # Already processed
    'document_type': 'maintenance',  # or 'incident', 'financial', 'technical_drawing', 'general'
    'metadata': {
        'source': 'maximo',
        'department': 'engineering',
        'language': 'english',  # or 'malayalam' or 'mixed'
        'confidence_score': 0.85,  # From document processing
        'ocr_confidence': 0.92,     # From OCR processing
        'processing_method': 'markitdown',  # or 'tesseract'
        'user_id': 'user_123'
    }
}
```

### **Step 4: Technical Drawing Handling**

Based on detailed_flow.md Step 11: *"Technical Drawing Processing"*

```python
def _process_technical_drawing(self, text: str, metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Process technical drawings (CAD files, engineering drawings)
    Extract metadata and create searchable placeholder text
    """
    logger.info("Processing technical drawing")
    
    technical_metadata = {}
    
    # Extract technical drawing metadata
    for field, pattern in self.technical_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            technical_metadata[field] = match.group(1).strip()
    
    # Create searchable placeholder text
    placeholder_text = self._create_technical_placeholder(technical_metadata, metadata)
    
    # Combine original text with placeholder
    combined_text = f"{text}\n\n[Technical Drawing Metadata: {placeholder_text}]"
    
    return combined_text, technical_metadata
```

This enhanced data preprocessing workflow ensures that:

- ✅ **All document types** are handled appropriately (maintenance, incident, financial, technical drawings, general)
- ✅ **Malayalam documents** are properly translated while preserving original text
- ✅ **Low-confidence extractions** receive enhanced processing
- ✅ **Technical drawings** have metadata extracted and searchable placeholders created
- ✅ **Quality validation** prevents poor data from entering the RAG pipeline
- ✅ **KMRL-specific terms** are standardized across all documents
- ✅ **Bilingual content** is handled appropriately for both languages

The RAG worker acts as the **final preprocessing layer** before embedding generation, ensuring all documents meet the quality standards required for effective RAG processing while preserving the multilingual and technical nature of KMRL's document corpus.
