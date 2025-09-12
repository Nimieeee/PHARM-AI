#!/usr/bin/env python3
"""
Debug script to validate conversation creation issues
"""

import asyncio
import logging
from datetime import datetime
from supabase_manager import connection_manager
from services.user_service import user_service
from services.conversation_service import conversation_service

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_conversation_creation():
    """Debug conversation creation with detailed logging."""
    
    print("=== DEBUGGING CONVERSATION CREATION ===")
    
    # Test 1: Check database schema for conversations table
    print("\n1. Checking conversations table schema...")
    try:
        client = connection_manager.get_client()
        if client:
            # Try to describe the conversations table structure
            result = client.rpc('exec_sql', {
                'sql': "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'conversations' ORDER BY ordinal_position",
                'params': []
            }).execute()
            print("✅ exec_sql function exists and working")
            if result.data:
                print("Conversations table columns:")
                for col in result.data:
                    print(f"  - {col['column_name']}: {col['data_type']} (nullable: {col['is_nullable']})")
        else:
            print("❌ No Supabase client available")
    except Exception as e:
        print(f"❌ exec_sql function test failed: {e}")
        
        # Fallback: try to query conversations table structure via direct query
        try:
            result = connection_manager.execute_query(
                table='conversations',
                operation='select',
                limit=1
            )
            print("✅ Can query conversations table directly")
            if result.data:
                print(f"Sample conversation columns: {list(result.data[0].keys())}")
        except Exception as e2:
            print(f"❌ Cannot query conversations table: {e2}")
    
    # Test 2: Check user lookup and UUID handling
    print("\n2. Checking user UUID handling...")
    test_user_id = "e4443c52948edad6132f34b6378a9901"  # From the logs
    
    try:
        # Test the user lookup that's failing
        user_data = user_service.get_user_by_id(test_user_id)
        if user_data:
            print(f"✅ Found user data: {user_data['username']}")
            print(f"   - Legacy user_id: {user_data.get('user_id')}")
            print(f"   - UUID (id): {user_data.get('id')}")
            print(f"   - ID type: {type(user_data.get('id'))}")
            
            # Test the UUID that would be used for conversation creation
            user_uuid = user_data['id']
            print(f"   - user_uuid for conversation: '{user_uuid}' (type: {type(user_uuid)})")
            
        else:
            print(f"❌ User not found for user_id: {test_user_id}")
    except Exception as e:
        print(f"❌ User lookup failed: {e}")
    
    # Test 3: Try minimal conversation creation
    print("\n3. Testing conversation creation...")
    if user_data:
        try:
            user_uuid = user_data['id']
            print(f"Attempting to create conversation with user_uuid: {user_uuid}")
            
            # Test minimal data insertion
            minimal_data = {
                'conversation_id': 'debug-test-conv-001',
                'user_uuid': user_uuid,
                'title': 'Debug Test Conversation',
                'created_at': datetime.now().isoformat(),
                'is_archived': False
            }
            
            print(f"Minimal data: {minimal_data}")
            
            result = connection_manager.execute_query(
                table='conversations',
                operation='insert',
                data=minimal_data
            )
            
            if result.data:
                print("✅ Minimal conversation creation successful")
                # Clean up
                connection_manager.execute_query(
                    table='conversations',
                    operation='delete',
                    eq={'conversation_id': 'debug-test-conv-001'}
                )
                print("✅ Test conversation cleaned up")
            else:
                print("❌ Minimal conversation creation failed - no data returned")
                
        except Exception as e:
            print(f"❌ Conversation creation failed: {e}")
            print(f"Error type: {type(e)}")
            if hasattr(e, 'details'):
                print(f"Error details: {e.details}")
    
    # Test 4: Check if user_id column exists in conversations
    print("\n4. Testing alternative field names...")
    if user_data:
        try:
            user_uuid = user_data['id']
            
            # Try with user_id instead of user_uuid
            alt_data = {
                'conversation_id': 'debug-test-conv-002', 
                'user_id': user_uuid,  # Using user_id instead of user_uuid
                'title': 'Debug Test Conversation Alt',
                'created_at': datetime.now().isoformat(),
                'is_archived': False
            }
            
            print(f"Testing with user_id field: {alt_data}")
            
            result = connection_manager.execute_query(
                table='conversations',
                operation='insert', 
                data=alt_data
            )
            
            if result.data:
                print("✅ Conversation creation with user_id successful")
                # Clean up
                connection_manager.execute_query(
                    table='conversations',
                    operation='delete',
                    eq={'conversation_id': 'debug-test-conv-002'}
                )
                print("✅ Test conversation cleaned up")
            else:
                print("❌ Conversation creation with user_id failed")
                
        except Exception as e:
            print(f"❌ Alternative conversation creation failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_conversation_creation())