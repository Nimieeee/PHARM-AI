"""
Performance Configuration for PharmGPT
Centralized settings for optimization
"""

import streamlit as st

# Caching Configuration
CACHE_TTL_SECONDS = 300  # 5 minutes default cache
LONG_CACHE_TTL_SECONDS = 1800  # 30 minutes for heavy operations

# RAG System Performance
RAG_LAZY_LOADING = True  # Load RAG components only when needed
RAG_GLOBAL_EMBEDDINGS_CACHE = True  # Share embeddings model across conversations
RAG_BATCH_SIZE = 50  # Process documents in batches

# File Processing Performance
MAX_FILE_PROCESSING_SIZE = 10 * 1024 * 1024  # 10MB
FILE_PROCESSING_CHUNK_SIZE = 1024 * 1024  # 1MB chunks
ASYNC_FILE_PROCESSING = True  # Process files asynchronously when possible

# Session State Optimization
BATCH_SAVE_CONVERSATIONS = True  # Batch conversation saves to reduce I/O
CONVERSATION_CACHE_SIZE = 100  # Max conversations to keep in memory
SESSION_STATE_CLEANUP_INTERVAL = 50  # Clean up session state every N operations

# API Performance
API_RESPONSE_CACHING = True  # Cache identical API requests
API_STREAMING_CHUNK_SIZE = 50  # Update UI every N characters in streaming
API_TIMEOUT_SECONDS = 30  # API request timeout

# UI Performance
LAZY_COMPONENT_LOADING = True  # Load UI components only when needed
REDUCE_RERUN_FREQUENCY = True  # Minimize st.rerun() calls
OPTIMIZE_CHAT_DISPLAY = True  # Optimize chat message rendering

# Memory Management
ENABLE_GARBAGE_COLLECTION = True  # Periodic garbage collection
MAX_MEMORY_USAGE_MB = 512  # Target memory usage limit
CLEAR_UNUSED_CACHE_INTERVAL = 100  # Clear unused cache every N operations

def apply_performance_optimizations():
    """Apply performance optimizations to Streamlit."""
    
    # Configure Streamlit for better performance
    if 'performance_optimized' not in st.session_state:
        
        # Set up periodic cleanup
        if ENABLE_GARBAGE_COLLECTION:
            import gc
            gc.collect()
        
        # Configure session state cleanup
        if len(st.session_state) > SESSION_STATE_CLEANUP_INTERVAL:
            cleanup_session_state()
        
        st.session_state.performance_optimized = True

def cleanup_session_state():
    """Clean up unused session state variables."""
    
    # Remove old cache entries
    keys_to_remove = []
    for key in st.session_state.keys():
        if (key.startswith('cache_') or 
            key.startswith('temp_') or 
            key.startswith('old_')):
            keys_to_remove.append(key)
    
    # Keep only recent cache entries
    if len(keys_to_remove) > CLEAR_UNUSED_CACHE_INTERVAL:
        for key in keys_to_remove[:CLEAR_UNUSED_CACHE_INTERVAL]:
            if key in st.session_state:
                del st.session_state[key]

def get_memory_usage():
    """Get current memory usage in MB."""
    try:
        import psutil
        import os
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
    except ImportError:
        return 0

def optimize_for_memory():
    """Optimize application for memory usage."""
    current_memory = get_memory_usage()
    
    if current_memory > MAX_MEMORY_USAGE_MB:
        # Clear caches
        st.cache_data.clear()
        st.cache_resource.clear()
        
        # Force garbage collection
        if ENABLE_GARBAGE_COLLECTION:
            import gc
            gc.collect()
        
        # Clean up session state
        cleanup_session_state()

# Performance monitoring
def log_performance_metrics():
    """Log performance metrics for monitoring."""
    if 'performance_metrics' not in st.session_state:
        st.session_state.performance_metrics = {
            'page_loads': 0,
            'api_calls': 0,
            'file_uploads': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    return st.session_state.performance_metrics

def increment_metric(metric_name: str):
    """Increment a performance metric."""
    metrics = log_performance_metrics()
    metrics[metric_name] = metrics.get(metric_name, 0) + 1