-- PostgreSQL Setup for KMRL Knowledge Hub

-- Create database
CREATE DATABASE kmrl_db;

-- Create user
CREATE USER kmrl_user WITH PASSWORD 'kmrl_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE kmrl_db TO kmrl_user;

-- Connect to kmrl_db
\c kmrl_db;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    source VARCHAR(50) NOT NULL,
    content_type VARCHAR(100),
    file_size BIGINT,
    storage_path TEXT,
    metadata JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    confidence_score FLOAT,
    language VARCHAR(10),
    department VARCHAR(50),
    uploaded_by UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create document_chunks table
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_text TEXT,
    chunk_index INTEGER,
    embedding JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create notifications table
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255),
    message TEXT,
    notification_type VARCHAR(50),
    priority VARCHAR(20),
    recipients JSONB,
    document_id UUID REFERENCES documents(id),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create departments table
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100),
    code VARCHAR(10) UNIQUE,
    description TEXT,
    head VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_documents_source ON documents(source);
CREATE INDEX idx_documents_department ON documents(department);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_notifications_type ON notifications(notification_type);
CREATE INDEX idx_notifications_priority ON notifications(priority);

-- Insert default departments
INSERT INTO departments (name, code, description) VALUES
('Engineering', 'ENG', 'Maintenance and technical operations'),
('Finance', 'FIN', 'Financial management and accounting'),
('Human Resources', 'HR', 'Personnel and training'),
('Safety', 'SAF', 'Safety and compliance'),
('Operations', 'OPS', 'Train operations and scheduling'),
('Executive', 'EXEC', 'Executive management and policy');
