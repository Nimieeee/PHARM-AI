"""
Chatbot Page - Main Chat Interface
"""

import streamlit as st
import time
import io
from PIL import Image
from utils.conversation_manager import (
    get_current_messages, add_message_to_current_conversation, 
    create_new_conversation
)
from openai_client import chat_completion_stream, chat_completion, get_available_model_modes
from prompts import pharmacology_system_prompt
from rag_interface_chromadb import initialize_rag_system, get_rag_enhanced_prompt
from auth import can_user_upload, record_user_upload
from config import MODEL_CONFIGS

# Default model mode
DEFAULT_MODE = "normal"

def render_chatbot_page():
    """Render the main chatbot page."""
    # Check if we have a conversation, if not show welcome screen
    if not st.session_state.current_conversation_id:
        render_welcome_screen()
    else:
        render_chat_interface()

def render_welcome_screen():
    """Render welcome screen when no conversation is active."""
    st.markdown("# 💊 PharmBot")
    st.markdown("### Your AI Pharmacology Expert")
    st.markdown("Ready to help you learn and understand pharmacology concepts.")
    st.markdown("---")
    
    # Start chat button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start New Chat", key="start_chat", use_container_width=True, type="primary"):
            create_new_conversation()
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Quick example questions
    st.markdown("### 💡 Example Questions")
    
    examples = [
        "Explain the mechanism of action of ACE inhibitors",
        "What are the contraindications for NSAIDs?",
        "How do beta-blockers work in treating hypertension?",
        "Describe the pharmacokinetics of warfarin"
    ]
    
    for example in examples:
        if st.button(f"💬 {example}", key=f"example_{hash(example)}", use_container_width=True):
            create_new_conversation()
            add_message_to_current_conversation("user", example)
            st.rerun()

def render_chat_interface():
    """Render the main chat interface."""
    # Custom CSS for toggle switch
    st.markdown("""
    <style>
        .stToggle > div > div > div > div {
            background-color: #667eea !important;
        }
        .stToggle > div > div > div > div[data-checked="true"] {
            background-color: #764ba2 !important;
        }
        .stToggle label {
            font-weight: 600;
            color: #333;
        }
        .toggle-container {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 15px;
            padding: 15px;
            margin: 10px 0;
            border: 1px solid #e0e0e0;
        }
    </style>
    """, unsafe_allow_html=True)
    
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
                st.session_state.model_mode = DEFAULT_MODE if DEFAULT_MODE in available_modes else list(available_modes.keys())[0]
            
            # Create a single toggle switch
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
            new_mode = "turbo" if turbo_enabled else "normal"
            st.session_state.model_mode = new_mode
            
        else:
            st.error("Both Normal and Turbo modes need to be available. Please check your API keys.")
            return
    
    st.markdown("---")
    
    # Display chat messages
    display_chat_messages()
    
    # Chat input at the bottom - using session state approach for maximum reliability
    st.markdown("---")
    
    # Create a container for the input
    input_container = st.container()
    
    with input_container:
        # Use columns for layout - message box, upload button, send button
        col1, col2, col3 = st.columns([5, 1, 1])
        
        with col1:
            # Use session state to manage input value
            if "chat_input_value" not in st.session_state:
                st.session_state.chat_input_value = ""
            
            # Text input with session state
            user_input = st.text_input(
                "Message",
                value=st.session_state.chat_input_value,
                placeholder="Ask me anything about pharmacology...",
                label_visibility="collapsed",
                key=f"reliable_input_{st.session_state.current_conversation_id}"
            )
        
        with col2:
            # Upload button with dynamic key to clear after each upload
            if "upload_counter" not in st.session_state:
                st.session_state.upload_counter = 0
            
            uploaded_file = st.file_uploader(
                "📎",
                type=['pdf', 'txt', 'csv', 'docx', 'doc', 'png', 'jpg', 'jpeg'],
                key=f"file_uploader_{st.session_state.current_conversation_id}_{st.session_state.upload_counter}",
                help="Upload document (Max 10MB, unlimited uploads)",
                label_visibility="collapsed"
            )
        
        with col3:
            send_clicked = st.button("Send", type="primary", use_container_width=True)
    
    # Show file selection status
    if uploaded_file:
        st.info(f"📎 File selected: {uploaded_file.name} (ready to upload with your message)")
    
    # Handle input submission (with or without file)
    if send_clicked:
        if user_input.strip() or uploaded_file:
            # Clear the input by resetting session state
            st.session_state.chat_input_value = ""
            
            if uploaded_file:
                # Process file with custom message
                file_key = f"processed_{st.session_state.current_conversation_id}_{uploaded_file.name}_{len(uploaded_file.getvalue())}"
                if file_key not in st.session_state:
                    st.session_state[file_key] = True
                    custom_prompt = user_input.strip() if user_input.strip() else None
                    process_uploaded_file(uploaded_file, custom_prompt)
                    st.rerun()
            else:
                # Process regular message
                handle_chat_input(user_input.strip())
                st.rerun()
        else:
            st.error("Please enter a message or select a file to upload.")
    
    # Update session state if user typed something
    if user_input != st.session_state.chat_input_value:
        st.session_state.chat_input_value = user_input

