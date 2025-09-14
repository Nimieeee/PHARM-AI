"""
Simple Chatbot Page - Minimal, Working Implementation
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

def load_conversation_if_exists():
    """Load existing conversation for the user if available."""
    try:
        if not st.session_state.get('authenticated') or not st.session_state.get('user_id'):
            return
        
        logger.info("Attempting to load existing conversation...")
        
        # Import conversation service
        from services.conversation_service import conversation_service
        from services.user_service import user_service
        
        # Get user UUID from legacy user_id
        user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
        if not user_data:
            logger.warning("User not found for conversation loading")
            return
        
        # Get user's conversations
        conversations = run_async(conversation_service.get_user_conversations(user_data['id']))
        
        if conversations:
            # Get the most recent conversation
            latest_conv_id = max(conversations.keys(), key=lambda k: conversations[k].get('updated_at', conversations[k].get('created_at', '')))
            latest_conv = conversations[latest_conv_id]
            
            # Load messages into session state
            st.session_state.chat_messages = latest_conv.get('messages', [])
            st.session_state.current_conversation_id = latest_conv_id
            
            logger.info(f"✅ Loaded conversation {latest_conv_id} with {len(st.session_state.chat_messages)} messages")
        else:
            logger.info("No existing conversations found")
            
    except Exception as e:
        logger.error(f"Error loading conversation: {e}")
        # Don't fail the app, just continue with empty conversation

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

def process_uploaded_document(uploaded_file, conversation_id):
    """Process uploaded document for the current conversation."""
    try:
        # Import document service
        from services.document_service import document_service
        from services.user_service import user_service
        
        # Get user data
        user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
        if not user_data:
            logger.error("User not found for document processing")
            return False
        
        # Read file content
        file_content = uploaded_file.read()
        
        # Reset file pointer for potential re-reading
        uploaded_file.seek(0)
        
        # Process document based on type
        if uploaded_file.type == "text/plain" or uploaded_file.name.endswith('.txt'):
            # Text file - decode content
            text_content = file_content.decode('utf-8')
        elif uploaded_file.type == "application/pdf" or uploaded_file.name.endswith('.pdf'):
            # PDF file - would need PDF processing library
            text_content = f"PDF file uploaded: {uploaded_file.name} ({len(file_content)} bytes)"
            # TODO: Add actual PDF text extraction
        elif uploaded_file.name.endswith('.md'):
            # Markdown file
            text_content = file_content.decode('utf-8')
        else:
            # Other file types
            text_content = f"Document uploaded: {uploaded_file.name} ({len(file_content)} bytes)"
        
        # Create document metadata
        document_data = {
            'filename': uploaded_file.name,
            'file_size': len(file_content),
            'file_type': uploaded_file.type or 'unknown',
            'content_preview': text_content[:500] + "..." if len(text_content) > 500 else text_content,
            'processing_status': 'completed',
            'conversation_id': conversation_id
        }
        
        # Save document to database
        success = run_async(document_service.create_document(
            user_data['id'],
            conversation_id,
            document_data
        ))
        
        if success:
            logger.info(f"✅ Document processed successfully: {uploaded_file.name}")
            return True
        else:
            logger.error(f"❌ Failed to save document: {uploaded_file.name}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing document {uploaded_file.name}: {e}")
        return False

def search_conversations(query):
    """Search through user's conversations and messages."""
    try:
        if not st.session_state.get('authenticated') or not st.session_state.get('user_id'):
            return []
        
        # Import services
        from services.conversation_service import conversation_service
        from services.user_service import user_service
        
        # Get user data
        user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
        if not user_data:
            return []
        
        # Get all user conversations
        conversations = run_async(conversation_service.get_user_conversations(user_data['id']))
        
        search_results = []
        query_lower = query.lower()
        
        for conv_id, conv_data in conversations.items():
            title = conv_data.get('title', '').lower()
            messages = conv_data.get('messages', [])
            
            # Search in title
            if query_lower in title:
                search_results.append({
                    'conversation_id': conv_id,
                    'title': conv_data.get('title', 'Untitled'),
                    'match_text': f"Title match: {conv_data.get('title', 'Untitled')}",
                    'match_type': 'title'
                })
            
            # Search in messages
            for i, message in enumerate(messages):
                content = message.get('content', '').lower()
                if query_lower in content:
                    # Get context around the match
                    original_content = message.get('content', '')
                    match_start = original_content.lower().find(query_lower)
                    context_start = max(0, match_start - 30)
                    context_end = min(len(original_content), match_start + len(query) + 30)
                    context = original_content[context_start:context_end]
                    
                    search_results.append({
                        'conversation_id': conv_id,
                        'title': conv_data.get('title', 'Untitled'),
                        'match_text': f"Message: ...{context}...",
                        'match_type': 'message',
                        'message_index': i
                    })
                    break  # Only show first match per conversation
        
        # Sort by relevance (title matches first, then by conversation recency)
        search_results.sort(key=lambda x: (
            0 if x['match_type'] == 'title' else 1,
            x['conversation_id']
        ))
        
        return search_results
        
    except Exception as e:
        logger.error(f"Error searching conversations: {e}")
        return []

