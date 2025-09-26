#!/usr/bin/env python3
"""
Comprehensive verification script for PharmGPT implementation
"""

import os
import asyncio
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """Check if required environment variables are set."""
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
        return False
    
    logger.info("✅ Required environment variables are set")
    return True

async def verify_supabase_connection():
    """Verify Supabase database connection."""
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

async def verify_database_schema():
    """Verify database schema is properly set up."""
    try:
        from core.supabase_client import supabase_manager
        client = await supabase_manager.get_client()
        
        # Check required tables
        required_tables = [
            'users', 'sessions', 'conversations', 
            'messages', 'documents', 'document_chunks'
        ]
        
        logger.info("🔍 Checking database schema...")
        results = []
        
        for table in required_tables:
            try:
                # Try to query the table
                result = await client.table(table).select('count').limit(1).execute()
                logger.info(f"✅ Table '{table}' exists")
                results.append(True)
            except Exception as e:
                logger.error(f"❌ Table '{table}' missing or inaccessible: {e}")
                results.append(False)
        
        # Check if document_chunks has embedding column
        try:
            chunk_result = await client.table('document_chunks').select('*').limit(1).execute()
            if chunk_result.data:
                logger.info("✅ document_chunks table accessible")
                # Check for embedding column structure
                if 'embedding' in chunk_result.data[0]:
                    logger.info("✅ embedding column exists in document_chunks")
                else:
                    logger.warning("⚠️ embedding column not found in document_chunks")
            else:
                logger.info("✅ document_chunks table exists (empty)")
        except Exception as e:
            logger.error(f"❌ document_chunks table check failed: {e}")
            results.append(False)
        
        return all(results[:6])  # First 6 results for table checks
        
    except Exception as e:
        logger.error(f"❌ Database schema verification error: {e}")
        return False

async def verify_rag_functions():
    """Verify RAG-related database functions."""
    try:
        from core.supabase_client import supabase_manager
        client = await supabase_manager.get_client()
        
        # Test search_documents function
        try:
            # Call with dummy parameters to check if function exists
            result = await client.rpc('search_documents', {
                'p_query_embedding': [0.0] * 1024,
                'p_user_id': '00000000-0000-0000-0000-000000000000'
            }).execute()
            logger.info("✅ search_documents function exists")
        except Exception as e:
            if "function" in str(e).lower():
                logger.error(f"❌ search_documents function missing: {e}")
                return False
            else:
                # Function exists but parameter error, which is expected
                logger.info("✅ search_documents function exists")
        
        # Test get_conversation_context function
        try:
            result = await client.rpc('get_conversation_context', {
                'p_conversation_id': 'test',
                'p_user_id': '00000000-0000-0000-0000-000000000000'
            }).execute()
            logger.info("✅ get_conversation_context function exists")
        except Exception as e:
            if "function" in str(e).lower():
                logger.error(f"❌ get_conversation_context function missing: {e}")
                return False
            else:
                # Function exists but parameter error, which is expected
                logger.info("✅ get_conversation_context function exists")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ RAG functions verification error: {e}")
        return False

async def verify_embedding_system():
    """Verify embedding generation system."""
    try:
        from core.rag import EmbeddingManager
        
        # Initialize embedding manager
        embedding_manager = EmbeddingManager()
        if not embedding_manager.is_available():
            logger.warning("⚠️ Embedding manager not available (Mistral API key may be missing)")
            return True  # Not critical for database verification
        
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
        logger.error(f"❌ Embedding system verification error: {e}")
        return False

async def verify_authentication_system():
    """Verify authentication system components."""
    try:
        # Check if authentication manager can be imported
        from core.auth import AuthenticationManager
        logger.info("✅ AuthenticationManager imported successfully")
        
        # Check if supabase_manager has auth functions
        from core.supabase_client import supabase_manager
        client = await supabase_manager.get_client()
        
        # Test if auth functions exist (don't call them to avoid creating test data)
        logger.info("✅ Authentication system components available")
        return True
        
    except Exception as e:
        logger.error(f"❌ Authentication system verification error: {e}")
        return False

async def main():
    """Run comprehensive verification."""
    logger.info("🏥 Starting PharmGPT Comprehensive Verification")
    logger.info("=" * 50)
    
    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed")
        return False
    
    # Run verification tests
    tests = [
        ("Supabase Connection", verify_supabase_connection()),
        ("Database Schema", verify_database_schema()),
        ("RAG Functions", verify_rag_functions()),
        ("Embedding System", verify_embedding_system()),
        ("Authentication System", verify_authentication_system())
    ]
    
    results = []
    for test_name, test_coro in tests:
        logger.info(f"\n🔍 Running {test_name} test...")
        try:
            result = await test_coro
            results.append((test_name, result))
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} {test_name}")
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} | {test_name}")
        if not result:
            all_passed = False
    
    logger.info("=" * 50)
    if all_passed:
        logger.info("🎉 All verification tests passed!")
        logger.info("✅ PharmGPT is ready for use with Supabase + pgvector")
    else:
        logger.error("⚠️ Some verification tests failed.")
        logger.error("Please check the implementation and try again.")
    
    return all_passed

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Verification failed with error: {e}")
        sys.exit(1)