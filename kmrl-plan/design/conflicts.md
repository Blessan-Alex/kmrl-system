# KMRL Document Processing System - Design Conflicts Resolution

**Author**: Systems Architect  
**Date**: 2024-12-19  
**Purpose**: Documentation of conflicts between source files and resolution decisions

## Conflicts Identified

### 1. Flow Ordering Conflicts

#### Conflict: Document Processing Steps
**Source Files**: `flow.md` vs `detailed_flow.md`
- **flow.md Phase 2**: Shows "Worker Picks Task From Queue" → "File validation" → "Quality Assessment"
- **detailed_flow.md Section 7**: Shows "Worker Picks Task from Queue" → "File Type Detection" → "Quality Assessment"

**Resolution**: Used `detailed_flow.md` as authoritative source
- **Rationale**: More detailed and comprehensive step breakdown
- **Implementation**: File validation is implicit in the file type detection process

#### Conflict: RAG Pipeline Steps
**Source Files**: `flow.md` vs `flow2.md`
- **flow.md Phase 3**: Shows "Data Preprocessing" → "Smart Chunking" → "Generate Embeddings"
- **flow2.md Steps 20-24**: Shows "Data Preprocessing" → "Smart Chunking" → "Generate Embeddings" → "Store in Vector Database"

**Resolution**: Used `flow2.md` as authoritative source
- **Rationale**: Includes explicit vector storage step
- **Implementation**: Added "Mark Document as RAG Ready" step from `detailed_flow.md`

### 2. Component Naming Conflicts

#### Conflict: Database Names
**Source Files**: Multiple files
- **flow.md**: "Postgress" (typo)
- **detailed_flow.md**: "PostgreSQL"
- **flow2.md**: "PostgreSQL"

**Resolution**: Standardized to "PostgreSQL"
- **Rationale**: Correct spelling and industry standard
- **Implementation**: Used "PostgreSQL" throughout all diagrams

#### Conflict: Storage Service Names
**Source Files**: Multiple files
- **flow.md**: "Minio/S3"
- **detailed_flow.md**: "MinIO/S3"
- **flow2.md**: "MinIO/S3"

**Resolution**: Standardized to "MinIO/S3"
- **Rationale**: Correct capitalization for MinIO
- **Implementation**: Used "MinIO/S3" throughout all diagrams

### 3. Processing Method Conflicts

#### Conflict: OCR Engine Specification
**Source Files**: `flow.md` vs `detailed_flow.md`
- **flow.md**: "OCR Processing [Tesseract]"
- **detailed_flow.md**: "Malayalam OCR (mal+eng)" and "English OCR (eng)"

**Resolution**: Used detailed specification from `detailed_flow.md`
- **Rationale**: More specific language support requirements
- **Implementation**: Specified both Malayalam and English OCR capabilities

#### Conflict: Text Extraction Method
**Source Files**: Multiple files
- **flow.md**: "Markitdown Processing"
- **detailed_flow.md**: "Use Markitdown for Office docs"
- **flow2.md**: "Markitdown for Office docs"

**Resolution**: Used comprehensive approach from `detailed_flow.md`
- **Rationale**: Specifies when to use Markitdown vs. other methods
- **Implementation**: Documented different extraction methods for different file types

### 4. Notification System Conflicts

#### Conflict: Notification Triggers
**Source Files**: `detailed_flow.md` vs `flow2.md`
- **detailed_flow.md**: Shows specific similarity thresholds (≥0.85, ≥0.90, etc.)
- **flow2.md**: Shows "Category-specific thresholds"

**Resolution**: Used specific thresholds from `detailed_flow.md`
- **Rationale**: More actionable and measurable
- **Implementation**: Implemented specific thresholds for different notification types

#### Conflict: Notification Channels
**Source Files**: Multiple files
- **detailed_flow.md**: "Email (normal priority), SMS (urgent priority), Slack (high priority)"
- **flow2.md**: "Email, SMS, Slack based on priority"

**Resolution**: Used detailed specification from `detailed_flow.md`
- **Rationale**: Clear mapping of priority to channel
- **Implementation**: Implemented priority-based channel selection

