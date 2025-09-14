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
    """Render the enhanced chatbot interface with full functionality."""
    
    # Load user conversations
    load_user_conversations()
    
    # Enhanced sidebar for conversation management
    render_enhanced_sidebar()
    
    # Main chat area with improved layout
    render_main_chat_area()

def load_user_conversations():
    """Load user conversations from database."""
    if not st.session_state.get('authenticated') or not st.session_state.get('user_id'):
        return
    
    try:
        from auth import load_user_conversations as load_conversations
        conversations = load_conversations(st.session_state.user_id)
        st.session_state.conversations = conversations
        logger.info(f"Loaded {len(conversations)} conversations")
    except Exception as e:
        logger.error(f"Failed to load conversations: {e}")
        st.session_state.conversations = {}

def render_enhanced_sidebar():
    """Render enhanced sidebar with conversation management."""
    with st.sidebar:
        st.markdown("### 💊 PharmGPT")
        st.markdown(f"**Welcome, {st.session_state.username}!**")
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏠 Home", use_container_width=True):
                st.switch_page("app.py")
        with col2:
            if st.button("🚪 Logout", use_container_width=True):
                logout_current_user()
                st.switch_page("app.py")
        
        st.markdown("---")
        
        # New conversation button
        if st.button("➕ New Conversation", use_container_width=True, type="primary"):
            create_new_conversation()
        
        # Model selection
        st.markdown("### ⚙️ Settings")
        model_mode = st.selectbox(
            "AI Model",
            ["normal", "turbo"],
            index=0 if st.session_state.get('selected_model_mode', 'normal') == 'normal' else 1,
            format_func=lambda x: "🧠 Normal Mode" if x == "normal" else "⚡ Turbo Mode"
        )
        st.session_state.selected_model_mode = model_mode
        
        # Conversation list
        render_conversation_list()
        
        # Current conversation info
        render_conversation_info()

def create_new_conversation():
    """Create a new conversation."""
    st.session_state.chat_messages = []
    st.session_state.current_conversation_id = None
    if 'conversation_documents' in st.session_state:
        st.session_state.conversation_documents = {}
    st.rerun()

def render_conversation_list():
    """Render the list of conversations."""
    st.markdown("### 💬 Conversations")
    
    conversations = st.session_state.get('conversations', {})
    
    if not conversations:
        st.info("No conversations yet. Start chatting to create your first conversation!")
        return
    
    # Sort conversations by updated_at (most recent first)
    sorted_conversations = sorted(
        conversations.items(),
        key=lambda x: x[1].get('updated_at', x[1].get('created_at', '')),
        reverse=True
    )
    
    # Show recent conversations (limit to 10)
    for conv_id, conv_data in sorted_conversations[:10]:
        title = conv_data.get('title', 'Untitled Chat')
        message_count = len(conv_data.get('messages', []))
        
        # Truncate long titles
        display_title = title[:30] + "..." if len(title) > 30 else title
        
        # Highlight current conversation
        is_current = st.session_state.get('current_conversation_id') == conv_id
        button_type = "primary" if is_current else "secondary"
        
        if st.button(
            f"💬 {display_title}\n({message_count} messages)",
            key=f"conv_{conv_id}",
            use_container_width=True,
            type=button_type,
            help=f"Switch to: {title}"
        ):
            load_conversation(conv_id)
    
    # Show more conversations option
    if len(conversations) > 10:
        with st.expander(f"📁 Show {len(conversations) - 10} more conversations"):
            for conv_id, conv_data in sorted_conversations[10:]:
                title = conv_data.get('title', 'Untitled Chat')
                message_count = len(conv_data.get('messages', []))
                display_title = title[:25] + "..." if len(title) > 25 else title
                
                if st.button(
                    f"{display_title} ({message_count})",
                    key=f"conv_more_{conv_id}",
                    use_container_width=True
                ):
                    load_conversation(conv_id)

def load_conversation(conversation_id):
    """Load a specific conversation."""
    conversations = st.session_state.get('conversations', {})
    if conversation_id in conversations:
        st.session_state.current_conversation_id = conversation_id
        st.session_state.chat_messages = conversations[conversation_id].get('messages', [])
        logger.info(f"Loaded conversation: {conversation_id}")
        st.rerun()

def render_conversation_info():
    """Render current conversation information."""
    if not st.session_state.get('current_conversation_id'):
        return
    
    st.markdown("---")
    st.markdown("### 📊 Current Chat")
    
    # Message count
    message_count = len(st.session_state.get('chat_messages', []))
    st.metric("Messages", message_count)
    
    # Document count
    conv_id = st.session_state.current_conversation_id
    doc_count = 0
    if 'conversation_documents' in st.session_state:
        doc_count = len(st.session_state.conversation_documents.get(conv_id, []))
    
    if doc_count > 0:
        st.metric("Documents", doc_count)
    
    # Conversation actions
    with st.expander("🔧 Actions"):
        if st.button("🗑️ Delete Chat", use_container_width=True):
            delete_current_conversation()
        
        if st.button("📋 Duplicate Chat", use_container_width=True):
            duplicate_current_conversation()

