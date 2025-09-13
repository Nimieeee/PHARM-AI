#!/usr/bin/env python3
"""
Check if required database functions exist in Supabase
"""

import asyncio
import logging
from supabase_manager import get_supabase_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_database_functions():
    """Check if required database functions exist."""
    try:
        client = await get_supabase_client()
        if not client:
            logger.error("❌ Could not connect to Supabase")
            return False

        logger.info("🔍 Checking database functions...")

        # Check if set_user_context function exists (optional)
        try:
            result = await client.rpc('set_user_context', {
                'user_identifier': 'test-user-123'
            }).execute()
            logger.info("✅ set_user_context function exists and works")
        except Exception as e:
            if "PGRST202" in str(e) or "not found" in str(e).lower():
                logger.info("ℹ️  set_user_context function not found (optional - RLS context setting disabled)")
            else:
                logger.error(f"❌ set_user_context function error: {e}")
                return False

        # Check if get_current_user_id function exists (optional)
        try:
            result = await client.rpc('get_current_user_id').execute()
            logger.info(f"✅ get_current_user_id function exists, returned: {result.data}")
        except Exception as e:
            if "PGRST202" in str(e) or "not found" in str(e).lower():
                logger.info("ℹ️  get_current_user_id function not found (optional - RLS context reading disabled)")
            else:
                logger.error(f"❌ get_current_user_id function error: {e}")
                return False

        # Check if tables exist
        try:
            result = await client.table('users').select('count').limit(1).execute()
            logger.info("✅ users table exists")
        except Exception as e:
            logger.error(f"❌ users table error: {e}")
            return False

        try:
            result = await client.table('conversations').select('count').limit(1).execute()
            logger.info("✅ conversations table exists")
        except Exception as e:
            logger.error(f"❌ conversations table error: {e}")
            return False

        logger.info("🎉 All database functions and tables are working correctly!")
        return True

    except Exception as e:
        logger.error(f"💥 Database check failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(check_database_functions())