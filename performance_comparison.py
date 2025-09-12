"""
Performance Comparison Tool
Compare file-based vs Supabase performance
"""

import streamlit as st
import time
import asyncio
from typing import Dict, List
import matplotlib.pyplot as plt
import pandas as pd

def run_performance_comparison():
    """Run comprehensive performance comparison."""
    
    st.markdown("## 📊 Performance Comparison: Files vs Supabase")
    
    if not st.session_state.authenticated:
        st.warning("Please sign in to run performance tests.")
        return
    
    user_id = st.session_state.user_id
    
    # Test configuration
    col1, col2 = st.columns(2)
    with col1:
        iterations = st.slider("Test Iterations", 1, 20, 5)
    with col2:
        test_type = st.selectbox("Test Type", [
            "Load Conversations",
            "Save Conversations", 
            "Load Documents",
            "Full CRUD Operations"
        ])
    
    if st.button("Run Performance Test", type="primary"):
        
        with st.spinner("Running performance tests..."):
            results = {}
            
            if test_type == "Load Conversations":
                results = benchmark_load_conversations(user_id, iterations)
            elif test_type == "Save Conversations":
                results = benchmark_save_conversations(user_id, iterations)
            elif test_type == "Load Documents":
                results = benchmark_load_documents(user_id, iterations)
            elif test_type == "Full CRUD Operations":
                results = benchmark_full_crud(user_id, iterations)
        
        # Display results
        display_performance_results(results, test_type)

def benchmark_load_conversations(user_id: str, iterations: int) -> Dict:
    """Benchmark conversation loading."""
    
    # File-based timing
    file_times = []
    for i in range(iterations):
        start = time.time()
        from auth import load_user_conversations
        conversations = load_user_conversations(user_id)
        file_times.append(time.time() - start)
        
        # Show progress
        st.progress((i + 1) / (iterations * 2))
    
    # Supabase timing (if available)
    supabase_times = []
    try:
        from supabase_integration import supabase_manager
        if supabase_manager.is_available():
            for i in range(iterations):
                start = time.time()
                conversations = asyncio.run(supabase_manager.load_user_conversations(user_id))
                supabase_times.append(time.time() - start)
                
                # Show progress
                st.progress((iterations + i + 1) / (iterations * 2))
        else:
            st.info("Supabase not configured - only testing file-based system")
    except ImportError:
        st.info("Supabase integration not available")
    
    return {
        'file_times': file_times,
        'supabase_times': supabase_times,
        'file_avg': sum(file_times) / len(file_times),
        'supabase_avg': sum(supabase_times) / len(supabase_times) if supabase_times else 0,
        'conversation_count': len(conversations) if 'conversations' in locals() else 0
    }

def benchmark_save_conversations(user_id: str, iterations: int) -> Dict:
    """Benchmark conversation saving."""
    
    # Load existing conversations for testing
    from auth import load_user_conversations
    conversations = load_user_conversations(user_id)
    
    if not conversations:
        st.warning("No conversations found to test saving performance")
        return {}
    
    # File-based timing
    file_times = []
    for i in range(iterations):
        start = time.time()
        from auth import save_user_conversations
        save_user_conversations(user_id, conversations)
        file_times.append(time.time() - start)
        st.progress((i + 1) / (iterations * 2))
    
    # Supabase timing
    supabase_times = []
    try:
        from supabase_integration import supabase_manager
        if supabase_manager.is_available():
            for i in range(iterations):
                start = time.time()
                asyncio.run(supabase_manager.save_user_conversations(user_id, conversations))
                supabase_times.append(time.time() - start)
                st.progress((iterations + i + 1) / (iterations * 2))
    except ImportError:
        pass
    
    return {
        'file_times': file_times,
        'supabase_times': supabase_times,
        'file_avg': sum(file_times) / len(file_times),
        'supabase_avg': sum(supabase_times) / len(supabase_times) if supabase_times else 0,
        'conversation_count': len(conversations)
    }

def benchmark_load_documents(user_id: str, iterations: int) -> Dict:
    """Benchmark document loading for RAG."""
    
    # Get a conversation with documents
    from auth import load_user_conversations
    conversations = load_user_conversations(user_id)
    
    if not conversations:
        st.warning("No conversations found to test document loading")
        return {}
    
    # Find conversation with documents
    test_conv_id = None
    for conv_id in conversations.keys():
        from rag_interface_chromadb import get_conversation_document_count
        if get_conversation_document_count(conv_id) > 0:
            test_conv_id = conv_id
            break
    
    if not test_conv_id:
        st.warning("No conversations with documents found")
        return {}
    
    # File-based timing (RAG system)
    file_times = []
    for i in range(iterations):
        start = time.time()
        from rag_interface_chromadb import initialize_rag_system
        rag_system = initialize_rag_system(test_conv_id)
        if rag_system:
            documents = rag_system.get_documents_list()
        file_times.append(time.time() - start)
        st.progress((i + 1) / iterations)
    
    # Supabase timing would go here if RAG was integrated
    
    return {
        'file_times': file_times,
        'supabase_times': [],
        'file_avg': sum(file_times) / len(file_times),
        'supabase_avg': 0,
        'document_count': len(documents) if 'documents' in locals() else 0
    }

