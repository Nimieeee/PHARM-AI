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
    
    # Show current model status
    current_mode = st.session_state.get('selected_model_mode', 'normal')
    mode_emoji = "⚡" if current_mode == "turbo" else "🧠"
    mode_name = "Turbo Mode" if current_mode == "turbo" else "Normal Mode"
    
    # Enhanced streaming status
    if st.session_state.get('use_streaming', True):
        if st.session_state.get('fluid_streaming', True):
            streaming_status = "💫 Fluid Streaming"
        else:
            streaming_status = "🌊 Standard Streaming"
    else:
        streaming_status = "📄 Non-streaming"
    
    st.caption(f"🎯 {mode_emoji} {mode_name} • {streaming_status}")
    
    # Simple controls
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col2:
        # Initialize model preference
        if 'selected_model_mode' not in st.session_state:
            st.session_state.selected_model_mode = "normal"
        
        # Model selection toggle
        is_turbo = st.toggle("⚡ Turbo Mode", 
                           value=(st.session_state.selected_model_mode == "turbo"),
                           help="Switch between Normal (Groq Llama) and Turbo (OpenRouter) modes")
        
        st.session_state.selected_model_mode = "turbo" if is_turbo else "normal"
    
    with col3:
        # Initialize streaming preference
        if 'use_streaming' not in st.session_state:
            st.session_state.use_streaming = True
        
        use_streaming = st.toggle("🌊 Streaming", 
                                value=st.session_state.use_streaming, 
                                help="Enable streaming responses")
        st.session_state.use_streaming = use_streaming
    
    with col4:
        # Initialize streaming quality preference
        if 'fluid_streaming' not in st.session_state:
            st.session_state.fluid_streaming = True
        
        fluid_streaming = st.toggle("💫 Fluid", 
                                   value=st.session_state.fluid_streaming,
                                   help="Enable ultra-smooth streaming (more updates)")
        st.session_state.fluid_streaming = fluid_streaming
    
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
                
                # Choose streaming or non-streaming based on toggle
                if st.session_state.use_streaming:
                    # Try streaming with enhanced fluidity
                    try:
                        # Show initial streaming message with mode info
                        streaming_type = "Fluid" if st.session_state.fluid_streaming else "Standard"
                        response_placeholder.markdown(f"🔄 Generating response ({mode_name} • {streaming_type} Streaming)...")
                        logger.info(f"Starting {streaming_type.lower()} streaming response with {selected_mode} mode...")
                        
                        stream_worked = False
                        chunk_count = 0
                        last_update_length = 0
                        
                        for chunk in chat_completion_stream(model, api_messages):
                            if chunk:  # Only process non-empty chunks
                                stream_worked = True
                                full_response += chunk
                                chunk_count += 1
                                
                                # Adaptive streaming based on fluid setting
                                current_length = len(full_response)
                                
                                if st.session_state.fluid_streaming:
                                    # Ultra-fluid: Update every chunk for maximum smoothness
                                    cursor_styles = ["▌", "█", "▎", "▊", "▋", "▍"]
                                    cursor = cursor_styles[chunk_count % len(cursor_styles)]
                                    response_placeholder.markdown(full_response + cursor)
                                    last_update_length = current_length
                                else:
                                    # Standard: Update every few chunks for balanced performance
                                    if (current_length - last_update_length >= 8) or (chunk_count % 3 == 0):
                                        cursor_styles = ["▌", "█"]
                                        cursor = cursor_styles[chunk_count % len(cursor_styles)]
                                        response_placeholder.markdown(full_response + cursor)
                                        last_update_length = current_length
                        
                        # Final display without cursor - clean finish
                        if stream_worked and full_response.strip():
                            response_placeholder.markdown(full_response)
                            logger.info(f"✅ Fluid streaming completed ({selected_mode}): {len(full_response)} chars, {chunk_count} chunks")
                        else:
                            logger.warning("Streaming failed or empty, trying fallback...")
                            raise Exception("Streaming failed or empty response")
                            
                    except Exception as stream_error:
                        logger.warning(f"Streaming failed: {stream_error}, trying non-streaming...")
                        
                        # Fallback to non-streaming
                        response_placeholder.markdown(f"🔄 Generating response ({mode_name} • Fallback)...")
                        full_response = chat_completion(model, api_messages)
                        
                        if full_response and not full_response.startswith("Error:"):
                            response_placeholder.markdown(full_response)
                            logger.info(f"✅ Non-streaming fallback completed ({selected_mode}): {len(full_response)} chars")
                        else:
                            raise Exception(f"Both streaming and non-streaming failed: {full_response}")
                else:
                    # Use non-streaming directly
                    response_placeholder.markdown(f"🔄 Generating response ({mode_name} • Non-streaming)...")
                    logger.info(f"Using non-streaming response with {selected_mode} mode...")
                    
                    full_response = chat_completion(model, api_messages)
                    
                    if full_response and not full_response.startswith("Error:"):
                        response_placeholder.markdown(full_response)
                        logger.info(f"✅ Non-streaming completed ({selected_mode}): {len(full_response)} chars")
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
            st.write(f"• Model mode: {st.session_state.get('selected_model_mode', 'normal')}")
            st.write(f"• Streaming: {st.session_state.get('use_streaming', True)}")
            st.write(f"• Fluid mode: {st.session_state.get('fluid_streaming', True)}")
        
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