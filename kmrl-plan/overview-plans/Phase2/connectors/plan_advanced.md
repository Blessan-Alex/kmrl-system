Got it 👍 — let’s now expand the **Advanced workflow (production-grade)** for connectors.
I’ll mirror the same step-by-step approach as the hackathon one, but with **more modularity, resilience, and compliance features**.

---

# 🔹 Advanced Connector Workflow (Production-grade)

### **1. Connector Services (per source)**

* Each connector (Gmail, Drive, SharePoint, Maximo, WhatsApp, Manual Upload) runs as its own **service** (Docker container / independent module).
* Follows a **connector SDK pattern**: `auth → fetch → scan → store → emit event`.
* Supports **incremental sync** (delta queries, webhooks) and **historical sync** (paged backfill jobs).
* Maintains **checkpoint state** in Postgres (`last_msg_id`, `last_drive_file_time`).

---

### **2. Security & Validation**

* **Ingest everything** (don’t filter early).
* Run **malware/virus scan** (ClamAV or commercial scanner).
* Run **file type validation** (check magic bytes + MIME type).
* If unsupported → quarantine in MinIO (separate bucket), log reason.
* If clean → proceed.

---

### **3. Storage**

* Store **original raw file** in **MinIO** (`/source/yyyy/mm/dd/file_id`).
* Store **metadata record** in Postgres (see schema below).
* Compute **checksum (SHA256)** to avoid duplicates.

---

### **4. Event Bus**

* Connector publishes a **normalized ingestion event** to a queue system:

  * Kafka (preferred) or Redis Streams.
  * Event includes: `{doc_id, minio_path, metadata_id, status, ingestion_ts}`.
* Guarantees **durable delivery** and replay (Kafka advantage).

---

### **5. Document Classification**

* A lightweight consumer listens to events:

  * Derives **document type** (invoice, safety_circular, HR_policy, etc.).
  * Derives **department** (Finance, Engineering, HR) — via rules/ML model.
  * Updates metadata in Postgres.

---

### **6. Processing Queue**

* Event then pushed into a **“ready_for_extraction” topic/queue**.
* Workers consume and run downstream jobs: OCR, NLP, embeddings, etc.
* Failures go into a **DLQ (Dead Letter Queue)** with reprocess option.

---

### **7. Airflow Integration**

Airflow now plays a **supervisory role**:

* **Backfill DAGs** → fetch historical Gmail/Drive/SharePoint files in batches (rate-limited).
* **Audit DAGs** → daily check that all events in Postgres also exist in MinIO + Kafka.
* **Reprocessing DAGs** → re-run extraction jobs (e.g., after new embedding model).
* **Lineage DAGs** → map document from ingestion → processing → vector DB.

---

# 🔹 Advanced Metadata Schema (Postgres)

(Table: `documents`)

| Field                | Type      | Purpose                                        |
| -------------------- | --------- | ---------------------------------------------- |
| **id** (PK)          | UUID      | Unique pipeline doc ID                         |
| **source_system**    | VARCHAR   | Gmail / Drive / SharePoint / Maximo / WhatsApp |
| **source_id**        | VARCHAR   | File/message ID from source (dedupe key)       |
| **minio_path**       | VARCHAR   | Location of stored raw file                    |
| **file_name**        | VARCHAR   | Original filename                              |
| **file_ext**         | VARCHAR   | pdf, docx, jpg                                 |
| **mime_type**        | VARCHAR   | MIME type                                      |
| **file_size**        | INT       | Bytes                                          |
| **checksum**         | VARCHAR   | SHA256 for deduplication                       |
| **ingestion_ts**     | TIMESTAMP | When ingested                                  |
| **connector_ts**     | TIMESTAMP | When connector processed                       |
| **department**       | VARCHAR   | Derived department                             |
| **doc_category**     | VARCHAR   | Invoice / Safety / HR / Engineering / etc.     |
| **language**         | VARCHAR   | en, ml, bilingual                              |
| **sender**           | VARCHAR   | (email sender / uploader id)                   |
| **status**           | VARCHAR   | success / quarantined / rejected               |
| **rejection_reason** | VARCHAR   | reason for rejection                           |
| **retry_count**      | INT       | retries attempted                              |
| **tags**             | JSONB     | extracted tags (key entities, keywords)        |

---

# 🔹 Advanced Workflow DAG (Airflow Orchestration)

```python
from airflow import DAG
from airflow.operators.docker_operator import DockerOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "kmrl",
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
}

with DAG(
    dag_id="connector_ingestion_advanced",
    default_args=default_args,
    schedule_interval="*/15 * * * *",  # 15 min sync
    start_date=datetime(2025, 10, 1),
    catchup=False,
) as dag:

    # Example: Gmail Connector container
    gmail_sync = DockerOperator(
        task_id="gmail_connector",
        image="kmrl/gmail-connector:latest",
        command="--mode incremental --checkpoint last_sync",
    )

    drive_sync = DockerOperator(
        task_id="drive_connector",
        image="kmrl/drive-connector:latest",
        command="--mode incremental --checkpoint last_sync",
    )

    sharepoint_sync = DockerOperator(
        task_id="sharepoint_connector",
        image="kmrl/sharepoint-connector:latest",
        command="--mode incremental --checkpoint last_sync",
    )

    audit_step = DockerOperator(
        task_id="audit_metadata",
        image="kmrl/audit-service:latest",
        command="--check-ingestion-completeness",
    )

    [gmail_sync, drive_sync, sharepoint_sync] >> audit_step
```

---

# 🔹 Key Differences (Hackathon vs Advanced)

| Aspect               | Hackathon (MVP)                 | Advanced (Production)                               |
| -------------------- | ------------------------------- | --------------------------------------------------- |
| **Connector design** | Python scripts in Airflow tasks | Independent services (Docker, modular SDK)          |
| **Sync**             | Simple polling                  | Webhooks + incremental delta queries                |
| **File handling**    | Accept only allowed file types  | Accept all → scan → quarantine unsupported          |
| **Security**         | Basic ClamAV scan               | Full AV + PII scan + quarantine                     |
| **Storage**          | MinIO + Postgres                | MinIO + Postgres with dedupe, DLQ                   |
| **Event system**     | Redis/Celery                    | Kafka (preferred) or Redis Streams                  |
| **Metadata**         | Minimal fields                  | Extended schema (checksum, tags, retries, language) |
| **Airflow role**     | Run connector scripts           | Orchestrate backfills, audits, lineage              |
| **Recovery**         | Manual re-run                   | DLQ, retries, reprocessing DAGs                     |

---

✅ **Summary**

* **Hackathon** = keep it simple: scripts → scan → MinIO + Postgres → Redis queue.
* **Advanced** = modular connector services, ingest everything, secure scanning, publish to Kafka, rich metadata, Airflow for orchestration/backfills/audits.

---

Would you like me to **draw a side-by-side diagram (Hackathon vs Advanced workflows)** so your team can present the contrast visually in the brainstorming session?
