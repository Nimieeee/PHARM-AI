"""
Document Processing Health Monitor
Real-time monitoring for document processing on Streamlit Cloud
"""

import streamlit as st
import asyncio
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def show_document_processing_status():
    """Show document processing status in sidebar or main area."""
    
    # Quick health check
    try:
        # Check RAG dependencies
        from rag_system_chromadb import _check_dependencies
        deps_ok = _check_dependencies()
        
        if deps_ok:
            st.success("✅ Document processing available")
            
            # Show additional details in expander
            with st.expander("📊 Document System Status"):
                show_detailed_status()
        else:
            st.error("❌ Document processing unavailable")
            st.info("💡 Some dependencies may be missing on Streamlit Cloud")
            
    except Exception as e:
        st.error(f"❌ Status check failed: {str(e)}")

def show_detailed_status():
    """Show detailed document processing status."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Dependencies:**")
        check_dependencies_status()
    
    with col2:
        st.write("**System Status:**")
        check_system_status()

def check_dependencies_status():
    """Check and display dependency status."""
    
    dependencies = {
        'ChromaDB': 'chromadb',
        'SentenceTransformers': 'sentence_transformers',
        'PyPDF2': 'PyPDF2',
        'python-docx': 'docx',
        'Pandas': 'pandas',
        'PIL': 'PIL'
    }
    
    for name, module in dependencies.items():
        try:
            if module == 'docx':
                import docx
            elif module == 'PIL':
                from PIL import Image
            else:
                __import__(module)
            st.write(f"✅ {name}")
        except ImportError:
            st.write(f"❌ {name}")

def check_system_status():
    """Check and display system status."""
    
    # Check configuration
    try:
        from config import get_api_keys, get_supabase_config
        
        groq_key, openrouter_key = get_api_keys()
        supabase_url, supabase_key = get_supabase_config()
        
        st.write(f"✅ Config Loading" if groq_key or openrouter_key else "⚠️ Config Loading")
        st.write(f"✅ Database Config" if supabase_url and supabase_key else "❌ Database Config")
        
    except Exception:
        st.write("❌ Config Loading")
    
    # Check RAG system
    try:
        if st.session_state.get('authenticated') and st.session_state.get('user_id'):
            from rag_system_chromadb import initialize_rag_system
            
            test_conversation = 'health-check'
            rag_system = initialize_rag_system(test_conversation)
            
            if rag_system and rag_system._initialize_components():
                st.write("✅ RAG System")
            else:
                st.write("⚠️ RAG System")
        else:
            st.write("ℹ️ RAG System (login required)")
            
    except Exception:
        st.write("❌ RAG System")

def show_document_upload_tips():
    """Show tips for successful document uploads."""
    
    st.info("""
    **📄 Document Upload Tips:**
    
    **Supported Formats:**
    - PDF files (text-based, not scanned images)
    - Word documents (.docx)
    - Text files (.txt)
    - CSV files (.csv)
    - Images with text (PNG, JPG) - requires OCR
    
    **Best Practices:**
    - Keep files under 10MB
    - Use clear, readable text
    - Avoid heavily formatted documents
    - For images, ensure text is clear and high contrast
    
    **If upload fails:**
    - Try a different file format
    - Check file size (max 10MB)
    - Ensure file is not corrupted
    - Try uploading a simple text file first
    """)

def monitor_document_processing_performance():
    """Monitor document processing performance metrics."""
    
    if 'document_processing_stats' not in st.session_state:
        st.session_state.document_processing_stats = {
            'total_uploads': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'avg_processing_time': 0.0
        }
    
    stats = st.session_state.document_processing_stats
    
    if stats['total_uploads'] > 0:
        success_rate = (stats['successful_uploads'] / stats['total_uploads']) * 100
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Uploads", stats['total_uploads'])
        
        with col2:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        
        with col3:
            if stats['avg_processing_time'] > 0:
                st.metric("Avg Time", f"{stats['avg_processing_time']:.1f}s")

def record_document_processing_attempt(success: bool, processing_time: float = 0.0):
    """Record a document processing attempt for monitoring."""
    
    if 'document_processing_stats' not in st.session_state:
        st.session_state.document_processing_stats = {
            'total_uploads': 0,
            'successful_uploads': 0,
            'failed_uploads': 0,
            'avg_processing_time': 0.0
        }
    
    stats = st.session_state.document_processing_stats
    
    stats['total_uploads'] += 1
    
    if success:
        stats['successful_uploads'] += 1
    else:
        stats['failed_uploads'] += 1
    
    if processing_time > 0:
        # Update average processing time
        current_avg = stats['avg_processing_time']
        total_successful = stats['successful_uploads']
        
        if total_successful > 1:
            stats['avg_processing_time'] = (
                (current_avg * (total_successful - 1) + processing_time) / total_successful
            )
        else:
            stats['avg_processing_time'] = processing_time

# Quick status check function for other modules
def is_document_processing_available() -> bool:
    """Quick check if document processing is available."""
    try:
        from rag_system_chromadb import _check_dependencies
        return _check_dependencies()
    except:
        return False

def get_document_processing_status() -> Dict[str, Any]:
    """Get comprehensive document processing status."""
    
    status = {
        'available': False,
        'dependencies_ok': False,
        'config_ok': False,
        'rag_system_ok': False,
        'database_ok': False,
        'errors': []
    }
    
    try:
        # Check dependencies
        from rag_system_chromadb import _check_dependencies
        status['dependencies_ok'] = _check_dependencies()
        
        # Check configuration
        from config import get_api_keys, get_supabase_config
        groq_key, openrouter_key = get_api_keys()
        supabase_url, supabase_key = get_supabase_config()
        status['config_ok'] = bool(groq_key or openrouter_key)
        
        # Check RAG system (if authenticated)
        if st.session_state.get('authenticated') and st.session_state.get('user_id'):
            from rag_system_chromadb import initialize_rag_system
            rag_system = initialize_rag_system('health-check')
            status['rag_system_ok'] = bool(rag_system and rag_system._initialize_components())
        
        # Check database
        try:
            from utils.database_status import is_database_healthy
            status['database_ok'] = asyncio.run(is_database_healthy())
        except:
            status['database_ok'] = False
        
        # Overall availability
        status['available'] = (
            status['dependencies_ok'] and 
            status['config_ok'] and 
            (not st.session_state.get('authenticated') or status['rag_system_ok'])
        )
        
    except Exception as e:
        status['errors'].append(str(e))
    
    return status