def delete_current_conversation():
    """Delete the current conversation."""
    conv_id = st.session_state.get('current_conversation_id')
    if not conv_id:
        return
    
    try:
        from utils.conversation_manager import run_async, delete_conversation
        success = run_async(delete_conversation(conv_id))
        
        if success:
            # Remove from session state
            if conv_id in st.session_state.conversations:
                del st.session_state.conversations[conv_id]
            
            # Clear current conversation
            st.session_state.current_conversation_id = None
            st.session_state.chat_messages = []
            
            st.success("✅ Conversation deleted!")
            st.rerun()
        else:
            st.error("❌ Failed to delete conversation")
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        st.error(f"❌ Error: {e}")

def duplicate_current_conversation():
    """Duplicate the current conversation."""
    conv_id = st.session_state.get('current_conversation_id')
    if not conv_id:
        return
    
    try:
        from utils.conversation_manager import run_async, duplicate_conversation
        new_conv_id = run_async(duplicate_conversation(conv_id))
        
        if new_conv_id:
            st.success("✅ Conversation duplicated!")
            # Reload conversations to show the new one
            load_user_conversations()
            st.rerun()
        else:
            st.error("❌ Failed to duplicate conversation")
    except Exception as e:
        logger.error(f"Error duplicating conversation: {e}")
        st.error(f"❌ Error: {e}")

def render_main_chat_area():
    """Render the main chat area with enhanced features."""
    
    # Chat header with conversation title
    render_chat_header()
    
    # Initialize chat messages
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    # Show welcome message for new conversations
    if not st.session_state.chat_messages:
        render_welcome_message()
    
    # Create a container for messages that will scroll
    message_container = st.container()
    
    with message_container:
        # Display chat messages with enhanced features
        render_chat_messages()
    
    # Fixed bottom input area
    render_bottom_input_area()

def render_chat_header():
    """Render the chat header with conversation title."""
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        if st.session_state.get('current_conversation_id'):
            conversations = st.session_state.get('conversations', {})
            conv_id = st.session_state.current_conversation_id
            title = conversations.get(conv_id, {}).get('title', 'Untitled Chat')
            st.title(f"💊 {title}")
        else:
            st.title("💊 PharmGPT Chat")
    
    with col2:
        # Model indicator
        mode = st.session_state.get('selected_model_mode', 'normal')
        mode_icon = "⚡" if mode == "turbo" else "🧠"
        st.markdown(f"**{mode_icon} {mode.title()} Mode**")
    
    with col3:
        # Document indicator
        conv_id = st.session_state.get('current_conversation_id')
        if conv_id and 'conversation_documents' in st.session_state:
            doc_count = len(st.session_state.conversation_documents.get(conv_id, []))
            if doc_count > 0:
                st.markdown(f"**📎 {doc_count} docs**")

