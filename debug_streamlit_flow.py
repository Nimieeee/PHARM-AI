"""
Diagnostic script to identify duplicate requests in Streamlit flow
"""

import streamlit as st
import logging
import time
from datetime import datetime

# Configure detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DebugTracker:
    """Track function calls to identify duplicates"""
    def __init__(self):
        self.calls = {}
        self.start_time = time.time()
    
    def track_call(self, function_name: str, details: str = ""):
        """Track a function call with timestamp"""
        current_time = time.time()
        if function_name not in self.calls:
            self.calls[function_name] = []
        
        call_info = {
            'timestamp': datetime.now().isoformat(),
            'elapsed': current_time - self.start_time,
            'details': details,
            'session_state': dict(st.session_state) if 'st' in globals() else {}
        }
        
        self.calls[function_name].append(call_info)
        logger.info(f"TRACKED: {function_name} - {details} (elapsed: {call_info['elapsed']:.3f}s)")
        
        # Detect duplicates
        if len(self.calls[function_name]) > 1:
            last_call = self.calls[function_name][-2]
            time_diff = call_info['elapsed'] - last_call['elapsed']
            if time_diff < 1.0:  # Less than 1 second between calls
                logger.warning(f"DUPLICATE DETECTED: {function_name} called again after {time_diff:.3f}s")
    
    def get_summary(self):
        """Get summary of all tracked calls"""
        summary = {}
        for func, calls in self.calls.items():
            summary[func] = {
                'total_calls': len(calls),
                'first_call': calls[0]['timestamp'] if calls else None,
                'last_call': calls[-1]['timestamp'] if calls else None,
                'duplicates': len([c for i, c in enumerate(calls) if i > 0 and c['elapsed'] - calls[i-1]['elapsed'] < 1.0])
            }
        return summary

# Global debug tracker
debug_tracker = DebugTracker()

def add_debug_logging():
    """Add debug logging to key functions"""
    
    # Patch initialize_session_state
    try:
        from utils.session_manager import initialize_session_state
        original_initialize_session_state = initialize_session_state
        
        def debug_initialize_session_state():
            debug_tracker.track_call("initialize_session_state", f"authenticated: {st.session_state.get('authenticated', False)}")
            return original_initialize_session_state()
        
        # Replace the function
        import utils.session_manager
        utils.session_manager.initialize_session_state = debug_initialize_session_state
        logger.info("DEBUG: Patched initialize_session_state")
        
    except Exception as e:
        logger.error(f"Failed to patch initialize_session_state: {e}")
    
    # Patch initialize_auth_session
    try:
        from auth import initialize_auth_session
        original_initialize_auth_session = initialize_auth_session
        
        def debug_initialize_auth_session():
            debug_tracker.track_call("initialize_auth_session", f"session_id: {st.session_state.get('session_id', 'None')}")
            return original_initialize_auth_session()
        
        # Replace the function
        import auth
        auth.initialize_auth_session = debug_initialize_auth_session
        logger.info("DEBUG: Patched initialize_auth_session")
        
    except Exception as e:
        logger.error(f"Failed to patch initialize_auth_session: {e}")
    
    # Patch validate_session
    try:
        from auth import validate_session
        original_validate_session = validate_session
        
        def debug_validate_session(session_id: str):
            debug_tracker.track_call("validate_session", f"session_id: {session_id}")
            return original_validate_session(session_id)
        
        # Replace the function
        import auth
        auth.validate_session = debug_validate_session
        logger.info("DEBUG: Patched validate_session")
        
    except Exception as e:
        logger.error(f"Failed to patch validate_session: {e}")
    
    # Patch get_supabase_client
    try:
        from supabase_manager import get_supabase_client
        original_get_supabase_client = get_supabase_client
        
        def debug_get_supabase_client():
            debug_tracker.track_call("get_supabase_client", "client requested")
            return original_get_supabase_client()
        
        # Replace the function
        import supabase_manager
        supabase_manager.get_supabase_client = debug_get_supabase_client
        logger.info("DEBUG: Patched get_supabase_client")
        
    except Exception as e:
        logger.error(f"Failed to patch get_supabase_client: {e}")
    
    # Patch test_connection
    try:
        from supabase_manager import connection_manager
        original_test_connection = connection_manager.test_connection
        
        def debug_test_connection():
            debug_tracker.track_call("test_connection", "connection test requested")
            return original_test_connection()
        
        connection_manager.test_connection = debug_test_connection
        logger.info("DEBUG: Patched test_connection")
        
    except Exception as e:
        logger.error(f"Failed to patch test_connection: {e}")

def main():
    """Main debug function to run with Streamlit"""
    st.title("🔍 Streamlit Flow Debug Monitor")
    
    # Add debug logging
    add_debug_logging()
    
    # Show current session state
    st.subheader("Current Session State")
    st.json(dict(st.session_state))
    
    # Show debug summary
    st.subheader("Function Call Summary")
    summary = debug_tracker.get_summary()
    for func, stats in summary.items():
        with st.expander(f"{func} ({stats['total_calls']} calls, {stats['duplicates']} duplicates)"):
            st.json(stats)
    
    # Show detailed call history
    st.subheader("Detailed Call History")
    for func, calls in debug_tracker.calls.items():
        st.write(f"**{func}**")
        for i, call in enumerate(calls):
            st.text(f"  {i+1}. {call['timestamp']} - {call['details']} (t={call['elapsed']:.3f}s)")
    
    # Test buttons to trigger different flows
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Trigger Rerun"):
            st.rerun()
    
    with col2:
        if st.button("🔐 Trigger Auth Check"):
            from auth import initialize_auth_session
            initialize_auth_session()
            st.success("Auth check triggered")
    
    with col3:
        if st.button("🔗 Trigger Connection Test"):
            from supabase_manager import test_supabase_connection
            result = test_supabase_connection()
            st.success(f"Connection test: {'✅ Success' if result else '❌ Failed'}")

if __name__ == "__main__":
    main()