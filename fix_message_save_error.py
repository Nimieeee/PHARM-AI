#!/usr/bin/env python3
"""
Fix Message Save Error
Improve error handling and logging for message saving
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_streamlit_message_flow():
    """Test the message flow as it would happen in Streamlit."""
    try:
        print("🔍 Testing Streamlit message flow...")
        
        # Import the conversation manager functions
        from utils.conversation_manager import (
            create_new_conversation,
            add_message_to_current_conversation,
            get_current_messages
        )
        
        # Simulate Streamlit session state
        import streamlit as st
        
        # Mock session state for testing
        class MockSessionState:
            def __init__(self):
                self.data = {}
                self.user_id = "test_user_123"  # This should match a real user
                self.conversations = {}
                self.current_conversation_id = None
                self.conversation_counter = 0
            
            def get(self, key, default=None):
                return self.data.get(key, default)
            
            def __setitem__(self, key, value):
                self.data[key] = value
            
            def __getitem__(self, key):
                return self.data[key]
            
            def __contains__(self, key):
                return key in self.data
        
        # Replace st.session_state with our mock
        st.session_state = MockSessionState()
        
        # Set up a test user
        from services.user_service import user_service
        user_data = await user_service.get_user_by_username("test_user")
        if user_data:
            st.session_state.user_id = user_data['user_id']  # Use the legacy user_id
            print(f"   Using test user: {st.session_state.user_id}")
        else:
            print("   Test user not found, please run debug_message_save.py first")
            return
        
        # Test 1: Create new conversation
        print("\n1. Creating new conversation...")
        conversation_id = await create_new_conversation()
        if conversation_id:
            print(f"   ✅ Conversation created: {conversation_id}")
        else:
            print("   ❌ Failed to create conversation")
            return
        
        # Test 2: Add user message
        print("\n2. Adding user message...")
        user_message = "What are the side effects of aspirin?"
        success = await add_message_to_current_conversation("user", user_message)
        if success:
            print("   ✅ User message saved successfully")
        else:
            print("   ❌ Failed to save user message")
            return
        
        # Test 3: Verify message was saved
        print("\n3. Verifying message was saved...")
        messages = get_current_messages()
        if messages and len(messages) > 0:
            print(f"   ✅ Found {len(messages)} messages")
            print(f"   Last message: {messages[-1]['content'][:50]}...")
        else:
            print("   ❌ No messages found")
        
        # Test 4: Add assistant response
        print("\n4. Adding assistant response...")
        assistant_message = "Aspirin can cause gastrointestinal irritation, bleeding, and in rare cases, Reye's syndrome in children."
        success = await add_message_to_current_conversation("assistant", assistant_message)
        if success:
            print("   ✅ Assistant message saved successfully")
        else:
            print("   ❌ Failed to save assistant message")
        
        # Test 5: Final verification
        print("\n5. Final verification...")
        messages = get_current_messages()
        if messages and len(messages) >= 2:
            print(f"   ✅ Found {len(messages)} messages total")
            for i, msg in enumerate(messages):
                print(f"   Message {i+1} ({msg['role']}): {msg['content'][:30]}...")
        else:
            print(f"   ❌ Expected 2+ messages, found {len(messages) if messages else 0}")
        
        print("\n🎉 Streamlit message flow test completed!")
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streamlit_message_flow())