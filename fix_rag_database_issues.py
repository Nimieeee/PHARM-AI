#!/usr/bin/env python3
"""
Comprehensive fix for RAG database issues
"""

import asyncio
import logging
import sys
from supabase_manager import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_database_connection():
    """Check if we can connect to the database."""
    try:
        supabase = await get_supabase_client()
        if not supabase:
            return False
        
        # Test connection with a simple query
        result = await supabase.table('users').select('id').limit(1).execute()
        return True
        
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

async def check_document_chunks_table():
    """Check if document_chunks table exists and has correct structure."""
    try:
        supabase = await get_supabase_client()
        
        # Try to query the table structure
        result = await supabase.rpc('exec_sql', {
            'sql': """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'document_chunks'
            ORDER BY ordinal_position;
            """
        }).execute()
        
        if result.data:
            logger.info("✅ document_chunks table exists")
            for col in result.data:
                logger.info(f"   Column: {col['column_name']} ({col['data_type']})")
            return True
        else:
            logger.warning("⚠️ document_chunks table not found")
            return False
            
    except Exception as e:
        logger.error(f"Error checking table structure: {e}")
        return False

async def check_rls_policies():
    """Check RLS policies on document_chunks table."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.rpc('exec_sql', {
            'sql': """
            SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
            FROM pg_policies 
            WHERE tablename = 'document_chunks';
            """
        }).execute()
        
        if result.data:
            logger.info("✅ RLS policies found:")
            for policy in result.data:
                logger.info(f"   Policy: {policy['policyname']} ({policy['cmd']})")
            return True
        else:
            logger.warning("⚠️ No RLS policies found for document_chunks")
            return False
            
    except Exception as e:
        logger.error(f"Error checking RLS policies: {e}")
        return False

async def test_insert_permission():
    """Test if we can insert into document_chunks table."""
    try:
        supabase = get_supabase_client()
        
        # Get current user
        user = supabase.auth.get_user()
        if not user or not user.user:
            logger.error("❌ No authenticated user found")
            return False
        
        user_id = user.user.id
        logger.info(f"Testing insert with user ID: {user_id}")
        
        # Try a test insert
        import uuid
        test_data = {
            'document_uuid': str(uuid.uuid4()),
            'conversation_id': str(uuid.uuid4()),
            'user_uuid': user_id,
            'chunk_index': 0,
            'content': 'Test content for RLS check',
            'embedding': [0.1] * 384,  # Test embedding
            'metadata': '{}'
        }
        
        result = supabase.table('document_chunks').insert(test_data).execute()
        
        if result.data:
            logger.info("✅ Test insert successful")
            
            # Clean up test data
            test_id = result.data[0]['id']
            supabase.table('document_chunks').delete().eq('id', test_id).execute()
            logger.info("✅ Test data cleaned up")
            
            return True
        else:
            logger.error("❌ Test insert failed - no data returned")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test insert failed: {e}")
        return False

async def apply_comprehensive_fix():
    """Apply comprehensive fix for RAG database issues."""
    try:
        logger.info("🔧 Applying comprehensive RAG database fix...")
        
        supabase = get_supabase_client()
        
        # Read and apply the RLS fix
        with open('fix_document_chunks_rls_v2.sql', 'r') as f:
            sql_content = f.read()
        
        # Execute the fix
        try:
            result = supabase.rpc('exec_sql', {'sql': sql_content}).execute()
            logger.info("✅ RLS fix applied")
        except Exception as e:
            logger.warning(f"⚠️ RLS fix execution had issues: {e}")
        
        # Additional permissions fix
        additional_sql = """
        -- Ensure proper permissions for authenticated users
        GRANT ALL ON document_chunks TO authenticated;
        GRANT USAGE ON SEQUENCE document_chunks_id_seq TO authenticated;
        
        -- Ensure pgvector extension is available
        CREATE EXTENSION IF NOT EXISTS vector;
        
        -- Update RLS to be more permissive for testing
        DROP POLICY IF EXISTS "Allow all for authenticated users" ON document_chunks;
        CREATE POLICY "Allow all for authenticated users" ON document_chunks
        FOR ALL TO authenticated USING (true) WITH CHECK (true);
        """
        
        try:
            result = supabase.rpc('exec_sql', {'sql': additional_sql}).execute()
            logger.info("✅ Additional permissions applied")
        except Exception as e:
            logger.warning(f"⚠️ Additional permissions had issues: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error applying comprehensive fix: {e}")
        return False

async def main():
    """Main diagnostic and fix function."""
    print("🔍 RAG Database Issues Diagnostic and Fix")
    print("=" * 50)
    
    # Step 1: Check database connection
    logger.info("1. Checking database connection...")
    if not await check_database_connection():
        logger.error("❌ Cannot connect to database. Check your Supabase configuration.")
        return False
    
    # Step 2: Check table structure
    logger.info("2. Checking document_chunks table structure...")
    table_exists = await check_document_chunks_table()
    
    # Step 3: Check RLS policies
    logger.info("3. Checking RLS policies...")
    policies_exist = await check_rls_policies()
    
    # Step 4: Test insert permission
    logger.info("4. Testing insert permissions...")
    can_insert = await test_insert_permission()
    
    # Step 5: Apply fix if needed
    if not can_insert:
        logger.info("5. Applying comprehensive fix...")
        fix_applied = await apply_comprehensive_fix()
        
        if fix_applied:
            logger.info("6. Re-testing insert permissions...")
            can_insert_after_fix = await test_insert_permission()
            
            if can_insert_after_fix:
                logger.info("✅ Fix successful! RAG should now work properly.")
                return True
            else:
                logger.error("❌ Fix applied but insert still fails.")
                return False
        else:
            logger.error("❌ Failed to apply fix.")
            return False
    else:
        logger.info("✅ Database is working correctly!")
        return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)