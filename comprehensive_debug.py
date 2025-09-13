#!/usr/bin/env python3
"""
Comprehensive Debug Script
Test every component of the chatbot system to identify the exact issue
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_environment():
    """Test environment setup."""
    print("=== Environment Test ===")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check required packages
    required_packages = ['streamlit', 'openai', 'supabase', 'dotenv']
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} missing")
    
    # Check environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    env_vars = ['GROQ_API_KEY', 'OPENROUTER_API_KEY', 'SUPABASE_URL', 'SUPABASE_ANON_KEY']
    for var in env_vars:
        value = os.environ.get(var)
        print(f"{var}: {'✅ Present' if value else '❌ Missing'}")

def test_imports():
    """Test all imports."""
    print("\n=== Import Test ===")
    
    imports_to_test = [
        ('openai_client', ['chat_completion', 'chat_completion_stream', 'get_available_model_modes']),
        ('prompts', ['pharmacology_system_prompt']),
        ('utils.conversation_manager', ['get_current_messages', 'add_message_to_current_conversation', 'create_new_conversation', 'run_async']),
        ('services.conversation_service', ['conversation_service']),
        ('services.user_service', ['user_service']),
        ('supabase_manager', ['connection_manager'])
    ]
    
    for module_name, functions in imports_to_test:
        try:
            module = __import__(module_name, fromlist=functions)
            for func in functions:
                if hasattr(module, func):
                    print(f"✅ {module_name}.{func}")
                else:
                    print(f"❌ {module_name}.{func} missing")
        except Exception as e:
            print(f"❌ {module_name} import failed: {e}")

def test_api_detailed():
    """Detailed API test."""
    print("\n=== Detailed API Test ===")
    
    try:
        from openai_client import get_available_model_modes, chat_completion, chat_completion_stream
        from prompts import pharmacology_system_prompt
        
        # Test model availability
        modes = get_available_model_modes()
        print(f"Available modes: {list(modes.keys())}")
        
        for mode, config in modes.items():
            model = config["model"]
            print(f"\n--- Testing {mode} mode ---")
            print(f"Model: {model}")
            print(f"API URL: {config['base_url']}")
            print(f"API Key: {config['api_key'][:10]}..." if config['api_key'] else "No API key")
            
            # Test simple completion
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello World' and nothing else."}
            ]
            
            try:
                response = chat_completion(model, messages)
                print(f"✅ Simple completion: {response}")
            except Exception as e:
                print(f"❌ Simple completion failed: {e}")
                continue
            
            # Test pharmacology completion
            pharm_messages = [
                {"role": "system", "content": pharmacology_system_prompt},
                {"role": "user", "content": "What is aspirin? Answer in one sentence."}
            ]
            
            try:
                response = chat_completion(model, pharm_messages)
                print(f"✅ Pharmacology completion: {response[:100]}...")
            except Exception as e:
                print(f"❌ Pharmacology completion failed: {e}")
            
            # Test streaming
            try:
                print("Testing streaming...")
                chunks = []
                for chunk in chat_completion_stream(model, messages):
                    chunks.append(chunk)
                    if len(chunks) > 10:  # Limit for testing
                        break
                
                full_response = ''.join(chunks)
                print(f"✅ Streaming works: {full_response}")
            except Exception as e:
                print(f"❌ Streaming failed: {e}")
    
    except Exception as e:
        print(f"❌ API test failed: {e}")

async def test_database_operations():
    """Test database operations."""
    print("\n=== Database Operations Test ===")
    
    try:
        from supabase_manager import connection_manager
        from services.user_service import user_service
        from services.conversation_service import conversation_service
        
        # Test database connection
        print("Testing database connection...")
        connected = await connection_manager.test_connection()
        print(f"Database connection: {'✅ OK' if connected else '❌ Failed'}")
        
        if not connected:
            return
        
        # Test user operations
        print("Testing user operations...")
        test_user = await user_service.get_user_by_username("test_user")
        if test_user:
            print(f"✅ Test user found: {test_user['id']}")
            user_uuid = test_user['id']
        else:
            print("❌ Test user not found")
            return
        
        # Test conversation operations
        print("Testing conversation operations...")
        conv_id = await conversation_service.create_conversation(
            user_uuid, 
            "Debug Test Conversation",
            "meta-llama/llama-4-maverick-17b-128e-instruct"
        )
        
        if conv_id:
            print(f"✅ Conversation created: {conv_id}")
            
            # Test message addition
            message = {
                "role": "user",
                "content": "Test message",
                "timestamp": datetime.now().isoformat()
            }
            
            success = await conversation_service.add_message(user_uuid, conv_id, message)
            print(f"Message addition: {'✅ OK' if success else '❌ Failed'}")
            
            # Clean up
            await conversation_service.delete_conversation(user_uuid, conv_id)
            print("✅ Test conversation cleaned up")
        else:
            print("❌ Failed to create conversation")
    
    except Exception as e:
        print(f"❌ Database operations test failed: {e}")

def test_session_state_simulation():
    """Test session state simulation."""
    print("\n=== Session State Simulation ===")
    
    try:
        # Mock Streamlit session state
        class MockSessionState:
            def __init__(self):
                self.data = {}
                self.authenticated = True
                self.user_id = "test_user_123"  # This should match a real user
                self.username = "Test User"
                self.conversations = {}
                self.current_conversation_id = None
                self.conversation_counter = 0
            
            def get(self, key, default=None):
                return getattr(self, key, self.data.get(key, default))
            
            def __getitem__(self, key):
                return getattr(self, key, self.data[key])
            
            def __setitem__(self, key, value):
                setattr(self, key, value)
                self.data[key] = value
            
            def __contains__(self, key):
                return hasattr(self, key) or key in self.data
        
        # Replace streamlit session state
        import streamlit as st
        st.session_state = MockSessionState()
        
        print("✅ Mock session state created")
        print(f"User ID: {st.session_state.user_id}")
        print(f"Authenticated: {st.session_state.authenticated}")
        
        return st.session_state
    
    except Exception as e:
        print(f"❌ Session state simulation failed: {e}")
        return None

async def test_complete_flow():
    """Test the complete chatbot flow."""
    print("\n=== Complete Flow Test ===")
    
    try:
        # Set up mock session state
        session_state = test_session_state_simulation()
        if not session_state:
            return
        
        from utils.conversation_manager import create_new_conversation, add_message_to_current_conversation, get_current_messages
        from openai_client import chat_completion, get_available_model_modes
        from prompts import pharmacology_system_prompt
        
        # Step 1: Create conversation
        print("1. Creating conversation...")
        conv_id = await create_new_conversation()
        if conv_id:
            print(f"✅ Conversation created: {conv_id}")
        else:
            print("❌ Failed to create conversation")
            return
        
        # Step 2: Add user message
        print("2. Adding user message...")
        user_msg = "What is pharmacology?"
        success = await add_message_to_current_conversation("user", user_msg)
        if success:
            print("✅ User message added")
        else:
            print("❌ Failed to add user message")
            return
        
        # Step 3: Get messages for API
        print("3. Preparing API messages...")
        current_messages = get_current_messages()
        api_messages = [{"role": "system", "content": pharmacology_system_prompt}]
        for msg in current_messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
        
        print(f"✅ API messages prepared: {len(api_messages)} messages")
        
        # Step 4: Generate AI response
        print("4. Generating AI response...")
        available_modes = get_available_model_modes()
        if not available_modes:
            print("❌ No available models")
            return
        
        model = available_modes[list(available_modes.keys())[0]]["model"]
        print(f"Using model: {model}")
        
        response = chat_completion(model, api_messages)
        if response and not response.startswith("Error:"):
            print(f"✅ AI response generated: {response[:100]}...")
            
            # Step 5: Save AI response
            print("5. Saving AI response...")
            success = await add_message_to_current_conversation("assistant", response)
            if success:
                print("✅ AI response saved")
                
                # Step 6: Verify final state
                final_messages = get_current_messages()
                print(f"✅ Final message count: {len(final_messages)}")
                
                for i, msg in enumerate(final_messages):
                    print(f"  Message {i+1} ({msg['role']}): {msg['content'][:50]}...")
                
                print("🎉 Complete flow test PASSED!")
                return True
            else:
                print("❌ Failed to save AI response")
        else:
            print(f"❌ AI response failed: {response}")
        
        return False
    
    except Exception as e:
        print(f"❌ Complete flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all diagnostic tests."""
    print("🔍 Comprehensive Chatbot Diagnostic\n")
    
    # Test 1: Environment
    test_environment()
    
    # Test 2: Imports
    test_imports()
    
    # Test 3: API
    test_api_detailed()
    
    # Test 4: Database
    await test_database_operations()
    
    # Test 5: Complete flow
    success = await test_complete_flow()
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("The chatbot should be working. If it's not working in Streamlit,")
        print("the issue might be with Streamlit Cloud deployment or session management.")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Check the failed tests above to identify the issue.")
    print(f"{'='*50}")

if __name__ == "__main__":
    asyncio.run(main())