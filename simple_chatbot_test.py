#!/usr/bin/env python3
"""
Simple Chatbot Test - Minimal Implementation
Test if the core functionality works without complex state management
"""

import streamlit as st
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_async(coro):
    """Run async function in Streamlit context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Error running async operation: {e}")
        raise

def simple_chatbot():
    """Simple chatbot implementation without complex state management."""
    st.title("🧪 Simple Chatbot Test")
    
    # Initialize simple session state
    if 'simple_messages' not in st.session_state:
        st.session_state.simple_messages = []
    
    # Display messages
    for message in st.session_state.simple_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about pharmacology..."):
        # Add user message
        st.session_state.simple_messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # Show thinking
                message_placeholder.markdown("🤔 Thinking...")
                
                # Import and use API
                from openai_client import chat_completion, get_available_model_modes
                from prompts import pharmacology_system_prompt
                
                # Get model
                available_modes = get_available_model_modes()
                if not available_modes:
                    message_placeholder.markdown("❌ No API models available")
                    return
                
                model = available_modes[list(available_modes.keys())[0]]["model"]
                
                # Prepare messages
                api_messages = [{"role": "system", "content": pharmacology_system_prompt}]
                for msg in st.session_state.simple_messages[-5:]:  # Last 5 messages for context
                    api_messages.append({"role": msg["role"], "content": msg["content"]})
                
                # Generate response
                message_placeholder.markdown("🔄 Generating response...")
                response = chat_completion(model, api_messages)
                
                if response and not response.startswith("Error:"):
                    # Display response
                    message_placeholder.markdown(response)
                    
                    # Add to messages
                    st.session_state.simple_messages.append({"role": "assistant", "content": response})
                    
                    st.success("✅ Response generated successfully!")
                else:
                    message_placeholder.markdown(f"❌ Error: {response}")
                    
            except Exception as e:
                error_msg = f"❌ Error generating response: {str(e)}"
                message_placeholder.markdown(error_msg)
                logger.error(f"Error in simple chatbot: {e}")

if __name__ == "__main__":
    simple_chatbot()