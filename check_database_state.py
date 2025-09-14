#!/usr/bin/env python3
"""
Check current database state to understand the schema
"""

import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_database_state():
    """Check what tables and columns currently exist."""
    
    print("🔍 Checking Current Database State")
    print("=" * 40)
    
    try:
        # Import Supabase connection
        from supabase_manager import connection_manager
        
        # Check what tables exist
        print("📊 Checking existing tables...")
        
        result = await connection_manager.execute_raw_sql(
            """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
            """
        )
        
        if result.data:
            tables = [row['table_name'] for row in result.data]
            print(f"✅ Found tables: {tables}")
        else:
            print("❌ No tables found")
            return False
        
        # Check documents table structure if it exists
        if 'documents' in tables:
            print("\n📄 Checking documents table structure...")
            
            result = await connection_manager.execute_raw_sql(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'documents'
                ORDER BY ordinal_position;
                """
            )
            
            if result.data:
                print("Documents table columns:")
                for row in result.data:
                    print(f"  - {row['column_name']}: {row['data_type']} ({'NULL' if row['is_nullable'] == 'YES' else 'NOT NULL'})")
            else:
                print("❌ Could not get documents table structure")
        
        # Check if document_chunks table exists
        if 'document_chunks' in tables:
            print("\n🧩 Checking document_chunks table structure...")
            
            result = await connection_manager.execute_raw_sql(
                """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'document_chunks'
                ORDER BY ordinal_position;
                """
            )
            
            if result.data:
                print("Document_chunks table columns:")
                for row in result.data:
                    print(f"  - {row['column_name']}: {row['data_type']} ({'NULL' if row['is_nullable'] == 'YES' else 'NOT NULL'})")
            else:
                print("❌ Could not get document_chunks table structure")
        else:
            print("\n🧩 document_chunks table does not exist yet")
        
        # Check if pgvector extension is enabled
        print("\n🔧 Checking pgvector extension...")
        
        result = await connection_manager.execute_raw_sql(
            "SELECT * FROM pg_extension WHERE extname = 'vector';"
        )
        
        if result.data:
            print("✅ pgvector extension is enabled")
        else:
            print("❌ pgvector extension not found")
        
        # Check existing functions
        print("\n⚙️ Checking existing functions...")
        
        result = await connection_manager.execute_raw_sql(
            """
            SELECT proname, pronargs 
            FROM pg_proc 
            WHERE proname LIKE '%document%' OR proname LIKE '%chunk%'
            ORDER BY proname;
            """
        )
        
        if result.data:
            print("Found functions:")
            for row in result.data:
                print(f"  - {row['proname']} ({row['pronargs']} args)")
        else:
            print("No document-related functions found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking database state: {e}")
        logger.exception("Database check error:")
        return False

async def main():
    """Run the database state check."""
    await check_database_state()

if __name__ == "__main__":
    asyncio.run(main())