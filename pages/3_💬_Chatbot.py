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
from config import APP_TITLE, APP_ICON, MAX_FILE_SIZE_MB

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
        
        # Contact Support button
        if st.button("📞 Contact Support", use_container_width=True):
            st.switch_page("pages/4_📞_Contact_Support.py")
        
        # Admin Dashboard button (only for admin user)
        if st.session_state.get('username') == 'admin':
            if st.button("🛠️ Admin Dashboard", use_container_width=True):
                st.switch_page("pages/.admin_dashboard.py")
        
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
        
        # Create conversation item with action buttons
        with st.container():
            # Main conversation button
            col1, col2, col3 = st.columns([6, 1, 1])
            
            with col1:
                if st.button(
                    f"💬 {display_title}\n({message_count} messages)",
                    key=f"conv_{conv_id}",
                    use_container_width=True,
                    type=button_type,
                    help=f"Switch to: {title}"
                ):
                    load_conversation(conv_id)
            
            with col2:
                # Delete button for each conversation
                if st.button("🗑️", key=f"delete_{conv_id}", help="Delete conversation"):
                    delete_specific_conversation(conv_id)
            
            # Removed export functionality
    
    # Show more conversations option
    if len(conversations) > 10:
        with st.expander(f"📁 Show {len(conversations) - 10} more conversations"):
            for conv_id, conv_data in sorted_conversations[10:]:
                title = conv_data.get('title', 'Untitled Chat')
                message_count = len(conv_data.get('messages', []))
                display_title = title[:20] + "..." if len(title) > 20 else title
                
                # More conversations with delete buttons
                col1, col2, col3 = st.columns([6, 1, 1])
                
                with col1:
                    if st.button(
                        f"{display_title} ({message_count})",
                        key=f"conv_more_{conv_id}",
                        use_container_width=True
                    ):
                        load_conversation(conv_id)
                
                with col2:
                    if st.button("🗑️", key=f"delete_more_{conv_id}", help="Delete conversation"):
                        delete_specific_conversation(conv_id)
                
                # Removed export functionality

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
        
        # Other actions
        if st.button("📋 Duplicate Chat", use_container_width=True):
            duplicate_current_conversation()
        
        if st.button("✏️ Rename Chat", use_container_width=True):
            st.session_state.show_rename_dialog = True
        
        # Show rename dialog if requested
        if st.session_state.get('show_rename_dialog', False):
            render_rename_dialog()

def delete_specific_conversation(conv_id: str):
    """Delete a specific conversation from the sidebar."""
    try:
        # Confirm deletion with user
        if f"confirm_delete_{conv_id}" not in st.session_state:
            st.session_state[f"confirm_delete_{conv_id}"] = False
        
        if not st.session_state[f"confirm_delete_{conv_id}"]:
            # First click - ask for confirmation
            st.session_state[f"confirm_delete_{conv_id}"] = True
            st.warning("⚠️ Click delete again to confirm")
            return
        
        # Second click - actually delete
        from utils.conversation_manager import run_async, delete_conversation
        success = run_async(delete_conversation(conv_id))
        
        if success:
            # Remove from session state
            if conv_id in st.session_state.conversations:
                del st.session_state.conversations[conv_id]
            
            # Clean up confirmation state
            del st.session_state[f"confirm_delete_{conv_id}"]
            
            # If this was the current conversation, switch to another or clear
            if st.session_state.get('current_conversation_id') == conv_id:
                remaining_conversations = list(st.session_state.conversations.keys())
                if remaining_conversations:
                    # Switch to the most recent conversation
                    st.session_state.current_conversation_id = remaining_conversations[0]
                    st.session_state.chat_messages = st.session_state.conversations[remaining_conversations[0]].get('messages', [])
                else:
                    # No conversations left
                    st.session_state.current_conversation_id = None
                    st.session_state.chat_messages = []
            
            st.success("✅ Conversation deleted!")
            st.rerun()
        else:
            st.error("❌ Failed to delete conversation")
            st.session_state[f"confirm_delete_{conv_id}"] = False
            
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        st.error(f"❌ Error: {e}")
        if f"confirm_delete_{conv_id}" in st.session_state:
            st.session_state[f"confirm_delete_{conv_id}"] = False

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

# Export functions removed

