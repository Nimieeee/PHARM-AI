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

def process_uploaded_document(uploaded_file):
    """Process uploaded document and return text content."""
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
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
            except Exception as pdf_error:
                logger.warning(f"PDF processing failed: {pdf_error}")
                text_content = f"[PDF Document: {uploaded_file.name} - {len(file_content)} bytes - Text extraction failed]"
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
                        raise Exception("No text extracted")
                finally:
                    os.unlink(tmp_path)
            except Exception as docx_error:
                logger.warning(f"DOCX processing failed: {docx_error}")
                text_content = f"[DOCX Document: {uploaded_file.name} - {len(file_content)} bytes - Text extraction failed]"
        else:
            text_content = f"[Document: {uploaded_file.name} - {len(file_content)} bytes - Unsupported format]"
        
        return text_content
        
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        return None

def save_document_to_conversation(uploaded_file, content):
    """Save document to conversation knowledge base with advanced RAG processing."""
    try:
        if not st.session_state.get('current_conversation_id'):
            return False
        
        conv_id = st.session_state.current_conversation_id
        
        # Save to session state for immediate access
        if 'conversation_documents' not in st.session_state:
            st.session_state.conversation_documents = {}
        
        if conv_id not in st.session_state.conversation_documents:
            st.session_state.conversation_documents[conv_id] = []
        
        # Add document to conversation knowledge base
        document_info = {
            'filename': uploaded_file.name,
            'content': content,
            'uploaded_at': datetime.now().isoformat(),
            'file_size': len(uploaded_file.getvalue())
        }
        
        st.session_state.conversation_documents[conv_id].append(document_info)
        
        # Process with advanced RAG (async in background)
        try:
            from services.rag_service import RAGService
            from services.user_service import user_service
            import uuid
            
            # Get user UUID
            user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
            if user_data:
                rag_service = RAGService()
                document_id = str(uuid.uuid4())
                
                # Process document for semantic search
                success = run_async(rag_service.process_document(
                    content, 
                    document_id, 
                    conv_id, 
                    user_data['id'],
                    metadata={
                        'filename': uploaded_file.name,
                        'file_size': len(uploaded_file.getvalue()),
                        'uploaded_at': datetime.now().isoformat()
                    }
                ))
                
                if success:
                    logger.info(f"✅ Document processed with advanced RAG: {uploaded_file.name}")
                else:
                    logger.warning(f"⚠️ RAG processing failed for: {uploaded_file.name}")
            
        except Exception as rag_error:
            logger.warning(f"Advanced RAG processing failed: {rag_error}")
            # Continue with basic storage
        
        logger.info(f"Document saved to conversation {conv_id}: {uploaded_file.name}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving document to conversation: {e}")
        return False

def get_conversation_context(user_query=""):
    """Get enhanced document context for current conversation using multi-strategy RAG."""
    try:
        conv_id = st.session_state.get('current_conversation_id')
        if not conv_id:
            return ""
        
        # Try advanced RAG search first
        if user_query:
            try:
                from services.rag_service import RAGService
                from services.user_service import user_service
                
                # Get user UUID
                user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
                if user_data:
                    rag_service = RAGService()
                    
                    # Multi-query strategy for thorough search
                    contexts = []
                    
                    # Original query
                    context1 = run_async(rag_service.get_conversation_context(
                        user_query, conv_id, user_data['id'], max_context_length=2000
                    ))
                    if context1:
                        contexts.append(context1)
                    
                    # Extract key terms for additional searches
                    key_terms = extract_key_terms(user_query)
                    for term in key_terms[:2]:  # Limit to 2 additional searches
                        context_term = run_async(rag_service.get_conversation_context(
                            term, conv_id, user_data['id'], max_context_length=1500
                        ))
                        if context_term and context_term not in contexts:
                            contexts.append(context_term)
                    
                    # Combine contexts
                    if contexts:
                        combined_context = "\n\n".join(contexts)
                        logger.info(f"✅ Retrieved multi-strategy RAG context: {len(combined_context)} chars")
                        return f"\n\n--- RELEVANT DOCUMENT EXCERPTS ---\n{combined_context}\n"
                    
            except Exception as rag_error:
                logger.warning(f"RAG search failed, falling back to simple context: {rag_error}")
        
        # Fallback to session-based documents (enhanced)
        if 'conversation_documents' in st.session_state:
            documents = st.session_state.conversation_documents.get(conv_id, [])
            if documents:
                context = "\n\n--- CONVERSATION DOCUMENTS ---\n"
                for doc in documents:
                    # Use more content and better formatting
                    content = doc['content']
                    if len(content) > 2000:
                        # For long documents, try to find relevant sections
                        if user_query:
                            relevant_section = find_relevant_section(content, user_query)
                            context += f"\n[Document: {doc['filename']}]\n{relevant_section}\n"
                        else:
                            # Show beginning and end for context
                            context += f"\n[Document: {doc['filename']}]\n{content[:1500]}...\n[End excerpt: ...{content[-500:]}]\n"
                    else:
                        context += f"\n[Document: {doc['filename']}]\n{content}\n"
                
                return context
        
        return ""
        
    except Exception as e:
        logger.error(f"Error getting conversation context: {e}")
        return ""

