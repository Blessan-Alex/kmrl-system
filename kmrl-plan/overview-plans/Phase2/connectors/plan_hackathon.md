Plan: 
Gmail/Drive → historical sync → incremental sync → pull all files → scan → reject/accept → store raw in MinIO + metadata in Postgres → push ID to Redis/Celery queue for extraction.

Metadata fields: id, minio_id, source_system, source_id, file_name, file_type, mime_type, file_size, ingestion_ts, department, doc_category, checksum, status, rejection_reason (+optional language, sender, tags).

DAGS
gmail_connector -> scan_and_store -> push_to_queue
drive_connector -> scan_and_store -> push_to_queue

Where:
gmail_connector / drive_connector → fetch files.
scan_and_store → virus scan + filter → store in MinIO + metadata in Postgres.
push_to_queue → enqueue doc_id for extraction.

Universal Log
Every connector should write to a **universal log table** (`ingestion_log`) or a central logging system:
* connector name
* action (fetch, scan, reject, store)
* status (success/failure)
* reason (if fail)
* timestamp
This gives **traceability** and helps debugging.


## 🔹 Hackathon Workflow (step-by-step)

1. **Connector (Gmail / Drive)**

   * Run once for **historical sync** (pull 50–100 docs).
   * Switch to **incremental sync** (poll new docs).

2. **File Handling**

   * Pull everything → scan with ClamAV → reject unsupported file types (keep a log entry).

3. **Storage**

   * **Raw file** → store in MinIO bucket (per connector, e.g., `gmail/2025/10/file.pdf`).
   * **Metadata** → store record in Postgres.

4. **Queue**

   * Push a message (doc_id, minio_id, metadata_id) into Redis/Celery queue.
   * Workers consume → do extraction later.

---

## 🔹 4. Metadata Schema (minimum needed)

Here’s a solid schema for Postgres `documents` table:

| Field                | Type               | Purpose                                                    |
| -------------------- | ------------------ | ---------------------------------------------------------- |
| **id** (PK)          | UUID / serial      | Unique identifier for pipeline                             |
| **minio_id**         | VARCHAR            | Path/ID of file in MinIO                                   |
| **source_system**    | VARCHAR            | Gmail, Drive, etc.                                         |
| **source_id**        | VARCHAR            | Gmail msg_id, Drive file_id (for dedupe)                   |
| **file_name**        | VARCHAR            | Original filename                                          |
| **file_type**        | VARCHAR            | PDF, DOCX, XLSX, PNG                                       |
| **mime_type**        | VARCHAR            | MIME info (application/pdf etc.)                           |
| **file_size**        | INT                | Size in bytes                                              |
| **ingestion_ts**     | TIMESTAMP          | When it was ingested                                       |
| **department**       | VARCHAR (nullable) | If you can derive (HR, Finance, Engineering)               |
| **doc_category**     | VARCHAR (nullable) | Derived from filename (e.g., “invoice”, “safety_circular”) |
| **checksum**         | VARCHAR            | SHA256 hash (for dedupe)                                   |
| **status**           | VARCHAR            | success / quarantined / rejected                           |
| **rejection_reason** | VARCHAR (nullable) | why it was dropped (unsupported type, malware)             |

👉 Later you can add:

* **language** (English, Malayalam, bilingual — from langdetect).
* **tags** (if keyword extraction is run early).
* **uploader / sender** (from email headers or Drive metadata).

---

## 🔹 5. Universal Log

Every connector should write to a **universal log table** (`ingestion_log`) or a central logging system:

* connector name
* action (fetch, scan, reject, store)
* status (success/failure)
* reason (if fail)
* timestamp

This gives **traceability** and helps debugging.

---

## 🔹 6. Hackathon DAG (connectors only)

```python
gmail_connector -> scan_and_store -> push_to_queue
drive_connector -> scan_and_store -> push_to_queue
```

Where:

* `gmail_connector` / `drive_connector` → fetch files.
* `scan_and_store` → virus scan + filter → store in MinIO + metadata in Postgres.
* `push_to_queue` → enqueue doc_id for extraction.

---

✅ **Answer Summary**

* **Queue**: not strictly needed to *fetch* files, but needed **after storage** to decouple processing.
* **Modular microservices**: each connector is an independent, reusable script/service following the same pattern.
* **Hackathon plan**: Gmail/Drive → historical sync → incremental sync → pull all files → scan → reject/accept → store raw in MinIO + metadata in Postgres → push ID to Redis/Celery queue for extraction.
* **Metadata fields**: `id, minio_id, source_system, source_id, file_name, file_type, mime_type, file_size, ingestion_ts, department, doc_category, checksum, status, rejection_reason (+optional language, sender, tags).`