def render_rename_dialog():
    """Render dialog to rename current conversation."""
    conv_id = st.session_state.get('current_conversation_id')
    if not conv_id:
        st.session_state.show_rename_dialog = False
        return
    
    conversations = st.session_state.get('conversations', {})
    current_title = conversations.get(conv_id, {}).get('title', 'Untitled Chat')
    
    st.markdown("**✏️ Rename Conversation**")
    
    new_title = st.text_input(
        "New title:",
        value=current_title,
        key="rename_input",
        placeholder="Enter new conversation title"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Save", use_container_width=True):
            if new_title and new_title.strip():
                try:
                    from utils.conversation_manager import run_async, update_conversation_title
                    success = run_async(update_conversation_title(conv_id, new_title.strip()))
                    
                    if success:
                        # Update local state
                        st.session_state.conversations[conv_id]['title'] = new_title.strip()
                        st.success("✅ Conversation renamed!")
                        st.session_state.show_rename_dialog = False
                        st.rerun()
                    else:
                        st.error("❌ Failed to rename conversation")
                except Exception as e:
                    logger.error(f"Error renaming conversation: {e}")
                    st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Please enter a valid title")
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_rename_dialog = False
            st.rerun()

# Document processing functions

def process_uploaded_document_multipage(uploaded_file):
    """Process uploaded document and return text content with enhanced support for images and PPTX."""
    try:
        # Read file content
        file_content = uploaded_file.read()
        uploaded_file.seek(0)  # Reset file pointer
        
        # Process based on file type
        if uploaded_file.type == "text/plain" or uploaded_file.name.endswith('.txt'):
            text_content = file_content.decode('utf-8')
            
        elif uploaded_file.name.endswith('.md'):
            text_content = file_content.decode('utf-8')
            
        elif uploaded_file.type == "application/pdf" or uploaded_file.name.endswith('.pdf'):
            try:
                import PyPDF2
                import io
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                text_content = ""
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content += f"\n--- Page {page_num} ---\n{page_text}\n"
                
                if not text_content.strip():
                    text_content = f"[PDF Document: {uploaded_file.name} - {len(file_content)} bytes - No extractable text found]"
                    
            except Exception as pdf_error:
                logger.warning(f"PDF processing failed: {pdf_error}")
                text_content = f"[PDF Document: {uploaded_file.name} - {len(file_content)} bytes - Text extraction failed: {pdf_error}]"
                
        elif uploaded_file.name.endswith('.docx'):
            try:
                import docx2txt
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name
                
                try:
                    text_content = docx2txt.process(tmp_path)
                    if not text_content.strip():
                        # Try alternative method with python-docx
                        try:
                            from docx import Document
                            doc = Document(tmp_path)
                            paragraphs = []
                            for paragraph in doc.paragraphs:
                                if paragraph.text.strip():
                                    paragraphs.append(paragraph.text)
                            text_content = "\n".join(paragraphs)
                        except:
                            raise Exception("No text extracted with any method")
                finally:
                    os.unlink(tmp_path)
                    
            except Exception as docx_error:
                logger.warning(f"DOCX processing failed: {docx_error}")
                text_content = f"[DOCX Document: {uploaded_file.name} - {len(file_content)} bytes - Text extraction failed: {docx_error}]"
                
        elif uploaded_file.name.endswith('.pptx'):
            # Enhanced PPTX processing
            try:
                from pptx import Presentation
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pptx') as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name
                
                try:
                    prs = Presentation(tmp_path)
                    slides_text = []
                    
                    for slide_num, slide in enumerate(prs.slides, 1):
                        slide_content = f"\n--- Slide {slide_num} ---\n"
                        
                        # Extract text from shapes
                        text_found = False
                        for shape in slide.shapes:
                            if hasattr(shape, "text") and shape.text.strip():
                                slide_content += f"{shape.text.strip()}\n"
                                text_found = True
                            
                            # Extract text from tables
                            if hasattr(shape, "table"):
                                table = shape.table
                                for row in table.rows:
                                    row_text = []
                                    for cell in row.cells:
                                        if cell.text.strip():
                                            row_text.append(cell.text.strip())
                                    if row_text:
                                        slide_content += " | ".join(row_text) + "\n"
                                        text_found = True
                        
                        # Extract notes
                        if slide.notes_slide and slide.notes_slide.notes_text_frame:
                            notes_text = slide.notes_slide.notes_text_frame.text.strip()
                            if notes_text:
                                slide_content += f"\nNotes: {notes_text}\n"
                                text_found = True
                        
                        if text_found:
                            slides_text.append(slide_content)
                    
                    text_content = "\n".join(slides_text)
                    
                    if not text_content.strip():
                        text_content = f"[PPTX Document: {uploaded_file.name} - {len(prs.slides)} slides - No extractable text found]"
                        
                finally:
                    os.unlink(tmp_path)
                    
            except Exception as pptx_error:
                logger.warning(f"PPTX processing failed: {pptx_error}")
                text_content = f"[PPTX Document: {uploaded_file.name} - {len(file_content)} bytes - Text extraction failed: {pptx_error}]"
                
        elif (uploaded_file.type and uploaded_file.type.startswith('image/')) or uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')):
            # Enhanced image processing with multiple OCR engines
            try:
                from utils.ocr_manager import process_image_file
                text_content = process_image_file(uploaded_file, file_content)
                
            except Exception as image_error:
                logger.warning(f"Image processing failed: {image_error}")
                # Fallback to basic image info
                try:
                    from PIL import Image
                    import tempfile
                    import os
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                        tmp_file.write(file_content)
                        tmp_path = tmp_file.name
                    
                    try:
                        image = Image.open(tmp_path)
                        image_info = f"Image: {uploaded_file.name}\nSize: {image.size[0]}x{image.size[1]} pixels\nFormat: {image.format}\n\n"
                        text_content = f"{image_info}IMAGE UPLOADED: OCR processing failed. Please describe what you see in the image and I can help explain the pharmacological concepts shown."
                    finally:
                        os.unlink(tmp_path)
                        
                except Exception as fallback_error:
                    text_content = f"[Image: {uploaded_file.name} - {len(file_content)} bytes - Processing failed: {image_error}]"
                
        else:
            text_content = f"[Document: {uploaded_file.name} - {len(file_content)} bytes - Unsupported format. Supported: TXT, MD, PDF, DOCX, PPTX, Images]"
        
        return text_content
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        return f"[Error processing {uploaded_file.name}: {e}]"

def save_document_to_conversation_multipage(uploaded_file, content):
    """Save document to conversation knowledge base with advanced RAG processing."""
    try:
        logger.info(f"Starting document save for: {uploaded_file.name}")
        
        # Check if we have a conversation ID
        if not st.session_state.get('current_conversation_id'):
            logger.error("No current conversation ID found")
            # Create a new conversation if none exists
            try:
                from utils.conversation_manager import run_async, create_new_conversation
                conv_id = run_async(create_new_conversation())
                if not conv_id:
                    logger.error("Failed to create new conversation for document")
                    return False
                st.session_state.current_conversation_id = conv_id
                logger.info(f"Created new conversation for document: {conv_id}")
            except Exception as conv_error:
                logger.error(f"Error creating conversation: {conv_error}")
                return False
        
        conv_id = st.session_state.current_conversation_id
        logger.info(f"Using conversation ID: {conv_id}")
        
        # Check authentication
        if not st.session_state.get('authenticated') or not st.session_state.get('user_id'):
            logger.error("User not authenticated")
            return False
        
        # Save to session state for immediate access
        if 'conversation_documents' not in st.session_state:
            st.session_state.conversation_documents = {}
        
        if conv_id not in st.session_state.conversation_documents:
            st.session_state.conversation_documents[conv_id] = []
        
        # Add document to conversation knowledge base
        try:
            document_info = {
                'filename': uploaded_file.name,
                'content': content,
                'uploaded_at': datetime.now().isoformat(),
                'file_size': len(uploaded_file.getvalue())
            }
            
            st.session_state.conversation_documents[conv_id].append(document_info)
            logger.info(f"Document added to session state: {uploaded_file.name}")
        except Exception as session_error:
            logger.error(f"Error adding document to session state: {session_error}")
            return False
        
        # Try RAG processing (optional - don't fail if this doesn't work)
        try:
            from services.rag_service import RAGService
            from services.user_service import user_service
            from utils.conversation_manager import run_async
            import uuid
            
            logger.info("Starting RAG processing...")
            
            # Get user UUID
            user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
            if user_data:
                rag_service = RAGService()
                document_id = str(uuid.uuid4())
                
                # Always process document for full knowledge base (default behavior)
                success = run_async(rag_service.process_document(
                    content, 
                    document_id, 
                    conv_id, 
                    user_data['id'],
                    metadata={
                        'filename': uploaded_file.name,
                        'file_size': len(uploaded_file.getvalue()),
                        'uploaded_at': datetime.now().isoformat(),
                        'processing_mode': 'full_document_knowledge_base_default'
                    },
                    use_full_document_mode=True  # Explicitly set to True as default
                ))
                
                if success:
                    logger.info(f"✅ Document processed for full knowledge base: {uploaded_file.name}")
                else:
                    logger.warning(f"⚠️ Full document processing failed for: {uploaded_file.name}")
            else:
                logger.warning("User data not found for RAG processing")
            
        except Exception as rag_error:
            logger.warning(f"RAG processing failed (non-critical): {rag_error}")
            # Continue - RAG failure shouldn't prevent document saving
        
        logger.info(f"Document successfully saved to conversation {conv_id}: {uploaded_file.name}")
        return True
        
    except Exception as e:
        logger.error(f"Critical error saving document to conversation: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

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
        
        # Show processing indicator if generating response
        if st.session_state.get('processing_input', False):
            with st.chat_message("assistant"):
                st.markdown("🤔 Thinking...")
                st.caption("Generating response...")
    
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
    # Ensure we have messages to display
    if not st.session_state.get('chat_messages'):
        return
    
    for i, message in enumerate(st.session_state.chat_messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Add timestamp for messages
            if "timestamp" in message:
                try:
                    timestamp = datetime.fromisoformat(message["timestamp"].replace('Z', '+00:00'))
                    st.caption(f"🕒 {timestamp.strftime('%H:%M:%S')}")
                except:
                    st.caption(f"🕒 Message {i+1}")
            
            # Add regenerate button for the last assistant message
            if (message["role"] == "assistant" and 
                i == len(st.session_state.chat_messages) - 1 and 
                i > 0 and 
                not st.session_state.get('processing_input', False)):  # Don't show during processing
                
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
    if st.session_state.get('processing_input', False):
        st.warning("⚠️ Please wait for the current response to complete.")
        return
    
    if message_index > 0 and st.session_state.chat_messages[message_index-1]["role"] == "user":
        user_prompt = st.session_state.chat_messages[message_index-1]["content"]
        
        # Remove the current assistant response
        st.session_state.chat_messages.pop()
        
        # Process the regeneration
        process_chat_input(user_prompt)

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
    
    # Chat input with processing state check
    if st.session_state.get('processing_input', False):
        st.info("🤔 Generating response... Please wait.")
        # Disable input during processing
        st.chat_input("Generating response...", disabled=True)
    else:
        prompt = st.chat_input("Ask me anything about pharmacology...")
        
        # Handle example prompts
        if st.session_state.get('example_prompt'):
            prompt = st.session_state.example_prompt
            st.session_state.example_prompt = None
        
        # Process chat input
        if prompt and not st.session_state.get('processing_input', False):
            process_chat_input(prompt)

def render_document_upload():
    """Render enhanced document upload area."""
    with st.expander("📎 Upload Documents (PDF, DOCX, Images)", expanded=False):
        st.info("📷 **Image OCR**: Only text content will be extracted from images for processing. Charts, graphs, and visual elements will not be analyzed.")
        uploaded_file = st.file_uploader(
            "Choose files to enhance your conversation",
            type=['txt', 'pdf', 'docx', 'md', 'pptx', 'png', 'jpg', 'jpeg'],
            help="Upload documents, presentations, or images for context-aware responses",
            key=f"doc_upload_{st.session_state.get('current_conversation_id', 'new')}"
        )
        
        if uploaded_file is not None:
            # Check file size limit
            file_size_mb = uploaded_file.size / (1024 * 1024)
            if file_size_mb > MAX_FILE_SIZE_MB:
                st.error(f"❌ File too large! Maximum size allowed is {MAX_FILE_SIZE_MB}MB. Your file is {file_size_mb:.1f}MB.")
                return
            
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
                    # Remove document and mark for cleanup
                    documents.pop(i)
                    
                    # Clean up processing flags for this document
                    file_key = f"{doc['filename']}_{doc.get('file_size', 0)}_{conv_id}"
                    if f'processed_doc_{file_key}' in st.session_state:
                        del st.session_state[f'processed_doc_{file_key}']
                    if f'processing_doc_{file_key}' in st.session_state:
                        del st.session_state[f'processing_doc_{file_key}']
                    
                    st.success(f"✅ Removed {doc['filename']}")
                    st.rerun()

def process_document_upload(uploaded_file):
    """Process uploaded document with enhanced features."""
    logger.info(f"Starting document upload process for: {uploaded_file.name}")
    
    # Check if this file has already been processed to prevent loops
    file_key = f"{uploaded_file.name}_{uploaded_file.size}_{st.session_state.get('current_conversation_id', 'new')}"
    
    if st.session_state.get(f'processed_doc_{file_key}', False):
        logger.info(f"Document already processed: {uploaded_file.name}")
        return  # Already processed, don't process again
    
    # Mark as being processed
    st.session_state[f'processing_doc_{file_key}'] = True
    
    with st.spinner(f"Processing {uploaded_file.name}..."):
        try:
            logger.info(f"Processing document content for: {uploaded_file.name}")
            
            # Process the document directly (no import needed)
            content = process_uploaded_document_multipage(uploaded_file)
            
            if content:
                logger.info(f"Document content extracted: {len(content)} characters")
                
                # Save to conversation
                success = save_document_to_conversation_multipage(uploaded_file, content)
                
                if success:
                    # Mark as successfully processed
                    st.session_state[f'processed_doc_{file_key}'] = True
                    st.session_state[f'processing_doc_{file_key}'] = False
                    
                    st.success(f"✅ Document processed: {uploaded_file.name}")
                    st.info(f"📄 Extracted {len(content)} characters of content")
                    
                    logger.info(f"Document successfully processed and saved: {uploaded_file.name}")
                    
                    # Don't call st.rerun() here - let the natural flow handle it
                else:
                    logger.error(f"Failed to save document: {uploaded_file.name}")
                    st.error("❌ Failed to save document - check logs for details")
                    st.session_state[f'processing_doc_{file_key}'] = False
            else:
                logger.error(f"Failed to extract content from document: {uploaded_file.name}")
                st.error("❌ Failed to process document - no content extracted")
                st.session_state[f'processing_doc_{file_key}'] = False
                
        except Exception as e:
            logger.error(f"Document upload error for {uploaded_file.name}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            st.error(f"❌ Error processing document: {str(e)}")
            st.session_state[f'processing_doc_{file_key}'] = False

def process_chat_input(prompt):
    """Process chat input with enhanced features."""
    logger.info(f"Processing user input: {prompt[:50]}...")
    
    # Prevent duplicate processing
    if st.session_state.get('processing_input', False):
        return
    
    st.session_state.processing_input = True
    
    try:
        # Add user message to session state first
        user_message = {
            "role": "user", 
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.chat_messages.append(user_message)
        
        # Generate assistant response
        try:
            # Generate response with enhanced context
            full_response = generate_enhanced_response(prompt)
            
            # Add assistant message to chat history
            assistant_message = {
                "role": "assistant", 
                "content": full_response,
                "timestamp": datetime.now().isoformat()
            }
            st.session_state.chat_messages.append(assistant_message)
            
            # Save conversation to database
            save_conversation_to_database()
            
            logger.info(f"Response generated and saved: {len(full_response)} characters")
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            error_message = f"Sorry, I encountered an error: {str(e)}"
            
            # Add error message to chat history
            st.session_state.chat_messages.append({
                "role": "assistant", 
                "content": error_message,
                "timestamp": datetime.now().isoformat()
            })
    
    finally:
        # Always reset processing flag
        st.session_state.processing_input = False
        
        # Force a rerun to display the new messages
        st.rerun()

def generate_enhanced_response(prompt):
    """Generate enhanced AI response with document context."""
    try:
        # Import AI functions
        from openai_client import chat_completion, get_available_model_modes
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
        if document_context and is_useful_document_context(document_context):
            enhanced_system_prompt += f"\n\n--- DOCUMENT CONTEXT ---\n{document_context}\n\nIMPORTANT: Use the above document context to enhance your pharmacology responses when relevant. If the documents contain error messages or are not related to pharmacology, focus on providing expert pharmacology knowledge based on the user's question instead."
        
        # Prepare messages for API (exclude the current user message to avoid duplication)
        api_messages = [{"role": "system", "content": enhanced_system_prompt}]
        
        # Add recent conversation history (last 8 messages, excluding the just-added user message)
        recent_messages = st.session_state.chat_messages[:-1][-8:]  # Exclude the last message (current user input)
        for msg in recent_messages:
            api_messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add the current user message
        api_messages.append({"role": "user", "content": prompt})
        
        # Generate the response (non-streaming for stability)
        full_response = chat_completion(model, api_messages)
        
        logger.info(f"Generated response: {len(full_response)} characters")
        return full_response
        
    except Exception as e:
        logger.error(f"Error in generate_enhanced_response: {e}")
        return f"Sorry, I encountered an error: {str(e)}"

def is_useful_document_context(context):
    """Check if document context is useful and not just error messages."""
    if not context or len(context.strip()) < 50:
        return False
    
    # Check for common error indicators
    error_indicators = [
        "OCR not available",
        "OCR failed",
        "Text extraction failed",
        "No extractable text found",
        "Processing failed",
        "install pytesseract",
        "Unsupported format",
        "text extraction is not available",
        "Please describe what you see"
    ]
    
    # If context is mostly error messages, it's not useful
    error_count = sum(1 for indicator in error_indicators if indicator.lower() in context.lower())
    
    # If more than 1 error indicator or context is very short, consider it not useful
    if error_count > 1 or len(context.strip()) < 100:
        return False
    
    return True

def clean_document_content(content):
    """Clean document content to remove unhelpful error messages."""
    if not content:
        return content
    
    # Remove common error message patterns
    error_patterns = [
        r"\[.*?OCR not available.*?\]",
        r"\[.*?OCR failed.*?\]",
        r"\[.*?Text extraction failed.*?\]",
        r"\[.*?install pytesseract.*?\]",
        r"\[.*?Processing failed.*?\]"
    ]
    
    import re
    cleaned_content = content
    for pattern in error_patterns:
        cleaned_content = re.sub(pattern, "", cleaned_content, flags=re.IGNORECASE | re.DOTALL)
    
    # Clean up extra whitespace
    cleaned_content = re.sub(r'\n\s*\n', '\n\n', cleaned_content.strip())
    
    return cleaned_content

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
                useful_docs = 0
                
                for doc in documents:
                    content = doc['content']
                    
                    # Filter out documents that are mostly error messages
                    if is_useful_document_context(content):
                        # Limit content length and clean it
                        clean_content = clean_document_content(content[:2000])
                        context += f"\n[Document: {doc['filename']}]\n{clean_content}\n"
                        useful_docs += 1
                    else:
                        # For non-useful documents (like failed OCR), provide basic info
                        context += f"\n[Document: {doc['filename']} - Visual content uploaded but text not extractable]\n"
                
                if useful_docs > 0:
                    return context
                else:
                    # No useful document content, return empty to avoid confusing the AI
                    return ""
        
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
            logger.warning("Cannot save conversation: user not authenticated")
            return False
        
        if not st.session_state.chat_messages:
            logger.info("No messages to save")
            return True
        
        # Import services
        from services.conversation_service import conversation_service
        from services.user_service import user_service
        
        # Get user UUID
        user_data = run_async_operation(user_service.get_user_by_id(st.session_state.user_id))
        if not user_data:
            logger.error("User data not found")
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
            logger.info(f"Created new conversation: {conversation_id}")
        
        # Update conversation with current messages
        success = run_async_operation(conversation_service.update_conversation(
            user_data['id'],
            st.session_state.current_conversation_id,
            {'messages': st.session_state.chat_messages}
        ))
        
        if success:
            # Update local conversations cache
            if 'conversations' not in st.session_state:
                st.session_state.conversations = {}
            
            st.session_state.conversations[st.session_state.current_conversation_id] = {
                'title': generate_conversation_title(),
                'messages': st.session_state.chat_messages.copy(),
                'updated_at': datetime.now().isoformat(),
                'model': st.session_state.get('selected_model_mode', 'normal'),
                'message_count': len(st.session_state.chat_messages)
            }
            
            logger.info(f"Conversation saved successfully: {len(st.session_state.chat_messages)} messages")
            return True
        else:
            logger.error("Failed to save conversation to database")
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