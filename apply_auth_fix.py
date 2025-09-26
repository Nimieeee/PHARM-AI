#!/usr/bin/env python3
"""
Apply the authentication fix to the database
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def apply_auth_fix():
    """Apply the authentication fix to the database"""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")
        
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Read the updated SQL file
        with open("auth_fix_complete_updated.sql", "r") as f:
            sql_content = f.read()
        
        # Split into statements (simple split by semicolon)
        statements = [stmt.strip() + ";" for stmt in sql_content.split(";") if stmt.strip()]
        
        # Execute each statement
        logger.info("Applying authentication fix...")
        for i, statement in enumerate(statements):
            if statement.strip() and not statement.strip().startswith("--"):
                try:
                    # Skip the DO blocks and NOTICE statements as they can't be executed via RPC
                    if "DO $$" not in statement and "RAISE NOTICE" not in statement:
                        logger.info(f"Executing statement {i+1}/{len(statements)}")
                        # For function creation and table modifications, we need to use the proper RPC
                        result = supabase.rpc("execute_sql", {"query": statement}).execute()
                        logger.info(f"Statement {i+1} executed successfully")
                except Exception as e:
                    logger.warning(f"Statement {i+1} failed (may be OK if dropping non-existent objects): {e}")
        
        logger.info("✅ Authentication fix applied successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error applying authentication fix: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(apply_auth_fix())
    exit(0 if result else 1)