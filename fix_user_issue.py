#!/usr/bin/env python3
"""
Fix User Issue
Create a proper test user and fix the user lookup issue
"""

import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_test_user():
    """Create a test user for debugging."""
    try:
        from services.user_service import user_service
        
        print("Creating test user...")
        
        # Try to create a test user
        success, message = await user_service.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com"
        )
        
        if success:
            print(f"✅ Test user created: {message}")
            
            # Get the created user
            user_data = await user_service.get_user_by_username("testuser")
            if user_data:
                print(f"✅ User details:")
                print(f"   Username: {user_data['username']}")
                print(f"   User ID: {user_data['user_id']}")
                print(f"   UUID: {user_data['id']}")
                return user_data
            else:
                print("❌ Failed to retrieve created user")
                return None
        else:
            if "already exists" in message:
                print("ℹ️ Test user already exists, retrieving...")
                user_data = await user_service.get_user_by_username("testuser")
                if user_data:
                    print(f"✅ Existing user found:")
                    print(f"   Username: {user_data['username']}")
                    print(f"   User ID: {user_data['user_id']}")
                    print(f"   UUID: {user_data['id']}")
                    return user_data
                else:
                    print("❌ User exists but couldn't retrieve")
                    return None
            else:
                print(f"❌ Failed to create user: {message}")
                return None
    
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return None

async def test_conversation_with_real_user():
    """Test conversation creation with a real user."""
    try:
        print("\n=== Testing with Real User ===")
        
        # Create or get test user
        user_data = await create_test_user()
        if not user_data:
            print("❌ Cannot proceed without user")
            return False
        
        # Mock session state with real user
        import streamlit as st
        
        class MockSessionState:
            def __init__(self, user_data):
                self.authenticated = True
                self.user_id = user_data['user_id']  # Use the real user_id
                self.username = user_data['username']
                self.conversations = {}
                self.current_conversation_id = None
                self.conversation_counter = 0
            
            def get(self, key, default=None):
                return getattr(self, key, default)
            
            def __getitem__(self, key):
                return getattr(self, key)
            
            def __setitem__(self, key, value):
                setattr(self, key, value)
            
            def __contains__(self, key):
                return hasattr(self, key)
        
        st.session_state = MockSessionState(user_data)
        
        print(f"Using real user: {st.session_state.user_id}")
        
        # Test conversation creation
        from utils.conversation_manager import create_new_conversation, add_message_to_current_conversation, get_current_messages
        
        print("1. Creating conversation...")
        conv_id = await create_new_conversation()
        if conv_id:
            print(f"✅ Conversation created: {conv_id}")
        else:
            print("❌ Failed to create conversation")
            return False
        
        # Test message addition
        print("2. Adding user message...")
        success = await add_message_to_current_conversation("user", "What is pharmacology?")
        if success:
            print("✅ User message added")
        else:
            print("❌ Failed to add user message")
            return False
        
        # Test AI response generation
        print("3. Generating AI response...")
        from openai_client import chat_completion, get_available_model_modes
        from prompts import pharmacology_system_prompt
        
        # Get messages for API
        current_messages = get_current_messages()
        api_messages = [{"role": "system", "content": pharmacology_system_prompt}]
        for msg in current_messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Generate response
        available_modes = get_available_model_modes()
        model = available_modes[list(available_modes.keys())[0]]["model"]
        
        response = chat_completion(model, api_messages)
        if response and not response.startswith("Error:"):
            print(f"✅ AI response generated: {response[:100]}...")
            
            # Save AI response
            success = await add_message_to_current_conversation("assistant", response)
            if success:
                print("✅ AI response saved")
                
                # Verify final state
                final_messages = get_current_messages()
                print(f"✅ Final message count: {len(final_messages)}")
                
                print("\n🎉 COMPLETE FLOW TEST PASSED!")
                print("The chatbot should work now with the real user.")
                return True
            else:
                print("❌ Failed to save AI response")
        else:
            print(f"❌ AI response failed: {response}")
        
        return False
    
    except Exception as e:
        print(f"❌ Error in conversation test: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the user fix."""
    print("🔧 Fixing User Issue\n")
    
    success = await test_conversation_with_real_user()
    
    if success:
        print("\n✅ USER ISSUE FIXED!")
        print("The chatbot should now work properly.")
        print("\nTo use in Streamlit:")
        print("1. Make sure you're signed in with username 'testuser' and password 'testpass123'")
        print("2. Or create a new user through the sign-up process")
    else:
        print("\n❌ USER ISSUE NOT RESOLVED")
        print("There may be other issues preventing the chatbot from working.")

if __name__ == "__main__":
    asyncio.run(main())