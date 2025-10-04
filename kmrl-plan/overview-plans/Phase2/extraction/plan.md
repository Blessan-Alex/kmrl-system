Nice — this is the exact kind of second-phase thinking that separates a good prototype from a production system. Below I give a complete, practical, industry-grade document-processing blueprint that plugs directly into your connector workflow (Gmail/Drive → MinIO + Postgres → Redis/Celery queue). I’ll explain how the worker picks up files, routing rules by file type, recommended libraries/tools (with notes for Malayalam/bilingual handling), image-quality thresholds & enhancement strategy, table extraction, quarantine/human-in-loop, what to store for the downstream RAG/preprocessing stage, Airflow placement, observability and testing. I’m acting like a hackathon judge + industry reviewer — i.e., pragmatic, security-aware, and production-minded.

I’ll call out concrete recommendations and tradeoffs, and I’ll cite sources for the important choices (OCR tooling, DWG→DXF options, docling, etc.). ([GitHub][1])([Tesseract OCR][2])([ezdxf.readthedocs.io][3])([indic-ocr.github.io][4])([about.gitlab.com][5])

---

# 1) Where this fits into your pipeline (recap)

You already have:
Gmail/Drive connector → historical + incremental sync → scan → accept/reject → raw → MinIO + metadata → push `doc_id` into Redis/Celery queue.

Now we design the *Document Processing Worker pipeline* that consumes that queue and produces cleaned, structured outputs ready for the downstream preprocessing / RAG pipeline.

---

# 2) How the worker picks up and routes a file (message contract)

**Queue message (what the connector should push):**

```json
{
  "doc_id": "uuid-123",
  "minio_path": "minio://kmrl-raw/gmail/2025/10/12345.pdf",
  "source_system": "gmail",
  "source_id": "gmail_msg_98765",
  "ingestion_ts": "2025-10-03T10:00:00Z",
  "file_name": "maintenance_report_2025-10-01.pdf",
  "mime_type": "application/pdf",
  "file_size": 234234,
  "checksum": "sha256:abcd..."
}
```

**Worker behavior**:

1. Pop message (Celery worker or Kafka consumer).
2. Fetch file from MinIO using `minio_path`.
3. Re-verify file type (magic bytes + `mime_type`) — *do not trust extension alone*.
4. Compute derived properties: `extension`, `mime`, `num_pages` (if PDF), `image_dims` (if image), `dpi` (if available), `checksum` (verify).
5. Route by file type to the appropriate processing pipeline (technical drawing, image, pdf, office doc, text, unknown).
6. Write an entry to `processing_log` with start_ts, worker_id, route_taken.

This achieves idempotency (message has `doc_id`) and traceability.

---

# 3) File-type routing (detailed)

### A — Technical drawings

Extensions: `.dwg, .dxf, .step, .stp, .iges, .igs`
**Goal:** convert to a canonical DXF/DWG representation, extract layers, text (annotations), geometry metadata, BOM tables, and embedded raster images.

**Steps & tools**

* If `.dwg` convert to `.dxf` with the **ODA File Converter (Open Design Alliance)** or an enterprise library (Aspose.CAD) and then parse with **ezdxf** for extraction and inspection. ODA provides CLI and is widely used. ezdxf can consume the converted DXF. ([Open Design][6])
* If STEP/IGES: use CAD readers (commercial toolkits or open-source parsers) to extract model metadata; for production you’ll likely need a commercial SDK (Aspose or ODA SDK) depending on complexity. ([Aspose Blog][7])

**Outputs to store**

* Canonical DXF (or converted representation) in MinIO.
* `drawings` table with `doc_id, dxf_path, layers_json, text_annotations, bounding_boxes, entities_count, units, version`.
* Also produce preview PNG(s) per view for UI.

**Notes**: DWG→DXF conversion is brittle with pure open-source; ODA Converter or Aspose is the pragmatic path for reliability. ([Open Design][6])

---

### B — Images (JPG/PNG/TIFF/WebP ...)

**Goal:** get high-quality text (bilingual) + detect if it contains tables, forms, or signatures → route accordingly.

