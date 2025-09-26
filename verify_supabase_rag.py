"""
Verification script for Supabase + pgvector RAG implementation
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
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'MISTRAL_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing environment variables: {missing_vars}")
        return False
    
    logger.info("✅ All required environment variables are set")
    return True

async def test_supabase_connection():
    """Test Supabase connection."""
    try:
        from core.supabase_client import supabase_manager
        result = await supabase_manager.test_connection()
        if result:
            logger.info("✅ Supabase connection successful")
            return True
        else:
            logger.error("❌ Supabase connection failed")
            return False
    except Exception as e:
        logger.error(f"❌ Supabase connection error: {e}")
        return False

async def test_embedding_functionality():
    """Test embedding generation."""
    try:
        from core.rag import EmbeddingManager
        
        # Initialize embedding manager
        embedding_manager = EmbeddingManager()
        if not embedding_manager.is_available():
            logger.error("❌ Embedding manager not available")
            return False
        
        # Test embedding generation
        test_texts = ["This is a test document for pharmacology research."]
        embeddings = await embedding_manager.generate_embeddings(test_texts)
        
        if embeddings and len(embeddings) > 0 and len(embeddings[0]) == 1024:
            logger.info("✅ Embedding generation successful")
            logger.info(f"   Generated embedding with {len(embeddings[0])} dimensions")
            return True
        else:
            logger.error("❌ Embedding generation failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Embedding test error: {e}")
        return False

async def test_database_schema():
    """Test if database schema is properly set up."""
    try:
        from core.supabase_client import supabase_manager
        
        # Test if required tables exist
        tables_to_check = ['users', 'conversations', 'documents', 'document_chunks']
        
        client = await supabase_manager.get_client()
        
        for table in tables_to_check:
            try:
                result = await client.table(table).select('count').limit(1).execute()
                logger.info(f"✅ Table '{table}' exists and is accessible")
            except Exception as e:
                logger.error(f"❌ Table '{table}' check failed: {e}")
                return False
        
        # Test if vector extension is available
        try:
            result = await client.rpc('search_documents', {
                'p_query_embedding': [0.0] * 1024,
                'p_user_id': '00000000-0000-0000-0000-000000000000'
            }).execute()
            logger.info("✅ pgvector extension is available")
        except Exception as e:
            logger.error(f"❌ pgvector extension test failed: {e}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Database schema test error: {e}")
        return False

async def main():
    """Run all verification tests."""
    logger.info("🏥 Starting PharmGPT Supabase + pgvector verification...")
    
    # Check environment
    if not check_environment():
        return False
    
    # Test components
    tests = [
        ("Supabase Connection", test_supabase_connection()),
        ("Embedding Functionality", test_embedding_functionality()),
        ("Database Schema", test_database_schema())
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
    logger.info("VERIFICATION SUMMARY")
    logger.info("="*50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} | {test_name}")
        if not result:
            all_passed = False
    
    logger.info("="*50)
    if all_passed:
        logger.info("🎉 All tests passed! Supabase + pgvector implementation is ready.")
    else:
        logger.error("⚠️  Some tests failed. Please check the implementation.")
    
    return all_passed

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)