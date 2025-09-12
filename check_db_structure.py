#!/usr/bin/env python3
"""
Check database structure
"""

from supabase_manager import get_supabase_client

def check_structure():
    """Check database structure"""
    try:
        supabase = get_supabase_client()
        
        # Check conversations table
        print("Checking conversations table...")
        result = supabase.table('conversations').select('*').limit(5).execute()
        if result.data:
            print(f"Sample conversation: {result.data[0]}")
            print(f"Conversation ID field: {result.data[0].get('id')}")
            print(f"Conversation conversation_id field: {result.data[0].get('conversation_id')}")
        
        # Check documents table structure by trying to insert minimal data
        print("\nChecking documents table structure...")
        try:
            # Try to insert with minimal fields to see what's required
            test_doc = {
                'user_uuid': '14ed4163-9a32-4bfd-aa27-dbcb4aee0b99',
                'document_id': 'test_structure_check',
                'filename': 'test.txt',
                'file_type': 'text/plain',
                'file_size': 100
            }
            result = supabase.table('documents').insert(test_doc).execute()
            print(f"Document insert successful: {result.data}")
            
            # Clean up
            supabase.table('documents').delete().eq('document_id', 'test_structure_check').execute()
            
        except Exception as e:
            print(f"Document insert failed: {e}")
        
        # Check what fields exist in documents table
        print("\nChecking existing documents...")
        result = supabase.table('documents').select('*').limit(1).execute()
        if result.data:
            print(f"Sample document fields: {list(result.data[0].keys())}")
        else:
            print("No documents found")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_structure()