def display_chat_messages():
    """Display chat messages for the current conversation."""
    messages = get_current_messages()
    for i, message in enumerate(messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Add regenerate button after the last assistant message
            if (message["role"] == "assistant" and 
                i == len(messages) - 1 and 
                len(messages) >= 2):  # At least one user message and one assistant response
                
                st.markdown("")  # Add some spacing
                col1, col2, col3 = st.columns([1, 1, 3])
                with col1:
                    if st.button("🔄 Regenerate", key=f"regenerate_{i}", help="Generate a new response"):
                        regenerate_last_response()
                        st.rerun()

def handle_chat_input(prompt):
    """Handle chat input and generate response."""
    # Ensure we have a conversation
    if not st.session_state.current_conversation_id:
        create_new_conversation()
    
    # Add user message
    add_message_to_current_conversation("user", prompt)
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate and display bot response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Show thinking message
            message_placeholder.markdown("🤔 Thinking...")
            
            # Enhance prompt with RAG if available
            enhanced_prompt = prompt
            try:
                rag_system = initialize_rag_system(st.session_state.current_conversation_id)
                if rag_system and len(rag_system.get_documents_list()) > 0:
                    message_placeholder.markdown("🔍 Searching knowledge base...")
                    enhanced_prompt = get_rag_enhanced_prompt(prompt, rag_system)
                    if enhanced_prompt != prompt:
                        message_placeholder.markdown("📚 Found relevant information in documents...")
                    else:
                        message_placeholder.markdown("💭 No relevant documents found, using general knowledge...")
                else:
                    message_placeholder.markdown("💭 No documents in this conversation...")
            except Exception as rag_error:
                message_placeholder.markdown("⚠️ Document search failed, using general knowledge...")
                enhanced_prompt = prompt
            
            message_placeholder.markdown("🔄 Generating response...")
            
            messages = get_messages_for_api(enhanced_prompt)
            
            # Get selected model from mode
            selected_mode = st.session_state.get("model_mode", DEFAULT_MODE)
            selected_model = MODEL_CONFIGS[selected_mode]["model"]
            
            # Generate streaming response
            message_placeholder.markdown("🔄 Generating response...")
            stream_worked = False
            
            for chunk in chat_completion_stream(selected_model, get_messages_for_api(enhanced_prompt)):
                stream_worked = True
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.02)
            
            # Show final response
            if stream_worked:
                message_placeholder.markdown(full_response)
            else:
                # Fallback to non-streaming
                full_response = chat_completion(selected_model, get_messages_for_api(enhanced_prompt))
                message_placeholder.markdown(full_response)
            
        except Exception as e:
            # Error fallback - still use enhanced prompt with RAG
            try:
                selected_mode = st.session_state.get("model_mode", DEFAULT_MODE)
                selected_model = MODEL_CONFIGS[selected_mode]["model"]
                full_response = chat_completion(selected_model, get_messages_for_api(enhanced_prompt))
                message_placeholder.markdown(full_response)
            except Exception as e2:
                error_msg = f"❌ Error: {str(e2)}"
                message_placeholder.markdown(error_msg)
                full_response = error_msg
        
        # Add bot response to conversation
        add_message_to_current_conversation("assistant", full_response)

def get_messages_for_api(user_input: str) -> list:
    """Get messages formatted for API call."""
    messages = [{"role": "system", "content": pharmacology_system_prompt}]
    
    # Add conversation history
    current_messages = get_current_messages()
    for msg in current_messages[-10:]:  # Keep last 10 messages for context
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add current user input
    messages.append({"role": "user", "content": user_input})
    
    return messages

def regenerate_last_response():
    """Regenerate the last assistant response."""
    messages = get_current_messages()
    
    if len(messages) < 2:
        st.error("No response to regenerate")
        return
    
    # Find the last user message to regenerate response for
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
    
    # Remove the last assistant message
    if st.session_state.current_conversation_id in st.session_state.conversations:
        st.session_state.conversations[st.session_state.current_conversation_id]["messages"].pop(last_assistant_index)
        
        # Save conversations
        from auth import save_user_conversations
        save_user_conversations(st.session_state.user_id, st.session_state.conversations)
    
    # Generate new response using the same logic as handle_chat_input but without adding user message
    generate_assistant_response(last_user_message)

