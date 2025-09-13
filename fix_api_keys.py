#!/usr/bin/env python3
"""
Fix API keys and test Streamlit integration
"""

import streamlit as st
import asyncio
import logging
from utils.conversation_manager import run_async, create_new_conversation, add_message_to_current_conversation
from openai_client import chat_completion, get_available_model_modes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_streamlit_integration():
    """Test Streamlit integration with proper session state."""
    st.title("🧪 PharmGPT Message Flow Test")
    
    # Initialize session state
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "e4443c52948edad6132f34b6378a9901"
    
    if 'conversations' not in st.session_state:
        st.session_state.conversations = {}
    
    if 'current_conversation_id' not in st.session_state:
        st.session_state.current_conversation_id = None
    
    if 'conversation_counter' not in st.session_state:
        st.session_state.conversation_counter = 0
    
    # Test API keys
    st.subheader("🔑 API Key Test")
    available_modes = get_available_model_modes()
    
    if available_modes:
        st.success(f"✅ API keys working! Available modes: {list(available_modes.keys())}")
        
        # Show model details
        for mode, config in available_modes.items():
            st.info(f"**{mode.title()} Mode**: {config['model']}")
    else:
        st.error("❌ No API keys available!")
        return
    
    # Test conversation creation
    st.subheader("💬 Conversation Test")
    
    if st.button("Create Test Conversation"):
        try:
            conversation_id = run_async(create_new_conversation())
            if conversation_id:
                st.success(f"✅ Conversation created: {conversation_id}")
            else:
                st.error("❌ Failed to create conversation")
        except Exception as e:
            st.error(f"❌ Error creating conversation: {e}")
    
    # Test message sending
    st.subheader("📝 Message Test")
    
    if st.session_state.current_conversation_id:
        st.info(f"Current conversation: {st.session_state.current_conversation_id}")
        
        test_message = st.text_input("Test message:", "Hello, this is a test message")
        
        if st.button("Send Test Message"):
            try:
                # Add user message
                run_async(add_message_to_current_conversation("user", test_message))
                st.success("✅ User message added")
                
                # Generate AI response
                with st.spinner("Generating AI response..."):
                    messages = [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": test_message}
                    ]
                    
                    # Use the first available model
                    model = list(available_modes.values())[0]["model"]
                    response = chat_completion(model, messages)
                    
                    # Add AI response
                    run_async(add_message_to_current_conversation("assistant", response))
                    
                    st.success("✅ AI response generated and added")
                    st.write("**AI Response:**", response)
                    
            except Exception as e:
                st.error(f"❌ Error sending message: {e}")
                logger.error(f"Message sending error: {e}")
    else:
        st.warning("⚠️ No active conversation. Create one first.")
    
    # Show current conversation
    if st.session_state.current_conversation_id and st.session_state.current_conversation_id in st.session_state.conversations:
        st.subheader("💬 Current Conversation")
        messages = st.session_state.conversations[st.session_state.current_conversation_id]["messages"]
        
        for i, msg in enumerate(messages):
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
    
    # Debug info
    with st.expander("🔍 Debug Info"):
        st.write("**Session State:**")
        st.json({
            "user_id": st.session_state.user_id,
            "current_conversation_id": st.session_state.current_conversation_id,
            "conversations_count": len(st.session_state.conversations),
            "conversation_counter": st.session_state.conversation_counter
        })

if __name__ == "__main__":
    test_streamlit_integration()