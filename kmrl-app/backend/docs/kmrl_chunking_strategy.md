# KMRL Document Chunking Strategy

## Overview

Based on the KMRL problem statement and document types, this document outlines a comprehensive chunking strategy for processing diverse document types in the KMRL system.

## Document Categories & Chunking Strategies

### 1. **Engineering Drawings & Technical Documents**
**Document Types**: `.dwg`, `.dxf`, `.step`, `.stp`, `.iges`, `.igs`

**Chunking Strategy**: **Metadata-Based Chunking**
- Extract technical metadata (dimensions, materials, specifications)
- Create structured chunks with:
  - Drawing number and revision
  - Component specifications
  - Material properties
  - Dimensional data
- **Chunk Size**: 1-2 sentences per chunk
- **Overlap**: None (each drawing is self-contained)

```python
# Example chunk structure for technical drawings
{
    "chunk_id": "drawing_001_rev_a",
    "content": "Drawing DWG-001 Rev A: Main bearing housing, Material: Cast Iron, Dimensions: 200x150x75mm",
    "metadata": {
        "drawing_number": "DWG-001",
        "revision": "A",
        "component": "Main bearing housing",
        "material": "Cast Iron",
        "dimensions": "200x150x75mm"
    }
}
```

### 2. **Maintenance Job Cards**
**Document Types**: PDFs, Word docs, scanned forms

**Chunking Strategy**: **Section-Based Chunking**
- Split by logical sections:
  - Job identification
  - Safety requirements
  - Step-by-step procedures
  - Parts and materials
  - Sign-off sections
- **Chunk Size**: 2-3 sentences per chunk
- **Overlap**: 1 sentence between sections

```python
# Example chunk structure for maintenance cards
{
    "chunk_id": "maintenance_001_safety",
    "content": "Safety Requirements: Lockout/tagout procedures must be followed. Personal protective equipment required: safety glasses, hard hat, steel-toed boots.",
    "metadata": {
        "job_id": "MAINT-001",
        "section": "safety_requirements",
        "equipment": "traction_motor",
        "priority": "high"
    }
}
```

### 3. **Incident Reports**
**Document Types**: PDFs, Word docs, forms

**Chunking Strategy**: **Event-Based Chunking**
- Split by incident components:
  - Incident summary
  - Timeline of events
  - Root cause analysis
  - Corrective actions
  - Lessons learned
- **Chunk Size**: 3-4 sentences per chunk
- **Overlap**: 1-2 sentences between events

```python
# Example chunk structure for incident reports
{
    "chunk_id": "incident_001_timeline",
    "content": "Timeline: 14:30 - Signal failure detected at MG Road station. 14:35 - Manual signal operation initiated. 14:45 - Train service restored with 15-minute delay.",
    "metadata": {
        "incident_id": "INC-001",
        "section": "timeline",
        "location": "MG Road station",
        "severity": "medium",
        "date": "2024-01-15"
    }
}
```

### 4. **Financial Documents**
**Document Types**: Excel files, PDFs, invoices, purchase orders

**Chunking Strategy**: **Table-Based Chunking**
- Extract tabular data as structured chunks
- Preserve table relationships
- Include row and column headers
- **Chunk Size**: 1 table row or 2-3 related rows
- **Overlap**: Column headers repeated

```python
# Example chunk structure for financial documents
{
    "chunk_id": "invoice_001_line_item",
    "content": "Invoice INV-001: Item: Traction Motor Bearings, Quantity: 4, Unit Price: ₹15,000, Total: ₹60,000, Vendor: ABC Bearings Ltd",
    "metadata": {
        "document_type": "invoice",
        "invoice_number": "INV-001",
        "vendor": "ABC Bearings Ltd",
        "amount": 60000,
        "currency": "INR"
    }
}
```

### 5. **Regulatory Directives & Compliance**
**Document Types**: PDFs, official documents

**Chunking Strategy**: **Paragraph-Based Chunking**
- Split by regulatory sections
- Preserve legal structure
- Include reference numbers
- **Chunk Size**: 2-3 paragraphs per chunk
- **Overlap**: 1 paragraph between sections

```python
# Example chunk structure for regulatory documents
{
    "chunk_id": "regulation_001_section_2",
    "content": "Section 2: Safety Requirements - All metro rail systems must comply with Commissioner of Metro Rail Safety (CMRS) guidelines. Regular safety audits are mandatory every six months.",
    "metadata": {
        "regulation_id": "REG-001",
        "section": "safety_requirements",
        "authority": "CMRS",
        "compliance_level": "mandatory",
        "audit_frequency": "6_months"
    }
}
```

### 6. **Environmental Impact Studies**
**Document Types**: PDFs, technical reports

**Chunking Strategy**: **Chapter-Based Chunking**
- Split by study sections:
  - Executive summary
  - Methodology
  - Findings
  - Recommendations
