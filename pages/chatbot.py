"""
Clean Chatbot Page - Simple and Reliable Chat Interface
"""

import streamlit as st
import time
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Import functions
from utils.conversation_manager import (
    get_current_messages, 
    add_message_to_current_conversation, 
    create_new_conversation,
    run_async
)
from openai_client import (
    chat_completion_stream, 
    chat_completion, 
    get_available_model_modes,
    get_model_configs
)
from prompts import pharmacology_system_prompt

def get_selected_model(mode_key="model_mode", default_mode="normal"):
    """Get the selected model for the given mode."""
    selected_mode = st.session_state.get(mode_key, default_mode)
    model_configs = get_model_configs()
    return model_configs[selected_mode]["model"]

def render_chatbot_page():
    """Render the main chatbot page."""
    # Check authentication
    if not st.session_state.get('authenticated'):
        st.error("Please sign in to use the chatbot.")
        return
    
    # Check if we have a conversation, if not show welcome screen
    if not st.session_state.get('current_conversation_id'):
        render_welcome_screen()
    else:
        render_chat_interface()

def render_welcome_screen():
    """Render welcome screen when no conversation is active."""
    st.markdown("# 💊 PharmGPT")
    st.markdown("### Your AI Pharmacology Expert")
    st.markdown("Ready to help you learn and understand pharmacology concepts.")
    st.markdown("---")

    # Start chat button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start New Chat", key="start_chat", use_container_width=True, type="primary"):
            try:
                conversation_id = run_async(create_new_conversation())
                if conversation_id:
                    st.rerun()
                else:
                    st.error("Failed to create conversation. Please try again.")
            except Exception as e:
                logger.error(f"Error starting new chat: {e}")
                st.error("Failed to start new chat. Please try again.")

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick example questions
    st.markdown("### 💡 Example Questions")
    examples = [
        "Explain the mechanism of action of ACE inhibitors",
        "What are the contraindications for NSAIDs?",
        "How do beta-blockers work in treating hypertension?",
        "Describe the pharmacokinetics of warfarin"
    ]

    for i, example in enumerate(examples):
        if st.button(f"💬 {example}", key=f"example_{i}", use_container_width=True):
            try:
                conversation_id = run_async(create_new_conversation())
                if conversation_id:
                    success = run_async(add_message_to_current_conversation("user", example))
                    if success:
                        st.rerun()
                    else:
                        st.error("Failed to send message. Please try again.")
                else:
                    st.error("Failed to create conversation. Please try again.")
            except Exception as e:
                logger.error(f"Error with example question: {e}")
                st.error("Failed to process example question. Please try again.")

def render_chat_interface():
    """Render the main chat interface."""
    # Get current conversation
    current_conv = st.session_state.conversations[st.session_state.current_conversation_id]

    # Conversation header with model toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 💬 {current_conv['title']}")

    with col2:
        # Model mode toggle switch
        available_modes = get_available_model_modes()
        if available_modes and len(available_modes) >= 2:
            # Initialize selected mode in session state
            if "model_mode" not in st.session_state:
                st.session_state.model_mode = "normal"

            # Create a toggle switch
            current_mode = st.session_state.model_mode
            is_turbo = current_mode == "turbo"

            # Toggle switch
            turbo_enabled = st.toggle(
                "⚡ Turbo Mode",
                value=is_turbo,
                help="Switch between Normal Mode (Llama Maverick) and Turbo Mode (Sonoma Sky Alpha)",
                key="turbo_toggle"
            )

            # Update mode based on toggle
            st.session_state.model_mode = "turbo" if turbo_enabled else "normal"
        else:
            st.error("Both Normal and Turbo modes need to be available. Please check your API keys.")
            return

    st.markdown("---")

    # Display chat messages
    display_chat_messages()

    # Chat input at the bottom
    st.markdown("---")
    render_chat_input()

