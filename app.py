"""
PharmGPT - AI Pharmacology Assistant
Main Homepage - Multipage Streamlit Application
"""

import streamlit as st
import logging
from utils.session_manager import initialize_session_state
from utils.theme import apply_theme
from auth import initialize_auth_session
from config import APP_TITLE, APP_ICON

# Configure logging
logger = logging.getLogger(__name__)

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

def get_user_stats():
    """Get user statistics for the homepage."""
    try:
        if not st.session_state.get('authenticated'):
            return {}
        
        from utils.conversation_manager import get_conversation_stats
        stats = get_conversation_stats()
        
        # Add document count
        total_documents = 0
        if 'conversation_documents' in st.session_state:
            for conv_docs in st.session_state.conversation_documents.values():
                total_documents += len(conv_docs)
        
        stats['total_documents'] = total_documents
        stats['last_active'] = 'Today'  # Simplified for now
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return {}

def get_recent_conversations():
    """Get recent conversations for the homepage."""
    try:
        conversations = st.session_state.get('conversations', {})
        
        # Sort by updated_at (most recent first)
        sorted_conversations = sorted(
            conversations.items(),
            key=lambda x: x[1].get('updated_at', x[1].get('created_at', '')),
            reverse=True
        )
        
        recent = []
        for conv_id, conv_data in sorted_conversations:
            # Format last updated time
            try:
                from datetime import datetime
                updated_at = datetime.fromisoformat(conv_data.get('updated_at', conv_data.get('created_at', '')))
                last_updated = updated_at.strftime('%m/%d %H:%M')
            except:
                last_updated = 'Recently'
            
            # Get model icon
            model = conv_data.get('model', 'normal')
            model_icon = "⚡" if model == "turbo" else "🧠"
            
            recent.append({
                'id': conv_id,
                'title': conv_data.get('title', 'Untitled Chat'),
                'message_count': len(conv_data.get('messages', [])),
                'last_updated': last_updated,
                'model_icon': model_icon
            })
        
        return recent
        
    except Exception as e:
        logger.error(f"Error getting recent conversations: {e}")
        return []

