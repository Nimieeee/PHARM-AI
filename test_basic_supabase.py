#!/usr/bin/env python3
"""
Test script to verify Supabase connection without problematic operations
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_basic_operations():
    """Test basic Supabase operations without order clauses or triggers."""
    
    try:
        from supabase_manager import connection_manager
        from services.user_service import user_service
        
        print("Testing basic Supabase connection...")
        
        # Test 1: Connection test
        if connection_manager.test_connection():
            print("✅ Connection test passed")
        else:
            print("❌ Connection test failed")
            return False
        
        # Test 2: Simple user query without order
        try:
            result = connection_manager.execute_query(
                table='users',
                operation='select',
                columns='count',
                limit=1
            )
            print(f"✅ Simple query passed - got result: {bool(result.data)}")
        except Exception as e:
            print(f"❌ Simple query failed: {e}")
        
        # Test 3: User service test
        try:
            # Test with a known user
            user_data = await user_service.get_user_by_username('admin')
            if user_data:
                print(f"✅ User service test passed - found user: {user_data.get('username')}")
            else:
                print("⚠️  User service test - no admin user found")
        except Exception as e:
            print(f"❌ User service test failed: {e}")
        
        print("\n🎉 Basic tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_basic_operations())
