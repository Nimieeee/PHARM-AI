#!/usr/bin/env python3
"""
Test New Chat Isolation
Simulates creating a new chat and verifying no documents from other chats appear
"""

from rag_interface_chromadb import initialize_rag_system, get_conversation_document_count
from rag_system_chromadb import ChromaRAGSystem
import uuid
from pathlib import Path
import shutil

class MockStreamlitSession:
    """Mock Streamlit session state for testing."""
    def __init__(self):
        self.authenticated = True
        self.user_id = "test-user-newchat"
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
    
    def __getattr__(self, name):
        return self._data.get(name)
    
    def __setattr__(self, name, value):
        if name.startswith('_') or name in ['authenticated', 'user_id', 'current_conversation_id']:
            super().__setattr__(name, value)
        else:
            self._data[name] = value

def test_new_chat_isolation():
    """Test that a new chat has no documents from existing chats."""
    print("🔍 Testing new chat isolation...")
    
    # Simulate existing chat with documents
    print("\n📝 Step 1: Create existing chat with documents")
    existing_chat_id = str(uuid.uuid4())
    existing_rag = ChromaRAGSystem("test-user-newchat", existing_chat_id)
    
    # Add document to existing chat
    doc_content = "Aspirin is a common pain reliever used for headaches and inflammation."
    success = existing_rag.add_document(
        doc_content.encode('utf-8'),
        "aspirin_info.txt",
        "text/plain"
    )
    
    if not success:
        print("❌ Failed to add document to existing chat")
        return False
    
    existing_docs = existing_rag.get_documents_list()
    print(f"   Existing chat documents: {len(existing_docs)}")
    
    # Simulate creating a new chat
    print("\n📝 Step 2: Create new chat")
    new_chat_id = str(uuid.uuid4())
    new_rag = ChromaRAGSystem("test-user-newchat", new_chat_id)
    
    # Check if new chat has any documents
    new_docs = new_rag.get_documents_list()
    print(f"   New chat documents: {len(new_docs)}")
    
    # Search in new chat for content from existing chat
    search_results = new_rag.search_documents("aspirin", n_results=5)
    print(f"   New chat search for 'aspirin': {len(search_results)} results")
    
    # Check if any results contain content from existing chat
    has_aspirin_content = any("aspirin" in result['content'].lower() for result in search_results)
    print(f"   New chat contains aspirin content: {has_aspirin_content}")
    
    # Verify isolation - new chat should have no documents and no aspirin content
    if len(new_docs) == 0 and not has_aspirin_content:
        print("   ✅ Perfect isolation - new chat is clean")
        return True
    else:
        print("   ❌ Isolation failed - new chat has contamination")
        print(f"      New docs: {len(new_docs)}")
        print(f"      Search results: {len(search_results)}")
        print(f"      Has aspirin content: {has_aspirin_content}")
        return False

def test_multiple_new_chats():
    """Test creating multiple new chats and verify they're all isolated."""
    print("\n🔍 Testing multiple new chats...")
    
    # Create base chat with document
    base_chat_id = str(uuid.uuid4())
    base_rag = ChromaRAGSystem("test-user-newchat", base_chat_id)
    
    base_doc = "Pharmacokinetics describes how drugs move through the body."
    base_rag.add_document(
        base_doc.encode('utf-8'),
        "pharmacokinetics.txt",
        "text/plain"
    )
    
    # Create multiple new chats
    new_chats = []
    for i in range(3):
        chat_id = str(uuid.uuid4())
        rag = ChromaRAGSystem("test-user-newchat", chat_id)
        new_chats.append((chat_id, rag))
    
    # Check each new chat
    all_clean = True
    for i, (chat_id, rag) in enumerate(new_chats):
        docs = rag.get_documents_list()
        search_results = rag.search_documents("pharmacokinetics", n_results=5)
        
        # Check if any results contain pharmacokinetics content
        has_pharma_content = any("pharmacokinetics" in result['content'].lower() for result in search_results)
        
        print(f"   New chat {i+1}: {len(docs)} docs, has pharma content: {has_pharma_content}")
        
        if len(docs) > 0 or has_pharma_content:
            all_clean = False
    
    if all_clean:
        print("   ✅ All new chats are clean")
        return True
    else:
        print("   ❌ Some new chats have contamination")
        return False

def test_conversation_id_uniqueness():
    """Test that conversation IDs are properly unique and isolated."""
    print("\n🔍 Testing conversation ID uniqueness...")
    
    # Create chats with similar but different IDs
    chat_ids = [
        "conversation-1",
        "conversation-2", 
        "conversation-11",  # Similar to conversation-1
        "conversation-1a"   # Similar to conversation-1
    ]
    
    rags = {}
    for chat_id in chat_ids:
        rag = ChromaRAGSystem("test-user-newchat", chat_id)
        rags[chat_id] = rag
        
        # Add unique document to each
        doc_content = f"This is document for {chat_id} with unique content."
        rag.add_document(
            doc_content.encode('utf-8'),
            f"doc_{chat_id}.txt",
            "text/plain"
        )
    
    # Test cross-contamination by checking if documents from other conversations appear
    contamination_found = False
    for chat_id, rag in rags.items():
        # Get all documents in this conversation
        docs = rag.get_documents_list()
        
        for doc in docs:
            # Check if this document's filename suggests it belongs to another conversation
            for other_chat_id in chat_ids:
                if (chat_id != other_chat_id and 
                    other_chat_id in doc['filename'] and 
                    chat_id not in doc['filename']):  # Make sure it's not just a substring match
                    print(f"   ❌ Chat {chat_id} contains document from {other_chat_id}: {doc['filename']}")
                    contamination_found = True
    
    if not contamination_found:
        print("   ✅ All conversation IDs properly isolated")
        return True
    else:
        print("   ❌ Cross-contamination found between similar IDs")
        return False

def cleanup_test_data():
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")
    
    try:
        test_dir = Path("user_data") / "rag_test-user-newchat"
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("   ✅ Test data cleaned up")
    except Exception as e:
        print(f"   ⚠️ Error cleaning up: {e}")

if __name__ == "__main__":
    print("🧪 New Chat Isolation Test")
    print("=" * 50)
    
    tests = [
        ("New Chat Isolation", test_new_chat_isolation),
        ("Multiple New Chats", test_multiple_new_chats),
        ("Conversation ID Uniqueness", test_conversation_id_uniqueness)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        print("-" * 30)
        
        if test_func():
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED")
    
    cleanup_test_data()
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! New chats are perfectly isolated.")
        print("✅ Uploads from other chats do NOT appear in new chats.")
    else:
        print("❌ Some isolation issues detected.")
        print("🔍 Check the failed tests above for details.")