### 5. User Interface Conflicts

#### Conflict: Dashboard Approach
**Source Files**: `detailed_flow.md` vs `flow2.md`
- **detailed_flow.md**: "Department Dashboards" with specific departments
- **flow2.md**: "Department Dashboards [Role-based views]"

**Resolution**: Combined both approaches
- **Rationale**: Role-based views within department-specific dashboards
- **Implementation**: Single dashboard with role-based filtering and views

#### Conflict: Search Interface
**Source Files**: Multiple files
- **detailed_flow.md**: "Intelligent Search Interface"
- **flow2.md**: "Intelligent Search [RAG-powered search]"

**Resolution**: Used comprehensive specification from `detailed_flow.md`
- **Rationale**: More detailed feature specification
- **Implementation**: Implemented advanced search with filters, suggestions, and analytics

## Resolution Methodology

### 1. Source Priority
1. **Primary**: `detailed_flow.md` - Most comprehensive and detailed
2. **Secondary**: `flow2.md` - Good high-level overview
3. **Tertiary**: `flow.md` - Basic flow structure

### 2. Conflict Resolution Rules
1. **Completeness**: Choose the most complete specification
2. **Specificity**: Prefer specific details over general statements
3. **Consistency**: Maintain consistency across all diagrams
4. **Industry Standards**: Use standard terminology and practices

### 3. Documentation Standards
1. **Assumptions**: Document all assumptions made
2. **Rationale**: Explain reasoning for each decision
3. **Implementation**: Show how resolution affects implementation
4. **Validation**: Provide validation criteria for decisions

## Assumptions Made

### Technical Assumptions
1. **File Size Limits**: Assumed 200MB max for uploads, 50MB for processing
2. **Processing Time**: Assumed 5-minute SLA for 95% of documents
3. **Concurrency**: Assumed 100 concurrent users maximum
4. **Storage**: Assumed 1TB initial storage requirement

### Business Assumptions
1. **User Roles**: Assumed 4 main departments (Operations, Engineering, Finance, HR)
2. **Document Types**: Assumed 10+ file formats supported
3. **Languages**: Assumed English and Malayalam support required
4. **Compliance**: Assumed standard document retention requirements

### Operational Assumptions
1. **Availability**: Assumed 99.9% uptime requirement
2. **Support**: Assumed 8x5 support model
3. **Backup**: Assumed daily backup with 30-day retention
4. **Monitoring**: Assumed 24x7 monitoring with alerting

## Validation Requirements

### Technical Validation
- [ ] **Architecture Review**: Validate all technical decisions
- [ ] **Performance Testing**: Validate assumed performance requirements
- [ ] **Security Review**: Validate security assumptions
- [ ] **Integration Testing**: Validate external system assumptions

### Business Validation
- [ ] **User Research**: Validate user role and workflow assumptions
- [ ] **Compliance Review**: Validate regulatory requirements
- [ ] **Cost Analysis**: Validate cost and resource assumptions
- [ ] **ROI Assessment**: Validate business value assumptions

### Operational Validation
- [ ] **Support Model**: Validate support and maintenance assumptions
- [ ] **Disaster Recovery**: Validate backup and recovery assumptions
- [ ] **Monitoring**: Validate observability and alerting assumptions
- [ ] **Training**: Validate user training and adoption assumptions

## Recommendations

### Immediate Actions
1. **Stakeholder Review**: Review all assumptions with business stakeholders
2. **Technical Validation**: Validate technical assumptions with engineering team
3. **User Research**: Conduct user interviews to validate workflow assumptions

### Medium-term Actions
1. **Prototype Testing**: Test assumptions with working prototype
2. **Performance Validation**: Validate performance assumptions with load testing
3. **Security Assessment**: Validate security assumptions with security team

### Long-term Actions
1. **Continuous Validation**: Establish process for ongoing assumption validation
2. **Feedback Loop**: Create feedback mechanism for assumption updates
3. **Documentation Updates**: Maintain assumption documentation as system evolves