- **Chunk Size**: 4-5 sentences per chunk
- **Overlap**: 2 sentences between chapters

### 7. **HR Policies & Legal Opinions**
**Document Types**: Word docs, PDFs

**Chunking Strategy**: **Policy-Based Chunking**
- Split by policy sections
- Preserve legal language
- Include policy numbers
- **Chunk Size**: 3-4 sentences per chunk
- **Overlap**: 1 sentence between policies

### 8. **Board Meeting Minutes**
**Document Types**: Word docs, PDFs

**Chunking Strategy**: **Agenda-Based Chunking**
- Split by agenda items
- Preserve discussion context
- Include decisions and actions
- **Chunk Size**: 2-3 sentences per chunk
- **Overlap**: 1 sentence between agenda items

## Multilingual Handling

### **Malayalam-English Documents**
**Strategy**: **Language-Aware Chunking**
- Detect language per sentence
- Create separate chunks for each language
- Maintain context across languages
- **Translation**: Translate Malayalam to English for processing
- **Preservation**: Keep original Malayalam text

```python
# Example multilingual chunk structure
{
    "chunk_id": "multilingual_001_eng",
    "content": "Safety procedures must be followed during maintenance work.",
    "original_malayalam": "പരിപാലന പ്രവർത്തന സമയത്ത് സുരക്ഷാ നടപടികൾ പാലിക്കണം",
    "language": "english",
    "translation_confidence": 0.95
}
```

## Chunking Implementation Strategy

### **Phase 1: Document Classification**
1. **Auto-detect document type** using file extension and content analysis
2. **Apply appropriate chunking strategy** based on document type
3. **Extract metadata** during chunking process

### **Phase 2: Smart Chunking**
1. **Use LangChain's RecursiveCharacterTextSplitter** as base
2. **Implement custom splitters** for each document type
3. **Apply semantic chunking** for complex documents
4. **Maintain chunk relationships** and hierarchy

### **Phase 3: Quality Control**
1. **Validate chunk quality** using confidence scoring
2. **Check for information loss** during chunking
3. **Ensure metadata completeness**
4. **Flag low-quality chunks** for human review

## Chunking Parameters by Document Type

| Document Type | Chunk Size | Overlap | Strategy | Special Handling |
|---------------|------------|---------|----------|-----------------|
| Engineering Drawings | 1-2 sentences | None | Metadata-based | Technical specifications |
| Maintenance Cards | 2-3 sentences | 1 sentence | Section-based | Safety procedures |
| Incident Reports | 3-4 sentences | 1-2 sentences | Event-based | Timeline preservation |
| Financial Docs | 1 table row | Headers | Table-based | Numerical data |
| Regulatory Docs | 2-3 paragraphs | 1 paragraph | Paragraph-based | Legal structure |
| Environmental Studies | 4-5 sentences | 2 sentences | Chapter-based | Technical content |
| HR Policies | 3-4 sentences | 1 sentence | Policy-based | Legal language |
| Board Minutes | 2-3 sentences | 1 sentence | Agenda-based | Decision tracking |

## Implementation Code Structure

```python
class KMRLDocumentChunker:
    def __init__(self):
        self.chunkers = {
            'engineering_drawing': EngineeringDrawingChunker(),
            'maintenance_card': MaintenanceCardChunker(),
            'incident_report': IncidentReportChunker(),
            'financial_document': FinancialDocumentChunker(),
            'regulatory_document': RegulatoryDocumentChunker(),
            'environmental_study': EnvironmentalStudyChunker(),
            'hr_policy': HRPolicyChunker(),
            'board_minutes': BoardMinutesChunker()
        }
    
    def chunk_document(self, document, doc_type):
        chunker = self.chunkers.get(doc_type)
        if chunker:
            return chunker.chunk(document)
        else:
            return self.default_chunker.chunk(document)
```

## Quality Metrics

### **Chunk Quality Indicators**
- **Completeness**: All relevant information captured
- **Coherence**: Chunks make sense independently
- **Metadata Richness**: Sufficient context for retrieval
- **Language Accuracy**: Proper handling of multilingual content

### **Success Criteria**
- **Retrieval Accuracy**: >90% relevant chunks for queries
- **Context Preservation**: Maintain document structure
- **Metadata Completeness**: All required fields populated
- **Processing Speed**: <5 seconds per document

## Next Steps

1. **Implement base chunking classes** for each document type
2. **Create multilingual processing pipeline**
3. **Develop quality validation system**
4. **Test with sample KMRL documents**
5. **Optimize chunking parameters** based on results
6. **Integrate with RAG pipeline**

This strategy ensures that KMRL's diverse document types are processed optimally for RAG applications while preserving their unique characteristics and maintaining high-quality retrieval performance.
