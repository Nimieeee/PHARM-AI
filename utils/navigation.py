"""
Navigation System for Multipage App
"""

import streamlit as st

def render_navigation():
    """Render navigation sidebar for multipage app."""
    # Handle authentication flow
    if not st.session_state.get('authenticated', False):
        # Show navigation for unauthenticated users
        render_public_navigation()
    else:
        # Show navigation for authenticated users
        render_authenticated_navigation()

def render_public_navigation():
    """Render minimal navigation for unauthenticated users."""
    with st.sidebar:
        st.markdown("# 💊 PharmGPT")
        st.markdown("### Navigation")
        
        # Home button
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")
        
        # Sign In button
        if st.button("🔐 Sign In", use_container_width=True, type="primary"):
            st.switch_page("pages/2_🔐_Sign_In.py")
        
        # Contact Support button
        if st.button("📞 Contact Support", use_container_width=True):
            st.switch_page("pages/4_📞_Contact_Support.py")
        
        st.markdown("---")
        st.markdown("### About PharmGPT")
        st.markdown("""
        Your AI-powered pharmacology learning companion.
        
        **Features:**
        - Expert pharmacology knowledge
        - Document analysis
        - Conversation history
        - Multiple AI models
        """)

def render_authenticated_navigation():
    """Render navigation for authenticated users."""
    with st.sidebar:
        st.markdown("# 💊 PharmGPT")
        st.markdown(f"**Welcome, {st.session_state.username}!**")
        
        st.markdown("### Navigation")
        
        # Home button
        if st.button("🏠 Home", use_container_width=True):
            st.switch_page("app.py")
        
        # Chatbot button
        if st.button("💬 Chatbot", use_container_width=True, type="primary"):
            st.switch_page("pages/3_💬_Chatbot.py")
        
        # Contact Support button
        if st.button("📞 Contact Support", use_container_width=True):
            st.switch_page("pages/4_📞_Contact_Support.py")
        
        # Admin Dashboard button (only for admin user)
        if st.session_state.get('username') == 'admin':
            if st.button("🛠️ Admin Dashboard", use_container_width=True):
                st.switch_page("pages/nimi_admin.py")
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            from auth import logout_current_user
            logout_current_user()
            st.switch_page("app.py")
        
        st.markdown("---")
        
        # Show conversation management if on chatbot page
        current_page = st.session_state.get('current_page', '')
        if current_page == 'chatbot' or 'Chatbot' in str(st.session_state.get('page', '')):
            render_conversation_sidebar()

def render_conversation_sidebar():
    """Render conversation management in sidebar."""
    st.markdown("### Conversations")
    
    # New conversation button
    if st.button("➕ New Chat", use_container_width=True):
        st.session_state.chat_messages = []
        st.session_state.current_conversation_id = None
        st.rerun()
    
    # Model selection
    st.markdown("### Settings")
    model_mode = st.selectbox(
        "AI Model",
        ["normal", "turbo"],
        index=0 if st.session_state.get('selected_model_mode', 'normal') == 'normal' else 1,
        format_func=lambda x: "🧠 Normal Mode" if x == "normal" else "⚡ Turbo Mode"
    )
    st.session_state.selected_model_mode = model_mode
    
    # Show conversation stats
    if st.session_state.get('chat_messages'):
        message_count = len(st.session_state.chat_messages)
        st.markdown(f"**Messages:** {message_count}")
    
    # OCR Status
    with st.expander("🔍 OCR Status"):
        try:
            from utils.ocr_manager import get_ocr_status
            ocr_status = get_ocr_status()
            
            if ocr_status['ocr_working']:
                st.success("✅ OCR Available")
                st.info("🔧 Tesseract: Ready")
            else:
                st.info("ℹ️ OCR Not Available")
                st.caption("Text extraction from images is not available")
                
        except Exception:
            st.info("ℹ️ OCR Status Unknown")
    
    # Tips
    with st.expander("💡 Tips"):
        st.markdown("""
        - Upload documents for enhanced responses
        - Use regenerate button to get different answers
        - Switch between Normal and Turbo modes
        - Your conversations are automatically saved
        - Upload images with text for OCR extraction
        """)