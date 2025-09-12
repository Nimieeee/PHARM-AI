#!/usr/bin/env python3
"""
Test script to verify conversation creation fixes
Run this after applying the database fix script
"""

import asyncio
import streamlit as st
from services.user_service import user_service
from services.conversation_service import conversation_service
from supabase_manager import connection_manager

async def test_conversation_creation():
    """Test conversation creation with the fixes applied."""
    
    print("🔧 Testing Conversation Creation Fixes")
    print("=" * 50)
    
    # Test with a known user from the logs
    test_user_id = "e4443c52948edad6132f34b6378a9901"
    
    try:
        # Step 1: Get user data
        print(f"\n1. Looking up user: {test_user_id}")
        user_data = user_service.get_user_by_id(test_user_id)
        
        if not user_data:
            print("❌ User not found - cannot test conversation creation")
            return False
            
        user_uuid = user_data['id']
        username = user_data['username']
        print(f"✅ Found user: {username} (UUID: {user_uuid})")
        
        # Step 2: Test conversation creation
        print(f"\n2. Testing conversation creation...")
        title = "Test Conversation - Fix Verification"
        
        conversation_id = await conversation_service.create_conversation(
            user_uuid=user_uuid,
            title=title,
            model="meta-llama/llama-4-maverick-17b-128e-instruct"
        )
        
        print(f"✅ Conversation created successfully: {conversation_id}")
        
        # Step 3: Verify conversation exists
        print(f"\n3. Verifying conversation exists...")
        conversation = await conversation_service.get_conversation(user_uuid, conversation_id)
        
        if conversation:
            print(f"✅ Conversation verified: '{conversation['title']}'")
            print(f"   - ID: {conversation['conversation_id']}")
            print(f"   - Model: {conversation['model']}")
            print(f"   - Created: {conversation['created_at']}")
        else:
            print("❌ Conversation not found after creation")
            return False
        
        # Step 4: Test adding a message
        print(f"\n4. Testing message addition...")
        test_message = {
            "role": "user",
            "content": "Hello, this is a test message to verify the fix works!"
        }
        
        success = await conversation_service.add_message(user_uuid, conversation_id, test_message)
        
        if success:
            print("✅ Message added successfully")
        else:
            print("❌ Failed to add message")
            return False
        
        # Step 5: Clean up test conversation
        print(f"\n5. Cleaning up test conversation...")
        deleted = await conversation_service.delete_conversation(user_uuid, conversation_id)
        
        if deleted:
            print("✅ Test conversation cleaned up successfully")
        else:
            print("⚠️  Warning: Could not clean up test conversation")
        
        print(f"\n🎉 ALL TESTS PASSED! Conversation creation is working properly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        if hasattr(e, 'details'):
            print(f"   Details: {e.details}")
            
        return False

# Test using streamlit run context if available
if __name__ == "__main__":
    # Initialize streamlit secrets context
    try:
        import streamlit as st
        # This will fail outside streamlit, but that's okay
        asyncio.run(test_conversation_creation())
    except Exception as e:
        print(f"Note: Run this with `streamlit run test_conversation_fix.py` for full testing")
        print(f"Error: {e}")