"""
PharmGPT Chatbot Interface
Clean implementation with conversation-specific knowledge bases
"""

import logging
import asyncio
from typing import Dict, List, Optional, Tuple
import uuid
import time

import streamlit as st

# Core imports
from core.config import config, APP_TITLE, APP_ICON, MAX_FILE_SIZE_MB, ALLOWED_FILE_TYPES
from core.auth import require_authentication, get_current_user, get_current_user_id, render_user_info
from core.conversations import (
    create_conversation, get_user_conversations, get_conversation_messages,
    add_message, update_conversation_title, delete_conversation
)
from core.rag import process_document, get_relevant_context, get_rag_status
from core.utils import DocumentProcessor, ErrorHandler, format_file_size, truncate_text, format_timestamp

# Configure logging
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=f"{APP_TITLE} - Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)


def apply_chatbot_css():
    """Apply custom CSS for chatbot interface."""
    st.markdown("""
    <style>
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        max-width: 80%;
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: auto;
    }
    .assistant-message {
        background: #f8f9fa;
        color: #333;
        border-left: 4px solid #1f77b4;
    }
    .conversation-sidebar {
        background: #f1f3f4;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .file-upload-area {
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background: #fafafa;
        margin: 1rem 0;
    }
    .context-preview {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        font-size: 0.9em;
        max-height: 200px;
        overflow-y: auto;
    }
    .message-metadata {
        font-size: 0.8em;
        color: #666;
        margin-top: 0.5rem;
    }
    .conversation-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 5px;
        cursor: pointer;
        border-left: 3px solid transparent;
    }
    .conversation-item:hover {
        background: #e9ecef;
        border-left: 3px solid #1f77b4;
    }
    .conversation-active {
        background: #d4edda !important;
        border-left: 3px solid #28a745 !important;
    }
    </style>
    """, unsafe_allow_html=True)


def run_async(coro):
    """Helper to run async functions in Streamlit."""
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


# Session state initialization
def initialize_chatbot_session():
    """Initialize chatbot session state."""
    if 'current_conversation_id' not in st.session_state:
        st.session_state.current_conversation_id = None
    if 'conversations' not in st.session_state:
        st.session_state.conversations = []
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'message_input' not in st.session_state:
        st.session_state.message_input = ""
    if 'document_context' not in st.session_state:
        st.session_state.document_context = ""


def load_conversations():
    """Load user conversations."""
    try:
        conversations = get_user_conversations()
        st.session_state.conversations = conversations
        logger.info(f"Loaded {len(conversations)} conversations")
    except Exception as e:
        ErrorHandler.handle_streamlit_error(e, "Loading Conversations")
        st.session_state.conversations = []


def load_conversation_messages(conversation_id: str):
    """Load messages for a specific conversation."""
    try:
        messages = get_conversation_messages(conversation_id)
        st.session_state.messages = messages
        st.session_state.current_conversation_id = conversation_id
        logger.info(f"Loaded {len(messages)} messages for conversation {conversation_id}")
    except Exception as e:
        ErrorHandler.handle_streamlit_error(e, "Loading Messages")
        st.session_state.messages = []


def create_new_conversation(title: str) -> Optional[str]:
    """Create a new conversation."""
    try:
        conversation_id = create_conversation(title)
        if conversation_id:
            st.success(f"✅ Created new conversation: {title}")
            load_conversations()  # Refresh conversations list
            return conversation_id
        else:
            st.error("❌ Failed to create conversation")
            return None
    except Exception as e:
        ErrorHandler.handle_streamlit_error(e, "Creating Conversation")
        return None


