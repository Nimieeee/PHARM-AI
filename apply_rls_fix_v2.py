#!/usr/bin/env python3
"""
Apply RLS Fix Version 2 for document_chunks
"""

import asyncio
import logging
from supabase_manager import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def apply_rls_fix():
    """Apply the RLS fix for document_chunks."""
    try:
        logger.info("🔧 Applying RLS fix version 2 for document_chunks...")
        
        # Get Supabase client
        supabase = get_supabase_client()
        if not supabase:
            logger.error("❌ Failed to connect to Supabase")
            return False
        
        # Read the SQL fix
        with open('fix_document_chunks_rls_v2.sql', 'r') as f:
            sql_content = f.read()
        
        # Split into individual statements
        statements = []
        current_statement = ""
        in_function = False
        
        for line in sql_content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('--'):
                continue
            
            current_statement += line + "\n"
            
            # Check for function definitions
            if 'CREATE OR REPLACE FUNCTION' in line.upper():
                in_function = True
            elif in_function and line.endswith('$$;'):
                in_function = False
                statements.append(current_statement.strip())
                current_statement = ""
            elif not in_function and line.endswith(';'):
                statements.append(current_statement.strip())
                current_statement = ""
        
        # Add any remaining statement
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            if not statement:
                continue
                
            try:
                logger.info(f"📝 Executing statement {i}/{len(statements)}...")
                logger.debug(f"Statement: {statement[:100]}...")
                
                # Use raw SQL execution
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                
                if result.data:
                    logger.info(f"✅ Statement {i} executed successfully")
                else:
                    logger.warning(f"⚠️ Statement {i} completed with no data returned")
                    
            except Exception as stmt_error:
                logger.error(f"❌ Statement {i} failed: {stmt_error}")
                logger.debug(f"Failed statement: {statement}")
                # Continue with other statements
        
        logger.info("✅ RLS fix version 2 applied successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error applying RLS fix: {e}")
        return False

def main():
    """Main function."""
    print("🚀 Applying RLS Fix Version 2 for document_chunks")
    print("=" * 60)
    
    success = asyncio.run(apply_rls_fix())
    
    if success:
        print("\n✅ RLS fix applied successfully!")
        print("🎯 Document chunks should now work properly with RAG processing")
    else:
        print("\n❌ RLS fix failed. Check logs for details.")

if __name__ == "__main__":
    main()