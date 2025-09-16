"""
Contact Support Page
"""

import streamlit as st
import json
import os
from datetime import datetime
from utils.session_manager import initialize_session_state
from utils.theme import apply_theme
from auth import initialize_auth_session
from config import APP_TITLE, APP_ICON

# Page configuration
st.set_page_config(
    page_title=f"Contact Support - {APP_TITLE}",
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    """Main contact support page."""
    # Initialize session state and authentication
    initialize_session_state()
    initialize_auth_session()
    
    # Apply theme
    apply_theme()
    
    # Render contact support page
    render_contact_support()

def save_support_ticket(ticket_data):
    """Save support ticket to local file."""
    try:
        # Create support tickets directory if it doesn't exist
        support_dir = "user_data/support_tickets"
        os.makedirs(support_dir, exist_ok=True)
        
        # Generate ticket ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        username = st.session_state.get('username', 'anonymous')
        ticket_id = f"TICKET_{username}_{timestamp}"
        
        # Add metadata to ticket
        ticket_data.update({
            'ticket_id': ticket_id,
            'created_at': datetime.now().isoformat(),
            'status': 'open',
            'username': username,
            'authenticated': st.session_state.get('authenticated', False)
        })
        
        # Save to file
        ticket_file = os.path.join(support_dir, f"{ticket_id}.json")
        with open(ticket_file, 'w') as f:
            json.dump(ticket_data, f, indent=2)
        
        return ticket_id
        
    except Exception as e:
        st.error(f"Error saving support ticket: {e}")
        return None

def render_contact_support():
    """Render the contact support page."""
    
    # Custom CSS for the contact page
    st.markdown("""
    <style>
    .support-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .support-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    .contact-method {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #e9ecef;
    }
    .faq-item {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 3px solid #28a745;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header with logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("pharmGPT.png", width=150)
        except:
            st.markdown("# 💊 PharmGPT")  # Fallback if logo not found
    
    st.markdown("""
    <div class="support-header">
        <h1>📞 Contact Support</h1>
        <h3>We're here to help!</h3>
        <p>Get assistance with PharmGPT or report any issues</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Navigation back to main app
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        col_back, col_chat = st.columns(2)
        with col_back:
            if st.button("🏠 Back to Home", use_container_width=True):
                st.switch_page("app.py")
        with col_chat:
            if st.session_state.get('authenticated', False):
                if st.button("💬 Back to Chat", use_container_width=True, type="primary"):
                    st.switch_page("pages/3_💬_Chatbot.py")
    
    st.markdown("---")
    
    # Check if admin mode is enabled
    admin_mode = st.session_state.get('admin_mode', False) and st.session_state.get('username') == 'admin'
    
    if admin_mode:
        # Admin Panel
        st.success("🛠️ **Admin Panel Active** - You have access to support management tools.")
        
        # Admin controls
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👤 Switch to User Mode", use_container_width=True):
                st.session_state.admin_mode = False
                st.rerun()
        with col2:
            if st.button("🏠 Back to App", use_container_width=True):
                st.session_state.admin_mode = False
                st.switch_page("app.py")
        
        st.markdown("---")
        
        # Admin tabs
        tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🎫 All Tickets", "📈 Statistics"])
        
        with tab1:
            render_admin_dashboard()
        
        with tab2:
            render_admin_tickets()
        
        with tab3:
            render_admin_statistics()
    
    else:
        # Regular user tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Submit Ticket", "❓ FAQ", "📧 Contact Info", "🔧 System Info"])
        
        with tab1:
            render_support_ticket_form()
        
        with tab2:
            render_faq_section()
        
        with tab3:
            render_contact_info()
        
        with tab4:
            render_system_info()

def render_support_ticket_form():
    """Render the support ticket submission form."""
    st.markdown("### 📝 Submit a Support Ticket")
    st.markdown("Fill out the form below and we'll get back to you as soon as possible.")
    
    with st.form("support_ticket_form"):
        # User information
        if st.session_state.get('authenticated', False):
            st.info(f"Logged in as: **{st.session_state.get('username', 'Unknown')}**")
            contact_email = st.text_input("Contact Email", placeholder="your.email@example.com")
        else:
            st.warning("You're not logged in. Please provide your contact information.")
            contact_name = st.text_input("Your Name", placeholder="John Doe")
            contact_email = st.text_input("Contact Email*", placeholder="your.email@example.com")
        
        # Issue details
        issue_type = st.selectbox(
            "Issue Type*",
            [
                "Technical Issue",
                "Login/Authentication Problem",
                "Feature Request",
                "Bug Report",
                "Performance Issue",
                "Document Upload Problem",
                "AI Response Issue",
                "Account Issue",
                "Other"
            ]
        )
        
        priority = st.selectbox(
            "Priority",
            ["Low", "Medium", "High", "Critical"],
            index=1
        )
        
        subject = st.text_input("Subject*", placeholder="Brief description of the issue")
        
        description = st.text_area(
            "Detailed Description*",
            placeholder="Please describe the issue in detail. Include steps to reproduce if applicable.",
            height=150
        )
        
        # Additional information
        st.markdown("#### Additional Information")
        
        browser_info = st.text_input("Browser/Device", placeholder="Chrome 120, Safari on iPhone, etc.")
        
        error_message = st.text_area(
            "Error Messages",
            placeholder="Copy and paste any error messages you received",
            height=100
        )
        
        # Attachments note
        st.info("📎 **Note**: For file attachments or screenshots, please mention them in your description and we'll follow up via email.")
        
        # Submit button
        submitted = st.form_submit_button("🚀 Submit Ticket", type="primary", use_container_width=True)
        
        if submitted:
            # Validate required fields
            if not contact_email:
                st.error("❌ Contact email is required")
                return
            
            if not subject:
                st.error("❌ Subject is required")
                return
            
            if not description:
                st.error("❌ Detailed description is required")
                return
            
            # Prepare ticket data
            ticket_data = {
                'contact_email': contact_email,
                'issue_type': issue_type,
                'priority': priority,
                'subject': subject,
                'description': description,
                'browser_info': browser_info,
                'error_message': error_message
            }
            
            # Add name if not authenticated
            if not st.session_state.get('authenticated', False):
                ticket_data['contact_name'] = contact_name
            else:
                ticket_data['contact_name'] = st.session_state.get('username', 'User')
            
            # Save ticket
            ticket_id = save_support_ticket(ticket_data)
            
            if ticket_id:
                # Send confirmation email
                from utils.email_manager import send_ticket_confirmation
                email_sent = send_ticket_confirmation(ticket_data)
                
                st.success(f"✅ **Support ticket submitted successfully!**")
                st.info(f"**Ticket ID**: {ticket_id}")
                
                if email_sent:
                    st.success(f"📧 **Confirmation email sent to**: {contact_email}")
                else:
                    st.warning("⚠️ Ticket saved but confirmation email failed to send")
                
                st.markdown("""
                **What happens next?**
                - You should receive an email confirmation shortly
                - Our support team will review your ticket
                - We typically respond within 24-48 hours
                - You can reference your ticket ID in future communications
                """)
                
                # Show confirmation preview
                with st.expander("📧 Email Confirmation Preview"):
                    from utils.email_manager import get_confirmation_template
                    confirmation_text = get_confirmation_template(ticket_data)
                    st.text(confirmation_text)
                    
            else:
                st.error("❌ Failed to submit ticket. Please try again or contact us directly.")

def render_faq_section():
    """Render the FAQ section."""
    st.markdown("### ❓ Frequently Asked Questions")
    
    faqs = [
        {
            "question": "How do I sign up for PharmGPT?",
            "answer": "Click the 'Sign Up' button on the homepage and create an account with your email and password. No email verification is required for the demo version."
        },
        {
            "question": "Can I upload documents to enhance AI responses?",
            "answer": "Yes! You can upload PDFs, text files, and images. The AI will use your documents to provide more relevant and personalized responses."
        },
        {
            "question": "What's the difference between Normal and Turbo modes?",
            "answer": "Normal mode gives faster, more concise answers. Turbo mode provides detailed, comprehensive responses. You can switch between modes in the chatbot settings."
        },
        {
            "question": "Are my conversations saved?",
            "answer": "Yes, all your conversations are automatically saved and can be accessed from the sidebar. You can create multiple conversations and switch between them."
        },
        {
            "question": "Is PharmGPT suitable for clinical decision-making?",
            "answer": "No. PharmGPT is designed for educational purposes only. Always consult qualified healthcare professionals for clinical decisions and patient care."
        },
        {
            "question": "Can I delete my conversations?",
            "answer": "Yes, you can delete individual conversations using the delete button (🗑️) next to each conversation in the sidebar."
        },
        {
            "question": "What file formats can I upload?",
            "answer": "You can upload PDF files, text files (.txt), and images (PNG, JPG, JPEG). Images are processed using OCR to extract text content."
        },
        {
            "question": "How do I reset my password?",
            "answer": "Currently, password reset is not available in the demo version. If you forget your password, you'll need to create a new account."
        },
        {
            "question": "Why am I getting slow responses?",
            "answer": "Response speed depends on your internet connection and the complexity of your question."
        },
        {
            "question": "Can I export my conversation history?",
            "answer": "Currently, conversation export is not available. This feature may be added in future updates based on user feedback."
        }
    ]
    
    for i, faq in enumerate(faqs):
        with st.expander(f"**{faq['question']}**"):
            st.markdown(f"<div class='faq-item'>{faq['answer']}</div>", unsafe_allow_html=True)

def render_contact_info():
    """Render contact information."""
    st.markdown("### 📧 Contact Information")
    
    st.markdown("""
    <div class="contact-method">
        <h4>📧 Email Support</h4>
        <p><strong>support@pharmgpt.demo</strong></p>
        <p>For general inquiries, technical issues, and feature requests</p>
        <p><em>Response time: 24-48 hours</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="contact-method">
        <h4>🐛 Bug Reports</h4>
        <p><strong>bugs@pharmgpt.demo</strong></p>
        <p>Report technical issues, errors, or unexpected behavior</p>
        <p><em>Response time: 12-24 hours for critical issues</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="contact-method">
        <h4>💡 Feature Requests</h4>
        <p><strong>features@pharmgpt.demo</strong></p>
        <p>Suggest new features or improvements</p>
        <p><em>Response time: 48-72 hours</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("### 🕒 Support Hours")
    st.info("""
    **Monday - Friday**: 9:00 AM - 6:00 PM (EST)
    
    **Saturday - Sunday**: Limited support for critical issues only
    
    **Note**: This is a demo application. In a production environment, support hours and response times would be clearly defined based on your service level agreement.
    """)

def render_system_info():
    """Render system information for troubleshooting."""
    st.markdown("### 🔧 System Information")
    st.markdown("This information helps our support team troubleshoot issues more effectively.")
    
    # User session info
    st.markdown("#### User Session")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Authenticated**: {'Yes' if st.session_state.get('authenticated', False) else 'No'}")
        if st.session_state.get('authenticated', False):
            st.info(f"**Username**: {st.session_state.get('username', 'Unknown')}")
    
    with col2:
        st.info(f"**Session ID**: {st.session_state.get('session_id', 'Not available')}")
        st.info(f"**Current Page**: Contact Support")
    
    # App statistics
    st.markdown("#### App Statistics")
    col1, col2 = st.columns(2)
    
    with col1:
        conversations_count = len(st.session_state.get('conversations', {}))
        st.info(f"**Total Conversations**: {conversations_count}")
        
        current_conv_id = st.session_state.get('current_conversation_id')
        st.info(f"**Current Conversation**: {'Set' if current_conv_id else 'None'}")
    
    with col2:
        total_messages = 0
        for conv in st.session_state.get('conversations', {}).values():
            total_messages += len(conv.get('messages', []))
        st.info(f"**Total Messages**: {total_messages}")
        
        chat_messages_count = len(st.session_state.get('chat_messages', []))
        st.info(f"**Current Chat Messages**: {chat_messages_count}")
    
    # System capabilities
    st.markdown("#### System Capabilities")
    
    # Check OCR status
    try:
        from utils.ocr_manager import get_ocr_status
        ocr_status = get_ocr_status()
        
        col1, col2 = st.columns(2)
        with col1:
            if ocr_status['ocr_working']:
                st.success("✅ **OCR**: Available")
            else:
                st.error("❌ **OCR**: Not Available")
        
        with col2:
            if ocr_status.get('easyocr_available'):
                st.success("✅ **EasyOCR**: Ready")
            elif ocr_status.get('tesseract_available'):
                st.success("✅ **Tesseract**: Ready")
            else:
                st.warning("⚠️ **OCR Engine**: None Available")
                
    except Exception as e:
        st.error(f"❌ **OCR Status**: Error checking ({str(e)})")
    
    # Environment info
    st.markdown("#### Environment")
    import sys
    import platform
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Streamlit Version**: {st.__version__}")
        st.info(f"**Python Version**: {sys.version.split()[0]}")
    
    with col2:
        st.info(f"**Platform**: {platform.system()} {platform.release()}")
        st.info(f"**Architecture**: {platform.machine()}")
    
    # Export system info button
    if st.button("📋 Copy System Info to Clipboard", use_container_width=True):
        system_info = f"""
PharmGPT System Information
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

User Session:
- Authenticated: {'Yes' if st.session_state.get('authenticated', False) else 'No'}
- Username: {st.session_state.get('username', 'Not logged in')}
- Session ID: {st.session_state.get('session_id', 'Not available')}

App Statistics:
- Total Conversations: {len(st.session_state.get('conversations', {}))}
- Total Messages: {sum(len(conv.get('messages', [])) for conv in st.session_state.get('conversations', {}).values())}
- Current Chat Messages: {len(st.session_state.get('chat_messages', []))}

Environment:
- Streamlit Version: {st.__version__}
- Python Version: {sys.version.split()[0]}
- Platform: {platform.system()} {platform.release()}
- Architecture: {platform.machine()}
"""
        st.code(system_info, language="text")
        st.success("✅ System information displayed above. Copy and paste this into your support ticket if requested.")

def render_admin_dashboard():
    """Render the admin dashboard."""
    from utils.support_manager import get_support_stats, update_support_ticket
    
    st.markdown("### 📊 Support Dashboard")
    
    # Get stats
    stats = get_support_stats()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Tickets", stats['total_tickets'])
    
    with col2:
        st.metric("Open Tickets", stats['open_tickets'])
    
    with col3:
        st.metric("Closed Tickets", stats['closed_tickets'])
    
    with col4:
        resolution_rate = 0
        if stats['total_tickets'] > 0:
            resolution_rate = round((stats['closed_tickets'] / stats['total_tickets']) * 100, 1)
        st.metric("Resolution Rate", f"{resolution_rate}%")
    
    # Recent tickets
    st.markdown("### 🕒 Recent Tickets")
    
    if stats['recent_tickets']:
        for ticket in stats['recent_tickets']:
            with st.expander(f"🎫 {ticket.get('ticket_id', 'Unknown')} - {ticket.get('subject', 'No Subject')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Type**: {ticket.get('issue_type', 'Unknown')}")
                    st.write(f"**Priority**: {ticket.get('priority', 'Medium')}")
                    st.write(f"**Status**: {ticket.get('status', 'open')}")
                
                with col2:
                    st.write(f"**User**: {ticket.get('username', 'Anonymous')}")
                    st.write(f"**Email**: {ticket.get('contact_email', 'Not provided')}")
                    created_at = ticket.get('created_at', '')
                    if created_at:
                        try:
                            dt = datetime.fromisoformat(created_at)
                            st.write(f"**Created**: {dt.strftime('%Y-%m-%d %H:%M')}")
                        except:
                            st.write(f"**Created**: {created_at}")
                
                st.write(f"**Description**: {ticket.get('description', 'No description')}")
                
                # Quick actions
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Mark as Closed", key=f"close_{ticket.get('ticket_id')}"):
                        if update_support_ticket(ticket.get('ticket_id'), {'status': 'closed'}):
                            st.success("Ticket marked as closed!")
                            st.rerun()
                
                with col2:
                    if st.button(f"Mark as Open", key=f"open_{ticket.get('ticket_id')}"):
                        if update_support_ticket(ticket.get('ticket_id'), {'status': 'open'}):
                            st.success("Ticket marked as open!")
                            st.rerun()
    else:
        st.info("No support tickets found.")

def render_admin_tickets():
    """Render all tickets view for admin."""
    from utils.support_manager import get_support_tickets
    
    st.markdown("### 🎫 All Support Tickets")
    
    # Get all tickets
    tickets = get_support_tickets()
    
    if not tickets:
        st.info("No support tickets found.")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "open", "closed"])
    
    with col2:
        # Get unique issue types
        issue_types = list(set([t.get('issue_type', 'Unknown') for t in tickets]))
        type_filter = st.selectbox("Filter by Type", ["All"] + issue_types)
    
    with col3:
        priority_filter = st.selectbox("Filter by Priority", ["All", "Low", "Medium", "High", "Critical"])
    
    # Apply filters
    filtered_tickets = tickets
    
    if status_filter != "All":
        filtered_tickets = [t for t in filtered_tickets if t.get('status') == status_filter]
    
    if type_filter != "All":
        filtered_tickets = [t for t in filtered_tickets if t.get('issue_type') == type_filter]
    
    if priority_filter != "All":
        filtered_tickets = [t for t in filtered_tickets if t.get('priority') == priority_filter]
    
    st.write(f"Showing {len(filtered_tickets)} of {len(tickets)} tickets")
    
    # Display tickets
    for ticket in filtered_tickets:
        with st.container():
            # Ticket header
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{ticket.get('ticket_id', 'Unknown')}**")
                st.caption(ticket.get('subject', 'No Subject'))
            
            with col2:
                status = ticket.get('status', 'open')
                if status == 'open':
                    st.error(f"🔴 {status.upper()}")
                else:
                    st.success(f"🟢 {status.upper()}")
            
            with col3:
                priority = ticket.get('priority', 'Medium')
                if priority == 'Critical':
                    st.error(f"🚨 {priority}")
                elif priority == 'High':
                    st.warning(f"⚠️ {priority}")
                else:
                    st.info(f"ℹ️ {priority}")
            
            with col4:
                created_at = ticket.get('created_at', '')
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at)
                        st.caption(dt.strftime('%m/%d %H:%M'))
                    except:
                        st.caption(created_at[:10])
            
            # Expandable details
            with st.expander("View Details"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**User**: {ticket.get('username', 'Anonymous')}")
                    st.write(f"**Email**: {ticket.get('contact_email', 'Not provided')}")
                    st.write(f"**Type**: {ticket.get('issue_type', 'Unknown')}")
                    st.write(f"**Browser**: {ticket.get('browser_info', 'Not provided')}")
                
                with col2:
                    st.write(f"**Priority**: {ticket.get('priority', 'Medium')}")
                    st.write(f"**Status**: {ticket.get('status', 'open')}")
                    st.write(f"**Authenticated**: {'Yes' if ticket.get('authenticated') else 'No'}")
                
                st.write("**Description**:")
                st.write(ticket.get('description', 'No description provided'))
                
                if ticket.get('error_message'):
                    st.write("**Error Message**:")
                    st.code(ticket.get('error_message'))
            
            st.markdown("---")

def render_admin_statistics():
    """Render statistics view for admin."""
    from utils.support_manager import get_support_stats, export_support_tickets
    
    st.markdown("### 📈 Support Statistics")
    
    stats = get_support_stats()
    
    # Overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Issue Types")
        if stats['by_type']:
            for issue_type, count in stats['by_type'].items():
                st.write(f"**{issue_type}**: {count}")
        else:
            st.info("No data available")
    
    with col2:
        st.markdown("#### Priority Distribution")
        if stats['by_priority']:
            for priority, count in stats['by_priority'].items():
                st.write(f"**{priority}**: {count}")
        else:
            st.info("No data available")
    
    # Export functionality
    st.markdown("#### Export Data")
    if st.button("📥 Export All Tickets (JSON)"):
        export_file = export_support_tickets('json')
        if export_file:
            st.success(f"✅ Tickets exported to: {export_file}")
        else:
            st.error("❌ Failed to export tickets")
if _
_name__ == "__main__":
    main()