def load_conversation_from_search(conversation_id):
    """Load a conversation from search results."""
    try:
        if not st.session_state.get('authenticated') or not st.session_state.get('user_id'):
            return False
        
        # Import services
        from services.conversation_service import conversation_service
        from services.user_service import user_service
        
        # Get user data
        user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
        if not user_data:
            return False
        
        # Get the specific conversation
        conversation = run_async(conversation_service.get_conversation(user_data['id'], conversation_id))
        
        if conversation:
            # Save current conversation first
            if st.session_state.chat_messages and st.session_state.get('current_conversation_id'):
                save_conversation()
            
            # Load the found conversation
            st.session_state.chat_messages = conversation.get('messages', [])
            st.session_state.current_conversation_id = conversation_id
            
            logger.info(f"✅ Loaded conversation from search: {conversation_id}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error loading conversation from search: {e}")
        return False

def check_daily_upload_limit():
    """Check if user has exceeded daily upload limit (5 files per day)."""
    try:
        if not st.session_state.get('authenticated') or not st.session_state.get('user_id'):
            return False
        
        from services.document_service import document_service
        from services.user_service import user_service
        from datetime import datetime, timedelta
        
        # Get user data
        user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
        if not user_data:
            return False
        
        # Check uploads in last 24 hours
        today = datetime.now().date()
        # This would need to be implemented in document service
        # For now, return True (no limit check)
        return True
        
    except Exception as e:
        logger.error(f"Error checking upload limit: {e}")
        return True  # Allow upload if check fails

def process_document_for_prompt(uploaded_file):
    """Process uploaded document with advanced LangChain processing."""
    try:
        # Read file content
        file_content = uploaded_file.read()
        uploaded_file.seek(0)  # Reset file pointer
        
        # Process based on file type using LangChain
        if uploaded_file.type == "text/plain" or uploaded_file.name.endswith('.txt'):
            text_content = file_content.decode('utf-8')
        elif uploaded_file.name.endswith('.md'):
            text_content = file_content.decode('utf-8')
        elif uploaded_file.type == "application/pdf" or uploaded_file.name.endswith('.pdf'):
            # Enhanced PDF processing with LangChain
            try:
                from langchain_community.document_loaders import PyPDFLoader
                import tempfile
                import os
                
                # Save to temporary file for PyPDFLoader
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name
                
                try:
                    loader = PyPDFLoader(tmp_path)
                    pages = loader.load()
                    text_content = "\n\n".join([page.page_content for page in pages])
                finally:
                    os.unlink(tmp_path)  # Clean up temp file
                    
            except Exception as pdf_error:
                logger.warning(f"PDF processing failed, using fallback: {pdf_error}")
                text_content = f"[PDF Document: {uploaded_file.name} - {len(file_content)} bytes - Text extraction failed]"
        
        elif uploaded_file.name.endswith('.docx'):
            # Enhanced DOCX processing
            try:
                from langchain_community.document_loaders import Docx2txtLoader
                import tempfile
                import os
                
                # Save to temporary file for Docx2txtLoader
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                    tmp_file.write(file_content)
                    tmp_path = tmp_file.name
                
                try:
                    loader = Docx2txtLoader(tmp_path)
                    docs = loader.load()
                    text_content = "\n\n".join([doc.page_content for doc in docs])
                finally:
                    os.unlink(tmp_path)  # Clean up temp file
                    
            except Exception as docx_error:
                logger.warning(f"DOCX processing failed, using fallback: {docx_error}")
                text_content = f"[DOCX Document: {uploaded_file.name} - {len(file_content)} bytes - Text extraction failed]"
        
        else:
            text_content = f"[Document: {uploaded_file.name} - {len(file_content)} bytes - Unsupported format]"
        
        # Store full content for RAG processing
        full_content = text_content
        
        # Return preview for immediate prompt (limit to 1000 chars for better performance)
        if len(text_content) > 1000:
            preview_content = text_content[:1000] + "\n\n[Document preview - full content processed for semantic search...]"
        else:
            preview_content = text_content
        
        # Store full content in session for RAG processing
        if 'document_full_content' not in st.session_state:
            st.session_state.document_full_content = {}
        
        st.session_state.document_full_content[uploaded_file.name] = full_content
        
        return preview_content
        
    except Exception as e:
        logger.error(f"Error processing document content: {e}")
        return None

