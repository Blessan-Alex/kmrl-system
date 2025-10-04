Perfect ✅ — let’s mirror what we did for **connectors**: a **Hackathon (MVP) workflow** for document processing (fast to implement, just enough for demo), and an **Advanced workflow** (production-grade, modular, resilient).

Both fit into your bigger system:
**Connectors → MinIO (raw) + Postgres (metadata) → Queue → Document Processing Worker(s)**

---

# 🔹 Hackathon Document Processing Workflow (MVP)

### Flow

1. **Worker picks message**

   * Consumes from Redis/Celery queue.
   * Fetches raw file from MinIO using `minio_path`.

2. **File type detection**

   * Use extension + MIME check.
   * Route into basic categories: `pdf, image, office, text, technical_drawing, unknown`.

3. **Processing routes**

   * **PDFs**: PyMuPDF → extract text; if no text, Tesseract OCR per page.
   * **Images**: Tesseract (English + Malayalam traineddata) → OCR.
   * **Office docs**: python-docx / openpyxl / pptx → extract text.
   * **Text/CSV**: read directly, simple normalization.
   * **Technical drawings**: For hackathon, just **store as-is + metadata** (skip complex DWG→DXF).
   * **Unknown**: log + flag for human review.

4. **Minimal preprocessing**

   * Basic language detection (langdetect).
   * Chunk into ~500 words per chunk.
   * Save extracted text + metadata to Postgres `extraction_outputs`.

5. **Queue to embedding pipeline**

   * Push `doc_id + chunk_ids` to queue for next stage (RAG/embedding).

---

### Hackathon Airflow DAG

```python
connectors -> scan/store -> queue_extraction

queue_extraction -> doc_processing_worker -> postgres (extraction_outputs)
```

👉 **Focus**: only PDFs + Images + Office docs + Text. Skip advanced CAD/table logic.
👉 **Goal**: show end-to-end: Gmail → MinIO → OCR → text in Postgres → ready for embeddings.

---


