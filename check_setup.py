#!/usr/bin/env python3
"""
Final Setup Verification Script
This script checks if PharmGPT is ready for use
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_setup():
    """Comprehensive setup verification."""
    logger.info("🏥 PharmGPT Setup Verification")
    logger.info("=" * 40)
    
    # 1. Environment variables
    logger.info("\n1. Environment Variables Check:")
    required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
    env_status = True
    
    for var in required_vars:
        if os.getenv(var):
            logger.info(f"   ✅ {var}: SET")
        else:
            logger.error(f"   ❌ {var}: MISSING")
            env_status = False
    
    # Optional: Mistral API key
    if os.getenv('MISTRAL_API_KEY'):
        logger.info("   ✅ MISTRAL_API_KEY: SET (for embeddings)")
    else:
        logger.warning("   ⚠️  MISTRAL_API_KEY: MISSING (embeddings will use dummy vectors)")
    
    # 2. File structure
    logger.info("\n2. File Structure Check:")
    required_files = [
        'app.py',
        'pages/3_💬_Chatbot.py',
        'core/__init__.py',
        'core/config.py',
        'core/auth.py',
        'core/conversations.py',
        'core/rag.py',
        'core/supabase_client.py'
    ]
    
    file_status = True
    for file_path in required_files:
        if os.path.exists(file_path):
            logger.info(f"   ✅ {file_path}")
        else:
            logger.error(f"   ❌ {file_path}: NOT FOUND")
            file_status = False
    
    # 3. Database setup (basic check)
    logger.info("\n3. Database Setup Check:")
    try:
        from core.supabase_client import supabase_manager
        import asyncio
        
        # This is a basic connection test
        async def test_connection():
            return await supabase_manager.test_connection()
        
        result = asyncio.run(test_connection())
        if result:
            logger.info("   ✅ Supabase connection: SUCCESS")
            db_status = True
        else:
            logger.error("   ❌ Supabase connection: FAILED")
            db_status = False
            
    except Exception as e:
        logger.error(f"   ❌ Supabase connection test failed: {e}")
        db_status = False
    
    # Summary
    logger.info("\n" + "=" * 40)
    logger.info("SETUP VERIFICATION SUMMARY")
    logger.info("=" * 40)
    
    all_checks = [env_status, file_status, db_status]
    passed_checks = sum(all_checks)
    
    if passed_checks == 3:
        logger.info("🎉 ALL CHECKS PASSED!")
        logger.info("✅ PharmGPT is ready for use!")
        logger.info("\n🚀 To start the application:")
        logger.info("   streamlit run app.py")
        return True
    else:
        logger.error(f"⚠️  {3 - passed_checks} CHECK(S) FAILED")
        logger.error("❌ PharmGPT is not ready yet.")
        logger.info("\n📋 Next steps:")
        if not env_status:
            logger.info("   1. Set required environment variables in .env file")
        if not file_status:
            logger.info("   2. Ensure all required files are present")
        if not db_status:
            logger.info("   3. Execute complete_database_setup.sql in Supabase SQL Editor")
        return False

if __name__ == "__main__":
    try:
        result = check_setup()
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"❌ Setup verification failed: {e}")
        sys.exit(1)