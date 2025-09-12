"""
RAG Interface for PharmBot Streamlit App
Handles document upload, management, and RAG-enhanced conversations
"""

import streamlit as st
from rag_system import RAGSystem
from PIL import Image
import io
from datetime import datetime
from typing import Optional

def initialize_rag_system() -> Optional[RAGSystem]:
    """Initialize RAG system for the current user."""
    if not st.session_state.authenticated:
        return None
    
    if "rag_system" not in st.session_state:
        st.session_state.rag_system = RAGSystem(st.session_state.user_id)
    
    return st.session_state.rag_system

def render_document_upload_section():
    """Render the document upload section."""
    st.markdown("### 📄 Upload Documents")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose files to add to your knowledge base",
        type=['pdf', 'txt', 'csv', 'docx', 'doc', 'png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        help="Supported formats: PDF, Text, CSV, Word documents, and Images"
    )
    
    if uploaded_files:
        rag_system = initialize_rag_system()
        if not rag_system:
            st.error("Please sign in to upload documents.")
            return
        
        for uploaded_file in uploaded_files:
            with st.expander(f"📎 {uploaded_file.name}", expanded=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**File:** {uploaded_file.name}")
                    st.write(f"**Type:** {uploaded_file.type}")
                    st.write(f"**Size:** {uploaded_file.size:,} bytes")
                
                with col2:
                    if st.button(f"Add to Knowledge Base", key=f"add_{uploaded_file.name}"):
                        with st.spinner(f"Processing {uploaded_file.name}..."):
                            file_content = uploaded_file.read()
                            
                            # Handle images separately
                            if uploaded_file.type.startswith('image/'):
                                image = Image.open(io.BytesIO(file_content))
                                success = rag_system.add_image(image, uploaded_file.name)
                            else:
                                success = rag_system.add_document(
                                    file_content, 
                                    uploaded_file.name, 
                                    uploaded_file.type
                                )
                            
                            if success:
                                st.success(f"✅ {uploaded_file.name} added successfully!")
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to add {uploaded_file.name}")

def render_knowledge_base_management():
    """Render the knowledge base management section."""
    rag_system = initialize_rag_system()
    if not rag_system:
        return
    
    st.markdown("### 📚 Knowledge Base")
    
    documents = rag_system.get_documents_list()
    
    if not documents:
        st.info("No documents in your knowledge base yet. Upload some documents above!")
        return
    
    # Statistics
    total_docs = len(documents)
    total_chunks = sum(doc["chunks_count"] for doc in documents)
    total_size = sum(doc["size_bytes"] for doc in documents)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Documents", total_docs)
    with col2:
        st.metric("Text Chunks", total_chunks)
    with col3:
        st.metric("Total Size", f"{total_size/1024:.1f} KB")
    
    st.markdown("---")
    
    # Document list
    for doc in sorted(documents, key=lambda x: x["added_at"], reverse=True):
        with st.expander(f"📄 {doc['filename']}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Type:** {doc['file_type']}")
                st.write(f"**Chunks:** {doc['chunks_count']}")
                st.write(f"**Size:** {doc['size_bytes']:,} bytes")
                st.write(f"**Added:** {doc['added_at'][:19].replace('T', ' ')}")
            
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{doc['file_hash']}"):
                    if rag_system.delete_document(doc['file_hash']):
                        st.success("Document deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete document")
    
    # Clear all button
    st.markdown("---")
    if st.button("🗑️ Clear All Documents", type="secondary"):
        if st.button("⚠️ Confirm Clear All", key="confirm_clear_all"):
            if rag_system.clear_all_documents():
                st.success("All documents cleared!")
                st.rerun()
            else:
                st.error("Failed to clear documents")

def render_rag_search_test():
    """Render RAG search test section."""
    rag_system = initialize_rag_system()
    if not rag_system:
        return
    
    st.markdown("### 🔍 Test Knowledge Base Search")
    
    query = st.text_input(
        "Search your documents:",
        placeholder="Enter a question or topic to search...",
        help="Test how well your documents can answer questions"
    )
    
    if query:
        with st.spinner("Searching..."):
            results = rag_system.search_documents(query, n_results=3)
            
            if results:
                st.markdown("#### Search Results:")
                for i, result in enumerate(results, 1):
                    with st.expander(f"Result {i} - {result['metadata'].get('filename', 'Unknown')}", expanded=i==1):
                        st.write(f"**Relevance Score:** {result['relevance_score']:.3f}")
                        st.write(f"**Source:** {result['metadata'].get('filename', 'Unknown')}")
                        st.markdown("**Content:**")
                        st.write(result['content'])
            else:
                st.info("No relevant documents found. Try uploading more documents or rephrasing your query.")

def render_rag_sidebar():
    """Render RAG-related sidebar content."""
    rag_system = initialize_rag_system()
    if not rag_system:
        return
    
    # RAG status
    documents = rag_system.get_documents_list()
    doc_count = len(documents)
    
    if doc_count > 0:
        st.success(f"📚 Knowledge Base: {doc_count} documents")
    else:
        st.info("📚 No documents uploaded yet")
    
    # Quick upload
    with st.expander("📤 Quick Upload"):
        uploaded_file = st.file_uploader(
            "Add document",
            type=['pdf', 'txt', 'csv', 'docx', 'png', 'jpg'],
            key="sidebar_upload"
        )
        
        if uploaded_file:
            if st.button("Add Document", key="sidebar_add"):
                with st.spinner("Processing..."):
                    file_content = uploaded_file.read()
                    
                    if uploaded_file.type.startswith('image/'):
                        image = Image.open(io.BytesIO(file_content))
                        success = rag_system.add_image(image, uploaded_file.name)
                    else:
                        success = rag_system.add_document(
                            file_content, 
                            uploaded_file.name, 
                            uploaded_file.type
                        )
                    
                    if success:
                        st.success("Document added!")
                        st.rerun()

def get_rag_enhanced_prompt(original_prompt: str, rag_system: RAGSystem) -> str:
    """Enhance a prompt with RAG context."""
    if not rag_system:
        return original_prompt
    
    # Get relevant context
    context = rag_system.get_context_for_query(original_prompt)
    
    if not context:
        return original_prompt
    
    # Create enhanced prompt
    enhanced_prompt = f"""Based on the following context from the user's documents, please answer the question. If the context doesn't contain relevant information, answer based on your general knowledge but mention that you're not using the user's specific documents.

Context from user's documents:
{context}

User's question: {original_prompt}

Please provide a comprehensive answer, citing the sources when using information from the provided context."""
    
    return enhanced_prompt

def render_rag_page():
    """Render the main RAG management page."""
    st.markdown("# 📚 Knowledge Base Management")
    st.markdown("Upload and manage documents to enhance your PharmBot conversations with your own content.")
    
    if not st.session_state.authenticated:
        st.warning("Please sign in to access the Knowledge Base features.")
        return
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload Documents", "📚 Manage Documents", "🔍 Test Search"])
    
    with tab1:
        render_document_upload_section()
    
    with tab2:
        render_knowledge_base_management()
    
    with tab3:
        render_rag_search_test()
    
    # Instructions
    st.markdown("---")
    st.markdown("### 💡 How it Works")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Supported File Types:**
        - 📄 PDF documents
        - 📝 Text files (.txt)
        - 📊 CSV files
        - 📋 Word documents (.docx, .doc)
        - 🖼️ Images (.png, .jpg, .jpeg) - text extracted via OCR
        """)
    
    with col2:
        st.markdown("""
        **Features:**
        - 🔍 Semantic search through your documents
        - 💬 RAG-enhanced conversations
        - 🔒 Private document storage per user
        - 📊 Document management and statistics
        - 🖼️ OCR text extraction from images
        """)