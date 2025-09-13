"""
Chatbot Page - Main Chat Interface
"""

import streamlit as st
import time
import io
import asyncio
from PIL import Image
from utils.conversation_manager import (
    get_current_messages, add_message_to_current_conversation, 
    create_new_conversation
)
from openai_client import chat_completion_stream, chat_completion, get_available_model_modes
from prompts import pharmacology_system_prompt
from rag_interface_chromadb import initialize_rag_system, get_rag_enhanced_prompt
from auth import can_user_upload, record_user_upload
from config import get_model_configs

# Helper function to get model for selected mode
def get_selected_model(mode_key="model_mode", default_mode="normal"):
    """Get the selected model for the given mode."""
    selected_mode = st.session_state.get(mode_key, default_mode)
    model_configs = get_model_configs()
    return model_configs[selected_mode]["model"]

# Default model mode
DEFAULT_MODE = "normal"

def run_async(coro):
    """Run async function in Streamlit context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)

def render_chatbot_page():
    """Render the main chatbot page."""
    # Check if we have a conversation, if not show welcome screen
    if not st.session_state.current_conversation_id:
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
            run_async(create_new_conversation())
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
            run_async(create_new_conversation())
            run_async(add_message_to_current_conversation("user", example))
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

            # Check file size if file is uploaded
            if uploaded_file is not None:
                file_size_mb = uploaded_file.size / (1024 * 1024)
                if file_size_mb > 10:
                    st.error(f"File size ({file_size_mb:.1f}MB) exceeds the 10MB limit. Please upload a smaller file.")
                    uploaded_file = None

        with col3:
            send_clicked = st.button("Send", type="primary", use_container_width=True)

    # Show file selection status
    if uploaded_file:
        st.info(f"📎 File selected: {uploaded_file.name} (ready to upload with your message)")

    # Handle input submission (with or without file)
    if send_clicked:
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🎯 SEND BUTTON CLICKED - Input: '{user_input}', File: {uploaded_file is not None}")
        
        if user_input.strip() or uploaded_file:
            # Clear the input by resetting session state
            st.session_state.chat_input_value = ""

            if uploaded_file:
                # Process file with custom message
                file_key = f"processed_{st.session_state.current_conversation_id}_{uploaded_file.name}_{len(uploaded_file.getvalue())}"
                if file_key not in st.session_state:
                    st.session_state[file_key] = True
                    custom_prompt = user_input.strip() if user_input.strip() else None
                    logger.info(f"🔄 Processing uploaded file: {uploaded_file.name}")
                    
                    # Process file immediately and handle any errors
                    try:
                        # Show processing message
                        with st.spinner(f"Processing {uploaded_file.name}..."):
                            run_async(process_uploaded_file(uploaded_file, custom_prompt))
                        logger.info(f"✅ File processing completed for: {uploaded_file.name}")
                        
                        # Force a rerun to show the results
                        st.rerun()
                        
                    except Exception as file_error:
                        logger.error(f"💥 File processing failed for {uploaded_file.name}: {file_error}")
                        st.error(f"❌ Failed to process file: {str(file_error)}")
                        # Clear the processing flag so user can try again
                        if file_key in st.session_state:
                            del st.session_state[file_key]
            else:
                # Process regular message
                logger.info(f"🔄 Processing regular message: '{user_input.strip()}'")
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
    # Debug logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🎯 HANDLE_CHAT_INPUT called with prompt: '{prompt}'")
    
    # Ensure we have a conversation
    if not st.session_state.current_conversation_id:
        logger.info("🆕 Creating new conversation for message...")
        run_async(create_new_conversation())

    # Add user message
    run_async(add_message_to_current_conversation("user", prompt))

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
            selected_model = get_selected_model("model_mode", DEFAULT_MODE)

            # Generate streaming response with optimized updates
            message_placeholder.markdown("🔄 Generating response...")
            stream_worked = False
            update_counter = 0

            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"🤖 Starting streaming with model: {selected_model}")
            logger.info(f"📝 Messages for API: {len(get_messages_for_api(enhanced_prompt))} messages")

            try:
                stream_iterator = chat_completion_stream(selected_model, get_messages_for_api(enhanced_prompt))
                logger.info("📡 Stream iterator created successfully")
                
                for chunk in stream_iterator:
                    stream_worked = True
                    full_response += chunk
                    update_counter += 1

                    # Debug first few chunks
                    if update_counter <= 5:
                        logger.info(f"📡 Chunk {update_counter}: '{chunk}'")

                    # Update UI less frequently for better performance
                    if update_counter % 3 == 0:  # Update every 3 chunks
                        message_placeholder.markdown(full_response + "▌")
                        time.sleep(0.01)  # Reduced sleep time
                        
                    # Safety check - if response is getting too long, break
                    if len(full_response) > 10000:
                        logger.warning("⚠️ Response getting too long, breaking stream")
                        break
                        
            except Exception as stream_error:
                logger.error(f"💥 Stream iteration error: {str(stream_error)}")
                # Don't re-raise, let it fall through to the non-streaming fallback

            logger.info(f"✅ Streaming completed: {update_counter} chunks, {len(full_response)} chars")

            # Show final response
            if stream_worked:
                message_placeholder.markdown(full_response)
                logger.info(f"✅ Final response displayed: {len(full_response)} chars")
            else:
                # Fallback to non-streaming
                logger.warning("⚠️ Streaming didn't work, trying non-streaming fallback")
                full_response = chat_completion(selected_model, get_messages_for_api(enhanced_prompt))
                message_placeholder.markdown(full_response)
                logger.info(f"✅ Non-streaming fallback completed: {len(full_response)} chars")

        except Exception as e:
            # Debug logging for errors
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"💥 Streaming error: {str(e)}")
            
            # Error fallback - still use enhanced prompt with RAG
            try:
                logger.info("🔄 Trying non-streaming fallback...")
                selected_model = get_selected_model("model_mode", DEFAULT_MODE)
                full_response = chat_completion(selected_model, get_messages_for_api(enhanced_prompt))
                message_placeholder.markdown(full_response)
                logger.info(f"✅ Non-streaming fallback successful: {len(full_response)} chars")
            except Exception as e2:
                logger.error(f"💥 Non-streaming fallback also failed: {str(e2)}")
                error_msg = f"❌ Error: {str(e2)}"
                message_placeholder.markdown(error_msg)
                full_response = error_msg

        # Add bot response to conversation
        run_async(add_message_to_current_conversation("assistant", full_response))

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
            except Exception as rag_error:
                message_placeholder.markdown("⚠️ Document search failed, using general knowledge...")
                enhanced_prompt = user_prompt

            message_placeholder.markdown("🔄 Generating new response...")

            # Get selected model from mode
            selected_model = get_selected_model("model_mode", DEFAULT_MODE)

            # Generate streaming response with optimized updates
            stream_worked = False
            update_counter = 0

            for chunk in chat_completion_stream(selected_model, get_messages_for_api(enhanced_prompt)):
                stream_worked = True
                full_response += chunk
                update_counter += 1

                # Update UI less frequently for better performance
                if update_counter % 3 == 0:  # Update every 3 chunks
                    message_placeholder.markdown(full_response + "▌")
                    time.sleep(0.01)  # Reduced sleep time

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
                selected_model = get_selected_model("model_mode", DEFAULT_MODE)
                full_response = chat_completion(selected_model, get_messages_for_api(enhanced_prompt))
                message_placeholder.markdown(full_response)
            except Exception as e2:
                error_msg = f"❌ Error generating response: {str(e2)}"
                message_placeholder.markdown(error_msg)
                full_response = error_msg

        # Add the new response to conversation
        run_async(add_message_to_current_conversation("assistant", full_response))

@st.cache_data(ttl=300)  # Cache for 5 minutes
def _process_file_content(file_content: bytes, filename: str, file_type: str):
    """Cached file content processing to avoid reprocessing same files."""
    return len(file_content), file_type.startswith('image/')

async def process_uploaded_file(uploaded_file, custom_prompt=None):
    """Process uploaded file with optional custom prompt - optimized for performance."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 PROCESS_UPLOADED_FILE started for: {uploaded_file.name}")
    
    try:
        # Get file content
        file_content = uploaded_file.getvalue()

        # Quick validation using cached function
        file_size, is_image = _process_file_content(file_content, uploaded_file.name, uploaded_file.type)

        # Check upload limit (cached)
        can_upload, limit_message = can_user_upload(st.session_state.user_id)
        if not can_upload:
            st.error(f"❌ {limit_message}")
            return

        # Check file size (10MB limit)
        max_file_size = 10 * 1024 * 1024
        if file_size > max_file_size:
            st.error(f"❌ File too large ({file_size / (1024*1024):.1f}MB). Max 10MB.")
            return

        # Ensure we have a conversation
        if not st.session_state.current_conversation_id:
            run_async(create_new_conversation())

        # Show immediate feedback
        st.info(f"📤 Processing {uploaded_file.name}...")

        # Process the upload asynchronously
        progress_placeholder = st.empty()
        
        try:
            progress_placeholder.markdown("🔄 Initializing document processor...")
            rag_system = initialize_rag_system(st.session_state.current_conversation_id)

            if rag_system:
                # Process file in background
                try:
                    progress_placeholder.markdown("📄 Processing document content...")

                    if is_image:
                        progress_placeholder.markdown("🖼️ Extracting text from image...")
                        image = Image.open(io.BytesIO(file_content))
                        result = await rag_system.add_image(image, uploaded_file.name)
                    else:
                        progress_placeholder.markdown("📝 Extracting and processing text...")
                        result = await rag_system.add_document(file_content, uploaded_file.name, uploaded_file.type)

                    progress_placeholder.empty()

                    if result == True:
                        # New document added successfully
                        record_user_upload(st.session_state.user_id, uploaded_file.name, file_size)
                        st.success(f"✅ Successfully processed {uploaded_file.name}")

                        # Generate prompt
                        if custom_prompt:
                            auto_prompt = f"I just uploaded a file called '{uploaded_file.name}'. {custom_prompt}"
                        else:
                            if is_image:
                                auto_prompt = f"I just uploaded an image called '{uploaded_file.name}'. Please analyze and explain what you can see in this image, focusing on any scientific, medical, or pharmacological content."
                            else:
                                auto_prompt = f"I just uploaded a document called '{uploaded_file.name}'. Please summarize the key points and main content of this document."

                        # Add message and generate response
                        run_async(add_message_to_current_conversation("user", auto_prompt))

                        # Display messages
                        with st.chat_message("user"):
                            st.markdown(auto_prompt)

                        # Generate response asynchronously
                        logger.info(f"🎯 About to call generate_file_analysis_response with prompt: {auto_prompt[:100]}...")
                        generate_file_analysis_response(auto_prompt)
                        logger.info(f"🏁 generate_file_analysis_response call completed")

                        # Clear uploader (don't rerun immediately - let response complete)
                        st.session_state.upload_counter += 1

                    elif result == "duplicate":
                        st.info(f"📚 Document '{uploaded_file.name}' already exists in this conversation's knowledge base.")
                        st.session_state.upload_counter += 1
                        # Don't rerun for duplicates - just update counter
                    else:
                        st.error(f"❌ Failed to process {uploaded_file.name}. The document may be corrupted or in an unsupported format.")
                        st.session_state.upload_counter += 1
                        # Don't rerun for errors - just update counter

                except Exception as e:
                    progress_placeholder.empty()
                    st.error(f"❌ Error processing file: {str(e)}")
                    st.info("💡 Try uploading a different file or check if the file is corrupted.")
            else:
                progress_placeholder.empty()
                st.error("❌ Document processing system unavailable")
                st.info("💡 This may be due to missing dependencies. Some document features may not work on Streamlit Cloud.")
                
        except Exception as e:
            if progress_placeholder:
                progress_placeholder.empty()
            st.error(f"❌ Error initializing document processor: {str(e)}")

    except Exception as e:
        logger.error(f"💥 PROCESS_UPLOADED_FILE failed for {uploaded_file.name}: {str(e)}")
        st.error(f"❌ Error handling file upload: {str(e)}")
    
    logger.info(f"🏁 PROCESS_UPLOADED_FILE completed for: {uploaded_file.name}")

