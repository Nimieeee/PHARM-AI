"""
Simple Chatbot Page - Minimal, Working Implementation
"""

import streamlit as st
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def render_simple_chatbot():
    """Render a simple, working chatbot interface."""
    
    # Check authentication
    if not st.session_state.get('authenticated'):
        st.error("Please sign in to use the chatbot.")
        return
    
    st.title("💊 PharmGPT - Simple Mode")
    st.caption("Simplified interface for testing")
    
    # Initialize messages in session state
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input using st.chat_input (simpler than forms)
    if prompt := st.chat_input("Ask me anything about pharmacology..."):
        logger.info(f"User input: {prompt[:50]}...")
        
        # Add user message to chat
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate and display AI response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            try:
                # Show thinking
                response_placeholder.markdown("🤔 Thinking...")
                
                # Import API functions
                from openai_client import chat_completion, get_available_model_modes
                from prompts import pharmacology_system_prompt
                
                # Get available models
                available_modes = get_available_model_modes()
                if not available_modes:
                    response_placeholder.markdown("❌ No API models available. Please check your API keys.")
                    return
                
                # Use first available model
                model = available_modes[list(available_modes.keys())[0]]["model"]
                logger.info(f"Using model: {model}")
                
                # Prepare messages for API
                api_messages = [{"role": "system", "content": pharmacology_system_prompt}]
                
                # Add recent conversation history (last 10 messages)
                for msg in st.session_state.chat_messages[-10:]:
                    api_messages.append({"role": msg["role"], "content": msg["content"]})
                
                # Show generating message
                response_placeholder.markdown("🔄 Generating response...")
                
                # Generate response
                response = chat_completion(model, api_messages)
                
                if response and not response.startswith("Error:"):
                    # Display the response
                    response_placeholder.markdown(response)
                    
                    # Add assistant response to chat
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                    
                    logger.info(f"✅ Response generated successfully: {len(response)} chars")
                    
                else:
                    error_msg = f"❌ Failed to generate response: {response}"
                    response_placeholder.markdown(error_msg)
                    logger.error(f"API response error: {response}")
                    
            except Exception as e:
                error_msg = f"❌ Error generating response: {str(e)}"
                response_placeholder.markdown(error_msg)
                logger.error(f"Exception in response generation: {e}")
    
    # Add some debug info
    with st.expander("🔧 Debug Info"):
        st.write(f"Total messages: {len(st.session_state.chat_messages)}")
        st.write(f"User: {st.session_state.get('username', 'Unknown')}")
        st.write(f"Authenticated: {st.session_state.get('authenticated', False)}")
        
        if st.button("Clear Chat"):
            st.session_state.chat_messages = []
            st.rerun()
        
        if st.button("Test API"):
            try:
                from openai_client import get_available_model_modes
                modes = get_available_model_modes()
                st.write(f"Available models: {list(modes.keys())}")
            except Exception as e:
                st.error(f"API test failed: {e}")

# Main function to call from app.py
def render_chatbot_page():
    """Main function called by the app."""
    render_simple_chatbot()