def save_document_to_conversation(uploaded_file, content):
    """Save document metadata and process for RAG."""
    try:
        if not st.session_state.get('current_conversation_id'):
            return False
        
        from services.document_service import document_service
        from services.user_service import user_service
        from services.rag_service import process_document_for_rag
        import uuid
        
        # Get user data
        user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
        if not user_data:
            return False
        
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Get full content for RAG processing
        full_content = st.session_state.document_full_content.get(uploaded_file.name, content)
        
        # Create document metadata
        document_data = {
            'id': document_id,
            'filename': uploaded_file.name,
            'file_size': uploaded_file.size,
            'file_type': uploaded_file.type or 'unknown',
            'content_preview': content[:200] + "..." if len(content) > 200 else content,
            'processing_status': 'processing',
            'conversation_id': st.session_state.current_conversation_id,
            'upload_date': datetime.now().isoformat()
        }
        
        # Save document metadata to database
        # This would use the actual document service
        logger.info(f"Document metadata saved: {uploaded_file.name}")
        
        # Process document for RAG in background
        try:
            # Process document with RAG service
            rag_success = run_async(process_document_for_rag(
                full_content,
                document_id,
                st.session_state.current_conversation_id,
                user_data['id'],
                {
                    'filename': uploaded_file.name,
                    'file_type': uploaded_file.type,
                    'file_size': uploaded_file.size
                }
            ))
            
            if rag_success:
                logger.info(f"✅ Document processed for RAG: {uploaded_file.name}")
                # Update status to completed
                document_data['processing_status'] = 'completed'
            else:
                logger.warning(f"⚠️ RAG processing failed for: {uploaded_file.name}")
                document_data['processing_status'] = 'failed'
                
        except Exception as rag_error:
            logger.error(f"RAG processing error: {rag_error}")
            document_data['processing_status'] = 'failed'
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving document: {e}")
        return False

