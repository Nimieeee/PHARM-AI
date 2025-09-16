"""
Secure Admin Support Dashboard
Access restricted to admin users only
"""

import streamlit as st
import json
from datetime import datetime
from utils.support_manager import get_support_tickets, get_support_stats, update_support_ticket
from utils.session_manager import initialize_session_state
from utils.theme import apply_theme

# Page configuration
st.set_page_config(
    page_title="PharmGPT Admin Dashboard",
    page_icon="🛠️",
    layout="wide"
)

# Immediate access control - check if user is authenticated and is admin
initialize_session_state()

# Block access if user is not authenticated or not admin
if not st.session_state.get('authenticated', False) or st.session_state.get('username') != 'admin':
    st.error("🚫 **Access Denied**")
    st.markdown("This page is restricted to authorized administrators only.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Go to Homepage", use_container_width=True, type="primary"):
            st.switch_page("app.py")
    with col2:
        if st.button("🔐 Sign In", use_container_width=True):
            st.switch_page("pages/2_🔐_Sign_In.py")
    
    st.stop()

def authenticate_admin():
    """Simple admin authentication."""
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        st.title("🔐 Admin Authentication")
        
        # Logo
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            try:
                st.image("pharmGPT.png", width=150)
            except:
                st.markdown("# 💊 PharmGPT Admin")  # Fallback if logo not found
        
        st.markdown("### Enter Admin Credentials")
        
        with st.form("admin_login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                # Simple hardcoded admin check (in production, use proper authentication)
                if username == "admin" and password == "Equanimity465@":
                    st.session_state.admin_authenticated = True
                    st.success("✅ Authentication successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        
        st.markdown("---")
        st.info("If you're looking for user support, please visit our [Contact Support](/4_📞_Contact_Support) page.")
        st.stop()

def main():
    """Main admin support dashboard."""
    # Authenticate admin first
    authenticate_admin()
    
    initialize_session_state()
    apply_theme()
    
    # Logo
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        try:
            st.image("pharmGPT.png", width=150)
        except:
            st.markdown("# 💊 PharmGPT Admin")  # Fallback if logo not found
    
    st.title("🛠️ PharmGPT Admin Dashboard")
    st.caption("Secure Admin Access - Support Ticket Management")
    
    # Admin info banner
    st.success("✅ **Admin Access Granted** - Welcome, Admin!")
    
    # Navigation and logout
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Back to App"):
            st.switch_page("app.py")
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.admin_authenticated = False
            st.rerun()
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🎫 All Tickets", "📈 Statistics"])
    
    with tab1:
        render_dashboard()
    
    with tab2:
        render_all_tickets()
    
    with tab3:
        render_statistics()

def render_dashboard():
    """Render the main dashboard."""
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

def render_all_tickets():
    """Render all tickets view."""
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
                
                # Raw ticket data
                if st.checkbox(f"Show Raw Data", key=f"raw_{ticket.get('ticket_id')}"):
                    st.json(ticket)
            
            st.markdown("---")

def render_statistics():
    """Render statistics view."""
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
        from utils.support_manager import export_support_tickets
        export_file = export_support_tickets('json')
        if export_file:
            st.success(f"✅ Tickets exported to: {export_file}")
        else:
            st.error("❌ Failed to export tickets")

if __name__ == "__main__":
    main()