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
    
    st.title("💊 PharmGPT")
    
    # Show current model status
    current_mode = st.session_state.get('selected_model_mode', 'normal')
    mode_emoji = "⚡" if current_mode == "turbo" else "🧠"
    mode_name = "Turbo Mode" if current_mode == "turbo" else "Normal Mode"
    
    st.caption(f"🎯 {mode_emoji} {mode_name} • 💫 Fluid Streaming")
    
    # Simple model selection control
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        # Initialize model preference
        if 'selected_model_mode' not in st.session_state:
            st.session_state.selected_model_mode = "normal"
        
        # Model selection toggle
        is_turbo = st.toggle("⚡ Turbo Mode", 
                           value=(st.session_state.selected_model_mode == "turbo"),
                           help="Switch between Normal (Groq Llama) and Turbo (OpenRouter) modes")
        
        st.session_state.selected_model_mode = "turbo" if is_turbo else "normal"
    
    # Set streaming defaults (always enabled, always fluid)
    st.session_state.use_streaming = True
    st.session_state.fluid_streaming = True
    
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
                
                # Use selected model mode
                selected_mode = st.session_state.selected_model_mode
                if selected_mode not in available_modes:
                    # Fallback to first available mode if selected mode is not available
                    selected_mode = list(available_modes.keys())[0]
                    st.warning(f"⚠️ Selected mode not available, using {selected_mode} instead")
                
                model = available_modes[selected_mode]["model"]
                model_name = available_modes[selected_mode].get("description", model)
                logger.info(f"Using {selected_mode} mode: {model}")
                
                # Prepare messages for API
                api_messages = [{"role": "system", "content": pharmacology_system_prompt}]
                
                # Add recent conversation history (last 10 messages)
                for msg in st.session_state.chat_messages[-10:]:
                    api_messages.append({"role": msg["role"], "content": msg["content"]})
                
                # Show which model is being used
                mode_emoji = "⚡" if selected_mode == "turbo" else "🧠"
                mode_name = "Turbo" if selected_mode == "turbo" else "Normal"
                
                # Always use fluid streaming for the best experience
                try:
                    response_placeholder.markdown(f"🔄 Generating response ({mode_name} • Fluid Streaming)...")
                    logger.info(f"Starting fluid streaming response with {selected_mode} mode...")
                    
                    stream_worked = False
                    chunk_count = 0
                    
                    for chunk in chat_completion_stream(model, api_messages):
                        if chunk:  # Only process non-empty chunks
                            stream_worked = True
                            full_response += chunk
                            chunk_count += 1
                            
                            # Ultra-fluid streaming: Update every chunk for maximum smoothness
                            cursor_styles = ["▌", "█", "▎", "▊", "▋", "▍"]
                            cursor = cursor_styles[chunk_count % len(cursor_styles)]
                            response_placeholder.markdown(full_response + cursor)
                    
                    # Final display without cursor - clean finish
                    if stream_worked and full_response.strip():
                        response_placeholder.markdown(full_response)
                        logger.info(f"✅ Fluid streaming completed ({selected_mode}): {len(full_response)} chars, {chunk_count} chunks")
                    else:
                        logger.warning("Streaming failed or empty, trying fallback...")
                        raise Exception("Streaming failed or empty response")
                        
                except Exception as stream_error:
                    logger.warning(f"Streaming failed: {stream_error}, trying non-streaming fallback...")
                    
                    # Fallback to non-streaming
                    response_placeholder.markdown(f"🔄 Generating response ({mode_name} • Fallback)...")
                    full_response = chat_completion(model, api_messages)
                    
                    if full_response and not full_response.startswith("Error:"):
                        response_placeholder.markdown(full_response)
                        logger.info(f"✅ Non-streaming fallback completed ({selected_mode}): {len(full_response)} chars")
                    else:
                        raise Exception(f"Both streaming and non-streaming failed: {full_response}")
                
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
            st.write(f"• Model mode: {st.session_state.get('selected_model_mode', 'normal')}")
            st.write("• Streaming: 💫 Fluid (Always On)")
        
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
                    
                    # Show details about each model
                    for mode, config in modes.items():
                        emoji = "⚡" if mode == "turbo" else "🧠"
                        st.write(f"{emoji} **{mode.title()}**: {config.get('description', config['model'])}")
                        
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