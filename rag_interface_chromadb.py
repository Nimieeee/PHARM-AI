"""
RAG Interface for ChromaDB integration with Streamlit - Supabase Version
"""

from typing import Optional
import streamlit as st
import asyncio
from rag_system_chromadb import initialize_rag_system, ConversationRAGSystem
from prompts import get_rag_enhanced_prompt
from services.document_service import document_service
from services.user_service import user_service

def get_rag_enhanced_prompt(user_query: str, rag_system: ConversationRAGSystem) -> str:
    """Get RAG-enhanced prompt with document context."""
    try:
        # Search for relevant context
        context = rag_system.get_context_for_query(user_query)
        
        if context:
            # Use the template from prompts.py
            from prompts import rag_enhanced_prompt_template
            return rag_enhanced_prompt_template.format(
                context=context,
                question=user_query
            )
        else:
            # No relevant context found, return original query
            return user_query
            
    except Exception as e:
        st.error(f"Error enhancing prompt with RAG: {e}")
        return user_query

def display_rag_sidebar(conversation_id: str):
    """Display RAG system sidebar with document management using Supabase."""
    if not st.session_state.authenticated:
        return
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Knowledge Base")
    
    try:
        # Get user UUID from legacy user_id
        user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
        if not user_data:
            st.sidebar.error("User not found")
            return
        
        # Get documents from Supabase
        from services.document_service import get_conversation_documents_sync
        documents = get_conversation_documents_sync(
            user_data['id'], 
            conversation_id
        )
        
        if documents:
            st.sidebar.markdown(f"**{len(documents)} document(s) in this conversation:**")
            
            for doc in documents:
                with st.sidebar.expander(f"📄 {doc['filename']}", expanded=False):
                    st.write(f"**Type:** {doc['file_type']}")
                    st.write(f"**Size:** {doc['file_size']} bytes")
                    st.write(f"**Chunks:** {doc['chunk_count']}")
                    st.write(f"**Added:** {doc['added_at'][:10]}")
                    
                    if doc.get('processing_error'):
                        st.error(f"Processing error: {doc['processing_error']}")
                    elif not doc.get('is_processed', True):
                        st.warning("Processing...")
                    
                    # Delete button
                    if st.button(f"🗑️ Delete", key=f"delete_{doc['document_hash']}", help="Delete this document"):
                        from services.document_service import delete_document_sync
                        success = delete_document_sync(
                            user_data['id'], 
                            doc['document_hash']
                        )
                        if success:
                            # Also delete from ChromaDB
                            rag_system = initialize_rag_system(conversation_id)
                            if rag_system:
                                rag_system.delete_document(doc['document_hash'])
                            st.success("Document deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete document")
            
            # Search functionality
            st.sidebar.markdown("---")
            st.sidebar.markdown("**🔍 Search Documents:**")
            search_query = st.sidebar.text_input("Search query", key=f"search_{conversation_id}")
            
            if search_query and st.sidebar.button("Search", key=f"search_btn_{conversation_id}"):
                # Search in Supabase metadata
                from services.document_service import search_documents_sync
                search_results = search_documents_sync(
                    user_data['id'], 
                    search_query, 
                    conversation_id
                )
                
                if search_results:
                    st.sidebar.markdown("**Search Results:**")
                    for i, result in enumerate(search_results[:3]):  # Show top 3 results
                        with st.sidebar.expander(f"Result {i+1}: {result['filename']}", expanded=False):
                            st.write(f"**Match:** {result.get('match_type', 'unknown')}")
                            st.write(f"**Type:** {result['file_type']}")
                            st.write(f"**Size:** {result['file_size']} bytes")
                else:
                    st.sidebar.info("No relevant documents found")
        
        else:
            st.sidebar.info("No documents uploaded yet")
            st.sidebar.markdown("Upload documents using the 📎 button in the chat to enhance responses with your content.")
    
    except Exception as e:
        st.sidebar.error(f"Error loading documents: {e}")

def get_rag_status(conversation_id: str) -> dict:
    """Get RAG system status for a conversation."""
    if not st.session_state.authenticated:
        return {"available": False, "reason": "Not authenticated"}
    
    rag_system = initialize_rag_system(conversation_id)
    
    if not rag_system:
        return {"available": False, "reason": "RAG system unavailable"}
    
    documents = rag_system.get_documents_list()
    
    return {
        "available": True,
        "document_count": len(documents),
        "documents": documents
    }

# Helper function to run async functions in Streamlit
def run_async(coro):
    """Run async function in Streamlit context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

def get_conversation_document_count(conversation_id: str = None) -> int:
    """Get document count for a specific conversation using Supabase."""
    if not st.session_state.authenticated:
        return 0
    
    # Use current conversation if none specified
    if conversation_id is None:
        conversation_id = st.session_state.get('current_conversation_id')
    
    if not conversation_id:
        return 0
    
    try:
        # Get user UUID from legacy user_id
        user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
        if not user_data:
            return 0
        
        # Get document count from Supabase
        from services.document_service import get_conversation_document_count_sync
        count = get_conversation_document_count_sync(
            user_data['id'], 
            conversation_id
        )
        return count
    except Exception:
        return 0

def get_all_user_documents_count() -> int:
    """Get total document count across all user conversations using Supabase."""
    if not st.session_state.authenticated or not st.session_state.user_id:
        return 0
    
    try:
        # Get user UUID from legacy user_id
        user_data = run_async(user_service.get_user_by_id(st.session_state.user_id))
        if not user_data:
            return 0
        
        # Get all user documents from Supabase
        from services.document_service import get_user_documents_sync
        documents = get_user_documents_sync(user_data['id'])
        return len(documents)
    except Exception:
        return 0