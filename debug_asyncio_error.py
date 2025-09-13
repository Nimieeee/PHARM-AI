#!/usr/bin/env python3
"""
Debug script to trace the exact source of asyncio authentication errors
"""

import sys
import traceback
import asyncio
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def trace_function_calls():
    """Trace all function calls to find where asyncio error occurs"""
    import sys
    
    def trace_calls(frame, event, arg):
        if event == 'call':
            filename = frame.f_code.co_filename
            function_name = frame.f_code.co_name
            if 'auth' in filename or 'service' in filename:
                print(f"TRACE: {filename}:{function_name}")
        return trace_calls
    
    sys.settrace(trace_calls)

def test_auth_step_by_step():
    """Test each authentication step individually"""
    print("🔍 Testing authentication step by step...")
    
    try:
        print("\n1. Testing basic imports...")
        import streamlit as st
        print("✅ Streamlit imported")
        
        from config import SESSION_TIMEOUT_HOURS
        print("✅ Config imported")
        
        print("\n2. Testing service imports...")
        from services.user_service import user_service
        print("✅ User service imported")
        
        from services.session_service import session_service
        print("✅ Session service imported")
        
        from services.conversation_service import conversation_service
        print("✅ Conversation service imported")
        
        print("\n3. Testing sync wrapper imports...")
        from services.session_service import create_session_sync, validate_session_sync, logout_session_sync
        print("✅ Session sync wrappers imported")
        
        from services.conversation_service import get_user_conversations_sync, update_conversation_sync
        print("✅ Conversation sync wrappers imported")
        
        print("\n4. Testing auth module import...")
        from auth import authenticate_user, create_user, login_user
        print("✅ Auth module imported")
        
        print("\n5. Testing authenticate_user function...")
        result = authenticate_user('test_user', 'test_pass')
        print(f"✅ authenticate_user result: {result}")
        
        print("\n6. Testing login_user function...")
        result = login_user('test_user', 'test_pass')
        print(f"✅ login_user result: {result}")
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Error at step: {e}")
        print(f"Error type: {type(e)}")
        print(f"Error args: {e.args}")
        traceback.print_exc()
        
        # Check if it's specifically an asyncio error
        if "asyncio" in str(e).lower() or "coroutine" in str(e).lower():
            print("\n🔍 ASYNCIO ERROR DETECTED!")
            print("Analyzing the call stack...")
            
            # Print detailed stack trace
            import traceback
            tb = traceback.format_exc()
            lines = tb.split('\n')
            for i, line in enumerate(lines):
                if line.strip():
                    print(f"{i:2d}: {line}")

def test_individual_functions():
    """Test individual functions that might be causing issues"""
    print("\n🧪 Testing individual functions...")
    
    try:
        # Test user service directly
        print("\n--- Testing user_service.authenticate_user ---")
        from services.user_service import user_service
        result = user_service.authenticate_user('test_user', 'test_pass')
        print(f"Result: {result}")
        
        # Test session service sync wrappers
        print("\n--- Testing session service sync wrappers ---")
        from services.session_service import create_session_sync
        # This should fail gracefully since user doesn't exist
        try:
            session_id = create_session_sync('test_user', 'fake-uuid')
            print(f"Session ID: {session_id}")
        except Exception as e:
            print(f"Expected error: {e}")
        
        # Test conversation service sync wrappers
        print("\n--- Testing conversation service sync wrappers ---")
        from services.conversation_service import get_user_conversations_sync
        try:
            conversations = get_user_conversations_sync('fake-uuid')
            print(f"Conversations: {conversations}")
        except Exception as e:
            print(f"Expected error: {e}")
            
    except Exception as e:
        print(f"❌ Error in individual function test: {e}")
        traceback.print_exc()

def check_event_loops():
    """Check for event loop issues"""
    print("\n🔄 Checking event loops...")
    
    try:
        # Check if there's already an event loop
        try:
            loop = asyncio.get_event_loop()
            print(f"✅ Event loop exists: {loop}")
            print(f"Loop is running: {loop.is_running()}")
            print(f"Loop is closed: {loop.is_closed()}")
        except RuntimeError as e:
            print(f"⚠️  No event loop: {e}")
            
        # Try to create a new event loop
        try:
            new_loop = asyncio.new_event_loop()
            print(f"✅ Can create new event loop: {new_loop}")
            new_loop.close()
        except Exception as e:
            print(f"❌ Cannot create new event loop: {e}")
            
    except Exception as e:
        print(f"❌ Error checking event loops: {e}")
        traceback.print_exc()

def main():
    """Main diagnostic function"""
    print("🚀 Starting comprehensive asyncio error diagnosis...")
    
    # Enable tracing
    # trace_function_calls()
    
    # Check event loops first
    check_event_loops()
    
    # Test individual functions
    test_individual_functions()
    
    # Test step by step
    test_auth_step_by_step()
    
    print("\n✅ Diagnosis complete!")

if __name__ == "__main__":
    main()