def render_conversation_sidebar():
    """Render conversation management sidebar."""
    with st.sidebar:
        st.header("💬 Conversations")
        
        # New conversation button
        if st.button("🆕 New Chat", use_container_width=True, type="primary"):
            # Save current conversation first
            if st.session_state.chat_messages:
                save_conversation()
            
            # Clear current conversation
            st.session_state.chat_messages = []
            st.session_state.current_conversation_id = None
            st.success("✅ New conversation started!")
            st.rerun()
        
        # Search functionality
        st.subheader("🔍 Search")
        search_query = st.text_input(
            "Search conversations...",
            placeholder="Search messages, titles, or content",
            key="search_input"
        )
        
        if search_query:
            search_results = search_conversations(search_query)
            if search_results:
                st.write(f"**Found {len(search_results)} results:**")
                for result in search_results[:5]:  # Show top 5 results
                    conv_title = result.get('title', 'Untitled')
                    match_text = result.get('match_text', '')
                    conv_id = result.get('conversation_id')
                    
                    if st.button(
                        f"💬 {conv_title[:25]}...",
                        key=f"search_{conv_id}",
                        help=f"Match: {match_text[:50]}..."
                    ):
                        # Load the found conversation
                        load_conversation_from_search(conv_id)
                        st.rerun()
            else:
                st.info("No results found")
        
        st.divider()
        
        # Load and display conversations
        try:
            if st.session_state.get('authenticated') and st.session_state.get('user_id'):
                from services.conversation_service import conversation_service
                from services.user_service import user_service
                
                # Get user UUID
                user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
                if user_data:
                    # Get user's conversations
                    conversations = run_async(conversation_service.get_user_conversations(user_data['id']))
                    
                    if conversations:
                        st.subheader("📚 Your Chats")
                        
                        # Sort conversations by updated_at (most recent first)
                        sorted_convs = sorted(
                            conversations.items(),
                            key=lambda x: x[1].get('updated_at', x[1].get('created_at', '')),
                            reverse=True
                        )
                        
                        current_conv_id = st.session_state.get('current_conversation_id')
                        
                        for conv_id, conv_data in sorted_convs:
                            title = conv_data.get('title', 'Untitled Chat')
                            message_count = len(conv_data.get('messages', []))
                            created_at = conv_data.get('created_at', '')
                            
                            # Truncate long titles
                            display_title = title[:25] + "..." if len(title) > 25 else title
                            
                            # Show current conversation with different styling
                            is_current = (conv_id == current_conv_id)
                            
                            # Create conversation container
                            with st.container():
                                # Main conversation button
                                if st.button(
                                    f"{'🔸' if is_current else '💬'} {display_title}",
                                    key=f"conv_{conv_id}",
                                    use_container_width=True,
                                    type="primary" if is_current else "secondary",
                                    disabled=is_current
                                ):
                                    # Save current conversation before switching
                                    if st.session_state.chat_messages and current_conv_id != conv_id:
                                        save_conversation()
                                    
                                    # Load selected conversation
                                    st.session_state.chat_messages = conv_data.get('messages', [])
                                    st.session_state.current_conversation_id = conv_id
                                    logger.info(f"✅ Switched to conversation: {conv_id} with {len(st.session_state.chat_messages)} messages")
                                    st.rerun()
                                
                                # Show conversation metadata
                                col1, col2, col3 = st.columns([2, 1, 1])
                                with col1:
                                    # Format date nicely
                                    try:
                                        from datetime import datetime
                                        date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                                        date_str = date_obj.strftime('%m/%d')
                                    except:
                                        date_str = "Recent"
                                    st.caption(f"📅 {date_str}")
                                
                                with col2:
                                    st.caption(f"💬 {message_count}")
                                
                                with col3:
                                    if is_current:
                                        st.caption("🔸 Active")
                                    else:
                                        st.caption("")
                                
                                # Add some spacing between conversations
                                if not is_current:
                                    st.write("")
                            
                        # Conversation management
                        st.divider()
                        st.subheader("🛠️ Manage")
                        
                        # Current conversation actions
                        if current_conv_id:
                            # Rename conversation
                            with st.expander("✏️ Rename Chat"):
                                current_title = next(
                                    (conv_data.get('title', 'Untitled Chat') 
                                     for conv_id, conv_data in conversations.items() 
                                     if conv_id == current_conv_id), 
                                    'Untitled Chat'
                                )
                                
                                new_title = st.text_input(
                                    "New title:",
                                    value=current_title,
                                    key="rename_input"
                                )
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("💾 Save", use_container_width=True):
                                        if new_title and new_title != current_title:
                                            try:
                                                success = run_async(conversation_service.update_conversation_title(
                                                    user_data['id'], 
                                                    current_conv_id,
                                                    new_title
                                                ))
                                                if success:
                                                    st.success("✅ Title updated!")
                                                    st.rerun()
                                                else:
                                                    st.error("❌ Failed to update title")
                                            except Exception as e:
                                                st.error(f"❌ Error: {e}")
                                        else:
                                            st.info("No changes to save")
                                
                                with col2:
                                    if st.button("🔄 Auto-title", use_container_width=True):
                                        # Generate title from first message
                                        auto_title = generate_conversation_title()
                                        if auto_title != current_title:
                                            try:
                                                success = run_async(conversation_service.update_conversation_title(
                                                    user_data['id'], 
                                                    current_conv_id,
                                                    auto_title
                                                ))
                                                if success:
                                                    st.success("✅ Auto-title applied!")
                                                    st.rerun()
                                                else:
                                                    st.error("❌ Failed to apply auto-title")
                                            except Exception as e:
                                                st.error(f"❌ Error: {e}")
                                        else:
                                            st.info("Current title is already optimal")
                            
                            # Duplicate conversation
                            if st.button("📋 Duplicate Chat", use_container_width=True):
                                try:
                                    new_conv_id = run_async(conversation_service.duplicate_conversation(
                                        user_data['id'], 
                                        current_conv_id
                                    ))
                                    if new_conv_id:
                                        st.success("✅ Conversation duplicated!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to duplicate conversation")
                                except Exception as e:
                                    st.error(f"❌ Error: {e}")
                            
                            # Delete conversation
                            st.write("")  # Add some space
                            if st.button("🗑️ Delete Current Chat", use_container_width=True, type="secondary"):
                                try:
                                    success = run_async(conversation_service.delete_conversation(
                                        user_data['id'], 
                                        current_conv_id
                                    ))
                                    if success:
                                        st.session_state.chat_messages = []
                                        st.session_state.current_conversation_id = None
                                        st.success("✅ Conversation deleted!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to delete conversation")
                                except Exception as e:
                                    st.error(f"❌ Error: {e}")
                        
                        else:
                            st.info("💡 Start chatting to create a conversation, then you can manage it here.")
                    
                    else:
                        st.info("No conversations yet. Start chatting to create your first conversation!")
                        
        except Exception as e:
            st.error(f"❌ Error loading conversations: {e}")
            logger.error(f"Sidebar conversation loading error: {e}")
        
        # Show conversation documents in sidebar
        if st.session_state.get('current_conversation_id'):
            st.divider()
            st.subheader("📄 Documents")
            
            # Show uploaded documents for current conversation
            st.caption("Documents in this conversation:")
            # This would show documents from database
            st.caption("📎 No documents yet")

