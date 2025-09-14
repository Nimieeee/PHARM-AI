"""
PharmGPT - AI Pharmacology Assistant
Main Homepage - Multipage Streamlit Application
"""

import streamlit as st
from utils.session_manager import initialize_session_state
from utils.theme import apply_theme
from auth import initialize_auth_session
from config import APP_TITLE, APP_ICON

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    """Main homepage entry point."""
    # Initialize session state and authentication
    initialize_session_state()
    initialize_auth_session()
    
    # Apply theme
    apply_theme()
    
    # Render homepage
    render_homepage()

def render_homepage():
    """Render the main homepage with authentication-aware content."""
    
    # Custom CSS for beautiful homepage
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    .auth-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.75rem 2rem;
        border: none;
        border-radius: 25px;
        font-size: 1.1rem;
        font-weight: bold;
        margin: 0.5rem;
        cursor: pointer;
        text-decoration: none;
        display: inline-block;
        transition: transform 0.2s;
    }
    .auth-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .welcome-text {
        font-size: 1.2rem;
        text-align: center;
        margin: 2rem 0;
        color: #555;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>💊 PharmGPT</h1>
        <h3>AI Pharmacology Assistant</h3>
        <p>Your intelligent companion for pharmacology learning and research</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check authentication status
    authenticated = st.session_state.get('authenticated', False)
    username = st.session_state.get('username', '')
    
    if authenticated:
        # Authenticated user view
        st.markdown(f"""
        <div class="welcome-text">
            <h2>Welcome back, {username}! 👋</h2>
            <p>Ready to explore pharmacology with AI assistance?</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Center the chatbot button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Start Chatting", use_container_width=True, type="primary"):
                st.switch_page("pages/3_💬_Chatbot.py")
        
        # Show features for authenticated users
        st.markdown("### ✨ What you can do:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <h4>🤖 AI-Powered Conversations</h4>
                <p>Get expert answers on drug mechanisms, interactions, and clinical pharmacology</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="feature-card">
                <h4>📚 Document Analysis</h4>
                <p>Upload PDFs, documents, and images for enhanced, context-aware responses</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <h4>💬 Persistent Conversations</h4>
                <p>Your chat history is saved and organized for easy reference</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="feature-card">
                <h4>⚡ Multiple AI Models</h4>
                <p>Switch between Normal and Turbo modes for different response styles</p>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Unauthenticated user view
        st.markdown("""
        <div class="welcome-text">
            <h2>Welcome to PharmGPT! 🎓</h2>
            <p>Your AI-powered pharmacology learning companion</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Authentication buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            col_signin, col_signup = st.columns(2)
            
            with col_signin:
                if st.button("🔐 Sign In", use_container_width=True, type="primary"):
                    st.switch_page("pages/2_🔐_Sign_In.py")
            
            with col_signup:
                if st.button("📝 Sign Up", use_container_width=True):
                    st.switch_page("pages/2_🔐_Sign_In.py")
        
        # Show features for unauthenticated users
        st.markdown("### 🌟 Key Features:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="feature-card">
                <h4>🔬 Expert Pharmacology Knowledge</h4>
                <p>Comprehensive understanding of drug mechanisms, interactions, and clinical applications</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="feature-card">
                <h4>🎯 Educational Focus</h4>
                <p>Designed specifically for students, researchers, and healthcare professionals</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="feature-card">
                <h4>🔒 Secure & Private</h4>
                <p>Your conversations and documents are kept private and secure</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="feature-card">
                <h4>📱 Modern Interface</h4>
                <p>ChatGPT-style interface with document upload and conversation management</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Example questions
        st.markdown("### 💡 Example Questions:")
        st.markdown("""
        - "Explain the mechanism of action of ACE inhibitors"
        - "What are the major drug interactions with warfarin?"
        - "How do beta-blockers work in cardiovascular disease?"
        - "Describe the pharmacokinetics of digoxin"
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p><strong>Educational Use Only</strong> - Always consult healthcare professionals for clinical decisions</p>
        <p>Built with ❤️ using Streamlit • Powered by AI</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()