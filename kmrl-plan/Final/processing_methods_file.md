Text Documents

16. Save Processing Results
    ├── Extracted text
    ├── Token count
    ├── Language detection
    ├── Processing method
    ├── OCR confidence (if applicable)
    ├── Metadata
    └── Status update

17. Index for Search
    ├── Document ID
    ├── Title
    ├── Content
    ├── Summary
    ├── Department
    ├── Priority
    ├── Action items
    ├── Deadlines
    ├── Source
    ├── Uploaded by
    ├── Created at
    ├── Processed at
    └── Metadata

18. Send Notifications
    ├── Department users
    ├── Priority alerts
    ├── Deadline notifications
    └── Processing completion

19. Document Ready
    ├── Available for search
    ├── Accessible to users
    ├── Notifications sent
    └── Status: Complete


Images

Office Documents (.docx, .doc, .xlsx, .xls, .pptx, .ppt)
├── Method: Markitdown
├── Confidence: 0.9
├── Human Review: Not required
└── Processing Time: 5-10 seconds

Text Files (.txt, .md, .rst, .html, .xml, .json, .csv)
├── Method: Direct extraction
├── Confidence: 0.95
├── Human Review: Not required
└── Processing Time: 1-3 seconds

PDFs with Text
├── Method: Markitdown
├── Confidence: 0.8
├── Human Review: Not required
└── Processing Time: 10-20 seconds

Technical Drawings

Images (.jpg, .jpeg, .png, .gif, .bmp, .tiff, .tif, .webp)
├── Method: OCR
├── Enhancement: Automatic if needed
├── Language: Auto-detect (Malayalam/English)
├── Confidence: 0.6-0.9
├── Human Review: If confidence < 0.7
└── Processing Time: 30-60 seconds

Mixed Content

CAD Files (.dwg, .dxf)
├── Method: Metadata extraction
├── Confidence: 0.3
├── Human Review: Required
├── Specialized Viewer: Required
└── Processing Time: 5-10 seconds

STEP Files (.step, .stp, .iges, .igs)
├── Method: Metadata extraction
├── Confidence: 0.3
├── Human Review: Required
├── Specialized Viewer: Required
└── Processing Time: 5-10 seconds

Quality Control Flow

PDFs with Images + Text
├── Method: Markitdown + OCR
├── Text extraction: Markitdown
├── Image processing: OCR
├── Confidence: 0.8
├── Human Review: Not required
└── Processing Time: 45-90 seconds


Error Handling Flow
Quality Assessment
├── File Size Check
│   ├── < 50MB: Good
│   ├── 50-100MB: Warning
│   └── > 100MB: Reject
├── Image Quality Check
│   ├── Resolution: ≥ 300x300
│   ├── Contrast: ≥ 100
│   ├── Blur: < 100
│   └── Quality: Good/Enhanceable/Poor
├── Text Density Check
│   ├── ≥ 10%: Good
│   ├── 5-10%: Warning
│   └── < 5%: Poor
└── Confidence Scoring
    ├── ≥ 0.7: Process
    ├── 0.3-0.7: Enhance + Review
    └── < 0.3: Reject