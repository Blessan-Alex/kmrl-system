"""
Database Initialization Script for KMRL Gateway Enhanced
Creates PostgreSQL tables and initializes the database
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from models.database import create_tables, engine, Base
from models.database_models import Document, ProcessingLog, DocumentVersion
import structlog

logger = structlog.get_logger()

def init_database():
    """Initialize the database with all tables"""
    try:
        logger.info("Initializing KMRL Gateway Enhanced database...")
        
        # Create all tables
        create_tables()
        
        logger.info("Database initialization completed successfully")
        logger.info("Created tables:")
        logger.info("- documents")
        logger.info("- processing_logs") 
        logger.info("- document_versions")
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def drop_database():
    """Drop all database tables (for testing/development)"""
    try:
        logger.info("Dropping all database tables...")
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        
        logger.info("Database tables dropped successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        return False

def reset_database():
    """Reset database by dropping and recreating all tables"""
    try:
        logger.info("Resetting database...")
        
        # Drop all tables
        drop_database()
        
        # Create all tables
        init_database()
        
        logger.info("Database reset completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="KMRL Gateway Enhanced Database Management")
    parser.add_argument("action", choices=["init", "drop", "reset"], 
                       help="Action to perform: init, drop, or reset")
    
    args = parser.parse_args()
    
    if args.action == "init":
        success = init_database()
    elif args.action == "drop":
        success = drop_database()
    elif args.action == "reset":
        success = reset_database()
    
    if success:
        print("✅ Database operation completed successfully")
        sys.exit(0)
    else:
        print("❌ Database operation failed")
        sys.exit(1)
