"""
Batch process a folder of mixed file types using the Phase 2 pipeline
without Redis/Celery. Saves JSON results per file and an index.json.

Usage:
  python3 batch_process_folder.py [--input ./test] [--output ./outputs]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any

from loguru import logger

# Local imports
from document_processor.utils.file_detector import FileTypeDetector
from document_processor.utils.quality_assessor import QualityAssessor
from document_processor.models import FileType, QualityDecision
from document_processor.processors.text_processor import TextProcessor
from document_processor.processors.image_processor import ImageProcessor
from document_processor.processors.cad_processor import CADProcessor
from document_processor.processors.enhanced_cad_processor import EnhancedCADProcessor

# Will be set by main() so helpers can write sidecar files
OUTPUT_DIR_GLOBAL: str | None = None


def route_to_processor(file_type: FileType):
    """Return a processor instance for the file type."""
    if file_type in (FileType.TEXT, FileType.OFFICE, FileType.PDF):
        return TextProcessor()
    if file_type == FileType.IMAGE:
        return ImageProcessor()
    if file_type == FileType.CAD:
        # Prefer enhanced processor
        return EnhancedCADProcessor()
    return None


def process_one_file(file_path: Path) -> Dict[str, Any]:
    """Process a single file end-to-end and return a JSON-serializable dict."""
    started_at = time.time()
    file_id = file_path.stem
    
    detector = FileTypeDetector()
    assessor = QualityAssessor()

    # 1) Detect file type
    file_type, mime_type, detect_conf = detector.detect_file_type(str(file_path))

    # Skip unsupported/unknown types explicitly
    if file_type == FileType.UNKNOWN:
        return {
            "file": str(file_path),
            "skipped": True,
            "reason": "unsupported_or_unknown_type",
        }

    # 2) Quality assessment (category string for assessor)
    quality = assessor.assess_quality(str(file_path), file_type.value)

    # 3) Decision / routing
    decision = quality.decision
    enhancement_needed = decision == QualityDecision.ENHANCE

    processing_result = None
    processor_name = None
    errors: list[str] = []
    warnings: list[str] = []

    if decision == QualityDecision.REJECT:
        errors.append("Rejected by quality assessment")
    else:
        processor = route_to_processor(file_type)
        if processor is None:
            errors.append(f"No processor for file type: {file_type.value}")
        else:
            processor_name = processor.__class__.__name__
            processing_result = processor.process(str(file_path), file_type, file_id=file_id, output_dir=OUTPUT_DIR_GLOBAL)
            errors.extend(processing_result.errors)
            warnings.extend(processing_result.warnings)

    finished_at = time.time()

    result: Dict[str, Any] = {
        "file": str(file_path),
        "file_id": file_id,
        "detected": {
            "type": file_type.value,
            "mime": mime_type,
            "confidence": round(detect_conf, 2),
        },
        "quality": {
            "file_size_valid": quality.file_size_valid,
            "image_quality": quality.image_quality_score,
            "text_density": quality.text_density,
            "overall_score": round(quality.overall_quality_score, 2),
            "decision": quality.decision.value,
            "issues": quality.issues,
            "recommendations": quality.recommendations,
        },
        "processing": {
            "attempted": decision != QualityDecision.REJECT,
            "processor": processor_name,
            "enhancement_needed": enhancement_needed,
        },
        "metrics": {
            "processing_time_sec": round(finished_at - started_at, 3),
        },
        "errors": errors,
        "warnings": warnings,
    }

    if processing_result and processing_result.success:
        result["processing"].update({
            "success": True,
            "text_chars": len(processing_result.extracted_text) if processing_result.extracted_text else 0,
            "metadata": processing_result.metadata,
            "text_preview": (processing_result.extracted_text[:500] + "...") if (processing_result.extracted_text and len(processing_result.extracted_text) > 500) else (processing_result.extracted_text or ""),
        })
        # Also write sidecar full text file
        if OUTPUT_DIR_GLOBAL:
            sidecar = file_path.with_suffix("")
            sidecar_txt = sidecar.name + ".extracted.txt"
            (Path(OUTPUT_DIR_GLOBAL) / sidecar_txt).write_text(processing_result.extracted_text or "", encoding="utf-8")
    elif decision != QualityDecision.REJECT and processing_result is not None:
        result["processing"]["success"] = False

    return result


def main():
    parser = argparse.ArgumentParser(description="Batch process a folder with Phase 2 pipeline")
    parser.add_argument("--input", default="./test", help="Input folder with mixed files")
    parser.add_argument("--output", default="./outputs", help="Output folder for JSON results")
    args = parser.parse_args()

    in_dir = Path(args.input).resolve()
    out_dir = Path(args.output).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    global OUTPUT_DIR_GLOBAL
    OUTPUT_DIR_GLOBAL = str(out_dir)

    if not in_dir.exists() or not in_dir.is_dir():
        logger.error(f"Input directory not found: {in_dir}")
        return 1

    logger.info(f"Scanning: {in_dir}")
    results = []
    for path in sorted(in_dir.iterdir()):
        if not path.is_file():
            continue
        try:
            logger.info(f"Processing file: {path.name}")
            res = process_one_file(path)
            results.append(res)
            # Write per-file JSON
            per_file_json = out_dir / f"{path.stem}.json"
            per_file_json.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.exception(f"Failed processing {path}")
            results.append({
                "file": str(path),
                "error": str(e)
            })

    # Write index.json
    (out_dir / "index.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Done. Wrote {len(results)} results to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


