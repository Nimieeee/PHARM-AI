#!/usr/bin/env python3
"""
Test conversation creation to debug the user_uuid issue
"""

import streamlit as st
import asyncio
from services.conversation_service import ConversationService
from services.user_service import UserService

async def test_conversation_creation():
    """Test creating a conversation with proper user_uuid."""
    
    # Get user service
    user_service = UserService()
    
    # Get the test user
    user = user_service.get_user_by_username("tolu")
    if not user:
        print("❌ User 'tolu' not found")
        return False
    
    print(f"✅ Found user: {user['username']}")
    print(f"   User UUID: {user['id']}")
    print(f"   User ID (legacy): {user['user_id']}")
    
    # Test conversation creation
    conv_service = ConversationService()
    
    try:
        conversation_id = await conv_service.create_conversation(
            user_uuid=user['id'],  # Use the UUID from the database
            title="Test Conversation",
            model="meta-llama/llama-4-maverick-17b-128e-instruct"
        )
        
        print(f"✅ Conversation created successfully: {conversation_id}")
        return True
        
    except Exception as e:
        print(f"❌ Conversation creation failed: {e}")
        return False

def main():
    print("🧪 Testing Conversation Creation")
    print("=" * 40)
    
    # Run the async test
    result = asyncio.run(test_conversation_creation())
    
    if result:
        print("\n🎉 Test passed! Conversation creation is working.")
    else:
        print("\n❌ Test failed! Check the error messages above.")

if __name__ == "__main__":
    main()