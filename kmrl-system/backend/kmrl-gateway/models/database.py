"""
Database Connection Management for KMRL Gateway
PostgreSQL connection handling with SQLAlchemy
Based on doc_processor implementation with KMRL-specific enhancements
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import structlog

load_dotenv()
logger = structlog.get_logger()

# Database configuration - PostgreSQL only
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://kmrl_user:kmrl_password@localhost:5432/kmrl_db")

# Test PostgreSQL connection
try:
    test_engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    test_engine.connect()
    logger.info("Using PostgreSQL database")
except Exception as e:
    logger.error(f"PostgreSQL connection failed: {e}")
    raise Exception(f"Cannot connect to PostgreSQL database: {e}")

# Create SQLAlchemy engine with PostgreSQL connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

def get_db():
    """Dependency to get a database session for each request"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

def drop_tables():
    """Drop all database tables (for testing/development)"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise
