#!/usr/bin/env python3
"""
Run database migration to add conversation_id to documents table
"""

import asyncio
from supabase_manager import get_supabase_client

async def run_migration():
    """Run the migration to add conversation_id column to documents table"""
    try:
        supabase = await get_supabase_client()

        # Read the migration SQL
        with open('add_conversation_id_to_documents.sql', 'r') as f:
            migration_sql = f.read()

        print("Running migration to add conversation_id to documents table...")

        # Execute the migration
        await supabase.rpc('execute_sql', {'query': migration_sql}).execute()

        print("Migration completed successfully!")
        print("Documents table now has conversation_id column")

    except Exception as e:
        print(f"Migration failed: {e}")
        print("You may need to run this migration manually in your Supabase SQL editor")
        print("\nSQL to run:")
        with open('add_conversation_id_to_documents.sql', 'r') as f:
            print(f.read())

if __name__ == "__main__":
    asyncio.run(run_migration())
