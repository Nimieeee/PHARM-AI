"""
Performance Monitoring for PharmGPT
Simple performance metrics and monitoring
"""

import streamlit as st
import time
from datetime import datetime
from performance_config import get_memory_usage, log_performance_metrics

def show_performance_sidebar():
    """Show performance metrics in sidebar (for debugging)."""
    if st.sidebar.checkbox("Show Performance Metrics", value=False):
        st.sidebar.markdown("### 📊 Performance Metrics")
        
        # Memory usage
        memory_mb = get_memory_usage()
        if memory_mb > 0:
            st.sidebar.metric("Memory Usage", f"{memory_mb:.1f} MB")
        
        # Performance metrics
        metrics = log_performance_metrics()
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("Page Loads", metrics.get('page_loads', 0))
            st.metric("API Calls", metrics.get('api_calls', 0))
        
        with col2:
            st.metric("File Uploads", metrics.get('file_uploads', 0))
            cache_hit_rate = 0
            if metrics.get('cache_hits', 0) + metrics.get('cache_misses', 0) > 0:
                cache_hit_rate = metrics.get('cache_hits', 0) / (metrics.get('cache_hits', 0) + metrics.get('cache_misses', 0)) * 100
            st.metric("Cache Hit Rate", f"{cache_hit_rate:.1f}%")
        
        # Session state info
        st.sidebar.markdown(f"**Session State Keys:** {len(st.session_state)}")
        
        # Clear metrics button
        if st.sidebar.button("Clear Metrics"):
            for key in ['performance_metrics']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

class PerformanceTimer:
    """Context manager for timing operations."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        # Log slow operations
        if duration > 1.0:  # More than 1 second
            st.warning(f"⚠️ Slow operation detected: {self.operation_name} took {duration:.2f}s")
        
        # Store timing in session state for monitoring
        if 'operation_timings' not in st.session_state:
            st.session_state.operation_timings = []
        
        st.session_state.operation_timings.append({
            'operation': self.operation_name,
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only last 50 timings
        if len(st.session_state.operation_timings) > 50:
            st.session_state.operation_timings = st.session_state.operation_timings[-50:]

def monitor_performance(func):
    """Decorator to monitor function performance."""
    def wrapper(*args, **kwargs):
        with PerformanceTimer(func.__name__):
            return func(*args, **kwargs)
    return wrapper

def show_performance_warnings():
    """Show performance warnings if needed."""
    
    # Check memory usage
    memory_mb = get_memory_usage()
    if memory_mb > 400:  # More than 400MB
        st.warning(f"⚠️ High memory usage detected: {memory_mb:.1f}MB. Consider refreshing the page.")
    
    # Check session state size
    if len(st.session_state) > 100:
        st.info("ℹ️ Large session state detected. Performance may be affected.")
    
    # Check for slow operations
    if 'operation_timings' in st.session_state:
        recent_timings = st.session_state.operation_timings[-10:]  # Last 10 operations
        slow_operations = [t for t in recent_timings if t['duration'] > 2.0]
        
        if len(slow_operations) > 3:  # More than 3 slow operations recently
            st.warning("⚠️ Multiple slow operations detected. The app may be running slowly.")

def optimize_session_state():
    """Clean up session state for better performance."""
    
    # Remove old temporary keys
    keys_to_remove = []
    for key in st.session_state.keys():
        if (key.startswith('temp_') or 
            key.startswith('old_') or
            key.startswith('cache_') and 'timestamp' in key):
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
    
    # Limit conversation cache size
    if 'conversations' in st.session_state and len(st.session_state.conversations) > 50:
        # Keep only the 50 most recent conversations
        conversations = st.session_state.conversations
        sorted_convs = sorted(conversations.items(), 
                            key=lambda x: x[1].get('created_at', ''), 
                            reverse=True)
        st.session_state.conversations = dict(sorted_convs[:50])