def render_conversation_sidebar():
    """Render conversation management sidebar."""
    st.sidebar.header("💬 Conversations")
    
    # User info
    render_user_info()
    
    # New conversation form
    with st.sidebar.expander("➕ New Conversation", expanded=False):
        with st.form("new_conversation_form"):
            conversation_title = st.text_input(
                "Conversation Title",
                placeholder="Enter conversation title...",
                max_chars=100
            )
            
            model_option = st.selectbox(
                "AI Model",
                options=['normal', 'advanced', 'fast'],
                format_func=lambda x: {
                    'normal': '🧠 Normal (Balanced)',
                    'advanced': '🚀 Advanced (More capable)',
                    'fast': '⚡ Fast (Quick responses)'
                }.get(x, x)
            )
            
            create_clicked = st.form_submit_button("Create Conversation", use_container_width=True)
            
            if create_clicked and conversation_title:
                conversation_id = create_new_conversation(conversation_title)
                if conversation_id:
                    st.session_state.current_conversation_id = conversation_id
                    load_conversation_messages(conversation_id)
                    st.rerun()
    
    # Load conversations
    if not st.session_state.conversations:
        load_conversations()
    
    # Conversation list
    if st.session_state.conversations:
        st.sidebar.subheader("Your Conversations")
        
        for conv in st.session_state.conversations:
            conv_id = conv['id']
            conv_title = conv.get('title', 'Untitled')
            message_count = conv.get('message_count', 0)
            updated_at = format_timestamp(conv.get('updated_at', ''))
            
            # Determine if this conversation is active
            is_active = conv_id == st.session_state.current_conversation_id
            
            # Create conversation item
            container = st.sidebar.container()
            
            with container:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Conversation button
                    button_label = f"{'📌 ' if is_active else '💬 '}{truncate_text(conv_title, 30)}"
                    if st.button(
                        button_label,
                        key=f"conv_{conv_id}",
                        use_container_width=True,
                        type="primary" if is_active else "secondary"
                    ):
                        load_conversation_messages(conv_id)
                        st.rerun()
                
                with col2:
                    # Conversation options
                    if st.button("⋮", key=f"options_{conv_id}"):
                        st.session_state[f"show_options_{conv_id}"] = True
                
                # Show conversation details
                st.caption(f"{message_count} messages • {updated_at}")
                
                # Conversation options (if expanded)
                if st.session_state.get(f"show_options_{conv_id}", False):
                    if st.button(f"🗑️ Delete", key=f"delete_{conv_id}"):
                        if delete_conversation(conv_id):
                            st.success("Conversation deleted")
                            if conv_id == st.session_state.current_conversation_id:
                                st.session_state.current_conversation_id = None
                                st.session_state.messages = []
                            load_conversations()
                            st.rerun()
                    
                    if st.button(f"✏️ Rename", key=f"rename_{conv_id}"):
                        st.session_state[f"renaming_{conv_id}"] = True
                    
                    if st.session_state.get(f"renaming_{conv_id}", False):
                        new_title = st.text_input(
                            "New title",
                            value=conv_title,
                            key=f"new_title_{conv_id}"
                        )
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Save", key=f"save_{conv_id}"):
                                if update_conversation_title(conv_id, new_title):
                                    st.success("Title updated")
                                    load_conversations()
                                    st.session_state[f"renaming_{conv_id}"] = False
                                    st.rerun()
                        with col2:
                            if st.button("Cancel", key=f"cancel_{conv_id}"):
                                st.session_state[f"renaming_{conv_id}"] = False
                                st.rerun()
                    
                    if st.button("Close", key=f"close_options_{conv_id}"):
                        st.session_state[f"show_options_{conv_id}"] = False
                        st.rerun()
                
                st.sidebar.divider()
    
    else:
        st.sidebar.info("No conversations yet. Create your first conversation above!")


def render_document_upload():
    """Render document upload interface."""
    if not st.session_state.current_conversation_id:
        st.warning("⚠️ Please select or create a conversation to upload documents.")
        return
    
    st.subheader("📄 Upload Documents")
    st.info("💡 Documents uploaded here will only be available in this conversation.")
    
    # File upload
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        type=list(ALLOWED_FILE_TYPES.keys()),
        accept_multiple_files=True,
        help=f"Maximum file size: {MAX_FILE_SIZE_MB}MB per file"
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Validate file
            file_size = len(uploaded_file.getvalue())
            
            if file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                st.error(f"❌ {uploaded_file.name}: File too large ({format_file_size(file_size)} > {MAX_FILE_SIZE_MB}MB)")
                continue
            
            # Process file
            with st.spinner(f"Processing {uploaded_file.name}..."):
                try:
                    # Extract text content
                    success, text_content, message, metadata = DocumentProcessor.process_uploaded_file(uploaded_file)
                    
                    if success and text_content:
                        st.success(f"✅ Extracted text from {uploaded_file.name}")
                        
                        # Show preview
                        with st.expander(f"Preview: {uploaded_file.name}"):
                            st.text_area(
                                "Content Preview",
                                value=truncate_text(text_content, 1000),
                                height=200,
                                disabled=True
                            )
                            st.json(metadata)
                        
                        # Process for RAG
                        if st.button(f"Add {uploaded_file.name} to Knowledge Base", key=f"add_{uploaded_file.name}"):
                            with st.spinner("Adding to knowledge base..."):
                                rag_success, rag_message, doc_id = run_async(process_document(
                                    conversation_id=st.session_state.current_conversation_id,
                                    user_id=get_current_user_id(),
                                    filename=uploaded_file.name,
                                    file_content=text_content,
                                    file_type=metadata.get('file_type', ''),
                                    file_size=metadata.get('file_size', 0)
                                ))
                                
                                if rag_success:
                                    st.success(f"🎉 {rag_message}")
                                else:
                                    st.error(f"❌ {rag_message}")
                    
                    else:
                        st.error(f"❌ Failed to process {uploaded_file.name}: {message}")
                
                except Exception as e:
                    ErrorHandler.handle_streamlit_error(e, f"Processing {uploaded_file.name}")


