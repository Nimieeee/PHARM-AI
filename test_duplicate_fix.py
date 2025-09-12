#!/usr/bin/env python3
"""
Test Duplicate Detection Fix
Verifies that duplicate detection works correctly per conversation
"""

from rag_system_chromadb import ChromaRAGSystem
from pathlib import Path
import shutil

def test_duplicate_detection_per_conversation():
    """Test that duplicate detection works correctly within and across conversations."""
    print("🔍 Testing duplicate detection per conversation...")
    
    # Create two conversations
    conv1 = ChromaRAGSystem("test-user-dup", "conv1")
    conv2 = ChromaRAGSystem("test-user-dup", "conv2")
    
    # Same document content and filename
    doc_content = b"Aspirin is a pain reliever medication."
    filename = "aspirin.txt"
    
    print("\n📝 Step 1: Add document to conversation 1")
    result1 = conv1.add_document(doc_content, filename, "text/plain")
    docs1 = conv1.get_documents_list()
    print(f"   Conv1 add result: {result1}")
    print(f"   Conv1 documents: {len(docs1)}")
    
    print("\n📝 Step 2: Add same document to conversation 1 again (should detect duplicate)")
    result1_dup = conv1.add_document(doc_content, filename, "text/plain")
    docs1_after = conv1.get_documents_list()
    print(f"   Conv1 duplicate add result: {result1_dup}")
    print(f"   Conv1 documents after duplicate: {len(docs1_after)}")
    
    print("\n📝 Step 3: Add same document to conversation 2 (should be allowed)")
    result2 = conv2.add_document(doc_content, filename, "text/plain")
    docs2 = conv2.get_documents_list()
    print(f"   Conv2 add result: {result2}")
    print(f"   Conv2 documents: {len(docs2)}")
    
    print("\n📝 Step 4: Add same document to conversation 2 again (should detect duplicate)")
    result2_dup = conv2.add_document(doc_content, filename, "text/plain")
    docs2_after = conv2.get_documents_list()
    print(f"   Conv2 duplicate add result: {result2_dup}")
    print(f"   Conv2 documents after duplicate: {len(docs2_after)}")
    
    # Verify results
    success = (
        len(docs1) == 1 and           # Conv1 has 1 document
        len(docs1_after) == 1 and     # Conv1 still has 1 document after duplicate
        len(docs2) == 1 and           # Conv2 has 1 document
        len(docs2_after) == 1         # Conv2 still has 1 document after duplicate
    )
    
    if success:
        print("\n✅ Duplicate detection working correctly!")
        print("   - Same document can be added to different conversations")
        print("   - Duplicates within same conversation are detected")
        print("   - Document count remains correct")
        return True
    else:
        print("\n❌ Duplicate detection failed!")
        print(f"   Conv1: {len(docs1)} -> {len(docs1_after)} documents")
        print(f"   Conv2: {len(docs2)} -> {len(docs2_after)} documents")
        return False

def cleanup_test_data():
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")
    
    try:
        test_dir = Path("user_data") / "rag_test-user-dup"
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("   ✅ Test data cleaned up")
    except Exception as e:
        print(f"   ⚠️ Error cleaning up: {e}")

if __name__ == "__main__":
    print("🧪 Duplicate Detection Fix Test")
    print("=" * 50)
    
    try:
        success = test_duplicate_detection_per_conversation()
        
        if success:
            print("\n🎉 TEST PASSED!")
            print("✅ Duplicate detection is working correctly per conversation")
        else:
            print("\n❌ TEST FAILED!")
            print("❌ Duplicate detection has issues")
    
    finally:
        cleanup_test_data()