def render_welcome_message():
    """Render welcome message for new conversations."""
    st.markdown("""
    <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 10px; margin: 1rem 0;">
        <h3>👋 Welcome to PharmGPT!</h3>
        <p>I'm your AI pharmacology assistant. Ask me anything about:</p>
        <div style="display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; margin-top: 1rem;">
            <span style="background: white; padding: 0.5rem 1rem; border-radius: 20px; border: 1px solid #e0e7ff;">🧬 Drug Mechanisms</span>
            <span style="background: white; padding: 0.5rem 1rem; border-radius: 20px; border: 1px solid #e0e7ff;">⚗️ Interactions</span>
            <span style="background: white; padding: 0.5rem 1rem; border-radius: 20px; border: 1px solid #e0e7ff;">📊 Pharmacokinetics</span>
            <span style="background: white; padding: 0.5rem 1rem; border-radius: 20px; border: 1px solid #e0e7ff;">🏥 Clinical Applications</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick start examples
    st.markdown("### 💡 Try these examples:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔬 How do ACE inhibitors work?", use_container_width=True):
            st.session_state.example_prompt = "How do ACE inhibitors work?"
            st.rerun()
        
        if st.button("💊 Warfarin drug interactions", use_container_width=True):
            st.session_state.example_prompt = "What are the major drug interactions with warfarin?"
            st.rerun()
    
    with col2:
        if st.button("⚡ Beta-blocker selectivity", use_container_width=True):
            st.session_state.example_prompt = "Explain beta-blocker selectivity and clinical implications"
            st.rerun()
        
        if st.button("🧪 NSAID side effects", use_container_width=True):
            st.session_state.example_prompt = "What are the side effects of NSAIDs and their mechanisms?"
            st.rerun()

def render_chat_messages():
    """Render chat messages with enhanced features."""
    for i, message in enumerate(st.session_state.chat_messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Add timestamp for messages
            if "timestamp" in message:
                timestamp = datetime.fromisoformat(message["timestamp"].replace('Z', '+00:00'))
                st.caption(f"🕒 {timestamp.strftime('%H:%M:%S')}")
            
            # Add regenerate button for the last assistant message
            if (message["role"] == "assistant" and 
                i == len(st.session_state.chat_messages) - 1 and 
                i > 0):
                
                col1, col2, col3 = st.columns([1, 1, 3])
                with col1:
                    if st.button("🔄 Regenerate", key=f"regen_{i}"):
                        regenerate_response(i)
                
                with col2:
                    if st.button("📋 Copy", key=f"copy_{i}"):
                        st.code(message["content"])
                        st.success("✅ Response copied!")

def regenerate_response(message_index):
    """Regenerate the assistant response."""
    if message_index > 0 and st.session_state.chat_messages[message_index-1]["role"] == "user":
        user_prompt = st.session_state.chat_messages[message_index-1]["content"]
        # Remove the current assistant response
        st.session_state.chat_messages.pop()
        # Set regeneration flag
        st.session_state.regenerate_response = True
        st.session_state.regenerate_prompt = user_prompt
        st.rerun()

def render_bottom_input_area():
    """Render the bottom input area with document upload."""
    
    # Add spacing to push input to bottom
    st.markdown("<br>" * 2, unsafe_allow_html=True)
    
    # Enhanced CSS for better input positioning
    st.markdown("""
    <style>
    .stChatInput {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 1rem 0;
        border-top: 1px solid #e0e0e0;
        z-index: 999;
        margin-top: 2rem;
    }
    .main .block-container {
        padding-bottom: 120px;
    }
    .upload-area {
        background: #f8fafc;
        border: 2px dashed #d1d5db;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Document upload area
    render_document_upload()
    
    # Chat input
    prompt = st.chat_input("Ask me anything about pharmacology...")
    
    # Handle example prompts
    if st.session_state.get('example_prompt'):
        prompt = st.session_state.example_prompt
        st.session_state.example_prompt = None
    
    # Handle regenerate response
    if st.session_state.get('regenerate_response', False):
        prompt = st.session_state.get('regenerate_prompt', '')
        st.session_state.regenerate_response = False
        st.session_state.regenerate_prompt = None
    
    # Process chat input
    if prompt:
        process_chat_input(prompt)

def render_document_upload():
    """Render enhanced document upload area."""
    with st.expander("📎 Upload Documents (PDF, DOCX, Images)", expanded=False):
        uploaded_file = st.file_uploader(
            "Choose files to enhance your conversation",
            type=['txt', 'pdf', 'docx', 'md', 'pptx', 'png', 'jpg', 'jpeg'],
            help="Upload documents, presentations, or images for context-aware responses",
            key=f"doc_upload_{st.session_state.get('current_conversation_id', 'new')}"
        )
        
        if uploaded_file is not None:
            process_document_upload(uploaded_file)
        
        # Show current documents
        show_current_documents()

def show_current_documents():
    """Show documents in current conversation."""
    conv_id = st.session_state.get('current_conversation_id')
    if not conv_id or 'conversation_documents' not in st.session_state:
        return
    
    documents = st.session_state.conversation_documents.get(conv_id, [])
    if documents:
        st.markdown("**📚 Documents in this conversation:**")
        for i, doc in enumerate(documents):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"• {doc['filename']} ({doc.get('file_size', 0)} bytes)")
            with col2:
                if st.button("🗑️", key=f"del_doc_{i}", help="Remove document"):
                    documents.pop(i)
                    st.rerun()

def process_document_upload(uploaded_file):
    """Process uploaded document with enhanced features."""
    with st.spinner(f"Processing {uploaded_file.name}..."):
        try:
            # Import document processing functions
            from pages.chatbot import process_uploaded_document, save_document_to_conversation
            
            # Process the document
            content = process_uploaded_document(uploaded_file)
            
            if content:
                # Save to conversation
                success = save_document_to_conversation(uploaded_file, content)
                
                if success:
                    st.success(f"✅ Document processed: {uploaded_file.name}")
                    st.info(f"📄 Extracted {len(content)} characters of content")
                    st.rerun()
                else:
                    st.error("❌ Failed to save document")
            else:
                st.error("❌ Failed to process document")
                
        except Exception as e:
            logger.error(f"Document upload error: {e}")
            st.error(f"❌ Error processing document: {e}")

def process_chat_input(prompt):
    """Process chat input with enhanced features."""
    logger.info(f"Processing user input: {prompt[:50]}...")
    
    # Add user message
    user_message = {
        "role": "user", 
        "content": prompt,
        "timestamp": datetime.now().isoformat()
    }
    st.session_state.chat_messages.append(user_message)
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    
    # Generate assistant response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        try:
            # Generate response with enhanced context
            full_response = generate_enhanced_response(prompt, response_placeholder)
            
            # Add assistant message to chat history
            assistant_message = {
                "role": "assistant", 
                "content": full_response,
                "timestamp": datetime.now().isoformat()
            }
            st.session_state.chat_messages.append(assistant_message)
            
            # Save conversation
            save_conversation_to_database()
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            error_message = f"Sorry, I encountered an error: {str(e)}"
            response_placeholder.markdown(error_message)
            
            st.session_state.chat_messages.append({
                "role": "assistant", 
                "content": error_message,
                "timestamp": datetime.now().isoformat()
            })

def generate_enhanced_response(prompt, response_placeholder):
    """Generate enhanced AI response with document context."""
    try:
        # Import AI functions
        from openai_client import chat_completion_stream, get_available_model_modes
        from prompts import pharmacology_system_prompt
        
        # Get available models
        available_modes = get_available_model_modes()
        if not available_modes:
            return "❌ No AI models available. Please check your API keys."
        
        # Use selected model mode
        selected_mode = st.session_state.get('selected_model_mode', 'normal')
        if selected_mode not in available_modes:
            selected_mode = list(available_modes.keys())[0]
        
        model = available_modes[selected_mode]["model"]
        
        # Get document context
        document_context = get_conversation_context(prompt)
        
        # Prepare enhanced system prompt
        enhanced_system_prompt = pharmacology_system_prompt
        if document_context:
            enhanced_system_prompt += f"\n\n{document_context}\n\nUse the above document context to enhance your responses when relevant."
        
        # Prepare messages for API
        api_messages = [{"role": "system", "content": enhanced_system_prompt}]
        
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
        response_placeholder.caption(f"🕒 {datetime.now().strftime('%H:%M:%S')} • {selected_mode.title()} Mode")
        
        return full_response
        
    except Exception as e:
        logger.error(f"Error in generate_enhanced_response: {e}")
        return f"Sorry, I encountered an error: {str(e)}"

def get_conversation_context(user_query=""):
    """Get document context for current conversation."""
    try:
        conv_id = st.session_state.get('current_conversation_id')
        if not conv_id:
            return ""
        
        # Try RAG system first
        try:
            from services.rag_service import RAGService
            from services.user_service import user_service
            
            # Get user UUID
            user_data = run_async_operation(user_service.get_user_by_id(st.session_state.user_id))
            if user_data:
                rag_service = RAGService()
                
                # Get full document context (default behavior)
                full_context = run_async_operation(rag_service.get_full_document_context(
                    conv_id, user_data['id'], max_context_length=15000
                ))
                
                if full_context:
                    return f"\n\n--- DOCUMENT KNOWLEDGE BASE ---\n{full_context}\n"
                    
        except Exception as rag_error:
            logger.warning(f"RAG system unavailable: {rag_error}")
        
        # Fallback to session-based documents
        if 'conversation_documents' in st.session_state:
            documents = st.session_state.conversation_documents.get(conv_id, [])
            if documents:
                context = "\n\n--- CONVERSATION DOCUMENTS ---\n"
                for doc in documents:
                    content = doc['content'][:2000]  # Limit content length
                    context += f"\n[Document: {doc['filename']}]\n{content}\n"
                return context
        
        return ""
        
    except Exception as e:
        logger.error(f"Error getting conversation context: {e}")
        return ""

def run_async_operation(coro):
    """Run async operation with proper event loop handling."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

def save_conversation_to_database():
    """Save current conversation to database."""
    try:
        if not st.session_state.get('authenticated') or not st.session_state.get('user_id'):
            return False
        
        if not st.session_state.chat_messages:
            return True
        
        # Import services
        from services.conversation_service import conversation_service
        from services.user_service import user_service
        
        # Get user UUID
        user_data = run_async_operation(user_service.get_user_by_id(st.session_state.user_id))
        if not user_data:
            return False
        
        # Create or update conversation
        if not st.session_state.current_conversation_id:
            # Generate title from first user message
            title = generate_conversation_title()
            conversation_id = run_async_operation(conversation_service.create_conversation(
                user_data['id'], 
                title, 
                st.session_state.get('selected_model_mode', 'normal')
            ))
            st.session_state.current_conversation_id = conversation_id
        
        # Update conversation with current messages
        success = run_async_operation(conversation_service.update_conversation(
            user_data['id'],
            st.session_state.current_conversation_id,
            {'messages': st.session_state.chat_messages}
        ))
        
        if success:
            logger.info(f"Conversation saved: {len(st.session_state.chat_messages)} messages")
            return True
        
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

if __name__ == "__main__":
    main()