def export_all_conversations(format_type: str):
    """Export all user conversations to a single file."""
    try:
        conversations = st.session_state.get('conversations', {})
        
        if not conversations:
            st.error("❌ No conversations to export")
            return
        
        with st.spinner(f"Exporting all conversations to {format_type.upper()}..."):
            from utils.export_manager import ConversationExporter
            
            # Create combined conversation data
            combined_data = {
                'title': f"All PharmGPT Conversations - {st.session_state.username}",
                'messages': [],
                'model': 'combined',
                'export_type': 'bulk',
                'conversation_count': len(conversations),
                'total_messages': sum(len(conv.get('messages', [])) for conv in conversations.values())
            }
            
            # Sort conversations by creation date
            sorted_conversations = sorted(
                conversations.items(),
                key=lambda x: x[1].get('created_at', ''),
                reverse=False  # Oldest first for chronological order
            )
            
            # Combine all messages with conversation separators
            for conv_id, conv_data in sorted_conversations:
                # Add conversation separator
                separator_message = {
                    'role': 'system',
                    'content': f"=== CONVERSATION: {conv_data.get('title', 'Untitled')} ===",
                    'timestamp': conv_data.get('created_at', ''),
                    'conversation_id': conv_id
                }
                combined_data['messages'].append(separator_message)
                
                # Add all messages from this conversation
                for message in conv_data.get('messages', []):
                    message_copy = message.copy()
                    message_copy['conversation_id'] = conv_id
                    message_copy['conversation_title'] = conv_data.get('title', 'Untitled')
                    combined_data['messages'].append(message_copy)
                
                # Add end separator
                end_separator = {
                    'role': 'system',
                    'content': f"=== END OF CONVERSATION ===",
                    'timestamp': conv_data.get('updated_at', conv_data.get('created_at', '')),
                    'conversation_id': conv_id
                }
                combined_data['messages'].append(end_separator)
            
            # Export using the conversation exporter
            exporter = ConversationExporter()
            exported_data = exporter.export_conversation(combined_data, format_type)
            
            if exported_data:
                # Generate filename
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"PharmGPT_All_Conversations_{st.session_state.username}_{timestamp}.{format_type}"
                
                # Provide download
                mime_types = {
                    'pdf': 'application/pdf',
                    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'txt': 'text/plain',
                    'md': 'text/markdown'
                }
                
                st.download_button(
                    label=f"📥 Download All Conversations ({format_type.upper()})",
                    data=exported_data,
                    file_name=filename,
                    mime=mime_types.get(format_type, 'application/octet-stream'),
                    use_container_width=True
                )
                
                st.success(f"✅ All conversations exported to {format_type.upper()}!")
                
                # Show export statistics
                file_size = len(exported_data)
                st.info(f"""
                📊 **Export Summary:**
                - **Format:** {format_type.upper()}
                - **Conversations:** {combined_data['conversation_count']}
                - **Total Messages:** {combined_data['total_messages']}
                - **File Size:** {file_size:,} bytes
                """)
                
            else:
                st.error(f"❌ Failed to export conversations to {format_type.upper()}")
                
    except Exception as e:
        logger.error(f"Bulk export error: {e}")
        st.error(f"❌ Export failed: {str(e)}")
        
        # Show helpful error message
        if "reportlab" in str(e).lower():
            st.info("💡 PDF export requires additional dependencies. Try Text export instead.")
        elif "docx" in str(e).lower():
            st.info("💡 Word export requires additional dependencies. Try Text export instead.")

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
        # Load user stats
        user_stats = get_user_stats()
        
        # Authenticated user view with stats
        st.markdown(f"""
        <div class="welcome-text">
            <h2>Welcome back, {username}! 👋</h2>
            <p>Ready to continue your pharmacology learning journey?</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show user stats
        if user_stats['total_conversations'] > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("💬 Conversations", user_stats['total_conversations'])
            
            with col2:
                st.metric("📝 Messages", user_stats['total_messages'])
            
            with col3:
                st.metric("📚 Documents", user_stats.get('total_documents', 0))
            
            with col4:
                st.metric("🕒 Last Active", user_stats.get('last_active', 'Today'))
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Continue Chatting", use_container_width=True, type="primary"):
                st.switch_page("pages/3_💬_Chatbot.py")
        
        # Export options for users with conversations
        if user_stats['total_conversations'] > 0:
            st.markdown("---")
            st.markdown("### 📤 Export Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📄 Export All as PDF", use_container_width=True):
                    export_all_conversations('pdf')
            
            with col2:
                if st.button("📝 Export All as Word", use_container_width=True):
                    export_all_conversations('docx')
            
            with col3:
                if st.button("📋 Export All as Text", use_container_width=True):
                    export_all_conversations('txt')
        
        # Recent conversations
        if user_stats['total_conversations'] > 0:
            st.markdown("### 📋 Recent Conversations")
            recent_conversations = get_recent_conversations()
            
            for conv in recent_conversations[:3]:  # Show last 3 conversations
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.markdown(f"**💬 {conv['title']}**")
                        st.caption(f"{conv['message_count']} messages • {conv['last_updated']}")
                    
                    with col2:
                        if st.button("Open", key=f"open_{conv['id']}", use_container_width=True):
                            st.session_state.current_conversation_id = conv['id']
                            st.switch_page("pages/3_💬_Chatbot.py")
                    
                    with col3:
                        st.markdown(f"**{conv['model_icon']}**")
            
            if user_stats['total_conversations'] > 3:
                st.info(f"📁 {user_stats['total_conversations'] - 3} more conversations available in the chatbot")
        
        # Export statistics
        if user_stats['total_conversations'] > 0:
            with st.expander("📊 Export Statistics & Options"):
                st.markdown("**Available Export Formats:**")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown("""
                    **📄 PDF**
                    - Professional format
                    - Great for printing
                    - Preserves formatting
                    """)
                
                with col2:
                    st.markdown("""
                    **📝 Word (DOCX)**
                    - Editable format
                    - Easy to share
                    - Professional layout
                    """)
                
                with col3:
                    st.markdown("""
                    **📋 Plain Text**
                    - Universal compatibility
                    - Lightweight
                    - Easy to read
                    """)
                
                with col4:
                    st.markdown("""
                    **📖 Markdown**
                    - Developer-friendly
                    - Version control ready
                    - Clean formatting
                    """)
                
                st.markdown("---")
                st.info("💡 **Tip:** Individual conversations can also be exported from the chatbot sidebar!")
        
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