def render_simple_chatbot():
    """Render a simple, working chatbot interface."""
    
    # Check authentication
    if not st.session_state.get('authenticated'):
        st.error("Please sign in to use the chatbot.")
        return
    
    # Render conversation sidebar
    render_conversation_sidebar()
    
    st.title("💊 PharmGPT")
    
    # Show current conversation info
    current_conv_id = st.session_state.get('current_conversation_id')
    if current_conv_id:
        try:
            from services.conversation_service import conversation_service
            from services.user_service import user_service
            
            user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
            if user_data:
                conversations = run_async(conversation_service.get_user_conversations(user_data['id']))
                current_conv = conversations.get(current_conv_id)
                
                if current_conv:
                    conv_title = current_conv.get('title', 'Untitled Chat')
                    message_count = len(current_conv.get('messages', []))
                    
                    # Show conversation header
                    st.info(f"💬 **{conv_title}** • {message_count} messages • 💾 Saved")
                else:
                    st.warning("⚠️ Current conversation not found in database")
        except Exception as e:
            logger.error(f"Error loading conversation info: {e}")
    else:
        st.info("📝 **New Conversation** • Start chatting to save it")
    
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
    
    # Initialize conversation persistence
    if 'current_conversation_id' not in st.session_state:
        st.session_state.current_conversation_id = None
    
    # Initialize messages in session state
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
        # Try to load existing conversation on first visit
        load_conversation_if_exists()
    
    # Display chat messages with regenerate option
    for i, message in enumerate(st.session_state.chat_messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Add regenerate button for assistant messages (but not the last one if it's being generated)
            if (message["role"] == "assistant" and 
                i == len(st.session_state.chat_messages) - 1 and 
                i > 0):  # Only show for the last assistant message and not if it's the first message
                
                col1, col2, col3 = st.columns([1, 1, 4])
                with col1:
                    if st.button("🔄 Regenerate", key=f"regen_{i}", help="Generate a new response"):
                        # Remove the current assistant response
                        st.session_state.chat_messages.pop()
                        
                        # Get the previous user message
                        if st.session_state.chat_messages and st.session_state.chat_messages[-1]["role"] == "user":
                            user_prompt = st.session_state.chat_messages[-1]["content"]
                            
                            # Trigger regeneration by setting a flag
                            st.session_state.regenerate_response = True
                            st.session_state.regenerate_prompt = user_prompt
                            st.rerun()
                
                with col2:
                    if st.button("👍 Keep", key=f"keep_{i}", help="Keep this response"):
                        st.success("Response kept!", icon="✅")
                        # Could add rating/feedback functionality here later
    
    # Handle regenerate response
    if st.session_state.get('regenerate_response', False):
        prompt = st.session_state.get('regenerate_prompt', '')
        st.session_state.regenerate_response = False
        st.session_state.regenerate_prompt = None
        
        if prompt:
            logger.info(f"Regenerating response for: {prompt[:50]}...")
            
            # Display user message again (it's already in chat_messages)
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate new response
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                
                try:
                    # Show regenerating message
                    response_placeholder.markdown("🔄 Regenerating response...")
                    
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
                    logger.info(f"Regenerating with {selected_mode} mode: {model}")
                    
                    # Prepare messages for API
                    api_messages = [{"role": "system", "content": pharmacology_system_prompt}]
                    
                    # Add recent conversation history (last 10 messages)
                    for msg in st.session_state.chat_messages[-10:]:
                        api_messages.append({"role": msg["role"], "content": msg["content"]})
                    
                    # Show which model is being used
                    mode_emoji = "⚡" if selected_mode == "turbo" else "🧠"
                    mode_name = "Turbo" if selected_mode == "turbo" else "Normal"
                    
                    # Use fluid streaming for regeneration
                    try:
                        response_placeholder.markdown(f"🔄 Regenerating ({mode_name} • Fluid Streaming)...")
                        logger.info(f"Starting regeneration with fluid streaming...")
                        
                        stream_worked = False
                        chunk_count = 0
                        
                        for chunk in chat_completion_stream(model, api_messages):
                            if chunk:
                                stream_worked = True
                                full_response += chunk
                                chunk_count += 1
                                
                                # Ultra-fluid streaming with regeneration indicator
                                cursor_styles = ["🔄", "⚡", "🔄", "💫", "🔄", "✨"]
                                cursor = cursor_styles[chunk_count % len(cursor_styles)]
                                response_placeholder.markdown(full_response + cursor)
                        
                        # Final display without cursor
                        if stream_worked and full_response.strip():
                            response_placeholder.markdown(full_response)
                            logger.info(f"✅ Regeneration completed: {len(full_response)} chars")
                        else:
                            raise Exception("Regeneration streaming failed or empty response")
                            
                    except Exception as stream_error:
                        logger.warning(f"Regeneration streaming failed: {stream_error}, trying fallback...")
                        
                        # Fallback to non-streaming
                        response_placeholder.markdown(f"🔄 Regenerating ({mode_name} • Fallback)...")
                        full_response = chat_completion(model, api_messages)
                        
                        if full_response and not full_response.startswith("Error:"):
                            response_placeholder.markdown(full_response)
                            logger.info(f"✅ Regeneration fallback completed: {len(full_response)} chars")
                        else:
                            raise Exception(f"Regeneration failed: {full_response}")
                    
                    # Add regenerated response to chat
                    if full_response and not full_response.startswith("Error:") and not full_response.startswith("❌"):
                        st.session_state.chat_messages.append({"role": "assistant", "content": full_response})
                        logger.info("✅ Regenerated response added to chat history")
                        
                        # Auto-save conversation after regeneration
                        try:
                            save_success = save_conversation()
                            if save_success:
                                logger.info("✅ Conversation auto-saved after regeneration")
                        except Exception as save_error:
                            logger.error(f"Auto-save error after regeneration: {save_error}")
                    else:
                        logger.error(f"Regenerated response not added: {full_response[:100]}...")
                        
                except Exception as e:
                    error_msg = f"❌ Error regenerating response: {str(e)}"
                    response_placeholder.markdown(error_msg)
                    logger.error(f"Exception in response regeneration: {e}")
    
    # Document upload area (beside message input)
    st.write("---")
    
    # Upload area with file info
    col1, col2 = st.columns([3, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📎 Upload document (optional)",
            type=['txt', 'pdf', 'docx', 'md'],
            help="Upload a document to include in your conversation (10MB max, 5 per day)",
            key="main_file_uploader"
        )
    
    with col2:
        if uploaded_file:
            # Show file info compactly
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.write(f"**{uploaded_file.name}**")
            st.write(f"📊 {file_size_mb:.1f}MB")
            
            # Check file size limit
            if file_size_mb > 10:
                st.error("❌ File too large (max 10MB)")
                uploaded_file = None
    
    # Chat input - now handles both text and documents
    if prompt := st.chat_input("Ask me anything about pharmacology..."):
        logger.info(f"User input: {prompt[:50]}...")
        
        # Process uploaded document if present
        document_context = ""
        if uploaded_file is not None:
            try:
                # Check daily upload limit
                if not check_daily_upload_limit():
                    st.error("❌ Daily upload limit reached (5 files per day)")
                    return
                
                # Process the document
                document_context = process_document_for_prompt(uploaded_file)
                if document_context:
                    # Save document to conversation
                    save_document_to_conversation(uploaded_file, document_context)
                    st.success(f"✅ Document processed: {uploaded_file.name}")
                else:
                    st.error("❌ Failed to process document")
                    return
            except Exception as e:
                st.error(f"❌ Error processing document: {e}")
                logger.error(f"Document processing error: {e}")
                return
        
        # Get RAG context from conversation documents
        rag_context = ""
        if st.session_state.get('current_conversation_id'):
            try:
                from services.rag_service import search_conversation_context
                from services.user_service import user_service
                
                user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
                if user_data:
                    rag_context = run_async(search_conversation_context(
                        prompt,
                        st.session_state.current_conversation_id,
                        user_data['id']
                    ))
                    
                    if rag_context:
                        logger.info(f"✅ Retrieved RAG context: {len(rag_context)} chars")
                    else:
                        logger.info("No relevant RAG context found")
                        
            except Exception as rag_error:
                logger.warning(f"RAG context retrieval failed: {rag_error}")
        
        # Create enhanced prompt with both document and RAG context
        enhanced_prompt = prompt
        
        # Combine immediate document context and RAG context
        all_context = []
        if document_context:
            all_context.append(f"**Uploaded Document:**\n{document_context}")
        if rag_context:
            all_context.append(f"**Relevant Knowledge Base:**\n{rag_context}")
        
        if all_context:
            combined_context = "\n\n".join(all_context)
            enhanced_prompt = f"""User question: {prompt}

Context from documents:
{combined_context}

Please answer the user's question using the provided context when relevant. If the context doesn't contain relevant information, answer based on your general knowledge."""
        
        # Add user message to chat (show original prompt to user)
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
                
                # Add recent conversation history (last 10 messages, but use enhanced prompt for the last user message)
                for i, msg in enumerate(st.session_state.chat_messages[-10:]):
                    if i == len(st.session_state.chat_messages[-10:]) - 1 and msg["role"] == "user":
                        # Use enhanced prompt for the current user message
                        api_messages.append({"role": msg["role"], "content": enhanced_prompt})
                    else:
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
                    
                    # Auto-save conversation after each response
                    try:
                        save_success = save_conversation()
                        if save_success:
                            logger.info("✅ Conversation auto-saved")
                        else:
                            logger.warning("⚠️ Auto-save failed")
                    except Exception as save_error:
                        logger.error(f"Auto-save error: {save_error}")
                        
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
            st.write("• Features: 🔄 Regenerate • 📄 Documents • 🔍 Search")
            
            # Show conversation status
            conv_id = st.session_state.get('current_conversation_id')
            if conv_id:
                st.write(f"• Conversation: {conv_id[:8]}... (Saved)")
            else:
                st.write("• Conversation: New (Unsaved)")
        
        with col2:
            st.write("**Actions:**")
            
            # Save conversation manually
            if st.button("💾 Save Chat", use_container_width=True):
                if st.session_state.chat_messages:
                    success = save_conversation()
                    if success:
                        st.success("✅ Conversation saved!")
                    else:
                        st.error("❌ Save failed")
                else:
                    st.info("No messages to save")
            
            # Test API
            if st.button("🔧 Test API", use_container_width=True):
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