**OCR options**

* **Docling** — high-level document parser that orchestrates OCR and layout extraction; supports many engines and exports to JSON/Markdown. Good for pipeline glue. ([GitHub][1])
* **Tesseract** (with traineddata for Malayalam `mal`): battle-tested, runs locally offline (traineddata available). Accuracy for Indic scripts can be lower without retraining; Indic-OCR projects provide better trained data and recipes. ([Tesseract OCR][2])
* **PaddleOCR** / **EasyOCR** — often better in image quality robustness and layout handling; PaddleOCR has good multi-language support and table detection models. Community recommends PaddleOCR for many languages. ([Reddit][8])
* **Cloud OCR** (Google Cloud Vision / Azure Read / Amazon Textract) — superior bilingual accuracy often, handles mixed language detection automatically, and has table/form extraction; but is paid and may have data residency/privacy implications. Google Vision explicitly supports multi-language OCR. ([Google Cloud][9])

**Malayalam / bilingual handling**

* Tesseract supports Malayalam via `mal.traineddata` and can be improved with retraining; also consider local projects like **Lekha OCR** specifically tuned for Malayalam (open source, but older). Test locally to measure accuracy. ([indic-ocr.github.io][4])
* Practical approach: **primary local engine (Tesseract or PaddleOCR)** + **fallback to cloud OCR** if confidence is low or text is mixed/unhandled.

**Image preprocessing (see next section)**.

---

### C — PDFs

PDFs fall into:

* **Text PDFs** — have embedded text layer (extract with PyMuPDF/fitz or pdfminer).
* **Image PDFs** — each page is an image → OCR.
* **Mixed** — combination; must treat per page.

**Tools**

* **PyMuPDF (fitz)** or **pdfplumber** for fast text layer extraction and page images. `PyMuPDF` is fast and gives page-level info.
* **Docling** does advanced layout + exports and may be a good top-level orchestrator. ([GitHub][1])
* **Camelot / Tabula-py** for **table extraction from data-like PDFs** (works best with vector PDFs); for scanned tables, use table-recognition models (PaddleOCR table module or TableNet) after OCR.

**Routing**

* For each page: if `page_has_text_layer` → extract text and run lightweight NER/keywords. If `page_is_image` → send to image OCR pipeline + table detection.

---

### D — Office documents (.docx/.xlsx/.pptx)

**Tools**

* **python-docx** for DOCX (text + styles + embedded images).
* **openpyxl / pandas** for XLSX/CSV (structured).
* **python-pptx** for PPTX.
* For older binary formats (.doc/.xls/.ppt), use LibreOffice headless to convert to modern formats or to PDF for unified processing.

**Notes**

* XLSX: if it’s tabular data, prefer to store table as JSON/CSV and keep a sample preview. Large datasets may be routed directly to a data lake rather than the doc pipeline.

---

### E — Text files (.txt, .md, .csv, .json)

* Load directly, detect encoding (chardet), normalize line endings.
* Large CSVs (datasets) should be flagged and possibly routed to a data-ingestion pipeline (not NLP pipeline) — but still store metadata and a pointer for RAG indexing if needed.

---

### F — Unknown / Binary / Unsupported

* Put into **quarantine** bucket with `status=unknown` and a tag for human review. Keep a `processing_attempts` count.
* Provide an admin UI to inspect and tag/approve.

---

# 4) Image quality assessment & enhancement (practical rules)

**Why**: OCR accuracy depends heavily on DPI, blur, skew, contrast. Enhance only when necessary to save resources.

**Quality metrics (compute quickly)**

* **DPI**: if >300 → good; 200–300 → ok; <200 → flag for enhancement.
* **Blur**: use `variance_of_laplacian` (OpenCV). Low variance = blurry. Example thresholds: `variance < 100` → blurry (tune on dataset).
* **Contrast / brightness**: histogram analysis; low contrast → enhancement.
* **Skew**: detect via Hough lines or deskew algorithms; skew > 3–5° → deskew.
* **Noise**: estimate via local variance.

**Decision**