def extract_key_terms(query, max_terms=3):
    """Extract key terms from user query for multi-query RAG."""
    try:
        import re
        
        # Remove common stop words
        stop_words = {
            'what', 'how', 'why', 'when', 'where', 'who', 'which', 'is', 'are', 'was', 'were',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'can', 'could', 'should', 'would', 'will', 'shall', 'may', 'might',
            'do', 'does', 'did', 'have', 'has', 'had', 'be', 'been', 'being', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
            'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
        }
        
        # Extract words (3+ characters, not stop words)
        words = re.findall(r'\b[a-zA-Z]{3,}\b', query.lower())
        key_terms = [word for word in words if word not in stop_words]
        
        # Return unique terms, prioritizing longer ones
        unique_terms = list(dict.fromkeys(key_terms))  # Preserve order, remove duplicates
        unique_terms.sort(key=len, reverse=True)  # Longer terms first
        
        return unique_terms[:max_terms]
        
    except Exception as e:
        logger.error(f"Error extracting key terms: {e}")
        return []

def find_relevant_section(content, query, section_size=1500):
    """Find the most relevant section of a document based on query."""
    try:
        query_words = query.lower().split()
        content_lower = content.lower()
        
        # Find positions of query words
        word_positions = []
        for word in query_words:
            pos = content_lower.find(word)
            if pos != -1:
                word_positions.append(pos)
        
        if not word_positions:
            # No matches found, return beginning
            return content[:section_size] + "..." if len(content) > section_size else content
        
        # Find the center of query word cluster
        center_pos = sum(word_positions) // len(word_positions)
        
        # Extract section around the center
        start_pos = max(0, center_pos - section_size // 2)
        end_pos = min(len(content), start_pos + section_size)
        
        # Adjust to word boundaries
        if start_pos > 0:
            # Find previous sentence or paragraph break
            for i in range(start_pos, max(0, start_pos - 100), -1):
                if content[i] in '.!?\n':
                    start_pos = i + 1
                    break
        
        if end_pos < len(content):
            # Find next sentence or paragraph break
            for i in range(end_pos, min(len(content), end_pos + 100)):
                if content[i] in '.!?\n':
                    end_pos = i + 1
                    break
        
        section = content[start_pos:end_pos].strip()
        
        # Add context indicators
        prefix = "..." if start_pos > 0 else ""
        suffix = "..." if end_pos < len(content) else ""
        
        return f"{prefix}{section}{suffix}"
        
    except Exception as e:
        logger.error(f"Error finding relevant section: {e}")
        return content[:section_size] + "..." if len(content) > section_size else content

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
        # Clear any pending document uploads when switching conversations
        if 'pending_document' in st.session_state:
            del st.session_state.pending_document
    
    # Initialize messages if not already done
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    
    # Simple model selection and document status
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        is_turbo = st.toggle("⚡ Turbo Mode", 
                           value=(st.session_state.selected_model_mode == "turbo"),
                           help="Switch between Normal and Turbo modes")
        st.session_state.selected_model_mode = "turbo" if is_turbo else "normal"
    
    # Show document status for current conversation
    conv_id = st.session_state.get('current_conversation_id')
    if conv_id and 'conversation_documents' in st.session_state:
        documents = st.session_state.conversation_documents.get(conv_id, [])
        if documents:
            doc_count = len(documents)
            st.info(f"📚 {doc_count} document{'s' if doc_count != 1 else ''} available in this conversation")
    
    # Display chat messages with regenerate button
    for i, message in enumerate(st.session_state.chat_messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Add regenerate button for the last assistant message
            if (message["role"] == "assistant" and 
                i == len(st.session_state.chat_messages) - 1 and 
                i > 0):  # Only show for the last assistant message
                
                if st.button("🔄 Regenerate", key=f"regen_{i}", help="Regenerate response"):
                    # Get the previous user message
                    if i > 0 and st.session_state.chat_messages[i-1]["role"] == "user":
                        user_prompt = st.session_state.chat_messages[i-1]["content"]
                        
                        # Remove the current assistant response
                        st.session_state.chat_messages.pop()
                        
                        # Set regeneration flag
                        st.session_state.regenerate_response = True
                        st.session_state.regenerate_prompt = user_prompt
                        st.rerun()
    
    # Document upload and chat input area
    st.markdown("---")
    
    # Document upload beside message input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Chat input
        prompt = st.chat_input("Ask me anything about pharmacology...")
    
    with col2:
        # Document upload
        uploaded_file = st.file_uploader(
            "📎 Upload",
            type=['txt', 'pdf', 'docx', 'md'],
            help="Upload a document for this conversation",
            key=f"doc_upload_{st.session_state.get('current_conversation_id', 'new')}"
        )
    
    # Handle document upload
    if uploaded_file is not None:
        with st.spinner(f"Processing {uploaded_file.name}..."):
            document_content = process_uploaded_document(uploaded_file)
            if document_content:
                success = save_document_to_conversation(uploaded_file, document_content)
                if success:
                    st.success(f"✅ {uploaded_file.name} added to conversation knowledge base!")
                else:
                    st.error("❌ Failed to save document")
            else:
                st.error("❌ Failed to process document")
    
    # Handle regenerate response
    if st.session_state.get('regenerate_response', False):
        prompt = st.session_state.get('regenerate_prompt', '')
        st.session_state.regenerate_response = False
        st.session_state.regenerate_prompt = None
    
    # Process chat input or regeneration
    if prompt:
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
                
                # Get enhanced document context for this conversation
                document_context = get_conversation_context(prompt)
                
                # Prepare system prompt with enhanced document context
                system_prompt = pharmacology_system_prompt
                if document_context:
                    system_prompt += f"\n\n{document_context}\n\nIMPORTANT: Use the above document excerpts as primary sources when answering questions. Reference specific information from the documents when relevant. If the user's question relates to the uploaded documents, prioritize information from those documents over general knowledge."
                
                # Prepare messages for API
                api_messages = [{"role": "system", "content": system_prompt}]
                
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