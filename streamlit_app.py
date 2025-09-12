import streamlit as st
from openai_client import chat_completion, chat_completion_stream
from prompts import pharmacology_system_prompt
from drug_database import get_drug_info, get_drug_categories, COMMON_DRUGS
import json
import uuid
from datetime import datetime
import re
import time

# Page configuration
st.set_page_config(
    page_title="PharmBot",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fixed model - Llama 4 Maverick for pharmacology
FIXED_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"

# System-aware CSS that adapts to light/dark mode
st.markdown("""
<style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* System-aware color variables */
    :root {
        --bg-primary: light-dark(#ffffff, #0e1117);
        --bg-secondary: light-dark(#f8f9fa, #262730);
        --bg-tertiary: light-dark(#e9ecef, #1e1e1e);
        --text-primary: light-dark(#1a1a1a, #fafafa);
        --text-secondary: light-dark(#2c2c2c, #e0e0e0);
        --text-muted: light-dark(#6c757d, #a0a0a0);
        --border-color: light-dark(#dee2e6, #3a3a3a);
        --border-hover: light-dark(#667eea, #8b9cf7);
        --shadow-light: light-dark(rgba(0,0,0,0.08), rgba(255,255,255,0.05));
        --shadow-medium: light-dark(rgba(0,0,0,0.15), rgba(255,255,255,0.1));
        --hover-bg: light-dark(#f0f0f0, #2a2a2a);
        --active-bg: light-dark(#e3f2fd, #1a2332);
        --active-border: light-dark(#2196f3, #4fc3f7);
    }
    
    /* Fallback for browsers that don't support light-dark() */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-primary: #0e1117;
            --bg-secondary: #262730;
            --bg-tertiary: #1e1e1e;
            --text-primary: #fafafa;
            --text-secondary: #e0e0e0;
            --text-muted: #a0a0a0;
            --border-color: #3a3a3a;
            --border-hover: #8b9cf7;
            --shadow-light: rgba(255,255,255,0.05);
            --shadow-medium: rgba(255,255,255,0.1);
            --hover-bg: #2a2a2a;
            --active-bg: #1a2332;
            --active-border: #4fc3f7;
        }
    }
    
    /* Custom styling with system-aware colors */
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 1rem;
    }
    

    
    .feature-card {
        background: var(--bg-primary);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px var(--shadow-light);
        border: 1px solid var(--border-color);
        transition: all 0.3s ease;
        height: 100%;
        text-align: center;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px var(--shadow-medium);
        border-color: var(--border-hover);
    }
    
    .feature-card .feature-icon {
        font-size: 3.5rem;
        margin-bottom: 1.5rem;
        display: block;
    }
    
    .feature-card h3 {
        color: var(--text-primary);
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1rem;
        margin-top: 0;
    }
    
    .feature-card p {
        color: var(--text-secondary);
        font-size: 1rem;
        line-height: 1.6;
        margin-bottom: 0;
    }
    
    .conversation-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 8px;
        cursor: pointer;
        border: 1px solid transparent;
        transition: all 0.2s ease;
    }
    
    .conversation-item:hover {
        background-color: var(--hover-bg);
        border: 1px solid var(--border-color);
    }
    
    .conversation-active {
        background-color: var(--active-bg);
        border: 1px solid var(--active-border);
    }
    
    /* Ensure text in about section is readable */
    .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
        color: var(--text-primary) !important;
    }
    
    .stMarkdown p {
        color: var(--text-secondary) !important;
    }
    
    /* Style the example buttons to match theme */
    .stButton > button {
        background-color: var(--bg-secondary);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: var(--hover-bg);
        border-color: var(--border-hover);
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if "conversations" not in st.session_state:
        st.session_state.conversations = {}
    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = None
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = FIXED_MODEL
    if "conversation_counter" not in st.session_state:
        st.session_state.conversation_counter = 0
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""


def create_new_conversation():
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    st.session_state.conversation_counter += 1
    st.session_state.conversations[conversation_id] = {
        "title": f"New Chat {st.session_state.conversation_counter}",
        "messages": [],
        "created_at": datetime.now(),
        "model": FIXED_MODEL
    }
    st.session_state.current_conversation_id = conversation_id
    return conversation_id

def get_current_messages():
    """Get messages from current conversation."""
    try:
        if (hasattr(st.session_state, 'current_conversation_id') and 
            st.session_state.current_conversation_id and 
            hasattr(st.session_state, 'conversations') and
            st.session_state.current_conversation_id in st.session_state.conversations):
            return st.session_state.conversations[st.session_state.current_conversation_id]["messages"]
    except Exception:
        pass
    return []

def add_message_to_current_conversation(role: str, content: str):
    """Add message to current conversation."""
    if not st.session_state.current_conversation_id:
        create_new_conversation()
    
    st.session_state.conversations[st.session_state.current_conversation_id]["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now()
    })
    
    # Update conversation title based on first user message
    if role == "user" and len(st.session_state.conversations[st.session_state.current_conversation_id]["messages"]) == 1:
        title = content[:50] + "..." if len(content) > 50 else content
        st.session_state.conversations[st.session_state.current_conversation_id]["title"] = title

def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    if conversation_id in st.session_state.conversations:
        del st.session_state.conversations[conversation_id]
        if st.session_state.current_conversation_id == conversation_id:
            # Switch to another conversation or create new one
            if st.session_state.conversations:
                st.session_state.current_conversation_id = list(st.session_state.conversations.keys())[0]
            else:
                st.session_state.current_conversation_id = None

def search_conversations(query: str):
    """Search conversations by title and content."""
    if not query.strip():
        return list(st.session_state.conversations.items())
    
    query_lower = query.lower()
    matching_conversations = []
    
    for conv_id, conv_data in st.session_state.conversations.items():
        # Search in title
        if query_lower in conv_data["title"].lower():
            matching_conversations.append((conv_id, conv_data))
            continue
        
        # Search in message content
        for message in conv_data["messages"]:
            if query_lower in message["content"].lower():
                matching_conversations.append((conv_id, conv_data))
                break
    
    return matching_conversations



def duplicate_conversation(conversation_id: str):
    """Create a duplicate of an existing conversation."""
    if conversation_id not in st.session_state.conversations:
        return None
    
    original_conv = st.session_state.conversations[conversation_id]
    new_conversation_id = str(uuid.uuid4())
    st.session_state.conversation_counter += 1
    
    st.session_state.conversations[new_conversation_id] = {
        "title": f"{original_conv['title']} (Copy)",
        "messages": original_conv["messages"].copy(),
        "created_at": datetime.now(),
        "model": original_conv.get("model", FIXED_MODEL)
    }
    
    return new_conversation_id

def rename_conversation(conversation_id: str, new_title: str):
    """Rename a conversation."""
    if conversation_id in st.session_state.conversations and new_title.strip():
        st.session_state.conversations[conversation_id]["title"] = new_title.strip()

def display_chat_messages():
    """Display chat messages from current conversation."""
    messages = get_current_messages()
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def get_bot_response(user_input: str, model: str) -> str:
    """Get response from the selected model."""
    try:
        messages = [{"role": "system", "content": pharmacology_system_prompt}]
        
        # Add conversation history
        current_messages = get_current_messages()
        for msg in current_messages[-10:]:  # Keep last 10 messages for context
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        response = chat_completion(model=model, messages=messages)
        return response
    except Exception as e:
        return f"Error: {str(e)}"

def get_bot_response_stream(user_input: str, model: str):
    """Get streaming response from the selected model."""
    try:
        messages = [{"role": "system", "content": pharmacology_system_prompt}]
        
        # Add conversation history
        current_messages = get_current_messages()
        for msg in current_messages[-10:]:  # Keep last 10 messages for context
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        # Yield from the stream
        for chunk in chat_completion_stream(model=model, messages=messages):
            yield chunk
            
    except Exception as e:
        yield f"Error: {str(e)}"

def render_sidebar():
    """Render the sidebar with conversations and settings."""
    with st.sidebar:
        # New Chat Button
        if st.button("➕ New Chat", key="new_chat", use_container_width=True):
            create_new_conversation()
            st.rerun()
        
        st.markdown("---")
        
        # Search Conversations
        st.subheader("🔍 Search Conversations")
        search_query = st.text_input(
            "Search in conversations...",
            value=st.session_state.search_query,
            placeholder="Search titles and messages",
            key="search_input"
        )
        st.session_state.search_query = search_query
        
        # Clear search button
        if search_query:
            if st.button("❌ Clear Search", key="clear_search"):
                st.session_state.search_query = ""
                st.rerun()
        
        st.markdown("---")
        
        # Conversations List
        st.subheader("💬 Conversations")
        
        if st.session_state.conversations:
            # Get conversations (filtered by search if applicable)
            if search_query.strip():
                conversations_to_show = search_conversations(search_query)
                if not conversations_to_show:
                    st.info("No conversations match your search.")
                else:
                    st.info(f"Found {len(conversations_to_show)} conversation(s)")
            else:
                # Sort conversations by creation date (newest first)
                conversations_to_show = sorted(
                    st.session_state.conversations.items(),
                    key=lambda x: x[1]["created_at"],
                    reverse=True
                )
            
            for conv_id, conv_data in conversations_to_show:
                # Conversation container
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        # Conversation button
                        is_active = conv_id == st.session_state.current_conversation_id
                        button_style = "🟢 " if is_active else ""
                        
                        if st.button(
                            f"{button_style}{conv_data['title'][:25]}...",
                            key=f"conv_{conv_id}",
                            use_container_width=True
                        ):
                            st.session_state.current_conversation_id = conv_id
                            st.rerun()
                    
                    with col2:
                        # More options dropdown
                        if st.button("⋯", key=f"more_{conv_id}", help="More options"):
                            st.session_state[f"show_options_{conv_id}"] = not st.session_state.get(f"show_options_{conv_id}", False)
                    
                    with col3:
                        # Delete button
                        if st.button("🗑️", key=f"del_{conv_id}", help="Delete conversation"):
                            delete_conversation(conv_id)
                            st.rerun()
                    
                    # Show options if toggled
                    if st.session_state.get(f"show_options_{conv_id}", False):
                        with st.expander("Options", expanded=True):
                            # Duplicate conversation
                            if st.button("📋 Duplicate", key=f"duplicate_{conv_id}", use_container_width=True):
                                new_conv_id = duplicate_conversation(conv_id)
                                if new_conv_id:
                                    st.session_state.current_conversation_id = new_conv_id
                                    st.success("Conversation duplicated!")
                                    st.rerun()
                            
                            # Rename conversation
                            new_title = st.text_input(
                                "Rename:",
                                value=conv_data['title'],
                                key=f"rename_{conv_id}"
                            )
                            if st.button("✏️ Rename", key=f"rename_btn_{conv_id}", use_container_width=True):
                                rename_conversation(conv_id, new_title)
                                st.success("Conversation renamed!")
                                st.rerun()
        else:
            st.info("No conversations yet. Start a new chat!")
        
        st.markdown("---")
        
        st.markdown("---")
        
        # Disclaimer
        st.warning("⚠️ **Disclaimer:** Educational purposes only. Consult healthcare professionals for medical advice.")

def main():
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Simple Homepage
    if not st.session_state.current_conversation_id:
        # Simple header
        st.markdown("# 💊 PharmBot")
        st.markdown("### Your AI Pharmacology Expert")
        st.markdown("Get instant answers to complex pharmacology questions and enhance your understanding of medicinal science.")
        st.markdown("---")
        
        # Prominent Start Chat Button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Chatting Now", key="start_chat_main", use_container_width=True, type="primary"):
                create_new_conversation()
                st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Features showcase with improved cards
        st.markdown("### ✨ What Makes PharmBot Special")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🧬</div>
                <h3>Deep Knowledge</h3>
                <p>Comprehensive understanding of drug mechanisms, interactions, and pharmacokinetics backed by scientific literature.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">⚡</div>
                <h3>Instant Answers</h3>
                <p>Get immediate responses to complex pharmacology questions with detailed explanations and clinical context.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🎓</div>
                <h3>Educational Focus</h3>
                <p>Perfect for students, researchers, and healthcare professionals seeking to expand their pharmaceutical knowledge.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Quick examples section
        st.markdown("### 💡 Try These Popular Questions")
        
        example_col1, example_col2 = st.columns(2)
        
        with example_col1:
            if st.button("🔬 How do ACE inhibitors work?", use_container_width=True):
                create_new_conversation()
                query = "Explain the mechanism of action of ACE inhibitors in detail"
                add_message_to_current_conversation("user", query)
                with st.spinner("Thinking..."):
                    response = get_bot_response(query, FIXED_MODEL)
                    add_message_to_current_conversation("assistant", response)
                st.rerun()
            
            if st.button("💊 What are NSAIDs side effects?", use_container_width=True):
                create_new_conversation()
                query = "What are the common and serious side effects of NSAIDs?"
                add_message_to_current_conversation("user", query)
                with st.spinner("Thinking..."):
                    response = get_bot_response(query, FIXED_MODEL)
                    add_message_to_current_conversation("assistant", response)
                st.rerun()
        
        with example_col2:
            if st.button("⚠️ Warfarin drug interactions", use_container_width=True):
                create_new_conversation()
                query = "What are the major drug interactions with warfarin and why do they occur?"
                add_message_to_current_conversation("user", query)
                with st.spinner("Thinking..."):
                    response = get_bot_response(query, FIXED_MODEL)
                    add_message_to_current_conversation("assistant", response)
                st.rerun()
            
            if st.button("📊 Digoxin pharmacokinetics", use_container_width=True):
                create_new_conversation()
                query = "Explain the pharmacokinetics of digoxin and its clinical implications"
                add_message_to_current_conversation("user", query)
                with st.spinner("Thinking..."):
                    response = get_bot_response(query, FIXED_MODEL)
                    add_message_to_current_conversation("assistant", response)
                st.rerun()
        
        # About section with maximum readability
        st.markdown("---")
        st.markdown("## 🎯 Why Choose PharmBot?")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🔬 Evidence-Based")
            st.write("All information is grounded in scientific literature and current pharmaceutical knowledge.")
            
            st.markdown("### 🎓 Educational") 
            st.write("Designed specifically for learning, with clear explanations and clinical context.")
            
            st.markdown("### 💬 Interactive")
            st.write("Engage in natural conversations and ask follow-up questions for deeper understanding.")
        

        
        # Footer with disclaimer
        st.markdown("---")
        st.error("⚠️ **Important Disclaimer**: PharmBot is designed for educational purposes only. The information provided should not replace professional medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals for clinical decisions and patient care.")
    
    else:
        # Current conversation header
        current_conv = st.session_state.conversations[st.session_state.current_conversation_id]
        
        # Conversation header
        st.markdown(f"### 💬 {current_conv['title']}")
        
        st.markdown("---")
        
        # Display current conversation
        display_chat_messages()
        
        # Chat input with enhanced placeholder
        placeholder_text = "Ask me anything about pharmacology..."
        if prompt := st.chat_input(placeholder_text):
            # Add user message
            add_message_to_current_conversation("user", prompt)
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get and display bot response with streaming
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                
                try:
                    # Show initial thinking message
                    message_placeholder.markdown("🤔 Thinking...")
                    
                    # Try streaming first
                    stream_worked = False
                    for chunk in get_bot_response_stream(prompt, FIXED_MODEL):
                        stream_worked = True
                        full_response += chunk
                        # Update the display with current response + cursor
                        message_placeholder.markdown(full_response + "▌")
                        time.sleep(0.02)  # Small delay to make streaming visible
                    
                    # If streaming worked, show final response
                    if stream_worked:
                        message_placeholder.markdown(full_response)
                    else:
                        # Fallback to non-streaming if no chunks received
                        message_placeholder.markdown("🔄 Falling back to standard response...")
                        full_response = get_bot_response(prompt, FIXED_MODEL)
                        message_placeholder.markdown(full_response)
                    
                except Exception as e:
                    # Fallback to non-streaming on error
                    try:
                        message_placeholder.markdown("🔄 Streaming failed, trying standard response...")
                        full_response = get_bot_response(prompt, FIXED_MODEL)
                        message_placeholder.markdown(full_response)
                    except Exception as e2:
                        error_msg = f"❌ Error: {str(e2)}"
                        message_placeholder.markdown(error_msg)
                        full_response = error_msg
            
            # Add bot response to conversation
            add_message_to_current_conversation("assistant", full_response)

if __name__ == "__main__":
    main()