def benchmark_full_crud(user_id: str, iterations: int) -> Dict:
    """Benchmark full CRUD operations."""
    
    results = {
        'create': {'file': [], 'supabase': []},
        'read': {'file': [], 'supabase': []},
        'update': {'file': [], 'supabase': []},
        'delete': {'file': [], 'supabase': []}
    }
    
    # This would implement full CRUD benchmarking
    # For now, just return load/save results
    load_results = benchmark_load_conversations(user_id, iterations // 2)
    save_results = benchmark_save_conversations(user_id, iterations // 2)
    
    return {
        'load': load_results,
        'save': save_results
    }

def display_performance_results(results: Dict, test_type: str):
    """Display performance comparison results."""
    
    st.markdown("### 📈 Performance Results")
    
    if test_type in ["Load Conversations", "Save Conversations"]:
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "File-based Average", 
                f"{results['file_avg']:.3f}s",
                help="Average time for file-based operations"
            )
        
        with col2:
            if results['supabase_avg'] > 0:
                st.metric(
                    "Supabase Average", 
                    f"{results['supabase_avg']:.3f}s",
                    help="Average time for Supabase operations"
                )
                
                # Performance comparison
                if results['file_avg'] > 0:
                    speedup = results['file_avg'] / results['supabase_avg']
                    if speedup > 1:
                        st.success(f"Supabase is {speedup:.1f}x faster")
                    else:
                        st.info(f"File-based is {1/speedup:.1f}x faster")
            else:
                st.info("Supabase not tested")
        
        with col3:
            st.metric(
                "Data Size", 
                f"{results.get('conversation_count', 0)} conversations",
                help="Number of conversations tested"
            )
        
        # Detailed timing chart
        if results['file_times'] or results['supabase_times']:
            
            chart_data = []
            
            for i, time_val in enumerate(results['file_times']):
                chart_data.append({'Iteration': i+1, 'Time (s)': time_val, 'System': 'File-based'})
            
            for i, time_val in enumerate(results['supabase_times']):
                chart_data.append({'Iteration': i+1, 'Time (s)': time_val, 'System': 'Supabase'})
            
            if chart_data:
                df = pd.DataFrame(chart_data)
                st.line_chart(df.pivot(index='Iteration', columns='System', values='Time (s)'))
        
        # Raw data
        with st.expander("Raw Timing Data"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**File-based Times (s):**")
                for i, t in enumerate(results['file_times']):
                    st.text(f"Run {i+1}: {t:.4f}s")
            
            with col2:
                if results['supabase_times']:
                    st.markdown("**Supabase Times (s):**")
                    for i, t in enumerate(results['supabase_times']):
                        st.text(f"Run {i+1}: {t:.4f}s")

def show_performance_recommendations():
    """Show performance recommendations based on usage patterns."""
    
    st.markdown("### 🎯 Performance Recommendations")
    
    # Analyze current usage
    if st.session_state.authenticated:
        from auth import load_user_conversations
        conversations = load_user_conversations(st.session_state.user_id)
        conv_count = len(conversations)
        
        # Count total messages
        total_messages = sum(len(conv.get('messages', [])) for conv in conversations.values())
        
        # Count documents
        from rag_interface_chromadb import get_all_user_documents_count
        doc_count = get_all_user_documents_count()
        
        # Show current usage
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Conversations", conv_count)
        with col2:
            st.metric("Total Messages", total_messages)
        with col3:
            st.metric("Documents", doc_count)
        
        # Recommendations
        st.markdown("#### Recommendations:")
        
        if conv_count < 10 and total_messages < 100:
            st.success("✅ **File-based system is optimal** for your current usage")
            st.info("Your data size is small enough that file-based storage provides the best performance")
        
        elif conv_count < 50 and total_messages < 1000:
            st.info("📊 **Either system would work well** for your usage")
            st.info("Consider Supabase if you plan to scale or need real-time features")
        
        else:
            st.warning("⚡ **Supabase recommended** for your usage level")
            st.info("With your data size, Supabase would provide better performance and scalability")
        
        # Additional factors
        st.markdown("#### Consider Supabase if you need:")
        st.markdown("""
        - 🔄 Real-time collaboration
        - 📱 Multi-device sync
        - 🔍 Advanced search capabilities
        - 📊 Analytics and reporting
        - 🔒 Enhanced backup and recovery
        - 🚀 Better scalability for multiple users
        """)
        
        st.markdown("#### Stick with files if you prefer:")
        st.markdown("""
        - 💻 Offline capability
        - 🔒 Complete data control
        - ⚡ Minimal latency for small datasets
        - 🎯 Simplicity and fewer dependencies
        """)

if __name__ == "__main__":
    run_performance_comparison()
    show_performance_recommendations()