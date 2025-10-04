-- Migration script to add Document_Extraction enhanced fields to documents table
-- Run this script to update the database schema

-- Add new columns for Document_Extraction integration
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_type_detected VARCHAR(50);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS quality_score FLOAT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS quality_decision VARCHAR(20);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS detection_confidence FLOAT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS language_detected VARCHAR(10);
ALTER TABLE documents ADD COLUMN IF NOT EXISTS needs_translation BOOLEAN DEFAULT FALSE;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS processing_metadata JSON;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS enhancement_applied BOOLEAN DEFAULT FALSE;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS human_review_required BOOLEAN DEFAULT FALSE;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_documents_file_type_detected ON documents(file_type_detected);
CREATE INDEX IF NOT EXISTS idx_documents_quality_score ON documents(quality_score);
CREATE INDEX IF NOT EXISTS idx_documents_language_detected ON documents(language_detected);
CREATE INDEX IF NOT EXISTS idx_documents_human_review_required ON documents(human_review_required);

-- Add comments for documentation
COMMENT ON COLUMN documents.file_type_detected IS 'File type detected by Document_Extraction (cad, image, pdf, office, text)';
COMMENT ON COLUMN documents.quality_score IS 'Quality score from Document_Extraction assessment (0.0-1.0)';
COMMENT ON COLUMN documents.quality_decision IS 'Quality decision from Document_Extraction (process, enhance, reject)';
COMMENT ON COLUMN documents.detection_confidence IS 'Confidence score for file type detection (0.0-1.0)';
COMMENT ON COLUMN documents.language_detected IS 'Language detected by Document_Extraction (mal, eng, etc.)';
COMMENT ON COLUMN documents.needs_translation IS 'Flag indicating if document needs translation';
COMMENT ON COLUMN documents.processing_metadata IS 'Additional metadata from Document_Extraction processing';
COMMENT ON COLUMN documents.enhancement_applied IS 'Flag indicating if image enhancement was applied';
COMMENT ON COLUMN documents.human_review_required IS 'Flag indicating if document requires human review';

-- Update existing records to have default values
UPDATE documents SET 
    file_type_detected = 'unknown',
    quality_score = 0.0,
    quality_decision = 'process',
    detection_confidence = 0.0,
    language_detected = 'unknown',
    needs_translation = FALSE,
    enhancement_applied = FALSE,
    human_review_required = FALSE
WHERE file_type_detected IS NULL;
