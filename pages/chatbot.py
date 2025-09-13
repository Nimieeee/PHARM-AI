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
        
        # Document Upload Section
        st.divider()
        st.subheader("📄 Documents")
        
        # Document upload
        uploaded_file = st.file_uploader(
            "Upload document for this conversation",
            type=['txt', 'pdf', 'docx', 'md'],
            help="Upload documents to enhance AI responses with your content"
        )
        
        if uploaded_file is not None:
            # Show file info
            st.write(f"📎 **{uploaded_file.name}**")
            st.write(f"📊 Size: {uploaded_file.size:,} bytes")
            st.write(f"🔖 Type: {uploaded_file.type}")
            
            # Process document button
            if st.button("🚀 Process Document", use_container_width=True, type="primary"):
                if not st.session_state.get('current_conversation_id'):
                    st.warning("⚠️ Please start a conversation first before uploading documents")
                else:
                    try:
                        with st.spinner("Processing document..."):
                            # Process the document
                            success = process_uploaded_document(uploaded_file, st.session_state.current_conversation_id)
                            
                            if success:
                                st.success("✅ Document processed successfully!")
                                st.info("💡 The AI can now reference this document in responses")
                            else:
                                st.error("❌ Failed to process document")
                                
                    except Exception as e:
                        st.error(f"❌ Error processing document: {e}")
                        logger.error(f"Document processing error: {e}")
        
        # Show conversation documents
        if st.session_state.get('current_conversation_id'):
            try:
                from services.document_service import document_service
                from services.user_service import user_service
                
                user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
                if user_data:
                    # Get documents for current conversation
                    documents = run_async(document_service.get_conversation_documents(
                        user_data['id'], 
                        st.session_state.current_conversation_id
                    ))
                    
                    if documents:
                        st.write("**📚 Conversation Documents:**")
                        for doc in documents:
                            doc_name = doc.get('filename', 'Unknown')
                            doc_size = doc.get('file_size', 0)
                            doc_status = doc.get('processing_status', 'unknown')
                            
                            # Show document with status
                            status_emoji = "✅" if doc_status == "completed" else "⏳" if doc_status == "processing" else "❌"
                            st.write(f"{status_emoji} {doc_name} ({doc_size:,} bytes)")
                    else:
                        st.caption("No documents uploaded yet")
                        
            except Exception as e:
                logger.error(f"Error loading conversation documents: {e}")
                    
                    else:
                        st.info("No conversations yet. Start chatting to create your first conversation!")
                        
        except Exception as e:
            st.error(f"❌ Error loading conversations: {e}")
            logger.error(f"Sidebar conversation loading error: {e}")

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
    
    # Chat input using st.chat_input (simpler than forms)
    elif prompt := st.chat_input("Ask me anything about pharmacology..."):
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