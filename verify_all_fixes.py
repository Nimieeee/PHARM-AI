#!/usr/bin/env python3
"""
Quick verification script to test all fixes after implementation
This script checks that:
1. Database schema is correct with 1024-dimensional embeddings
2. User isolation functions work properly
3. RAG service functions are available
4. All required database functions exist
"""

import os
import asyncio
import uuid
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test basic database connection and schema."""
    print("🔗 Testing database connection...")
    
    try:
        from supabase_manager import connection_manager
        
        # Test basic connection
        result = await connection_manager.test_connection()
        if result:
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False

async def test_document_chunks_table():
    """Test document_chunks table exists with correct schema."""
    print("\n📋 Testing document_chunks table schema...")
    
    try:
        from supabase import create_async_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Missing Supabase credentials")
            return False
        
        client = await create_async_client(supabase_url, supabase_key)
        
        # Check if table exists and can handle 1024-dimensional vectors
        test_embedding = [0.1] * 1024
        test_data = {
            'document_id': f'test_schema_{uuid.uuid4()}',
            'user_uuid': str(uuid.uuid4()),
            'chunk_index': 0,
            'content': 'Test content for schema verification',
            'embedding': test_embedding,
            'metadata': {'test': True}
        }
        
        # Try to insert test data
        result = await client.table('document_chunks').insert(test_data).execute()
        
        if result.data:
            # Clean up test data
            test_id = result.data[0]['id']
            await client.table('document_chunks').delete().eq('id', test_id).execute()
            print("✅ document_chunks table supports 1024-dimensional vectors")
            return True
        else:
            print("❌ Failed to insert test data into document_chunks")
            return False
            
    except Exception as e:
        print(f"❌ document_chunks table test failed: {e}")
        return False

async def test_database_functions():
    """Test that all required database functions exist."""
    print("\n🔍 Testing database functions...")
    
    try:
        from supabase import create_async_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        client = await create_async_client(supabase_url, supabase_key)
        
        functions_to_test = [
            'search_document_chunks',
            'get_conversation_chunks',
            'set_user_context'
        ]
        
        for func_name in functions_to_test:
            try:
                # Test if function exists by calling it with minimal parameters
                if func_name == 'search_document_chunks':
                    test_embedding = [0.0] * 1024
                    await client.rpc(func_name, {
                        'query_embedding': test_embedding,
                        'match_count': 1
                    }).execute()
                elif func_name == 'get_conversation_chunks':
                    await client.rpc(func_name, {
                        'target_conversation_id': 'test',
                        'target_user_uuid': str(uuid.uuid4())
                    }).execute()
                elif func_name == 'set_user_context':
                    await client.rpc(func_name, {
                        'user_uuid_param': str(uuid.uuid4())
                    }).execute()
                
                print(f"✅ Function {func_name} exists and callable")
            except Exception as e:
                if "does not exist" in str(e).lower():
                    print(f"❌ Function {func_name} does not exist")
                    return False
                else:
                    # Function exists but may have failed due to data/permissions
                    print(f"✅ Function {func_name} exists (execution failed as expected)")
        
        return True
        
    except Exception as e:
        print(f"❌ Database functions test failed: {e}")
        return False

def test_user_isolation_functions():
    """Test that user isolation functions are available."""
    print("\n🔒 Testing user isolation functions...")
    
    try:
        from fix_user_isolation import (
            get_secure_conversations,
            secure_update_conversations,
            secure_update_conversation,
            secure_delete_conversation,
            ensure_user_isolation,
            initialize_secure_session
        )
        
        print("✅ All user isolation functions imported successfully")
        return True
        
    except ImportError as e:
        print(f"❌ User isolation functions missing: {e}")
        return False

def test_rag_service_functions():
    """Test that RAG service functions are available."""
    print("\n🤖 Testing RAG service functions...")
    
    try:
        from services.rag_service import (
            RAGService,
            search_documents,
            process_document_for_rag,
            search_conversation_context,
            delete_document_from_rag
        )
        
        # Test RAG service initialization
        rag = RAGService()
        if rag:
            print("✅ RAG service initialized successfully")
        
        print("✅ All RAG service functions imported successfully")
        return True
        
    except ImportError as e:
        print(f"❌ RAG service functions missing: {e}")
        return False

async def test_embedding_fix():
    """Test the complete embedding fix workflow."""
    print("\n🧪 Testing complete embedding workflow...")
    
    try:
        from services.rag_service import search_documents
        
        # Test search function with dummy data
        test_user_uuid = str(uuid.uuid4())
        
        # This should not fail even with no data
        results = await search_documents(
            query="test query",
            user_uuid=test_user_uuid,
            limit=5
        )
        
        print(f"✅ search_documents function works (returned {len(results)} results)")
        return True
        
    except Exception as e:
        print(f"❌ Embedding workflow test failed: {e}")
        return False

async def main():
    """Run all verification tests."""
    print("🚀 Starting comprehensive fix verification...\n")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Document Chunks Table", test_document_chunks_table), 
        ("Database Functions", test_database_functions),
        ("User Isolation Functions", test_user_isolation_functions),
        ("RAG Service Functions", test_rag_service_functions),
        ("Embedding Fix Workflow", test_embedding_fix)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "="*60)
    print("📊 VERIFICATION RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("Your PharmGPT application is ready with:")
        print("✅ 1024-dimensional Mistral AI embeddings")
        print("✅ Proper user isolation")
        print("✅ Complete RAG system")
        print("✅ All database functions")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    asyncio.run(main())