* If ANY metric fails thresholds → send to **Image Enhancement** pipeline (fast transforms). Otherwise proceed to OCR.

**Enhancement steps (order)**

1. Grayscale conversion (if color not needed).
2. Deskew (Hough or projection-profile).
3. Upscale/SR (optional — use ESRGAN/Real-ESRGAN if very low DPI and you have GPU).
4. Denoise (Non-local means / bilateral filter).
5. Binarize (Otsu or adaptive threshold) for Tesseract.
6. Contrast/CLAHE.

**Do enhance every file?** No. Only when quality checks fail (saves compute). After enhancement, re-evaluate metrics; if still below threshold → route to human review.

---

# 5) OCR confidence and acceptance policy

* **Use OCR engine confidence scores** at word/line level. Compute `page_confidence = weighted_avg(word_conf)`.

* **Thresholds** (example, tune on data):

  * `page_confidence >= 0.85` → accept.
  * `0.6 <= page_confidence < 0.85` → flag for verification / soft review (store OCR text and highlight low-confidence regions).
  * `< 0.6` → enhancement if not tried, then retry OCR; if still <0.6 → send to human review / quarantine for manual transcription.

* For bilingual pages: run language detection on OCR output (fastlangdetect or compact langdetect) and compute per-language confidences. If mixture, preserve language spans (use per-line language detection).

---

# 6) Table extraction (images and PDFs)

* **Vector PDFs (text-based tables)**: use **Camelot** or **tabula-py** (works well when tables are border-based).
* **Scanned images/tables**:

  * Use **PaddleOCR table module** or deep learning table-detection (TableBank, TableNet) to find table regions, then apply OCR per cell/region and re-construct CSV/JSON.
  * Alternatively, convert page region to image and run table recognition models.
* **Store extracted tables** as **structured JSON** and also as CSV in MinIO. Also store bounding boxes for traceability.

---

# 7) Human-in-the-loop & adjudication

* **When to escalate**:

  * Malware detected (reject).
  * OCR confidence remains below threshold after enhancement.
  * Unknown file type or conversion failure (DWG conversion failure, STEP parse error).
  * Complex table extraction failure flagged by heuristics.

* **UI features needed**:

  * Visual preview with highlighted low-confidence regions.
  * Simple text edit + accept button.
  * Reprocess button (re-run with different OCR engine or parameters).
  * Approve/Reject with reason.

---

# 8) What to store in Postgres after processing (schema suggestions)

You need two layers:

A) `documents` (ingestion metadata — already present)
B) `extraction_outputs` (per doc / per page / per chunk)

**`extraction_outputs` table (normalized)**:

| Field          |      Type | Notes                                                          |
| -------------- | --------: | -------------------------------------------------------------- |
| id             |      UUID | PK                                                             |
| doc_id         |      UUID | FK to documents                                                |
| page_no        |       INT | page index for multipage docs                                  |
| chunk_id       |   VARCHAR | e.g., `doc-uuid_page-2_chunk-5`                                |
| chunk_text     |      TEXT | plaintext extracted                                            |
| chunk_html     |      TEXT | (optional) formatted HTML/markdown                             |
| language       |   VARCHAR | detected language(s)                                           |
| ocr_confidence |     FLOAT | 0..1                                                           |
| entities       |     JSONB | extracted NER/entities                                         |
| tables         |     JSONB | extracted table JSON (if any)                                  |
| signatures     |     JSONB | bounding boxes for signatures                                  |
| embeddings_id  |      UUID | pointer to embeddings in vector DB (or store vector elsewhere) |
| created_ts     | TIMESTAMP | when extraction finished                                       |

**Why chunking?** RAG systems perform better with ~200–1000 token chunks with overlap. Chunk here means a document chunk prepared for downstream embedding. Keep both raw `chunk_text` and the original page text for traceability.

---

# 9) What does the next pipeline (RAG) expect?

Minimum schema to be useful immediately:

* `doc_id`, `page_no`, `chunk_id`, `chunk_text`, `chunk_metadata` (json: department, doc_category, source_id, file_name, ingestion_ts), `language`, `ocr_confidence`, `minio_raw_path`, `minio_preview_path`.