def generate_assistant_response(user_prompt: str):
    """Generate assistant response for a given user prompt."""
    # Display the regeneration in progress
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Show thinking message
            message_placeholder.markdown("🔄 Regenerating response...")
            
            # Enhance prompt with RAG if available
            enhanced_prompt = user_prompt
            try:
                rag_system = initialize_rag_system(st.session_state.current_conversation_id)
                if rag_system and len(rag_system.get_documents_list()) > 0:
                    message_placeholder.markdown("🔍 Searching knowledge base...")
                    enhanced_prompt = get_rag_enhanced_prompt(user_prompt, rag_system)
                    if enhanced_prompt != user_prompt:
                        message_placeholder.markdown("📚 Found relevant information in documents...")
                    else:
                        message_placeholder.markdown("💭 No relevant documents found, using general knowledge...")
                else:
                    message_placeholder.markdown("💭 No documents in this conversation...")
            except Exception:
                message_placeholder.markdown("⚠️ Document search failed, using general knowledge...")
                enhanced_prompt = user_prompt
            
            message_placeholder.markdown("🔄 Generating new response...")
            
            # Get selected model from mode
            selected_mode = st.session_state.get("model_mode", DEFAULT_MODE)
            selected_model = MODEL_CONFIGS[selected_mode]["model"]
            
            # Generate streaming response
            stream_worked = False
            
            for chunk in chat_completion_stream(selected_model, get_messages_for_api(enhanced_prompt)):
                stream_worked = True
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
                time.sleep(0.02)
            
            # Show final response
            if stream_worked:
                message_placeholder.markdown(full_response)
            else:
                # Fallback to non-streaming
                full_response = chat_completion(selected_model, get_messages_for_api(enhanced_prompt))
                message_placeholder.markdown(full_response)
            
        except Exception as e:
            # Error fallback
            try:
                selected_mode = st.session_state.get("model_mode", DEFAULT_MODE)
                selected_model = MODEL_CONFIGS[selected_mode]["model"]
                full_response = chat_completion(selected_model, get_messages_for_api(enhanced_prompt))
                message_placeholder.markdown(full_response)
            except Exception as e2:
                error_msg = f"❌ Error generating response: {str(e2)}"
                message_placeholder.markdown(error_msg)
                full_response = error_msg
        
        # Add the new response to conversation
        add_message_to_current_conversation("assistant", full_response)





