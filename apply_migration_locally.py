#!/usr/bin/env python3
"""
Apply database migration locally before deploying to Streamlit Cloud
Run this once locally, then push to git for Streamlit Cloud deployment
"""

import os
from supabase import create_client

def apply_migration():
    """Apply the migration to add conversation_id column"""
    
    # Get Supabase credentials from environment or config
    SUPABASE_URL = os.getenv('SUPABASE_URL') or input("Enter your Supabase URL: ")
    SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY') or input("Enter your Supabase anon key: ")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    migration_sql = """
    -- Add conversation_id column to documents table
    ALTER TABLE documents 
    ADD COLUMN IF NOT EXISTS conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE;
    
    -- Create index for better performance
    CREATE INDEX IF NOT EXISTS idx_documents_conversation_id ON documents(conversation_id);
    
    -- Update the RLS policy for documents
    DROP POLICY IF EXISTS "Users can manage their own documents" ON documents;
    
    CREATE POLICY "Users can manage their own documents" ON documents
        FOR ALL USING (
            EXISTS (
                SELECT 1 FROM users 
                WHERE users.id = documents.user_uuid 
                AND (auth.uid()::text = users.user_id OR auth.uid() = users.id)
            )
            OR
            EXISTS (
                SELECT 1 FROM conversations c
                JOIN users u ON u.id = c.user_uuid
                WHERE c.id = documents.conversation_id
                AND (auth.uid()::text = u.user_id OR auth.uid() = u.id)
            )
        );
    """
    
    try:
        # Execute each statement separately
        statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
        
        for statement in statements:
            if statement:
                print(f"Executing: {statement[:50]}...")
                result = supabase.rpc('exec_sql', {'sql': statement})
                print("✓ Success")
        
        print("\n🎉 Migration completed successfully!")
        print("Your Streamlit Cloud app should now work properly.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print("\nPlease run the SQL manually in your Supabase dashboard:")
        print(migration_sql)

if __name__ == "__main__":
    apply_migration()