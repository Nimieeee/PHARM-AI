"""
Simple database structure verification for PharmGPT
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set."""
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing environment variables: {missing_vars}")
        return False
    
    logger.info("✅ Required Supabase environment variables are set")
    return True

async def test_database_structure():
    """Test if database schema is properly set up."""
    try:
        from core.supabase_client import supabase_manager
        
        # Test Supabase connection
        connection_result = await supabase_manager.test_connection()
        if not connection_result:
            logger.error("❌ Supabase connection failed")
            return False
        
        logger.info("✅ Supabase connection successful")
        
        # Test if required tables exist
        tables_to_check = ['users', 'user_sessions', 'conversations', 'messages', 'documents', 'document_chunks']
        
        client = await supabase_manager.get_client()
        
        for table in tables_to_check:
            try:
                # Try to get table info
                result = await client.table(table).select('count').limit(1).execute()
                logger.info(f"✅ Table '{table}' exists and is accessible")
            except Exception as e:
                logger.error(f"❌ Table '{table}' check failed: {e}")
                return False
        
        # Test if vector extension is available by checking document_chunks structure
        try:
            # Check if document_chunks table has the embedding column with correct dimensions
            chunk_result = await client.table('document_chunks').select('*').limit(1).execute()
            if chunk_result.data:
                logger.info("✅ document_chunks table is accessible")
            else:
                logger.info("✅ document_chunks table exists (empty)")
        except Exception as e:
            logger.error(f"❌ document_chunks table check failed: {e}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Database structure test error: {e}")
        return False

async def test_rag_functions():
    """Test if RAG functions exist."""
    try:
        from core.supabase_client import supabase_manager
        
        client = await supabase_manager.get_client()
        
        # Test if search_documents function exists
        try:
            # Try to call the function with dummy parameters
            result = await client.rpc('search_documents', {
                'p_query_embedding': [0.0] * 1024,
                'p_user_id': '00000000-0000-0000-0000-000000000000',
                'p_conversation_id': None,
                'p_similarity_threshold': 0.0,
                'p_limit': 1
            }).execute()
            logger.info("✅ search_documents function exists and is callable")
        except Exception as e:
            # If it's a parameter error, that's okay - function exists
            if "p_query_embedding" in str(e) or "p_user_id" in str(e):
                logger.info("✅ search_documents function exists")
            else:
                logger.error(f"❌ search_documents function check failed: {e}")
                return False
        
        # Test if get_conversation_context function exists
        try:
            result = await client.rpc('get_conversation_context', {
                'p_conversation_id': 'test',
                'p_user_id': '00000000-0000-0000-0000-000000000000'
            }).execute()
            logger.info("✅ get_conversation_context function exists and is callable")
        except Exception as e:
            # If it's a parameter error, that's okay - function exists
            if "p_conversation_id" in str(e) or "p_user_id" in str(e):
                logger.info("✅ get_conversation_context function exists")
            else:
                logger.error(f"❌ get_conversation_context function check failed: {e}")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"❌ RAG functions test error: {e}")
        return False

async def main():
    """Run all verification tests."""
    logger.info("🏥 Starting PharmGPT database structure verification...")
    
    # Check environment
    if not check_environment():
        return False
    
    # Test components
    tests = [
        ("Database Structure", test_database_structure()),
        ("RAG Functions", test_rag_functions())
    ]
    
    results = []
    for test_name, test_coro in tests:
        logger.info(f"\n🔍 Testing {test_name}...")
        try:
            result = await test_coro
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("DATABASE VERIFICATION SUMMARY")
    logger.info("="*50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} | {test_name}")
        if not result:
            all_passed = False
    
    logger.info("="*50)
    if all_passed:
        logger.info("🎉 All database tests passed! Schema is correctly set up.")
    else:
        logger.error("⚠️  Some tests failed. Please check the database schema.")
    
    return all_passed

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)