#!/usr/bin/env python3
"""
Simple Query Interface for OpenSearch RAG Engine
"""

import sys
import os
from typing import List, Dict, Any

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from opensearch_query_processor import OpenSearchQueryProcessor
from query_processing import opensearch_similarity_search, display_opensearch_results

def main():
    """Simple query interface for testing OpenSearch queries"""
    print("🚀 KMRM RAG Query Interface")
    print("=" * 50)
    print("This interface allows you to query your embeddings stored in OpenSearch")
    print()
    
    try:
        # Test OpenSearch connection
        print("🔌 Testing OpenSearch connection...")
        processor = OpenSearchQueryProcessor()
        
        # Get index stats
        stats = processor.get_index_stats()
        print(f"✅ Connected to OpenSearch!")
        print(f"   Index: {stats.get('index_name', 'Unknown')}")
        print(f"   Documents: {stats.get('total_documents', 'Unknown')}")
        
        # Get available departments
        departments = processor.search_departments()
        if departments:
            print(f"   Departments: {', '.join(departments)}")
        
        print("\n" + "=" * 50)
        
        while True:
            print("\n🔍 Query Options:")
            print("1. Quick search (vector similarity)")
            print("2. Text search (keyword matching)")
            print("3. Hybrid search (vector + text)")
            print("4. Search by department")
            print("5. Show index statistics")
            print("6. Exit")
            
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                query = input("Enter your query: ").strip()
                if query:
                    dept = input("Department filter (optional): ").strip() or None
                    results = opensearch_similarity_search(
                        query=query,
                        search_type="vector",
                        department=dept
                    )
                    display_opensearch_results(results, query)
            
            elif choice == "2":
                query = input("Enter search text: ").strip()
                if query:
                    dept = input("Department filter (optional): ").strip() or None
                    results = opensearch_similarity_search(
                        query=query,
                        search_type="text",
                        department=dept
                    )
                    display_opensearch_results(results, query)
            
            elif choice == "3":
                query = input("Enter your query: ").strip()
                if query:
                    dept = input("Department filter (optional): ").strip() or None
                    results = opensearch_similarity_search(
                        query=query,
                        search_type="hybrid",
                        department=dept
                    )
                    display_opensearch_results(results, query)
            
            elif choice == "4":
                if departments:
                    print(f"Available departments: {', '.join(departments)}")
                    dept = input("Enter department: ").strip()
                    if dept:
                        results = processor.search_by_text("", size=10, department=dept)
                        display_results_simple(results, f"Department: {dept}")
                else:
                    print("No departments found in index")
            
            elif choice == "5":
                stats = processor.get_index_stats()
                print(f"\n📊 Index Statistics:")
                print(f"   Total documents: {stats.get('total_documents', 'Unknown')}")
                print(f"   Index name: {stats.get('index_name', 'Unknown')}")
                
                sample = stats.get('sample_document')
                if sample:
                    print(f"   Sample document ID: {sample.get('document_id', 'Unknown')}")
                    print(f"   Sample text: {sample.get('text', '')[:100]}...")
                    print(f"   Embedding dimension: {len(sample.get('embedding', []))}")
            
            elif choice == "6":
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please try again.")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure OpenSearch is running on localhost:9200")
        print("2. Check if your embeddings index exists")
        print("3. Verify your OpenSearch connection settings")


def display_results_simple(results: List[Dict[str, Any]], title: str):
    """Simple results display"""
    print(f"\n{title}")
    print("=" * 50)
    
    if not results:
        print("No results found.")
        return
    
    print(f"Found {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['document_id']} (Chunk {result['chunk_index']})")
        print(f"   Score: {result['similarity_score']:.4f}")
        print(f"   Text: {result['text'][:100]}...")
        print("-" * 30)


if __name__ == "__main__":
    main()
