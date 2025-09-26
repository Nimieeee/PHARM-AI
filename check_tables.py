#!/usr/bin/env python3
"""
Test script to check actual table names in the database
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.supabase_client import supabase_manager

async def check_actual_tables():
    """Check what tables actually exist in the database."""
    try:
        # Test connection
        connection_result = await supabase_manager.test_connection()
        print(f"Connection test: {'✅ PASS' if connection_result else '❌ FAIL'}")
        
        if not connection_result:
            return False
            
        # Get client
        client = await supabase_manager.get_client()
        
        # Try to list available tables by checking common ones
        possible_tables = [
            'users', 'sessions', 'conversations', 'messages', 
            'documents', 'document_chunks', 'user_sessions'
        ]
        
        print("\nChecking table availability:")
        results = []
        
        for table in possible_tables:
            try:
                result = await client.table(table).select('count').limit(1).execute()
                print(f"Table '{table}': ✅ EXISTS")
                results.append(True)
            except Exception as e:
                print(f"Table '{table}': ❌ NOT FOUND - {str(e)[:100]}...")
                results.append(False)
        
        return any(results)
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(check_actual_tables())
    print(f"\nOverall result: {'✅ FOUND SOME TABLES' if result else '❌ NO TABLES FOUND'}")
    sys.exit(0 if result else 1)