#!/usr/bin/env python3
"""
Test ChromaDB Connection
Verifies that ChromaDB works properly for conversation-specific RAG
"""

import os
from pathlib import Path
from rag_system_chromadb import ChromaRAGSystem
import tempfile
from PIL import Image
import io

def test_chromadb_basic():
    """Test basic ChromaDB functionality."""
    print("🔍 Testing ChromaDB basic functionality...")
    
    try:
        # Create test RAG system
        test_user_id = "test-user-12345"
        test_conversation_id = "test-conversation-67890"
        
        rag_system = ChromaRAGSystem(test_user_id, test_conversation_id)
        
        # Check health
        health = rag_system.health_check()
        print(f"✅ RAG System Health: {health['status']}")
        print(f"📊 Mode: {health['mode']}")
        print(f"🔗 ChromaDB Ready: {health['chromadb_ready']}")
        print(f"📚 Documents: {health['documents_count']}")
        print(f"🔢 Vectors: {health['vector_count']}")
        
        return health['chromadb_ready']
        
    except Exception as e:
        print(f"❌ ChromaDB basic test failed: {e}")
        return False

def test_document_operations():
    """Test document add/search operations."""
    print("\n🔍 Testing document operations...")
    
    try:
        # Create test RAG system
        test_user_id = "test-user-12345"
        test_conversation_id = "test-conversation-67890"
        
        rag_system = ChromaRAGSystem(test_user_id, test_conversation_id)
        
        # Test adding a text document
        test_content = """
        Pharmacokinetics is the study of drug absorption, distribution, metabolism, and excretion.
        The four main processes are:
        1. Absorption - how the drug enters the body
        2. Distribution - how the drug spreads throughout the body
        3. Metabolism - how the drug is broken down
        4. Excretion - how the drug is eliminated from the body
        
        These processes determine the drug's bioavailability and half-life.
        """
        
        # Add document
        success = rag_system.add_document(
            file_content=test_content.encode('utf-8'),
            filename="pharmacokinetics_basics.txt",
            file_type="text/plain"
        )
        
        if success:
            print("✅ Document added successfully")
        else:
            print("❌ Failed to add document")
            return False
        
        # Test search
        results = rag_system.search_documents("What is pharmacokinetics?", n_results=3)
        
        if results:
            print(f"✅ Search returned {len(results)} results")
            for i, result in enumerate(results):
                print(f"   Result {i+1}: Score {result['relevance_score']:.3f}")
                print(f"   Content preview: {result['content'][:100]}...")
        else:
            print("❌ Search returned no results")
            return False
        
        # Test context generation
        context = rag_system.get_context_for_query("pharmacokinetics processes")
        if context:
            print(f"✅ Context generated: {len(context)} characters")
        else:
            print("❌ No context generated")
            return False
        
        # Test document listing
        docs = rag_system.get_documents_list()
        print(f"✅ Document list: {len(docs)} documents")
        
        return True
        
    except Exception as e:
        print(f"❌ Document operations test failed: {e}")
        return False

def test_conversation_isolation():
    """Test that different conversations have isolated knowledge bases."""
    print("\n🔍 Testing conversation isolation...")
    
    try:
        test_user_id = "test-user-12345"
        
        # Create two different conversation RAG systems
        rag_conv1 = ChromaRAGSystem(test_user_id, "conversation-1")
        rag_conv2 = ChromaRAGSystem(test_user_id, "conversation-2")
        
        # Add different documents to each conversation
        doc1_content = "Aspirin is a pain reliever and anti-inflammatory medication used for headaches."
        doc2_content = "Chocolate cake is a delicious dessert made with cocoa and sugar."
        
        # Add to conversation 1
        success1 = rag_conv1.add_document(
            file_content=doc1_content.encode('utf-8'),
            filename="aspirin_info.txt",
            file_type="text/plain"
        )
        
        # Add to conversation 2
        success2 = rag_conv2.add_document(
            file_content=doc2_content.encode('utf-8'),
            filename="cake_info.txt",
            file_type="text/plain"
        )
        
        if not (success1 and success2):
            print("❌ Failed to add documents to conversations")
            return False
        
        # Search in conversation 1 for aspirin
        results1 = rag_conv1.search_documents("aspirin", n_results=3)
        
        # Search in conversation 2 for aspirin (should find nothing)
        results2 = rag_conv2.search_documents("aspirin", n_results=3)
        
        # Debug: Print what was found
        print(f"   Debug - Conv2 aspirin results: {[r['content'][:50] for r in results2]}")
        
        # Search in conversation 2 for cake
        results3 = rag_conv2.search_documents("cake", n_results=3)
        
        print(f"✅ Conversation 1 aspirin search: {len(results1)} results")
        print(f"✅ Conversation 2 aspirin search: {len(results2)} results (should be 0)")
        print(f"✅ Conversation 2 cake search: {len(results3)} results")
        
        # Verify isolation by checking content
        conv1_has_aspirin = any("aspirin" in r['content'].lower() for r in results1)
        conv2_has_aspirin = any("aspirin" in r['content'].lower() for r in results2)
        conv2_has_cake = any("cake" in r['content'].lower() for r in results3)
        
        print(f"   Conv1 contains aspirin: {conv1_has_aspirin}")
        print(f"   Conv2 contains aspirin: {conv2_has_aspirin}")
        print(f"   Conv2 contains cake: {conv2_has_cake}")
        
        # Verify isolation
        if conv1_has_aspirin and not conv2_has_aspirin and conv2_has_cake:
            print("✅ Conversation isolation working correctly!")
            return True
        else:
            print("❌ Conversation isolation failed!")
            return False
        
    except Exception as e:
        print(f"❌ Conversation isolation test failed: {e}")
        return False

def test_image_processing():
    """Test image processing capabilities."""
    print("\n🔍 Testing image processing...")
    
    try:
        # Create a simple test image with text
        img = Image.new('RGB', (200, 100), color='white')
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        
        # Create test RAG system
        test_user_id = "test-user-12345"
        test_conversation_id = "test-conversation-images"
        
        rag_system = ChromaRAGSystem(test_user_id, test_conversation_id)
        
        # Test adding image
        success = rag_system.add_image(img, "test_diagram.png")
        
        if success:
            print("✅ Image added successfully")
            
            # Test search for image
            results = rag_system.search_documents("diagram", n_results=3)
            if results:
                print(f"✅ Image search returned {len(results)} results")
                return True
            else:
                print("❌ Image search returned no results")
                return False
        else:
            print("❌ Failed to add image")
            return False
        
    except Exception as e:
        print(f"❌ Image processing test failed: {e}")
        return False

def cleanup_test_data():
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")
    
    try:
        import shutil
        test_dir = Path("user_data") / "rag_test-user-12345"
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("✅ Test data cleaned up")
        else:
            print("✅ No test data to clean up")
        
    except Exception as e:
        print(f"⚠️ Error cleaning up test data: {e}")

if __name__ == "__main__":
    print("🧪 ChromaDB Integration Test")
    print("=" * 50)
    
    # Run tests
    tests = [
        ("Basic ChromaDB", test_chromadb_basic),
        ("Document Operations", test_document_operations),
        ("Conversation Isolation", test_conversation_isolation),
        ("Image Processing", test_image_processing),
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
    
    # Clean up
    cleanup_test_data()
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! ChromaDB is ready to use.")
    else:
        print("❌ Some tests failed. Check the errors above.")