# Codebase Audit Report

## Overview
This repository contains Python scripts for data extraction and processing (detection, quality assessment, routing, OCR including Malayalam, CAD handling), with batch and Celery-based async modes. The following audit classifies files as Core, Supportive, Optional, or Safe to Remove.

---

## File-by-File Audit

- Core
  - `config.py` — Central configuration (Redis, OCR, thresholds, enhancement). Required by processors/tasks.
  - `celery_app.py` — Celery app wired to Redis broker/backend.
  - `document_processor/worker.py` — Worker entrypoint.
  - `document_processor/tasks.py` — Celery tasks (`process_document`, `enhance_image`, `ocr_process`).
  - `document_processor/models.py` — Pydantic models for types/results.
  - `document_processor/utils/file_detector.py` — File type detection.
  - `document_processor/utils/quality_assessor.py` — Quality scoring and decision.
  - `document_processor/utils/language_detector.py` — Language detection and flags.
  - `document_processor/processors/base_processor.py` — Base interface and result creation.
  - `document_processor/processors/text_processor.py` — Office/Text/PDF processing with MarkItDown/PyPDF2 + mixed-content OCR.
  - `document_processor/processors/image_processor.py` — Image OCR with enhancement variants and Tesseract configs.
  - `document_processor/processors/cad_processor.py` — Basic CAD metadata extraction.
  - `document_processor/processors/enhanced_cad_processor.py` — Enhanced CAD handling (DXF/Converters).
  - `batch_process_folder.py` — Batch runner; writes per-file JSON and index; auto-generates reports.
  - `report_batch_results.py` — Aggregation of batch `index.json` into `reports/report.json` and `report.md`.
  - `requirements.txt` — Dependency manifest.

- Supportive
  - `AI_CODEBASE_GUIDE.txt` — High-level guide and run instructions.
  - `README.md` — Project overview and usage.
  - `WINDOWS_INSTALLATION_GUIDE.md` — OS-specific setup help.
  - `env.example` — Sample environment variables.
  - `tests/` — Test input files (office, PDFs, images, CAD).
  - `outputs/` — Generated outputs and reports from runs.
  - `logs/` — Runtime logs directory.
  - `cad_parser/processor.py` — Helper for DWG processing using external tools; used by enhanced CAD processor.
  - `document_processor/utils/cad_converter.py` — Optional DWG→DXF conversion helper.
  - `example_usage.py` — Example runners for direct and Celery flows.
  - `IMPLEMENTATION_MAPPING.md`, `IMPLEMENTATION_SUMMARY.md` — Docs describing implemented pieces.
  - `ref/KMRL – Detailed Flow.txt` — Reference of intended pipeline.

- Optional
  - `test_*.py` (various) — Manual and unit-like test scripts for PDFs, OCR, CAD, processing.
  - `plan.txt`, `plan copy.txt` — Planning notes.
  - `dwg_extracted_text.txt`, `extracted_text.txt`, `metro_*.txt`, `unit4_*` — Sample output artifacts; helpful for reference.
  - `oldtestout/` — Historical run outputs; useful for reference.


---

## Dependencies and Coupling Notes
- Processors depend on `config.py`, `models.py`, and `language_detector.py`.
- Celery tasks import processors and rely on `celery_app.py` + `REDIS_URL`.
- Batch runner writes `index.json` used by `report_batch_results.py`.
- Enhanced CAD may call `cad_parser/processor.py` and optional system tools (ODA/libredwg). If removed, CAD falls back to basic processor.
- Image OCR requires system Tesseract; on Windows, ensure `TESSERACT_CMD` detection or env var.

---

## Recommendation
- Keep all Core + Supportive files.
- Optional files help development/testing; keep if useful to your workflow.
- Safe to Remove items can be deleted to slim the repo; they are either outputs or legacy samples and not imported by the application.
