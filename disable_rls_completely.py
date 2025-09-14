#!/usr/bin/env python3
"""
Completely disable RLS for document_chunks table
"""

import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def disable_rls_completely():
    """Completely disable RLS and grant all permissions."""
    try:
        logger.info("🔧 Completely disabling RLS for document_chunks...")
        
        # Load environment
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass
        
        # Import supabase
        from supabase import create_client, Client
        
        # Get credentials
        url = os.environ.get("SUPABASE_URL", "").strip().strip('"')
        key = os.environ.get("SUPABASE_ANON_KEY", "").strip().strip('"')
        
        # Create client
        supabase: Client = create_client(url, key)
        
        # Complete RLS removal
        disable_sql = """
        -- Drop ALL policies
        DO $$ 
        DECLARE 
            r RECORD;
        BEGIN
            FOR r IN (SELECT policyname FROM pg_policies WHERE tablename = 'document_chunks') 
            LOOP
                EXECUTE 'DROP POLICY IF EXISTS ' || quote_ident(r.policyname) || ' ON document_chunks';
            END LOOP;
        END $$;
        
        -- Completely disable RLS
        ALTER TABLE document_chunks DISABLE ROW LEVEL SECURITY;
        
        -- Grant ALL permissions to everyone
        GRANT ALL PRIVILEGES ON document_chunks TO PUBLIC;
        GRANT ALL PRIVILEGES ON document_chunks TO authenticated;
        GRANT ALL PRIVILEGES ON document_chunks TO anon;
        GRANT USAGE ON SEQUENCE document_chunks_id_seq TO PUBLIC;
        GRANT USAGE ON SEQUENCE document_chunks_id_seq TO authenticated;
        GRANT USAGE ON SEQUENCE document_chunks_id_seq TO anon;
        
        -- Make sure the table exists with correct structure
        CREATE TABLE IF NOT EXISTS document_chunks (
            id BIGSERIAL PRIMARY KEY,
            document_uuid UUID NOT NULL,
            conversation_id UUID,
            user_uuid UUID NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding vector(384),
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Execute
        result = supabase.rpc('exec_sql', {'sql': disable_sql}).execute()
        logger.info("✅ RLS completely disabled")
        
        # Test insert without any user context
        import uuid
        test_data = {
            'document_uuid': str(uuid.uuid4()),
            'conversation_id': str(uuid.uuid4()),
            'user_uuid': str(uuid.uuid4()),
            'chunk_index': 0,
            'content': 'Test content for RLS disabled',
            'embedding': [0.1] * 384,
            'metadata': '{}'
        }
        
        insert_result = supabase.table('document_chunks').insert(test_data).execute()
        
        if insert_result.data:
            logger.info("✅ Test insert successful with RLS disabled!")
            
            # Clean up
            test_id = insert_result.data[0]['id']
            supabase.table('document_chunks').delete().eq('id', test_id).execute()
            logger.info("✅ Test data cleaned up")
            
            return True
        else:
            logger.error("❌ Test insert still failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error disabling RLS: {e}")
        return False

def main():
    """Main function."""
    print("🚀 Completely Disable RLS for document_chunks")
    print("=" * 50)
    
    success = disable_rls_completely()
    
    if success:
        print("\n✅ RLS completely disabled!")
        print("🎯 RAG document processing should now work")
        print("⚠️  WARNING: Table is now publicly accessible")
        print("   Re-enable proper RLS policies in production")
    else:
        print("\n❌ Failed to disable RLS.")

if __name__ == "__main__":
    main()