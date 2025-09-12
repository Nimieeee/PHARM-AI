"""
RAG Interface for ChromaDB integration with Streamlit
"""

from typing import Optional
import streamlit as st
from rag_system_chromadb import initialize_rag_system, ConversationRAGSystem
from prompts import get_rag_enhanced_prompt

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
    """Display RAG system sidebar with document management."""
    if not st.session_state.authenticated:
        return
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Knowledge Base")
    
    # Initialize RAG system
    rag_system = initialize_rag_system(conversation_id)
    
    if not rag_system:
        st.sidebar.error("RAG system unavailable")
        return
    
    # Get documents list
    documents = rag_system.get_documents_list()
    
    if documents:
        st.sidebar.markdown(f"**{len(documents)} document(s) in this conversation:**")
        
        for doc in documents:
            with st.sidebar.expander(f"📄 {doc['filename']}", expanded=False):
                st.write(f"**Type:** {doc['file_type']}")
                st.write(f"**Chunks:** {doc['chunk_count']}")
                st.write(f"**Added:** {doc['added_at'][:10]}")
                
                # Delete button
                if st.button(f"🗑️ Delete", key=f"delete_{doc['document_hash']}", help="Delete this document"):
                    if rag_system.delete_document(doc['document_hash']):
                        st.success("Document deleted!")
                        st.rerun()
                    else:
                        st.error("Failed to delete document")
        
        # Search functionality
        st.sidebar.markdown("---")
        st.sidebar.markdown("**🔍 Search Documents:**")
        search_query = st.sidebar.text_input("Search query", key=f"search_{conversation_id}")
        
        if search_query and st.sidebar.button("Search", key=f"search_btn_{conversation_id}"):
            results = rag_system.search_documents(search_query)
            
            if results:
                st.sidebar.markdown("**Search Results:**")
                for i, result in enumerate(results[:3]):  # Show top 3 results
                    with st.sidebar.expander(f"Result {i+1}: {result['filename']}", expanded=False):
                        st.write(f"**Relevance:** {result['relevance_score']:.2f}")
                        st.write(f"**Content:** {result['content'][:200]}...")
            else:
                st.sidebar.info("No relevant documents found")
    
    else:
        st.sidebar.info("No documents uploaded yet")
        st.sidebar.markdown("Upload documents using the 📎 button in the chat to enhance responses with your content.")

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

def get_conversation_document_count(conversation_id: str = None) -> int:
    """Get document count for a specific conversation."""
    if not st.session_state.authenticated:
        return 0
    
    # Use current conversation if none specified
    if conversation_id is None:
        conversation_id = st.session_state.get('current_conversation_id')
    
    if not conversation_id:
        return 0
    
    try:
        rag_system = initialize_rag_system(conversation_id)
        if rag_system:
            documents = rag_system.get_documents_list()
            return len(documents)
    except Exception:
        pass
    
    return 0

def get_all_user_documents_count() -> int:
    """Get total document count across all user conversations."""
    if not st.session_state.authenticated or not st.session_state.user_id:
        return 0
    
    total_count = 0
    
    try:
        # Get all conversations for the user
        conversations = st.session_state.get('conversations', {})
        
        for conv_id in conversations.keys():
            try:
                rag_system = initialize_rag_system(conv_id)
                if rag_system:
                    documents = rag_system.get_documents_list()
                    total_count += len(documents)
            except Exception:
                continue
    except Exception:
        pass
    
    return total_count