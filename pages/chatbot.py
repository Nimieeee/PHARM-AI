"""
Simplified Chatbot Page - Clean, Minimal Implementation
"""

import streamlit as st
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def run_async(coro):
    """Run async function in Streamlit context."""
    import asyncio
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

def save_conversation():
    """Save current conversation to database."""
    try:
        if not st.session_state.get('authenticated') or not st.session_state.get('user_id'):
            return False
        
        if not st.session_state.chat_messages:
            return True  # Nothing to save
        
        logger.info("Saving conversation to database...")
        
        # Import services
        from services.conversation_service import conversation_service
        from services.user_service import user_service
        
        # Get user UUID
        user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
        if not user_data:
            logger.error("User not found for conversation saving")
            return False
        
        # Create or update conversation
        if not st.session_state.current_conversation_id:
            # Create new conversation
            title = generate_conversation_title()
            conversation_id = run_async(conversation_service.create_conversation(
                user_data['id'], 
                title, 
                st.session_state.get('selected_model_mode', 'normal')
            ))
            st.session_state.current_conversation_id = conversation_id
            logger.info(f"✅ Created new conversation: {conversation_id}")
        
        # Update conversation with current messages
        success = run_async(conversation_service.update_conversation(
            user_data['id'],
            st.session_state.current_conversation_id,
            {'messages': st.session_state.chat_messages}
        ))
        
        if success:
            logger.info(f"✅ Conversation saved: {len(st.session_state.chat_messages)} messages")
            return True
        else:
            logger.error("Failed to save conversation")
            return False
            
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")
        return False

def generate_conversation_title():
    """Generate a title for the conversation based on the first user message."""
    if st.session_state.chat_messages:
        first_user_msg = next((msg for msg in st.session_state.chat_messages if msg["role"] == "user"), None)
        if first_user_msg:
            content = first_user_msg["content"]
            # Create title from first 50 characters
            title = content[:50] + "..." if len(content) > 50 else content
            return title
    
    # Fallback title
    return f"Chat {datetime.now().strftime('%m/%d %H:%M')}"

def load_conversation_messages():
    """Load messages for the current conversation."""
    try:
        current_conv_id = st.session_state.get('current_conversation_id')
        if current_conv_id and st.session_state.get('conversations'):
            conversation = st.session_state.conversations.get(current_conv_id)
            if conversation:
                st.session_state.chat_messages = conversation.get('messages', [])
                logger.info(f"Loaded {len(st.session_state.chat_messages)} messages for conversation {current_conv_id}")
            else:
                st.session_state.chat_messages = []
        else:
            st.session_state.chat_messages = []
    except Exception as e:
        logger.error(f"Error loading conversation messages: {e}")
        st.session_state.chat_messages = []

def render_simple_chatbot():
    """Render a simple, clean chatbot interface."""
    
    # Check authentication
    if not st.session_state.get('authenticated'):
        st.error("Please sign in to use the chatbot.")
        return
    
    st.title("💊 PharmGPT")
    
    # Initialize conversation ID
    if 'current_conversation_id' not in st.session_state:
        st.session_state.current_conversation_id = None
    
    # Initialize model preference
    if 'selected_model_mode' not in st.session_state:
        st.session_state.selected_model_mode = "normal"
    
    # Track conversation changes and load appropriate messages
    if 'last_loaded_conversation' not in st.session_state:
        st.session_state.last_loaded_conversation = None
    
    # Check if conversation changed
    current_conv_id = st.session_state.get('current_conversation_id')
    if st.session_state.last_loaded_conversation != current_conv_id:
        load_conversation_messages()
        st.session_state.last_loaded_conversation = current_conv_id
    
    # Initialize messages if not already done
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    # Simple model selection
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        is_turbo = st.toggle("⚡ Turbo Mode", 
                           value=(st.session_state.selected_model_mode == "turbo"),
                           help="Switch between Normal and Turbo modes")
        st.session_state.selected_model_mode = "turbo" if is_turbo else "normal"
    
    # Display chat messages
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about pharmacology..."):
        logger.info(f"User input: {prompt[:50]}...")
        
        # Add user message to chat history
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            
            try:
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
                    selected_mode = list(available_modes.keys())[0]
                
                model = available_modes[selected_mode]["model"]
                logger.info(f"Using {selected_mode} mode: {model}")
                
                # Prepare messages for API
                api_messages = [{"role": "system", "content": pharmacology_system_prompt}]
                
                # Add recent conversation history (last 10 messages)
                for msg in st.session_state.chat_messages[-10:]:
                    api_messages.append({"role": msg["role"], "content": msg["content"]})
                
                # Try streaming first
                try:
                    response_placeholder.markdown("💭 Thinking...")
                    
                    for chunk in chat_completion_stream(model, api_messages):
                        if chunk:
                            full_response += chunk
                            response_placeholder.markdown(full_response + "▌")
                    
                    # Final display without cursor
                    if full_response.strip():
                        response_placeholder.markdown(full_response)
                        logger.info(f"✅ Streaming completed: {len(full_response)} chars")
                    else:
                        raise Exception("Streaming failed or empty response")
                        
                except Exception as stream_error:
                    logger.warning(f"Streaming failed: {stream_error}, trying fallback...")
                    
                    # Fallback to non-streaming
                    response_placeholder.markdown("💭 Processing...")
                    full_response = chat_completion(model, api_messages)
                    
                    if full_response and not full_response.startswith("Error:"):
                        response_placeholder.markdown(full_response)
                        logger.info(f"✅ Fallback completed: {len(full_response)} chars")
                    else:
                        raise Exception(f"API call failed: {full_response}")
                
                # Add response to chat history
                if full_response and not full_response.startswith("Error:") and not full_response.startswith("❌"):
                    st.session_state.chat_messages.append({"role": "assistant", "content": full_response})
                    logger.info("✅ Response added to chat history")
                    
                    # Auto-save conversation
                    try:
                        save_success = save_conversation()
                        if save_success:
                            logger.info("✅ Conversation auto-saved")
                    except Exception as save_error:
                        logger.error(f"Auto-save error: {save_error}")
                else:
                    logger.error(f"Response not added: {full_response[:100]}...")
                    
            except Exception as e:
                error_msg = f"❌ Error generating response: {str(e)}"
                response_placeholder.markdown(error_msg)
                logger.error(f"Exception in response generation: {e}")

def render_chatbot_page():
    """Main function called by the app."""
    render_simple_chatbot()