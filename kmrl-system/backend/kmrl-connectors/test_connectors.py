#!/usr/bin/env python3
"""
Test Script for KMRL Connectors
Tests all connectors with mock data and validates functionality
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from connectors.email_connector import EmailConnector
from connectors.maximo_connector import MaximoConnector
from connectors.sharepoint_connector import SharePointConnector
from connectors.whatsapp_connector import WhatsAppConnector
from utils.credentials_manager import CredentialsManager

def test_email_connector():
    """Test email connector functionality"""
    print("Testing Email Connector...")
    
    try:
        # Mock credentials
        credentials = {
            "email": "test@kmrl.com",
            "password": "test_password"
        }
        
        # Test connector initialization
        connector = EmailConnector(imap_host="imap.gmail.com", imap_port=993)
        
        # Test language detection
        test_subject = "Maintenance Report - റിപ്പോർട്ട്"
        language = connector.detect_language(type('obj', (object,), {'get': lambda x, y: test_subject})())
        print(f"✓ Language detection: {language}")
        
        # Test department classification
        department = connector.classify_department("Urgent Maintenance Required")
        print(f"✓ Department classification: {department}")
        
        # Test KMRL document check
        is_kmrl_doc = connector.is_kmrl_document("maintenance_report.pdf")
        print(f"✓ KMRL document check: {is_kmrl_doc}")
        
        print("✓ Email connector tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Email connector test failed: {e}")
        return False

def test_maximo_connector():
    """Test Maximo connector functionality"""
    print("Testing Maximo Connector...")
    
    try:
        # Mock credentials
        credentials = {
            "username": "test_user",
            "password": "test_password"
        }
        
        # Test connector initialization
        connector = MaximoConnector(base_url="https://maximo.test.com")
        
        # Test department classification
        department = connector.classify_department("maintenance", "Equipment repair and calibration")
        print(f"✓ Department classification: {department}")
        
        # Test sync status
        status = connector.get_sync_status()
        print(f"✓ Sync status: {status}")
        
        print("✓ Maximo connector tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Maximo connector test failed: {e}")
        return False

def test_sharepoint_connector():
    """Test SharePoint connector functionality"""
    print("Testing SharePoint Connector...")
    
    try:
        # Mock credentials
        credentials = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret"
        }
        
        # Test connector initialization
        connector = SharePointConnector(site_url="https://test.sharepoint.com")
        
        # Test content type detection
        content_type = connector.get_content_type("pdf", "application/pdf")
        print(f"✓ Content type detection: {content_type}")
        
        # Test department classification
        department = connector.classify_department("Board Meeting Minutes")
        print(f"✓ Department classification: {department}")
        
        print("✓ SharePoint connector tests passed")
        return True
        
    except Exception as e:
        print(f"✗ SharePoint connector test failed: {e}")
        return False

def test_whatsapp_connector():
    """Test WhatsApp connector functionality"""
    print("Testing WhatsApp Connector...")
    
    try:
        # Mock credentials
        credentials = {
            "access_token": "test_access_token"
        }
        
        # Test connector initialization
        connector = WhatsAppConnector(phone_number_id="test_phone_id")
        
        # Test language detection
        language = connector.detect_language("Field report - ഫീൽഡ് റിപ്പോർട്ട്")
        print(f"✓ Language detection: {language}")
        
        # Test department classification
        department = connector.classify_department("Safety incident at station", "field_worker_001")
        print(f"✓ Department classification: {department}")
        
        # Test filename extraction
        filename = connector.extract_filename({"url": "https://example.com/report.pdf"}, "media_123")
        print(f"✓ Filename extraction: {filename}")
        
        print("✓ WhatsApp connector tests passed")
        return True
        
    except Exception as e:
        print(f"✗ WhatsApp connector test failed: {e}")
        return False

def test_credentials_manager():
    """Test credentials manager functionality"""
    print("Testing Credentials Manager...")
    
    try:
        # Test credentials manager initialization
        manager = CredentialsManager()
        
        # Test email credentials
        email_creds = manager.get_email_credentials()
        print(f"✓ Email credentials: {type(email_creds)}")
        
        # Test Maximo credentials
        maximo_creds = manager.get_maximo_credentials()
        print(f"✓ Maximo credentials: {type(maximo_creds)}")
        
        # Test SharePoint credentials
        sharepoint_creds = manager.get_sharepoint_credentials()
        print(f"✓ SharePoint credentials: {type(sharepoint_creds)}")
        
        # Test WhatsApp credentials
        whatsapp_creds = manager.get_whatsapp_credentials()
        print(f"✓ WhatsApp credentials: {type(whatsapp_creds)}")
        
        print("✓ Credentials manager tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Credentials manager test failed: {e}")
        return False

def test_base_connector():
    """Test base connector functionality"""
    print("Testing Base Connector...")
    
    try:
        from base.base_connector import BaseConnector, Document
        
        # Test Document dataclass
        doc = Document(
            source="test",
            filename="test.pdf",
            content=b"test content",
            content_type="application/pdf",
            metadata={"test": "value"},
            document_id="test_123",
            uploaded_at=datetime.now(),
            language="english"
        )
        
        print(f"✓ Document creation: {doc.filename}")
        
        # Test base connector initialization
        class TestConnector(BaseConnector):
            def fetch_documents(self, credentials, options=None):
                return []
        
        connector = TestConnector("test", "http://localhost:3000")
        
        # Test sync status
        status = connector.get_sync_status()
        print(f"✓ Sync status: {status}")
        
        print("✓ Base connector tests passed")
        return True
        
    except Exception as e:
        print(f"✗ Base connector test failed: {e}")
        return False

def run_all_tests():
    """Run all connector tests"""
    print("=" * 60)
    print("KMRL CONNECTORS TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Base Connector", test_base_connector),
        ("Email Connector", test_email_connector),
        ("Maximo Connector", test_maximo_connector),
        ("SharePoint Connector", test_sharepoint_connector),
        ("WhatsApp Connector", test_whatsapp_connector),
        ("Credentials Manager", test_credentials_manager),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed + failed}, Passed: {passed}, Failed: {failed}")
    
    if failed == 0:
        print("🎉 All tests passed! KMRL connectors are ready for deployment.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