Downstream systems will:

* Generate embeddings from `chunk_text` and store vectors in your vector DB (OpenSearch / Milvus / Pinecone etc.).
* Index the metadata for filtering (department, doc_category, date, source).

So ensure the document processing worker writes the `extraction_outputs` table plus triggers a task/message to the embedding worker (or let Airflow run batch embedding DAGs).

---

# 10) Airflow placement & DAGs

Airflow does **orchestration, not low-latency per-file processing**. Keep workers handling per-file jobs; use Airflow for the heavy/batch tasks:

**Airflow DAG examples**

1. **Daily Reprocess DAG** — re-run OCR/processing for files ingested the previous day with improved models.
2. **Backfill DAG** — orchestrates historical processing with rate limits.
3. **Model Upgrade DAG** — regenerate embeddings after an embedding model change.
4. **Audit DAG** — verify that `documents` entries have corresponding `extraction_outputs`, alert anomalies.
5. **Human-Review Task Trigger** — aggregate low-confidence docs and create a human-review job list (Airflow can create tasks that populate a review queue).

Airflow can call Celery tasks or trigger consumers to reprocess batches.

---

# 11) Observability, DLQs & retries

* **Metrics**: files processed/min, average OCR confidence, percent needing enhancement, per-connector failure rates. Export to Prometheus/Grafana.
* **Logs**: structured logs with `doc_id` correlation id.
* **DLQ**: processing failures (malware, conversion errors) → push to DLQ topic / quarantine bucket + admin alert.
* **Retries**: exponential backoff, limited retries (e.g., 3 attempts) before human review.
* **Sampling & QA**: periodically sample processed docs and compute end-to-end accuracy metrics (compare OCR vs human ground truth on sample).

---

# 12) Libraries & tool recommendations (quick list with sources)

* **Document orchestration / parsing**: Docling (great glue for OCR, layout, markdown/JSON export). ([GitHub][1])
* **OCR engines**: Tesseract (local + Malayalam traineddata), PaddleOCR (robust), EasyOCR (multilingual). Use fallback to **Google Vision / Azure / Amazon Textract** for edge accuracy or compliance decisions. ([Tesseract OCR][2])
* **Malayalam OCR**: try Tesseract + Indic-traineddata; evaluate **Lekha OCR** for legacy specialized Malayalam performance; test with real KMRL scans. ([indic-ocr.github.io][4])
* **Table extraction**: Camelot / Tabula for vector PDFs; PaddleOCR/table models or TableNet for scanned tables.
* **DWG→DXF**: ODA File Converter (Open Design Alliance) CLI or Aspose.CAD for robust conversion; use `ezdxf` to parse DXF programmatically. ([Open Design][6])

---

# 13) Human review workflow & UI suggestions

* Admin UI listing: low confidence docs, quarantined files, conversion failures.
* Inline editor to correct OCR text (with side-by-side preview) and accept corrected output back into `extraction_outputs`.
* Minimal crowdsourcing: allow trusted operators to quickly validate batches.

---

# 14) Testing plan (must for hackathon → production)

* **Unit tests** for each file type processor with small example files.
* **Integration tests**: push sample messages through the full ingestion→processing pipeline.
* **Regression dataset**: collect a labeled set (English, Malayalam, bilingual) with representative noise, handwritten notes, tables. Use it to measure OCR accuracy, table extraction success, and improve thresholds.
* **Load tests**: measure worker throughput and backfill behaviour — ensure MinIO + DB scale.

---

# 15) Final practical checklist (what to implement now for Phase-2)

1. Worker reads queue message (doc_id + minio_path).
2. File type verification (magic bytes) and routing.
3. Implement processors for: PDFs (PyMuPDF + docling), Images (OpenCV + Tesseract/PaddleOCR), Office (python-docx/openpyxl), Technical drawings (ODA + ezdxf or Aspose). ([GitHub][1])
4. Image quality checks + enhancement pipeline (OpenCV transforms; SR optional).
5. Table extraction strategy (Camelot for vector, PaddleOCR/TableNet for scanned).
6. Confidence thresholds + retry/enhance/human-review path.
7. Populate `extraction_outputs` (chunked) and push a message to embedding queue.
8. Airflow DAGs for backfills, reprocessing and audit.
9. Monitoring/metrics + DLQ + admin UI for human review.

