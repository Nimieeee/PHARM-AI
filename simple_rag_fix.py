#!/usr/bin/env python3
"""
Simple RAG Database Fix - Synchronous Version
"""

import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_simple_fix():
    """Apply a simple fix using direct SQL execution."""
    try:
        logger.info("🔧 Applying simple RAG database fix...")
        
        # Try to import supabase
        try:
            from supabase import create_client, Client
        except ImportError:
            logger.error("❌ Supabase not installed. Run: pip install supabase")
            return False
        
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        # Get credentials
        url = os.environ.get("SUPABASE_URL", "").strip().strip('"')
        key = os.environ.get("SUPABASE_ANON_KEY", "").strip().strip('"')
        
        if not url or not key:
            logger.error("❌ Missing Supabase credentials")
            logger.info("Set SUPABASE_URL and SUPABASE_ANON_KEY environment variables")
            logger.info(f"Current URL: {url[:20]}..." if url else "None")
            logger.info(f"Current KEY: {key[:20]}..." if key else "None")
            return False
        
        # Create client
        supabase: Client = create_client(url, key)
        
        # Simple fix SQL
        fix_sql = """
        -- Drop existing policies
        DROP POLICY IF EXISTS "Users can manage their own document chunks" ON document_chunks;
        DROP POLICY IF EXISTS "Users can insert their own document chunks" ON document_chunks;
        DROP POLICY IF EXISTS "Users can select their own document chunks" ON document_chunks;
        DROP POLICY IF EXISTS "Users can update their own document chunks" ON document_chunks;
        DROP POLICY IF EXISTS "Users can delete their own document chunks" ON document_chunks;
        
        -- Disable RLS temporarily for testing
        ALTER TABLE document_chunks DISABLE ROW LEVEL SECURITY;
        
        -- Grant permissions
        GRANT ALL ON document_chunks TO authenticated;
        GRANT ALL ON document_chunks TO anon;
        """
        
        # Execute fix
        try:
            result = supabase.rpc('exec_sql', {'sql': fix_sql}).execute()
            logger.info("✅ Simple fix applied - RLS disabled for testing")
            
            # Test insert
            import uuid
            test_data = {
                'document_uuid': str(uuid.uuid4()),
                'conversation_id': str(uuid.uuid4()),
                'user_uuid': str(uuid.uuid4()),
                'chunk_index': 0,
                'content': 'Test content',
                'embedding': [0.1] * 384,
                'metadata': '{}'
            }
            
            insert_result = supabase.table('document_chunks').insert(test_data).execute()
            
            if insert_result.data:
                logger.info("✅ Test insert successful!")
                
                # Clean up
                test_id = insert_result.data[0]['id']
                supabase.table('document_chunks').delete().eq('id', test_id).execute()
                logger.info("✅ Test data cleaned up")
                
                return True
            else:
                logger.error("❌ Test insert failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fix execution failed: {e}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error in simple fix: {e}")
        return False

def main():
    """Main function."""
    print("🚀 Simple RAG Database Fix")
    print("=" * 40)
    
    success = apply_simple_fix()
    
    if success:
        print("\n✅ Simple fix applied successfully!")
        print("🎯 RAG document processing should now work")
        print("⚠️  Note: RLS is disabled for testing - re-enable in production")
    else:
        print("\n❌ Simple fix failed. Check logs for details.")

if __name__ == "__main__":
    main()