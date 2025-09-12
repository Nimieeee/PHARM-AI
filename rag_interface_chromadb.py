"""
RAG Interface for PharmBot Streamlit App
Now using ChromaDB for reliable, unlimited vector storage
"""

import streamlit as st
from rag_system_chromadb import ChromaRAGSystem
from PIL import Image
import io
from datetime import datetime
from typing import Optional

def initialize_rag_system(conversation_id: str = None) -> Optional[ChromaRAGSystem]:
    """Initialize conversation-specific ChromaDB RAG system."""
    if not st.session_state.authenticated:
        return None
    
    # Use current conversation ID if not provided
    if conversation_id is None:
        conversation_id = getattr(st.session_state, 'current_conversation_id', None)
    
    if not conversation_id:
        return None
    
    # Create unique key for this conversation's RAG system
    rag_key = f"chromadb_rag_system_{conversation_id}"
    
    if rag_key not in st.session_state:
        try:
            st.session_state[rag_key] = ChromaRAGSystem(st.session_state.user_id, conversation_id)
        except Exception as e:
            st.error(f"❌ Failed to initialize ChromaDB RAG system for conversation: {e}")
            return None
    
    return st.session_state[rag_key]

def get_rag_enhanced_prompt(original_prompt: str, rag_system: ChromaRAGSystem) -> str:
    """Enhance a prompt with RAG context."""
    if not rag_system:
        return original_prompt
    
    # For generic queries like "explain", try to get all recent documents
    generic_queries = ['explain', 'describe', 'what is this', 'tell me about this', 'explain the image', 'describe the figure', 'what does this show']
    if any(query in original_prompt.lower() for query in generic_queries):
        # Get all documents and use the most recent ones
        documents = rag_system.get_documents_list()
        if documents:
            # Sort by added_at and get the most recent
            recent_docs = sorted(documents, key=lambda x: x.get('added_at', ''), reverse=True)[:3]
            
            context_parts = []
            for doc in recent_docs:
                # For images, try multiple search terms
                if doc.get('file_type') == 'image':
                    search_terms = [doc['filename'], 'image', 'figure', 'diagram', 'chart']
                    for term in search_terms:
                        doc_context = rag_system.get_context_for_query(term)
                        if doc_context:
                            context_parts.append(doc_context)
                            break
                else:
                    # Get some content from this document
                    doc_context = rag_system.get_context_for_query(doc['filename'])
                    if doc_context:
                        context_parts.append(doc_context)
            
            if context_parts:
                context = "\n\n".join(context_parts)
                enhanced_prompt = f"""The user has uploaded documents and is asking you to explain or describe them. Based on the following content from their most recently uploaded documents, please provide a comprehensive explanation:

Context from user's documents:
{context}

User's request: {original_prompt}

Please analyze and explain the content, focusing on the key concepts, findings, or information presented in these documents. If this appears to be scientific content (like genetics, pharmacology, or medical research), provide detailed scientific analysis."""
                return enhanced_prompt
    
    # Get relevant context for specific queries
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

def get_conversation_document_count(conversation_id: str = None) -> int:
    """Get the number of documents in the current conversation."""
    if not st.session_state.authenticated:
        return 0
    
    if conversation_id is None:
        conversation_id = getattr(st.session_state, 'current_conversation_id', None)
    
    if not conversation_id:
        return 0
    
    rag_system = initialize_rag_system(conversation_id)
    if rag_system:
        documents = rag_system.get_documents_list()
        return len(documents)
    
    return 0

def get_all_user_documents_count() -> int:
    """Get total number of documents across all conversations for the user."""
    if not st.session_state.authenticated:
        return 0
    
    from pathlib import Path
    import json
    
    user_rag_dir = Path("user_data") / f"rag_{st.session_state.user_id}"
    if not user_rag_dir.exists():
        return 0
    
    total_docs = 0
    for conv_dir in user_rag_dir.glob("conversation_*"):
        metadata_file = conv_dir / "documents_metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    total_docs += len(metadata)
            except:
                pass
    
    return total_docs

def migrate_from_pinecone_to_chromadb():
    """Migrate existing Pinecone RAG data to ChromaDB."""
    if not st.session_state.authenticated:
        return False
    
    from pathlib import Path
    import json
    
    user_rag_dir = Path("user_data") / f"rag_{st.session_state.user_id}"
    if not user_rag_dir.exists():
        return True  # Nothing to migrate
    
    migrated_conversations = 0
    
    for conv_dir in user_rag_dir.glob("conversation_*"):
        metadata_file = conv_dir / "documents_metadata.json"
        local_vectors_file = conv_dir / "local_vectors.json"
        
        # Check if this conversation has documents but no ChromaDB
        chroma_dir = conv_dir / "chroma_db"
        
        if metadata_file.exists() and not chroma_dir.exists():
            try:
                # Extract conversation ID from directory name
                conv_id = conv_dir.name.replace("conversation_", "")
                
                # Initialize ChromaDB RAG system for this conversation
                rag_system = ChromaRAGSystem(st.session_state.user_id, conv_id)
                
                # Load metadata to see what documents were there
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                print(f"📁 Found conversation {conv_id} with {len(metadata)} documents")
                print("   ⚠️ Note: Document content needs to be re-uploaded as we only have metadata")
                
                migrated_conversations += 1
                
            except Exception as e:
                print(f"❌ Error migrating conversation {conv_dir.name}: {e}")
    
    if migrated_conversations > 0:
        print(f"✅ Migrated {migrated_conversations} conversations to ChromaDB")
        print("📝 Note: You'll need to re-upload documents as only metadata was preserved")
    else:
        print("✅ No migration needed - all conversations already use ChromaDB")
    
    return True