---

# 16) Quick risks & mitigations (judge’s view)

* **Malayalam OCR accuracy** — risk: Tesseract might be poor on noisy or handwritten Malayalam. **Mitigation**: maintain fallback cloud OCR or specialist local models (Lekha) + human review for low confidence. ([indic-ocr.github.io][4])
* **DWG reliability** — risk: open-source DWG conversion is brittle. **Mitigation**: use ODA or commercial SDK for production. ([Open Design][6])
* **Table extraction brittleness** — risk: scanned tables produce garbage. **Mitigation**: use deep learning table detection + manual correction UI for business-critical docs.
* **Cost/privacy of cloud OCR** — weigh accuracy vs data residency; use local engines first and cloud only as fallback.

---

# 17) Short concrete next steps I’d implement this sprint (prioritized)

1. Build a **single Celery worker** that consumes the connector queue, fetches file from MinIO, re-verifies type, routes to processors. Implement PDF and Image processing first.
2. Integrate **Docling** as a high-level orchestrator for PDFs/images — it will speed the hackathon. ([GitHub][1])
3. Add image quality heuristics + OpenCV enhancement.
4. Implement `extraction_outputs` schema and push embeddings queue message when chunk ready.
5. Add a minimal human-review web page for low-confidence items.
6. Run tests on a labeled sample set (English + Malayalam) and iterate thresholds.

---

# Citations (most important claims)

* Docling project (document parsing, OCR orchestration). ([GitHub][1])
* Tesseract traineddata and language support (Malayalam availability / retrain possibilities). ([Tesseract OCR][2])
* Lekha OCR — Malayalam OCR specialized project. ([about.gitlab.com][5])
* DWG→DXF conversion options: ODA File Converter / ezdxf integration; Aspose.CAD for Python is an alternate commercial approach. ([Open Design][6])
* PaddleOCR / community recommendations for robust OCR and table models. ([Reddit][8])

---

If you want, I can now:

* produce the **Celery worker skeleton** (Python) that implements message parsing, type detection, and routing hooks for the processors; **or**
* produce a **detailed Airflow DAG** for batch reprocessing + human review scheduling; **or**
* provide a **sample SQL DDL** for `extraction_outputs` + example insert/update flows.

Which one should I generate next?

[1]: https://github.com/docling-project/docling?utm_source=chatgpt.com "docling-project/docling: Get your documents ready for gen AI"
[2]: https://tesseract-ocr.github.io/tessdoc/Data-Files.html?utm_source=chatgpt.com "Traineddata Files for Version 4.00 + | tessdoc - GitHub Pages"
[3]: https://ezdxf.readthedocs.io/en/stable/addons/odafc.html?utm_source=chatgpt.com "ODA File Converter Support — ezdxf 1.4.2 documentation"
[4]: https://indic-ocr.github.io/tessdata/?utm_source=chatgpt.com "Tesseract Models for Indian Languages - Indic-OCR"
[5]: https://gitlab.com/icfoss/lekha-OCR?utm_source=chatgpt.com "lekha-OCR Version 3.0 - icfoss"
[6]: https://www.opendesign.com/guestfiles/oda_file_converter?utm_source=chatgpt.com "ODA File Converter"
[7]: https://blog.aspose.com/cad/convert-dwg-to-dxf-in-python/?utm_source=chatgpt.com "Convert DWG to DXF in Python"
[8]: https://www.reddit.com/r/LocalLLaMA/comments/1eecto9/best_ocr/?utm_source=chatgpt.com "Best ocr : r/LocalLLaMA"
[9]: https://cloud.google.com/vision/docs/languages?utm_source=chatgpt.com "OCR Language Support | Cloud Vision API"