def display_chat_messages():
    """Display chat messages for the current conversation."""
    messages = get_current_messages()
    for i, message in enumerate(messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            # Add regenerate button after the last assistant message
            if (message["role"] == "assistant" and
                i == len(messages) - 1 and
                len(messages) >= 2):
                
                st.markdown("")
                col1, col2, col3 = st.columns([1, 1, 3])
                with col1:
                    if st.button("🔄 Regenerate", key=f"regenerate_{i}", help="Generate a new response"):
                        regenerate_last_response()
                        st.rerun()

def render_chat_input():
    """Render the chat input interface."""
    # Create input form
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            user_input = st.text_input(
                "Message",
                placeholder="Ask me anything about pharmacology...",
                label_visibility="collapsed"
            )
        
        with col2:
            send_clicked = st.form_submit_button("Send", type="primary", use_container_width=True)
    
    # Handle form submission
    if send_clicked and user_input.strip():
        logger.info(f"Processing user message: {user_input[:50]}...")
        
        try:
            # Add user message
            success = run_async(add_message_to_current_conversation("user", user_input.strip()))
            if not success:
                st.error("Failed to save your message. Please try again.")
                return
            
            # Display user message immediately
            with st.chat_message("user"):
                st.markdown(user_input.strip())
            
            # Generate and display AI response
            generate_ai_response(user_input.strip())
            
            # Don't rerun immediately - let the response complete first
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            st.error("Failed to process your message. Please try again.")

def generate_ai_response(user_prompt: str):
    """Generate and display AI response."""
    logger.info("Generating AI response")
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            # Show thinking message
            message_placeholder.markdown("🤔 Thinking...")

            # Get selected model
            selected_model = get_selected_model("model_mode", "normal")
            logger.info(f"Using model: {selected_model}")

            # Prepare messages for API
            messages = get_messages_for_api(user_prompt)
            
            # Try streaming first
            try:
                message_placeholder.markdown("🔄 Generating response...")
                logger.info(f"Starting streaming with model: {selected_model}")
                
                stream_worked = False
                update_counter = 0
                
                for chunk in chat_completion_stream(selected_model, messages):
                    if chunk:  # Only process non-empty chunks
                        stream_worked = True
                        full_response += chunk
                        update_counter += 1
                        
                        # Update UI every few chunks
                        if update_counter % 5 == 0:
                            message_placeholder.markdown(full_response + "▌")
                
                if stream_worked and full_response.strip():
                    message_placeholder.markdown(full_response)
                    logger.info(f"✅ Streaming response completed: {len(full_response)} chars")
                else:
                    logger.warning("Streaming produced empty response, trying fallback")
                    raise Exception("Streaming failed or empty response")
                    
            except Exception as stream_error:
                logger.warning(f"Streaming failed, trying non-streaming: {stream_error}")
                
                # Reset response for fallback
                full_response = ""
                
                # Fallback to non-streaming
                message_placeholder.markdown("🔄 Generating response (fallback)...")
                try:
                    full_response = chat_completion(selected_model, messages)
                    if full_response and full_response.strip():
                        message_placeholder.markdown(full_response)
                        logger.info(f"✅ Non-streaming response completed: {len(full_response)} chars")
                    else:
                        raise Exception("Non-streaming also failed or empty response")
                except Exception as fallback_error:
                    logger.error(f"Both streaming and non-streaming failed: {fallback_error}")
                    raise fallback_error

        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            error_msg = f"❌ Error generating response: {str(e)}"
            message_placeholder.markdown(error_msg)
            full_response = error_msg

        # Save AI response to conversation
        if full_response and not full_response.startswith("❌ Error"):
            try:
                success = run_async(add_message_to_current_conversation("assistant", full_response))
                if success:
                    logger.info("✅ AI response saved to conversation")
                    # Trigger a rerun after successful save
                    st.rerun()
                else:
                    logger.error("❌ Failed to save AI response")
                    st.error("Failed to save the response. Please try again.")
            except Exception as save_error:
                logger.error(f"Error saving AI response: {save_error}")
                st.error("Error saving the response. Please try again.")

def get_messages_for_api(user_input: str) -> list:
    """Get messages formatted for API call."""
    messages = [{"role": "system", "content": pharmacology_system_prompt}]

    # Add conversation history (last 10 messages for context)
    current_messages = get_current_messages()
    for msg in current_messages[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current user input
    messages.append({"role": "user", "content": user_input})

    return messages

def regenerate_last_response():
    """Regenerate the last assistant response."""
    logger.info("Regenerating last response")
    
    try:
        messages = get_current_messages()

        if len(messages) < 2:
            st.error("No response to regenerate")
            return

        # Find the last user message
        last_user_message = None
        last_assistant_index = None

        for i in range(len(messages) - 1, -1, -1):
            if messages[i]["role"] == "assistant" and last_assistant_index is None:
                last_assistant_index = i
            elif messages[i]["role"] == "user" and last_assistant_index is not None:
                last_user_message = messages[i]["content"]
                break

        if not last_user_message or last_assistant_index is None:
            st.error("Could not find message to regenerate")
            return

        # Remove the last assistant message from session state
        if st.session_state.current_conversation_id in st.session_state.conversations:
            st.session_state.conversations[st.session_state.current_conversation_id]["messages"].pop(last_assistant_index)

        # Generate new response
        generate_ai_response(last_user_message)
        
    except Exception as e:
        logger.error(f"Error regenerating response: {e}")
        st.error("Failed to regenerate response. Please try again.")