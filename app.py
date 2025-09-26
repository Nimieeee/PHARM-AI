"""
PharmGPT - AI Pharmacology Assistant
Main Application Entry Point - Clean Architecture
"""

import logging
import streamlit as st

# Import core modules
from core.config import config, APP_TITLE, APP_ICON
from core.auth import initialize_auth_session, is_authenticated, render_sign_in_form, render_user_info
from core.supabase_client import test_connection
from core.utils import ErrorHandler, validate_environment

# Configure logging
logging.basicConfig(
    level=config.LOG_LEVEL if hasattr(config, 'LOG_LEVEL') else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(**config.PAGE_CONFIG)


def apply_custom_css():
    """Apply custom CSS for better UI."""
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-good { background-color: #28a745; }
    .status-warning { background-color: #ffc107; }
    .status-error { background-color: #dc3545; }
    .stats-container {
        background: #e9ecef;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)


def render_status_indicator(status: bool, label: str) -> str:
    """Render status indicator with color."""
    color_class = "status-good" if status else "status-error"
    status_text = "✓" if status else "✗"
    return f'<span class="status-indicator {color_class}"></span>{label}: {status_text}'


def render_system_status():
    """Render system status information."""
    st.subheader("🏥 System Status")
    
    try:
        # Test database connection
        db_status = st.cache_data(test_connection, ttl=60)()  # Cache for 1 minute
        
        # Validate configuration
        config_validation = config.validate_configuration()
        
        # Check environment
        env_status = validate_environment()
        
        # Create status display
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Database & Configuration**")
            st.markdown(render_status_indicator(db_status, "Database Connection"), unsafe_allow_html=True)
            st.markdown(render_status_indicator(config_validation['supabase_url'], "Supabase URL"), unsafe_allow_html=True)
            st.markdown(render_status_indicator(config_validation['supabase_key'], "Supabase Key"), unsafe_allow_html=True)
            st.markdown(render_status_indicator(config_validation['mistral_key'], "Mistral API Key"), unsafe_allow_html=True)
        
        with col2:
            st.markdown("**Environment & Dependencies**")
            st.markdown(render_status_indicator(env_status['document_processing'], "Document Processing"), unsafe_allow_html=True)
            st.markdown(render_status_indicator(env_status['temp_directory'], "Temp Directory"), unsafe_allow_html=True)
            st.markdown(render_status_indicator(env_status['write_permissions'], "Write Permissions"), unsafe_allow_html=True)
            st.markdown(render_status_indicator(all(config_validation.values()), "Overall Status"), unsafe_allow_html=True)
        
        # Overall system ready indicator
        all_good = db_status and all(config_validation.values()) and env_status['document_processing']
        
        if all_good:
            st.success("🚀 All systems operational! PharmGPT is ready to use.")
        else:
            st.warning("⚠️ Some services may not be fully operational. Check configuration.")
            
            # Show detailed issues
            with st.expander("View Details"):
                if not db_status:
                    st.error("Database connection failed. Check Supabase credentials.")
                
                missing_configs = [k for k, v in config_validation.items() if not v]
                if missing_configs:
                    st.error(f"Missing configuration: {', '.join(missing_configs)}")
                
                if not env_status['document_processing']:
                    st.warning("Document processing libraries not available. File uploads may not work.")
        
    except Exception as e:
        ErrorHandler.handle_streamlit_error(e, "System Status Check")
        st.error("Unable to check system status.")


def render_features_overview():
    """Render features overview."""
    st.subheader("✨ Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>🔐 Secure Authentication</h4>
            <p>Enterprise-grade user authentication with persistent sessions. No more logout on refresh!</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>🤖 AI-Powered Responses</h4>
            <p>Advanced pharmacology AI using Mistral models for expert-level responses.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>📚 Document RAG System</h4>
            <p>Upload documents to each conversation for context-aware responses using pgvector.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="feature-card">
            <h4>💬 Conversation Management</h4>
            <p>Organize conversations with complete user isolation. Each conversation has its own knowledge base.</p>
        </div>
        """, unsafe_allow_html=True)


def render_user_stats():
    """Render user statistics if authenticated."""
    if not is_authenticated():
        return
    
    try:
        from core.conversations import get_conversation_stats
        stats = get_conversation_stats()
        
        if stats:
            st.subheader("📊 Your Usage Statistics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Conversations", stats.get('total_conversations', 0))
            
            with col2:
                st.metric("Messages", stats.get('total_messages', 0))
            
            with col3:
                st.metric("Active Chats", stats.get('active_conversations', 0))
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")


def render_getting_started():
    """Render getting started guide."""
    st.subheader("🚀 Getting Started")
    
    if is_authenticated():
        st.success("✅ You're signed in! Ready to start chatting.")
        st.info("💡 **Tip**: Visit the **💬 Chatbot** page to start your first conversation!")
        
        st.markdown("""
        **Quick Start Guide:**
        1. 🗨️ Go to the **Chatbot** page
        2. 📝 Start a new conversation
        3. 📄 Upload documents to add context (optional)
        4. 🤔 Ask your pharmacology questions
        5. 🧠 Get AI-powered responses with document context
        """)
    else:
        st.info("👆 Please sign in above to start using PharmGPT.")
        
        st.markdown("""
        **What you can do after signing in:**
        - 💬 Create unlimited conversations
        - 📚 Upload documents for each conversation
        - 🔍 Get context-aware AI responses
        - 📊 Track your usage statistics
        - 🔐 Enjoy persistent sessions (no logout on refresh!)
        """)


def render_homepage():
    """Render the main homepage content."""
    # Main header
    st.markdown(f"""
    <div class="main-header">
        <h1>{APP_ICON} {APP_TITLE}</h1>
        <h3>AI Pharmacology Assistant with Supabase + pgvector</h3>
        <p>Advanced RAG system • User isolation • Persistent sessions • Conversation-specific knowledge bases</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Authentication section
    if is_authenticated():
        st.success("🎉 Welcome back! You're successfully signed in.")
        render_user_info()
        render_user_stats()
    else:
        st.info("🔐 Sign in to access your personalized PharmGPT experience.")
        render_sign_in_form()
    
    # Features and status
    render_features_overview()
    render_getting_started()
    render_system_status()
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>{APP_TITLE} v{config.APP_VERSION} | Built with ❤️ for pharmacology education</p>
        <p>Powered by Supabase • pgvector • Mistral AI • Streamlit</p>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main application entry point."""
    try:
        # Initialize authentication session
        initialize_auth_session()
        
        # Apply custom styling
        apply_custom_css()
        
        # Render homepage
        render_homepage()
        
    except Exception as e:
        ErrorHandler.handle_streamlit_error(e, "Main Application", show_details=True)
        st.error("Application startup failed. Please refresh the page or contact support.")


if __name__ == "__main__":
    main()