def generate_file_analysis_response(auto_prompt: str):
    """Generate AI response for file analysis - optimized for performance."""
    import logging
    logger = logging.getLogger(__name__)
    
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            logger.info(f"🔍 Starting file analysis for prompt: {auto_prompt[:100]}...")
            message_placeholder.markdown("🔍 Analyzing your uploaded file...")

            # Get enhanced prompt (with caching)
            enhanced_prompt = auto_prompt
            try:
                rag_system = initialize_rag_system(st.session_state.current_conversation_id)
                if rag_system:
                    enhanced_prompt = get_rag_enhanced_prompt(auto_prompt, rag_system)
                    logger.info(f"✅ RAG enhancement successful, enhanced prompt length: {len(enhanced_prompt)}")
                else:
                    logger.warning("⚠️ RAG system not available")
            except Exception as rag_error:
                logger.error(f"❌ RAG enhancement failed: {rag_error}")
                pass  # Use original prompt if RAG fails

            # Get model config
            selected_model = get_selected_model("model_mode", DEFAULT_MODE)
            logger.info(f"🤖 Selected model: {selected_model}")

            # Generate response with optimized streaming
            message_placeholder.markdown("🔄 Generating analysis...")

            try:
                # Try streaming first
                for chunk in chat_completion_stream(selected_model, get_messages_for_api(enhanced_prompt)):
                    full_response += chunk
                    # Reduce update frequency for better performance
                    if len(full_response) % 50 == 0:  # Update every 50 characters
                        message_placeholder.markdown(full_response + "▌")

                message_placeholder.markdown(full_response)

            except Exception as stream_error:
                # Fallback to non-streaming
                message_placeholder.markdown("🔄 Switching to non-streaming mode...")
                try:
                    full_response = chat_completion(selected_model, get_messages_for_api(enhanced_prompt))
                    message_placeholder.markdown(full_response)
                except Exception as completion_error:
                    error_msg = f"❌ Both streaming and non-streaming failed:\nStreaming: {str(stream_error)}\nCompletion: {str(completion_error)}"
                    message_placeholder.markdown(error_msg)
                    full_response = error_msg

        except Exception as e:
            error_msg = f"❌ Error analyzing file: {str(e)}"
            logger.error(f"💥 File analysis failed: {e}")
            message_placeholder.markdown(error_msg)
            full_response = error_msg

        # Add response to conversation
        try:
            logger.info(f"💾 Saving response to conversation: {len(full_response)} characters")
            run_async(add_message_to_current_conversation("assistant", full_response))
            logger.info("✅ Response saved successfully")
        except Exception as save_error:
            logger.error(f"❌ Failed to save response: {save_error}")
            st.error(f"Failed to save response: {save_error}")