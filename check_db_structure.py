#!/usr/bin/env python3
"""
Check the current database structure to understand the authentication issue
"""

import os
import asyncio
import logging
from supabase import create_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_database_structure():
    """Check the current database structure"""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")

        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Check if we can connect
        logger.info("Testing database connection...")
        result = supabase.table('users').select('count').limit(1).execute()
        logger.info(f"✅ Database connection successful: {result}")
        
        # Try to get a simple count of users
        try:
            result = supabase.table('users').select('count').execute()
            logger.info(f"Users table count: {result}")
        except Exception as e:
            logger.info(f"Could not get user count: {e}")
        
        logger.info("✅ Database structure check completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking database structure: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(check_database_structure())
    exit(0 if result else 1)