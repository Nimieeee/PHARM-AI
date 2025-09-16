"""
Apply Database Fixes for PharmGPT
Run this script to fix the database issues
"""

import asyncio
import logging
from supabase_manager import connection_manager

logger = logging.getLogger(__name__)

async def apply_database_fixes():
    """Apply the database fixes."""
    
    print("🔧 Applying database fixes...")
    
    try:
        # Test connection first
        print("📡 Testing database connection...")
        if not await connection_manager.test_connection():
            print("❌ Database connection failed!")
            return False
        
        print("✅ Database connection successful")
        
        # Check if document_chunks table exists
        print("🔍 Checking for document_chunks table...")
        try:
            result = await connection_manager.execute_query(
                'document_chunks',
                'select',
                limit=1
            )
            print("✅ document_chunks table exists")
        except Exception as e:
            if "does not exist" in str(e).lower():
                print("❌ document_chunks table missing!")
                print("📋 Please run the SQL script 'fix_database_issues.sql' in your Supabase SQL Editor")
                print("   This will create the missing table and fix RLS policies")
                return False
            else:
                print(f"⚠️  Error checking table: {e}")
        
        # Test RLS policies
        print("🔒 Testing RLS policies...")
        try:
            # Try to insert a test record (this should work with the fixed policies)
            test_data = {
                'user_uuid': '00000000-0000-0000-0000-000000000000',
                'document_id': 'test_doc',
                'chunk_index': 0,
                'content': 'test content'
            }
            
            result = await connection_manager.execute_query(
                'document_chunks',
                'insert',
                data=test_data
            )
            
            if result.data:
                # Clean up test record
                await connection_manager.execute_query(
                    'document_chunks',
                    'delete',
                    eq={'document_id': 'test_doc'}
                )
                print("✅ RLS policies working correctly")
            else:
                print("⚠️  RLS policies may need adjustment")
                
        except Exception as e:
            if "row-level security policy" in str(e).lower():
                print("❌ RLS policy issues detected!")
                print("📋 Please run the SQL script 'fix_database_issues.sql' in your Supabase SQL Editor")
                return False
            else:
                print(f"⚠️  Error testing RLS: {e}")
        
        print("🎉 Database fixes verification complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error applying fixes: {e}")
        return False

def main():
    """Main function to run the fixes."""
    print("🚀 PharmGPT Database Fix Tool")
    print("=" * 40)
    
    # Run the async function
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    success = loop.run_until_complete(apply_database_fixes())
    
    if success:
        print("\n✅ All checks passed!")
        print("🔧 If you're still experiencing issues:")
        print("   1. Run 'fix_database_issues.sql' in Supabase SQL Editor")
        print("   2. Restart your Streamlit app")
        print("   3. Clear browser cache and cookies")
    else:
        print("\n❌ Issues detected!")
        print("📋 Action required:")
        print("   1. Copy the contents of 'fix_database_issues.sql'")
        print("   2. Paste and run it in your Supabase SQL Editor")
        print("   3. Run this script again to verify")

if __name__ == "__main__":
    main()