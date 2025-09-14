"""
Chatbot Page - Multipage Streamlit App with Fixed Message Input Position
"""

import streamlit as st
import sys
import os
import logging
from datetime import datetime

# Add the parent directory to the path so we can import from the main app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.session_manager import initialize_session_state
from utils.theme import apply_theme
from auth import initialize_auth_session, logout_current_user
from config import APP_TITLE, APP_ICON

# Configure logging
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=f"{APP_TITLE} - Chat",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Chatbot page entry point."""
    # Initialize session state and authentication
    initialize_session_state()
    apply_theme()
    initialize_auth_session()
    
    # Check authentication
    if not st.session_state.get('authenticated'):
        st.error("🔐 Please sign in to access the chatbot.")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔐 Go to Sign In", use_container_width=True, type="primary"):
                st.switch_page("pages/2_🔐_Sign_In.py")
            if st.button("← Back to Home", use_container_width=True):
                st.switch_page("app.py")
        return
    
    # Render the chatbot interface
    render_chatbot_interface()

def render_chatbot_interface():
    """Render the main chatbot interface with message input at bottom."""
    
    # Sidebar for conversation management
    with st.sidebar:
        st.markdown("### 💊 PharmGPT")
        st.markdown(f"**Welcome, {st.session_state.username}!**")
        
        # Navigation buttons
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout_current_user()
            st.switch_page("app.py")
        
        st.markdown("---")
        
        # Model selection
        st.markdown("### ⚙️ Settings")
        model_mode = st.selectbox(
            "AI Model",
            ["normal", "turbo"],
            index=0 if st.session_state.get('selected_model_mode', 'normal') == 'normal' else 1,
            format_func=lambda x: "🧠 Normal Mode" if x == "normal" else "⚡ Turbo Mode"
        )
        st.session_state.selected_model_mode = model_mode
        
        # New conversation button
        if st.button("➕ New Conversation", use_container_width=True, type="primary"):
            st.session_state.chat_messages = []
            st.session_state.current_conversation_id = None
            st.rerun()
    
    # Main chat area
    st.title("💊 PharmGPT Chat")
    
    # Initialize chat messages
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    # Create a container for messages that will scroll
    message_container = st.container()
    
    with message_container:
        # Display chat messages
        for i, message in enumerate(st.session_state.chat_messages):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Add regenerate button for the last assistant message
                if (message["role"] == "assistant" and 
                    i == len(st.session_state.chat_messages) - 1 and 
                    i > 0):
                    if st.button("🔄 Regenerate", key=f"regen_{i}"):
                        # Get the previous user message
                        if i > 0 and st.session_state.chat_messages[i-1]["role"] == "user":
                            user_prompt = st.session_state.chat_messages[i-1]["content"]
                            # Remove the current assistant response
                            st.session_state.chat_messages.pop()
                            # Set regeneration flag
                            st.session_state.regenerate_response = True
                            st.session_state.regenerate_prompt = user_prompt
                            st.rerun()
    
    # Add some spacing to push input to bottom
    st.markdown("<br>" * 3, unsafe_allow_html=True)
    
    # Fixed bottom input area with custom CSS
    st.markdown("""
    <style>
    .stChatInput {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 1rem;
        border-top: 1px solid #e0e0e0;
        z-index: 999;
    }
    .main .block-container {
        padding-bottom: 100px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Document upload and chat input in columns
    col1, col2 = st.columns([4, 1])
    
    with col1:
        # Chat input - this will be at the bottom
        prompt = st.chat_input("Ask me anything about pharmacology...")
    
    with col2:
        # Document upload
        uploaded_file = st.file_uploader(
            "📎 Upload",
            type=['txt', 'pdf', 'docx', 'md', 'png', 'jpg', 'jpeg'],
            help="Upload documents for this conversation",
            key=f"doc_upload_{st.session_state.get('current_conversation_id', 'new')}"
        )
    
    # Handle document upload
    if uploaded_file is not None:
        with st.spinner(f"Processing {uploaded_file.name}..."):
            # Process document (simplified for now)
            st.success(f"✅ Document uploaded: {uploaded_file.name}")
            # TODO: Implement document processing
    
    # Handle regenerate response
    if st.session_state.get('regenerate_response', False):
        prompt = st.session_state.get('regenerate_prompt', '')
        st.session_state.regenerate_response = False
        st.session_state.regenerate_prompt = None
    
    # Process chat input
    if prompt:
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with message_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        
        # Generate assistant response
        with message_container:
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                
                try:
                    # Import AI functions
                    from openai_client import chat_completion_stream, get_available_model_modes
                    from prompts import pharmacology_system_prompt
                    
                    # Get available models
                    available_modes = get_available_model_modes()
                    if not available_modes:
                        response_placeholder.markdown("❌ No AI models available. Please check your API keys.")
                        return
                    
                    # Use selected model mode
                    selected_mode = st.session_state.selected_model_mode
                    if selected_mode not in available_modes:
                        selected_mode = list(available_modes.keys())[0]
                    
                    model = available_modes[selected_mode]["model"]
                    
                    # Prepare messages for API
                    api_messages = [
                        {"role": "system", "content": pharmacology_system_prompt}
                    ]
                    
                    # Add recent conversation history (last 10 messages)
                    recent_messages = st.session_state.chat_messages[-10:]
                    for msg in recent_messages:
                        api_messages.append({"role": msg["role"], "content": msg["content"]})
                    
                    # Stream the response
                    full_response = ""
                    for chunk in chat_completion_stream(model, api_messages):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                    
                    # Final response without cursor
                    response_placeholder.markdown(full_response)
                    
                    # Add assistant message to chat history
                    st.session_state.chat_messages.append({
                        "role": "assistant", 
                        "content": full_response,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Save conversation (simplified for now)
                    # TODO: Implement conversation saving
                    
                except Exception as e:
                    logger.error(f"Error generating response: {e}")
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    response_placeholder.markdown(error_message)
                    st.session_state.chat_messages.append({
                        "role": "assistant", 
                        "content": error_message,
                        "timestamp": datetime.now().isoformat()
                    })

if __name__ == "__main__":
    main()