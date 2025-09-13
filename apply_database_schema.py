#!/usr/bin/env python3
"""
Apply database schema to Supabase using direct SQL execution
"""

import asyncio
import logging
from supabase_manager import get_supabase_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def apply_schema():
    """Apply the database schema functions that are missing."""
    try:
        client = await get_supabase_client()
        if not client:
            logger.error("❌ Could not connect to Supabase")
            return False

        logger.info("🔧 Applying missing database functions...")

        # The functions we need to create
        functions_sql = """
        -- Function to set user context for RLS (if needed)
        CREATE OR REPLACE FUNCTION set_user_context(user_identifier TEXT)
        RETURNS VOID AS $$
        BEGIN
            -- Set the user context for RLS policies
            PERFORM set_config('app.current_user_id', user_identifier, false);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;

        -- Function to get current user context
        CREATE OR REPLACE FUNCTION get_current_user_id()
        RETURNS TEXT AS $$
        BEGIN
            RETURN current_setting('app.current_user_id', true);
        END;
        $$ LANGUAGE plpgsql;
        """

        # Try to execute the functions using a different approach
        # Since we can't execute DDL directly, let's try using the SQL editor approach
        logger.info("📝 Functions to create:")
        print("\n" + "="*60)
        print("COPY AND PASTE THE FOLLOWING SQL INTO YOUR SUPABASE SQL EDITOR:")
        print("="*60)
        print(functions_sql)
        print("="*60)
        print("\n1. Go to your Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Paste the above SQL and run it")
        print("4. Then run this script again to verify\n")

        return False  # Return False so user knows to apply manually

    except Exception as e:
        logger.error(f"💥 Schema application failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(apply_schema())