def render_messages():
    """Render conversation messages."""
    if not st.session_state.messages:
        st.info("💬 No messages in this conversation yet. Start chatting below!")
        return
    
    # Messages container
    messages_container = st.container()
    
    with messages_container:
        for message in st.session_state.messages:
            role = message.get('role', 'user')
            content = message.get('content', '')
            created_at = format_timestamp(message.get('created_at', ''))
            model = message.get('model', '')
            
            if role == 'user':
                # User message
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 You</strong><br>
                    {content}
                    <div class="message-metadata">{created_at}</div>
                </div>
                """, unsafe_allow_html=True)
            
            elif role == 'assistant':
                # Assistant message
                st.markdown(f"""
                <div class="chat-message assistant-message">
                    <strong>🤖 PharmGPT</strong><br>
                    {content}
                    <div class="message-metadata">{created_at} • {model}</div>
                </div>
                """, unsafe_allow_html=True)


def get_ai_response(user_message: str, conversation_context: str = "") -> str:
    """Get AI response using OpenAI (placeholder for now)."""
    # This is a placeholder - you would integrate with your preferred AI model here
    # For now, return a simple response
    
    base_response = f"I understand you're asking about: {user_message[:100]}..."
    
    if conversation_context:
        return f"{base_response}\n\nBased on the documents you've uploaded, here's additional context:\n{conversation_context[:500]}..."
    
    return f"{base_response}\n\nThis is a placeholder response. Please integrate with your preferred AI model (OpenAI, Mistral, etc.) to get real pharmacology responses."


def render_chat_input():
    """Render chat input interface."""
    if not st.session_state.current_conversation_id:
        st.warning("⚠️ Please select or create a conversation to start chatting.")
        return
    
    st.subheader("💬 Chat")
    
    # Chat input form
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area(
            "Type your message:",
            placeholder="Ask me anything about pharmacology...",
            height=100,
            key="message_input_form"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            use_context = st.checkbox("🔍 Use document context", value=True)
        
        with col2:
            send_clicked = st.form_submit_button("Send 📤", use_container_width=True)
        
        if send_clicked and user_input.strip():
            # Add user message
            user_message_id = add_message(
                conversation_id=st.session_state.current_conversation_id,
                role="user",
                content=user_input,
                metadata={"timestamp": time.time()}
            )
            
            if user_message_id:
                # Get relevant context if requested
                context = ""
                if use_context:
                    with st.spinner("🔍 Searching documents for context..."):
                        context = run_async(get_relevant_context(
                            query=user_input,
                            conversation_id=st.session_state.current_conversation_id,
                            user_id=get_current_user_id()
                        ))
                
                # Generate AI response
                with st.spinner("🤖 Generating response..."):
                    ai_response = get_ai_response(user_input, context)
                
                # Add assistant message
                assistant_message_id = add_message(
                    conversation_id=st.session_state.current_conversation_id,
                    role="assistant",
                    content=ai_response,
                    model="placeholder-model",
                    metadata={
                        "timestamp": time.time(),
                        "context_used": len(context) > 0,
                        "context_length": len(context)
                    }
                )
                
                if assistant_message_id:
                    # Reload messages
                    load_conversation_messages(st.session_state.current_conversation_id)
                    st.rerun()
                else:
                    st.error("Failed to save assistant response")
            else:
                st.error("Failed to save your message")


def render_rag_status():
    """Render RAG system status."""
    with st.sidebar.expander("🔧 System Status"):
        rag_status = get_rag_status()
        
        st.markdown("**RAG System:**")
        st.write(f"• LangChain: {'✅' if rag_status['langchain_available'] else '❌'}")
        st.write(f"• Embeddings: {'✅' if rag_status['embeddings_available'] else '❌'}")
        st.write(f"• Model: {rag_status['model']}")
        st.write(f"• Dimensions: {rag_status['dimensions']}")
        
        if not rag_status['embeddings_available']:
            st.warning("⚠️ Embeddings not available. Documents won't provide context.")


def main():
    """Main chatbot interface."""
    # Require authentication
    require_authentication()
    
    # Apply custom CSS
    apply_chatbot_css()
    
    # Initialize session
    initialize_chatbot_session()
    
    # Page header
    st.title("💬 PharmGPT Chatbot")
    st.markdown("AI Pharmacology Assistant with conversation-specific knowledge bases")
    
    # Render sidebar
    render_conversation_sidebar()
    render_rag_status()
    
    # Main content
    if st.session_state.current_conversation_id:
        # Show current conversation
        current_conv = next(
            (c for c in st.session_state.conversations if c['id'] == st.session_state.current_conversation_id),
            None
        )
        
        if current_conv:
            st.success(f"📌 Current conversation: **{current_conv['title']}**")
            
            # Tab interface
            tab1, tab2 = st.tabs(["💬 Chat", "📄 Documents"])
            
            with tab1:
                # Render messages
                render_messages()
                
                # Chat input
                render_chat_input()
            
            with tab2:
                # Document upload
                render_document_upload()
        
        else:
            st.error("❌ Selected conversation not found. Please select another conversation.")
            st.session_state.current_conversation_id = None
    
    else:
        # No conversation selected
        st.info("👈 Please select or create a conversation from the sidebar to start chatting!")
        
        # Quick start guide
        st.subheader("🚀 Quick Start Guide")
        st.markdown("""
        1. **Create a Conversation**: Use the sidebar to create your first conversation
        2. **Upload Documents** (Optional): Add PDFs, DOCX, or text files for context
        3. **Start Chatting**: Ask pharmacology questions and get AI-powered responses
        4. **Use Context**: Toggle "Use document context" to include uploaded documents in responses
        """)


if __name__ == "__main__":
    main()