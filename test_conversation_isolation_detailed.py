#!/usr/bin/env python3
"""
Detailed Conversation Isolation Test
Tests that uploads from one chat do NOT appear in another chat
"""

import streamlit as st
from rag_interface_chromadb import initialize_rag_system, get_conversation_document_count
from rag_system_chromadb import ChromaRAGSystem
import tempfile
from pathlib import Path
import shutil

def simulate_streamlit_session():
    """Simulate Streamlit session state."""
    class MockSessionState:
        def __init__(self):
            self.authenticated = True
            self.user_id = "test-user-isolation"
            self.current_conversation_id = None
            self._data = {}
        
        def __getitem__(self, key):
            return self._data.get(key)
        
        def __setitem__(self, key, value):
            self._data[key] = value
        
        def __contains__(self, key):
            return key in self._data
        
        def get(self, key, default=None):
            return self._data.get(key, default)
    
    return MockSessionState()

def test_conversation_isolation_detailed():
    """Test detailed conversation isolation scenarios."""
    print("🔍 Testing detailed conversation isolation...")
    
    # Mock Streamlit session state
    mock_session = simulate_streamlit_session()
    
    # Test scenario 1: Upload to conversation A, switch to conversation B
    print("\n📝 Scenario 1: Upload to Conv A, check Conv B")
    
    conv_a_id = "conversation-a-12345"
    conv_b_id = "conversation-b-67890"
    
    # Create RAG systems directly (bypassing Streamlit session for clarity)
    rag_a = ChromaRAGSystem("test-user-isolation", conv_a_id)
    rag_b = ChromaRAGSystem("test-user-isolation", conv_b_id)
    
    # Add document to conversation A
    doc_content = "Pharmacokinetics studies drug absorption and distribution in the body."
    success = rag_a.add_document(
        doc_content.encode('utf-8'),
        "pharmacokinetics.txt",
        "text/plain"
    )
    
    if not success:
        print("❌ Failed to add document to conversation A")
        return False
    
    # Check document counts
    docs_a = rag_a.get_documents_list()
    docs_b = rag_b.get_documents_list()
    
    print(f"   Conversation A documents: {len(docs_a)}")
    print(f"   Conversation B documents: {len(docs_b)}")
    
    # Search in conversation B for content from A
    search_results_b = rag_b.search_documents("pharmacokinetics", n_results=5)
    print(f"   Conversation B search for 'pharmacokinetics': {len(search_results_b)} results")
    
    # Check if any results contain the content from A
    contamination = any("pharmacokinetics" in result['content'].lower() for result in search_results_b)
    
    if len(docs_a) == 1 and len(docs_b) == 0 and not contamination:
        print("   ✅ Scenario 1 PASSED - Perfect isolation")
    else:
        print("   ❌ Scenario 1 FAILED - Cross-conversation contamination detected")
        return False
    
    # Test scenario 2: Multiple documents in different conversations
    print("\n📝 Scenario 2: Multiple docs in different conversations")
    
    # Add different document to conversation B
    doc_b_content = "Chocolate cake recipe with cocoa powder and sugar."
    success_b = rag_b.add_document(
        doc_b_content.encode('utf-8'),
        "cake_recipe.txt",
        "text/plain"
    )
    
    if not success_b:
        print("❌ Failed to add document to conversation B")
        return False
    
    # Now both conversations have documents
    docs_a_after = rag_a.get_documents_list()
    docs_b_after = rag_b.get_documents_list()
    
    print(f"   Conversation A documents: {len(docs_a_after)}")
    print(f"   Conversation B documents: {len(docs_b_after)}")
    
    # Cross-search tests
    search_a_for_cake = rag_a.search_documents("cake", n_results=5)
    search_b_for_pharma = rag_b.search_documents("pharmacokinetics", n_results=5)
    
    print(f"   Conv A search for 'cake': {len(search_a_for_cake)} results")
    print(f"   Conv B search for 'pharmacokinetics': {len(search_b_for_pharma)} results")
    
    # Check content isolation
    a_has_cake = any("cake" in result['content'].lower() for result in search_a_for_cake)
    b_has_pharma = any("pharmacokinetics" in result['content'].lower() for result in search_b_for_pharma)
    
    if not a_has_cake and not b_has_pharma:
        print("   ✅ Scenario 2 PASSED - No cross-contamination")
    else:
        print("   ❌ Scenario 2 FAILED - Cross-contamination detected")
        print(f"      Conv A has cake content: {a_has_cake}")
        print(f"      Conv B has pharma content: {b_has_pharma}")
        return False
    
    # Test scenario 3: ChromaDB collection isolation
    print("\n📝 Scenario 3: ChromaDB collection isolation")
    
    # Check that collections are different
    collection_a = rag_a.collection_name
    collection_b = rag_b.collection_name
    
    print(f"   Collection A: {collection_a}")
    print(f"   Collection B: {collection_b}")
    
    if collection_a != collection_b:
        print("   ✅ Scenario 3 PASSED - Different ChromaDB collections")
    else:
        print("   ❌ Scenario 3 FAILED - Same ChromaDB collection used")
        return False
    
    # Test scenario 4: Directory isolation
    print("\n📝 Scenario 4: Directory isolation")
    
    dir_a = rag_a.conversation_rag_dir
    dir_b = rag_b.conversation_rag_dir
    
    print(f"   Directory A: {dir_a}")
    print(f"   Directory B: {dir_b}")
    
    if dir_a != dir_b and dir_a.exists() and dir_b.exists():
        print("   ✅ Scenario 4 PASSED - Separate directories")
    else:
        print("   ❌ Scenario 4 FAILED - Directory isolation issue")
        return False
    
    return True

def cleanup_test_data():
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")
    
    try:
        test_dir = Path("user_data") / "rag_test-user-isolation"
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("   ✅ Test data cleaned up")
        else:
            print("   ✅ No test data to clean up")
    except Exception as e:
        print(f"   ⚠️ Error cleaning up: {e}")

if __name__ == "__main__":
    print("🧪 Detailed Conversation Isolation Test")
    print("=" * 60)
    
    try:
        success = test_conversation_isolation_detailed()
        
        if success:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Conversation isolation is working perfectly")
            print("✅ Uploads from one chat do NOT appear in other chats")
        else:
            print("\n❌ TESTS FAILED!")
            print("❌ There are conversation isolation issues")
    
    finally:
        cleanup_test_data()