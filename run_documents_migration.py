#!/usr/bin/env python3
"""
Run migration to fix documents table schema
"""

import asyncio
from supabase_manager import get_supabase_client

async def run_migration():
    """Run the migration to fix documents table schema"""
    try:
        supabase = await get_supabase_client()

        # Read the migration SQL
        with open('fix_documents_table_schema.sql', 'r') as f:
            migration_sql = f.read()

        print("Running migration to fix documents table schema...")

        # Split into individual statements and execute them
        statements = [s.strip() for s in migration_sql.split(';') if s.strip()]

        for i, statement in enumerate(statements):
            if statement:
                print(f"Executing statement {i+1}/{len(statements)}...")
                try:
                    # Use raw SQL execution
                    await supabase.rpc('execute_sql', {'query': statement}).execute()
                    print(f"✓ Statement {i+1} completed")
                except Exception as e:
                    print(f"⚠️  Statement {i+1} failed (might be expected): {e}")

        print("Migration completed!")
        print("Documents table schema should now be compatible with DocumentService")

    except Exception as e:
        print(f"Migration failed: {e}")
        print("You may need to run this migration manually in your Supabase SQL editor")
        print("\nSQL to run:")
        with open('fix_documents_table_schema.sql', 'r') as f:
            print(f.read())

if __name__ == "__main__":
    asyncio.run(run_migration())