def process_uploaded_file(uploaded_file, custom_prompt=None):
    """Process uploaded file with optional custom prompt."""
    print(f"🔧 DEBUG: Starting file upload process for {uploaded_file.name}")
    print(f"🔧 DEBUG: File type: {uploaded_file.type}")
    print(f"🔧 DEBUG: Current conversation ID: {st.session_state.current_conversation_id}")
    
    try:
        # Get file content
        file_content = uploaded_file.getvalue()
        print(f"🔧 DEBUG: File content size: {len(file_content)} bytes")
        
        # Check upload limit
        print(f"🔧 DEBUG: Checking upload limits for user {st.session_state.user_id}")
        can_upload, limit_message = can_user_upload(st.session_state.user_id)
        print(f"🔧 DEBUG: Upload check result: {can_upload}, message: {limit_message}")
        
        if not can_upload:
            print(f"❌ DEBUG: Upload rejected - {limit_message}")
            st.error(f"❌ {limit_message}")
            return
        
        # Check file size (10MB limit)
        max_file_size = 10 * 1024 * 1024
        if len(file_content) > max_file_size:
            print(f"❌ DEBUG: File too large: {len(file_content) / (1024*1024):.1f}MB")
            st.error(f"❌ File too large ({len(file_content) / (1024*1024):.1f}MB). Max 10MB.")
            return
        
        # Ensure we have a conversation
        if not st.session_state.current_conversation_id:
            print(f"🔧 DEBUG: No conversation ID, creating new conversation")
            create_new_conversation()
            print(f"🔧 DEBUG: Created new conversation: {st.session_state.current_conversation_id}")
        
        # Process the upload
        print(f"🔧 DEBUG: Initializing RAG system for conversation {st.session_state.current_conversation_id}")
        rag_system = initialize_rag_system(st.session_state.current_conversation_id)
        
        if rag_system:
            print(f"✅ DEBUG: RAG system initialized successfully")
            with st.spinner(f"Processing {uploaded_file.name}..."):
                try:
                    print(f"🔧 DEBUG: Processing file {uploaded_file.name}...")
                    
                    if uploaded_file.type.startswith('image/'):
                        print(f"🔧 DEBUG: Processing as image")
                        image = Image.open(io.BytesIO(file_content))
                        result = rag_system.add_image(image, uploaded_file.name)
                    else:
                        print(f"🔧 DEBUG: Processing as document")
                        result = rag_system.add_document(file_content, uploaded_file.name, uploaded_file.type)
                    
                    print(f"🔧 DEBUG: RAG system processing result: {result}")
                    
                    if result == True:
                        # New document added successfully
                        print(f"✅ DEBUG: Document added successfully, recording upload")
                        record_user_upload(st.session_state.user_id, uploaded_file.name, len(file_content))
                        st.success(f"✅ Uploaded {uploaded_file.name}")
                        
                        # Use custom prompt or generate default prompt
                        if custom_prompt:
                            auto_prompt = f"I just uploaded a file called '{uploaded_file.name}'. {custom_prompt}"
                        else:
                            # Fallback to default prompts if no custom prompt provided
                            if uploaded_file.type.startswith('image/'):
                                auto_prompt = f"I just uploaded an image called '{uploaded_file.name}'. Please analyze and explain what you can see in this image, focusing on any scientific, medical, or pharmacological content."
                            else:
                                auto_prompt = f"I just uploaded a document called '{uploaded_file.name}'. Please summarize the key points and main content of this document."
                        
                        # Add the auto-generated prompt as a user message
                        add_message_to_current_conversation("user", auto_prompt)
                        
                        # Generate AI response
                        with st.chat_message("user"):
                            st.markdown(auto_prompt)
                        
                        with st.chat_message("assistant"):
                            message_placeholder = st.empty()
                            full_response = ""
                            
                            try:
                                # Show processing message
                                message_placeholder.markdown("🔍 Analyzing your uploaded file...")
                                
                                # Enhance prompt with RAG
                                rag_system = initialize_rag_system(st.session_state.current_conversation_id)
                                enhanced_prompt = auto_prompt
                                if rag_system:
                                    enhanced_prompt = get_rag_enhanced_prompt(auto_prompt, rag_system)
                                
                                # Get selected model from mode
                                selected_mode = st.session_state.get("model_mode", DEFAULT_MODE)
                                selected_model = MODEL_CONFIGS[selected_mode]["model"]
                                
                                # Generate streaming response
                                message_placeholder.markdown("🔄 Generating analysis...")
                                stream_worked = False
                                
                                for chunk in chat_completion_stream(selected_model, get_messages_for_api(enhanced_prompt)):
                                    stream_worked = True
                                    full_response += chunk
                                    message_placeholder.markdown(full_response + "▌")
                                    time.sleep(0.02)
                                
                                # Show final response
                                if stream_worked:
                                    message_placeholder.markdown(full_response)
                                else:
                                    # Fallback to non-streaming
                                    full_response = chat_completion(selected_model, get_messages_for_api(enhanced_prompt))
                                    message_placeholder.markdown(full_response)
                                
                            except Exception as e:
                                # Error fallback
                                try:
                                    selected_mode = st.session_state.get("model_mode", DEFAULT_MODE)
                                    selected_model = MODEL_CONFIGS[selected_mode]["model"]
                                    full_response = chat_completion(selected_model, get_messages_for_api(auto_prompt))
                                    message_placeholder.markdown(full_response)
                                except Exception as e2:
                                    error_msg = f"❌ Error analyzing file: {str(e2)}"
                                    message_placeholder.markdown(error_msg)
                                    full_response = error_msg
                            
                            # Add bot response to conversation
                            add_message_to_current_conversation("assistant", full_response)
                        
                        # Increment upload counter to clear the file uploader
                        st.session_state.upload_counter += 1
                        st.rerun()
                    elif result == "duplicate":
                        print(f"🔧 DEBUG: Document was duplicate")
                        # This should not happen anymore with conversation-specific hashing
                        st.info(f"📚 Document '{uploaded_file.name}' already exists in this conversation's knowledge base. You can still ask questions about it!")
                        # Still increment counter to clear uploader
                        st.session_state.upload_counter += 1
                    else:
                        print(f"❌ DEBUG: RAG system returned failure result: {result}")
                        st.error(f"❌ Failed to upload {uploaded_file.name}")
                        # Still increment counter to clear uploader
                        st.session_state.upload_counter += 1
                        
                except Exception as e:
                    print(f"❌ DEBUG: Exception during file processing: {e}")
                    import traceback
                    print(f"❌ DEBUG: File processing traceback: {traceback.format_exc()}")
                    st.error(f"❌ Error processing file: {str(e)}")
        else:
            print(f"❌ DEBUG: RAG system initialization failed!")
            st.error("❌ Upload system unavailable")
            
    except Exception as e:
        print(f"❌ CRITICAL DEBUG: Unexpected error in process_uploaded_file: {e}")
        import traceback
        print(f"❌ DEBUG: Full upload traceback: {traceback.format_exc()}")
        st.error(f"❌ Error handling file upload: {str(e)}")