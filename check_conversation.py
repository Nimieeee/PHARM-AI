#!/usr/bin/env python3
"""
Check if conversation exists
"""

import asyncio
from services.conversation_service import conversation_service
from services.user_service import user_service

async def check_conversation():
    """Check if conversation exists"""
    try:
        # Test user lookup
        user_data = user_service.get_user_by_id("e4443c52948edad6132f34b6378a9901")
        print(f"User data: {user_data}")
        
        if not user_data:
            print("❌ User not found!")
            return
        
        # Check conversations
        print("Getting user conversations...")
        conversations = await conversation_service.get_user_conversations(user_data['id'])
        print(f"User conversations: {conversations}")
        
        # Check specific conversation
        conv_id = "4c367352-4c54-4caa-a1bc-6ab8d43ce5be"
        print(f"Looking for conversation: {conv_id}")
        
        if conv_id in conversations:
            print(f"✓ Conversation exists: {conversations[conv_id]}")
        else:
            print(f"❌ Conversation {conv_id} not found")
            print("Creating a test conversation...")
            
            # Create a test conversation
            new_conv_id = await conversation_service.create_conversation(
                user_data['id'], 
                "Test Conversation for Documents"
            )
            print(f"Created new conversation: {new_conv_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_conversation())