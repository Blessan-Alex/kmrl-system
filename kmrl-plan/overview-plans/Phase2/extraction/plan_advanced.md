# 🔹 Advanced Document Processing Workflow (Production)

### Flow

1. **Worker picks message**

   * Consumer reads from Kafka/Redis Streams.
   * Fetch file from MinIO.
   * Re-check file type (magic bytes, not just extension).

2. **File classification & routing**

   * **Technical drawings (.dwg/.step/.iges)** → ODA/Aspose → DXF → ezdxf parse → metadata + preview PNG.
   * **Images** → OpenCV quality check → if low quality → image enhancement (deskew, denoise, upscaling). Then OCR (Tesseract/PaddleOCR + fallback cloud OCR).
   * **PDFs** → PyMuPDF extract text; per-page check for image vs text; hybrid pipeline (text layer + OCR for image pages).
   * **Office docs** → python-docx/openpyxl/pptx or convert with LibreOffice → extract text/images.
   * **Text/CSV/JSON** → direct parsing; large CSVs → flag to data ingestion route.
   * **Unknown** → quarantine bucket + human review task.

3. **OCR & NLP enrichment**

   * OCR with multilingual engine (English + Malayalam).
   * Language detection → mark `en/ml/mixed`.
   * Entity extraction (spacy / IndicNLP).
   * Table extraction (Camelot/Tabula for vector PDFs, PaddleOCR table module for scanned).
   * Signature/stamp detection (OpenCV bounding boxes).

4. **Chunking & schema**

   * Split into ~200–1000 token chunks with overlap.
   * Populate `extraction_outputs` table with:

     * `doc_id, page_no, chunk_id, chunk_text, language, confidence, tables, entities, signatures, minio_chunk_path`.

5. **Event for next stage**

   * Push “ready_for_embedding” event into Kafka/Redis queue → consumed by embedding pipeline.

---

### Advanced Airflow DAG

Airflow orchestrates **batch, backfill, and reprocessing**, not per-file realtime:

* **Backfill DAG**: reprocess all files from last year.
* **OCR Upgrade DAG**: rerun OCR with new model.
* **Embedding Upgrade DAG**: regenerate embeddings when model changes.
* **Audit DAG**: verify all docs in Postgres have extraction outputs.
* **Human Review DAG**: aggregate low-confidence OCR docs and assign review tasks.

---

# 🔹 Side-by-Side Comparison

| Feature                | Hackathon Workflow       | Advanced Workflow                                                      |
| ---------------------- | ------------------------ | ---------------------------------------------------------------------- |
| **Worker Queue**       | Redis/Celery             | Kafka / Redis Streams                                                  |
| **File detection**     | Extension + MIME         | Magic bytes + full type validation                                     |
| **Technical Drawings** | Just store raw           | Convert (DWG→DXF), parse layers, preview PNG                           |
| **Image handling**     | Always OCR w/ Tesseract  | Quality check → enhancement → OCR (Tesseract/PaddleOCR/Cloud fallback) |
| **PDFs**               | PyMuPDF + OCR if no text | Hybrid (text + OCR per page), table extraction                         |
| **Office docs**        | Basic extract libs       | Full parse + fallback to conversion                                    |
| **Language**           | Basic langdetect         | Multi-engine detection, bilingual tagging                              |
| **Tables**             | None                     | Camelot/Tabula + PaddleOCR table models                                |
| **Confidence policy**  | None                     | OCR confidence thresholds + human review route                         |
| **Storage**            | Raw text chunks          | Structured schema (chunks, tables, entities, signatures)               |
| **Airflow role**       | Run processing scripts   | Orchestrate backfills, audits, reprocessing, review flows              |

---

✅ **Summary**

* **Hackathon**: lightweight, implement fast → PDFs + Images + Office → OCR + text chunks → Postgres + ready for embeddings.
* **Advanced**: full modular routing by file type, quality-aware image OCR, table/NER extraction, human-in-loop, Airflow orchestrated reprocessing.

---

Do you want me to **draw a diagram showing Hackathon vs Advanced document processing workflows** (like a flowchart side-by-side) so your team can pitch this cleanly during brainstorming?