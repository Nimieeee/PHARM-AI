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
    
    # Simple controls
    col1, col2 = st.columns([3, 1])
    with col2:
        # Initialize streaming preference
        if 'use_streaming' not in st.session_state:
            st.session_state.use_streaming = True
        
        use_streaming = st.toggle("🌊 Streaming", value=st.session_state.use_streaming, help="Enable streaming responses")
        st.session_state.use_streaming = use_streaming
    
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
            full_response = ""
            
            try:
                # Show thinking
                response_placeholder.markdown("🤔 Thinking...")
                
                # Import API functions
                from openai_client import chat_completion_stream, chat_completion, get_available_model_modes
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
                
                # Choose streaming or non-streaming based on toggle
                if st.session_state.use_streaming:
                    # Try streaming
                    try:
                        response_placeholder.markdown("🔄 Generating response (streaming)...")
                        logger.info("Starting streaming response...")
                        
                        stream_worked = False
                        chunk_count = 0
                        
                        for chunk in chat_completion_stream(model, api_messages):
                            if chunk:  # Only process non-empty chunks
                                stream_worked = True
                                full_response += chunk
                                chunk_count += 1
                                
                                # Update UI every few chunks for smooth streaming
                                if chunk_count % 3 == 0:
                                    response_placeholder.markdown(full_response + "▌")
                        
                        # Final display without cursor
                        if stream_worked and full_response.strip():
                            response_placeholder.markdown(full_response)
                            logger.info(f"✅ Streaming completed: {len(full_response)} chars, {chunk_count} chunks")
                        else:
                            logger.warning("Streaming failed or empty, trying fallback...")
                            raise Exception("Streaming failed or empty response")
                            
                    except Exception as stream_error:
                        logger.warning(f"Streaming failed: {stream_error}, trying non-streaming...")
                        
                        # Fallback to non-streaming
                        response_placeholder.markdown("🔄 Generating response (fallback)...")
                        full_response = chat_completion(model, api_messages)
                        
                        if full_response and not full_response.startswith("Error:"):
                            response_placeholder.markdown(full_response)
                            logger.info(f"✅ Non-streaming fallback completed: {len(full_response)} chars")
                        else:
                            raise Exception(f"Both streaming and non-streaming failed: {full_response}")
                else:
                    # Use non-streaming directly
                    response_placeholder.markdown("🔄 Generating response (non-streaming)...")
                    logger.info("Using non-streaming response...")
                    
                    full_response = chat_completion(model, api_messages)
                    
                    if full_response and not full_response.startswith("Error:"):
                        response_placeholder.markdown(full_response)
                        logger.info(f"✅ Non-streaming completed: {len(full_response)} chars")
                    else:
                        raise Exception(f"Non-streaming failed: {full_response}")
                
                # Add assistant response to chat if successful
                if full_response and not full_response.startswith("Error:") and not full_response.startswith("❌"):
                    st.session_state.chat_messages.append({"role": "assistant", "content": full_response})
                    logger.info("✅ Response added to chat history")
                else:
                    logger.error(f"Response not added to history: {full_response[:100]}...")
                    
            except Exception as e:
                error_msg = f"❌ Error generating response: {str(e)}"
                response_placeholder.markdown(error_msg)
                logger.error(f"Exception in response generation: {e}")
    
    # Add some debug info
    with st.expander("🔧 Debug Info"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Session Info:**")
            st.write(f"• Total messages: {len(st.session_state.chat_messages)}")
            st.write(f"• User: {st.session_state.get('username', 'Unknown')}")
            st.write(f"• Authenticated: {st.session_state.get('authenticated', False)}")
            st.write(f"• Streaming: {st.session_state.get('use_streaming', True)}")
        
        with col2:
            st.write("**Actions:**")
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.chat_messages = []
                st.rerun()
            
            if st.button("Test API", use_container_width=True):
                try:
                    from openai_client import get_available_model_modes
                    modes = get_available_model_modes()
                    st.success(f"✅ Available models: {list(modes.keys())}")
                except Exception as e:
                    st.error(f"❌ API test failed: {e}")
        
        # Show recent messages
        if st.session_state.chat_messages:
            st.write("**Recent Messages:**")
            for i, msg in enumerate(st.session_state.chat_messages[-3:]):  # Last 3 messages
                role_icon = "👤" if msg["role"] == "user" else "🤖"
                content_preview = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
                st.write(f"{role_icon} {content_preview}")

# Main function to call from app.py
def render_chatbot_page():
    """Main function called by the app."""
    render_simple_chatbot()