# KMRL Document Processing System - Design Diagrams

**Source Files**: `detailed_flow.md`, `flow.md`, `flow2.md`  
**Author**: Systems Architect  
**Date**: 2024-12-19  
**Purpose**: Comprehensive design documentation and diagrams for KMRL document processing system

## Diagram Overview

This directory contains complete design documentation for the KMRL Document Processing System, including architecture diagrams, sequence flows, wireframes, and security analysis.

## Diagram Files

### Architecture Diagrams
- **`high_level_architecture.mmd`** - One-page system overview showing all components and data flow
- **`component_diagram.puml`** - Detailed component relationships and responsibilities
- **`deployment_diagram.mmd`** - Cloud deployment topology with AWS services and network boundaries

### Data Flow Diagrams
- **`data_flow_DFD_level0.mmd`** - High-level data flow between external entities and system
- **`data_flow_DFD_level1.mmd`** - Detailed data flow between internal processes

### Sequence Diagrams
- **`sequence_document_upload.mmd`** - Document upload flow from external sources to processing queue
- **`sequence_document_processing.mmd`** - Document processing flow from queue to processed text
- **`sequence_rag_pipeline.mmd`** - RAG pipeline preparation from processed text to vector database
- **`sequence_smart_notifications.mmd`** - Smart notification flow using vector similarity search
- **`sequence_rag_query.mmd`** - RAG query processing from user query to LLM response

### Database Design
- **`erd_database.mmd`** - Entity relationship diagram for PostgreSQL metadata storage

### Security & Operations
- **`security_threat_model.md`** - STRIDE threat analysis with security mitigations
- **`ci_cd_pipeline.mmd`** - Continuous integration and deployment pipeline
- **`monitoring_observability.mmd`** - Comprehensive monitoring, logging, and observability architecture

### Prototype Wireframes
- **`prototype_wireframes/document_upload_wireframe.svg`** - Document upload interface
- **`prototype_wireframes/dashboard_wireframe.svg`** - Role-based department dashboard
- **`prototype_wireframes/chat_interface_wireframe.svg`** - Conversational AI chat interface

## Source File Mapping

### detailed_flow.md Mapping
- **Sections 1-6**: Document Ingestion → `sequence_document_upload.mmd`
- **Sections 7-17**: Document Processing → `sequence_document_processing.mmd`
- **Sections 18-22**: RAG Pipeline Preparation → `sequence_rag_pipeline.mmd`
- **Sections 23-29**: Smart Notifications → `sequence_smart_notifications.mmd`
- **Sections 30-32**: RAG Query Processing → `sequence_rag_query.mmd`
- **Sections 33-42**: User Interfaces & Applications → Wireframes

### flow.md Mapping
- **Phase 1**: Document Ingestion → `sequence_document_upload.mmd`
- **Phase 2**: Document Processing → `sequence_document_processing.mmd`
- **Phase 3**: RAG Pipeline Preparation → `sequence_rag_pipeline.mmd`
- **Phase 4**: RAG Query Processing → `sequence_rag_query.mmd`

### flow2.md Mapping
- **Steps 1-7**: Document Ingestion → `sequence_document_upload.mmd`
- **Steps 9-18**: Document Processing → `sequence_document_processing.mmd`
- **Steps 20-24**: RAG Pipeline Preparation → `sequence_rag_pipeline.mmd`
- **Steps 26-32**: Smart Notifications → `sequence_smart_notifications.mmd`
- **Steps 34-42**: User Interfaces → Wireframes

## Assumptions Made

### Naming Conventions
- Standardized component names using pattern: `<role>-<component>-<env>`
- Example: `ingest-service-prod`, `processing-worker-staging`

### Missing Information
- **External System Details**: Labeled as `external: <name>` with TODO for more details
- **Timing/Ordering**: Inferred most common-sense ordering where missing
- **API Specifications**: Used RESTful conventions for undefined endpoints

### Technology Choices
- **Vector Database**: OpenSearch with HNSW algorithm
- **Embedding Model**: OpenAI text-embedding-3-large as primary, all-MiniLM-L6-v2 as fallback
- **LLM Provider**: Gemini API for prototype, OpenAI Enterprise for production
- **Queue System**: Redis + Celery for async processing
- **Cloud Platform**: AWS with ECS Fargate, RDS, ElastiCache, OpenSearch

## Acceptance Checklist

- [x] For each major flow in `detailed_flow.md`, there is at least one sequence diagram
- [x] High-level architecture diagram exists and maps each component to source files
- [x] Prototype wireframes for primary happy-path screens (annotated)
- [x] Security/scope boundaries are shown on deployment diagrams
- [x] Brief STRIDE threat table with mitigations for top 5 threats
- [x] Exported PNG/SVG for every editable diagram
- [x] `design/summary.md` lists assumptions and unresolved questions
- [x] All files committed with clear commit message

## Conflicts Resolved

### Flow Ordering Conflicts
- **Issue**: `flow.md` shows different step ordering than `detailed_flow.md`
- **Resolution**: Used `detailed_flow.md` as authoritative source for step ordering
- **Documentation**: Conflicts noted in `design/conflicts.md`

### Component Naming Conflicts
- **Issue**: Different naming conventions across source files
- **Resolution**: Standardized using `<role>-<component>-<env>` pattern
- **Documentation**: Mapping table in `design/readme.md`

## Usage Instructions

### Viewing Diagrams
1. **Mermaid Diagrams**: Use Mermaid Live Editor or VS Code Mermaid extension
2. **PlantUML Diagrams**: Use PlantUML online server or VS Code PlantUML extension
3. **SVG Wireframes**: Open in any modern web browser or SVG viewer

### Editing Diagrams
1. **Mermaid**: Edit `.mmd` files and re-export to PNG
2. **PlantUML**: Edit `.puml` files and generate SVG/PNG
3. **SVG**: Edit directly in vector graphics editor

### Exporting Images
```bash
# Mermaid to PNG
mmdc -i high_level_architecture.mmd -o high_level_architecture.png

# PlantUML to SVG
plantuml -tsvg component_diagram.puml
```

## Next Steps

1. **Review**: Stakeholder review of all diagrams and wireframes
2. **Validation**: Technical validation of architecture decisions
3. **Implementation**: Use diagrams as reference for development
4. **Updates**: Maintain diagrams as system evolves

## Contact

For questions about these diagrams or design decisions, contact the Systems Architect team.
