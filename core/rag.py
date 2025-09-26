"""
Advanced RAG Service for PharmGPT
Uses Supabase + pgvector for conversation-specific knowledge bases
Integrates with Mistral AI for 1024-dimensional embeddings
"""

import logging
import asyncio
from typing import List, Dict, Optional, Tuple, Any
import uuid
import json
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_mistralai import MistralAIEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain not available. Install with: pip install langchain langchain-mistralai")

from core.supabase_client import supabase_manager


class DocumentProcessor:
    """Handles document processing and text chunking."""
    
    def __init__(self):
        self.text_splitters = {
            'small': RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""]
            ) if LANGCHAIN_AVAILABLE else None,
            'medium': RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
                separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""]
            ) if LANGCHAIN_AVAILABLE else None,
            'large': RecursiveCharacterTextSplitter(
                chunk_size=1500,
                chunk_overlap=150,
                separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""]
            ) if LANGCHAIN_AVAILABLE else None
        }
    
    def chunk_text(self, text: str, chunk_size: str = 'medium') -> List[str]:
        """Split text into chunks."""
        if not LANGCHAIN_AVAILABLE:
            # Fallback simple chunking
            chunk_sizes = {'small': 500, 'medium': 1000, 'large': 1500}
            size = chunk_sizes.get(chunk_size, 1000)
            return [text[i:i+size] for i in range(0, len(text), size)]
        
        splitter = self.text_splitters.get(chunk_size, self.text_splitters['medium'])
        return splitter.split_text(text)
    
    def extract_metadata(self, filename: str, file_type: str, 
                        chunk_index: int, chunk_text: str) -> Dict:
        """Extract metadata for a chunk."""
        return {
            'filename': filename,
            'file_type': file_type,
            'chunk_index': chunk_index,
            'chunk_length': len(chunk_text),
            'word_count': len(chunk_text.split()),
            'processed_at': datetime.now().isoformat()
        }


class EmbeddingManager:
    """Manages embeddings using Mistral AI."""
    
    def __init__(self):
        self.embeddings = None
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Initialize Mistral AI embeddings."""
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain not available, embeddings disabled")
            return
        
        try:
            import os
            import streamlit as st
            
            # Get API key from secrets or environment
            api_key = None
            try:
                api_key = st.secrets.get("MISTRAL_API_KEY")
            except:
                pass
            
            if not api_key:
                api_key = os.getenv("MISTRAL_API_KEY")
            
            if api_key:
                self.embeddings = MistralAIEmbeddings(
                    model="mistral-embed",
                    mistral_api_key=api_key
                )
                logger.info("✅ Mistral AI embeddings initialized")
            else:
                logger.warning("❌ MISTRAL_API_KEY not found")
                
        except Exception as e:
            logger.error(f"Error initializing embeddings: {e}")
    
    def is_available(self) -> bool:
        """Check if embeddings are available."""
        return self.embeddings is not None
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not self.is_available():
            logger.warning("Embeddings not available, returning empty vectors")
            return [[0.0] * 1024 for _ in texts]  # Return zero vectors
        
        try:
            # Generate embeddings in batches to avoid rate limits
            batch_size = 20
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = await asyncio.get_event_loop().run_in_executor(
                    None, self.embeddings.embed_documents, batch
                )
                all_embeddings.extend(batch_embeddings)
                
                # Small delay between batches
                await asyncio.sleep(0.1)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return [[0.0] * 1024 for _ in texts]  # Return zero vectors
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for a single query."""
        if not self.is_available():
            return [0.0] * 1024  # Return zero vector
        
        try:
            embedding = await asyncio.get_event_loop().run_in_executor(
                None, self.embeddings.embed_query, query
            )
            return embedding
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            return [0.0] * 1024  # Return zero vector


class ConversationRAG:
    """RAG system with conversation-specific knowledge bases."""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.embedding_manager = EmbeddingManager()
    
    async def process_document(self, conversation_id: str, user_id: str,
                             filename: str, file_content: str, 
                             file_type: str, file_size: int) -> Tuple[bool, str, Optional[str]]:
        """Process and store a document for a specific conversation."""
        try:
            logger.info(f"Processing document {filename} for conversation {conversation_id}")
            
            # Save document metadata
            document_id = await supabase_manager.save_document(
                conversation_id=conversation_id,
                user_id=user_id,
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                content_preview=file_content[:500] if file_content else None
            )
            
            if not document_id:
                return False, "Failed to save document metadata", None
            
            # Chunk the document
            chunks = self.document_processor.chunk_text(file_content)
            logger.info(f"Document split into {len(chunks)} chunks")
            
            if not chunks:
                await supabase_manager.update_document_status(
                    document_id, 'failed', 0
                )
                return False, "No content to process", document_id
            
            # Generate embeddings
            embeddings = await self.embedding_manager.generate_embeddings(chunks)
            
            # Prepare chunk data
            chunk_data = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                metadata = self.document_processor.extract_metadata(
                    filename, file_type, i, chunk
                )
                
                chunk_data.append({
                    'document_id': document_id,
                    'conversation_id': conversation_id,
                    'user_id': user_id,
                    'chunk_index': i,
                    'content': chunk,
                    'metadata': metadata,
                    'embedding': embedding
                })
            
            # Save chunks
            success = await supabase_manager.save_document_chunks(chunk_data)
            
            if success:
                await supabase_manager.update_document_status(
                    document_id, 'completed', len(chunks)
                )
                logger.info(f"Successfully processed {filename} with {len(chunks)} chunks")
                return True, f"Document processed successfully! Created {len(chunks)} chunks.", document_id
            else:
                await supabase_manager.update_document_status(
                    document_id, 'failed', 0
                )
                return False, "Failed to save document chunks", document_id
                
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            if 'document_id' in locals() and document_id:
                await supabase_manager.update_document_status(
                    document_id, 'failed', 0
                )
            return False, f"Error processing document: {str(e)}", None
    
    async def search_conversation_documents(self, query: str, conversation_id: str,
                                          user_id: str, limit: int = 10,
                                          similarity_threshold: float = 0.7) -> List[Dict]:
        """Search documents within a specific conversation."""
        try:
            # Generate query embedding
            query_embedding = await self.embedding_manager.generate_query_embedding(query)
            
            # Search using conversation-specific context
            results = await supabase_manager.search_documents(
                query_embedding=query_embedding,
                user_id=user_id,
                conversation_id=conversation_id,
                similarity_threshold=similarity_threshold,
                limit=limit
            )
            
            logger.info(f"Found {len(results)} relevant chunks for query in conversation {conversation_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching conversation documents: {e}")
            return []
    
    async def search_all_user_documents(self, query: str, user_id: str,
                                      limit: int = 20,
                                      similarity_threshold: float = 0.7) -> List[Dict]:
        """Search across all user documents (global search)."""
        try:
            # Generate query embedding
            query_embedding = await self.embedding_manager.generate_query_embedding(query)
            
            # Search all user documents
            results = await supabase_manager.search_documents(
                query_embedding=query_embedding,
                user_id=user_id,
                conversation_id=None,  # Search all conversations
                similarity_threshold=similarity_threshold,
                limit=limit
            )
            
            logger.info(f"Found {len(results)} relevant chunks across all user documents")
            return results
            
        except Exception as e:
            logger.error(f"Error searching all user documents: {e}")
            return []
    
    async def get_conversation_context(self, conversation_id: str, 
                                     user_id: str, max_chunks: int = 50) -> str:
        """Get full context from all documents in a conversation."""
        try:
            # Get all chunks for the conversation
            chunks = await supabase_manager.get_conversation_context(
                conversation_id, user_id
            )
            
            if not chunks:
                return ""
            
            # Sort by filename and chunk index
            chunks.sort(key=lambda x: (x.get('filename', ''), x.get('chunk_index', 0)))
            
            # Limit to max_chunks to avoid token limits
            chunks = chunks[:max_chunks]
            
            # Build context string
            context_parts = []
            current_file = None
            
            for chunk in chunks:
                filename = chunk.get('filename', 'Unknown')
                content = chunk.get('content', '')
                
                if filename != current_file:
                    if current_file is not None:
                        context_parts.append("\n---\n")
                    context_parts.append(f"**File: {filename}**\n")
                    current_file = filename
                
                context_parts.append(content)
                context_parts.append("\n\n")
            
            context = "".join(context_parts).strip()
            logger.info(f"Built context from {len(chunks)} chunks ({len(context)} characters)")
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return ""
    
    async def get_relevant_context(self, query: str, conversation_id: str,
                                 user_id: str, max_context_length: int = 8000) -> str:
        """Get relevant context for a query, optimized for token limits."""
        try:
            # Search for relevant chunks
            relevant_chunks = await self.search_conversation_documents(
                query=query,
                conversation_id=conversation_id,
                user_id=user_id,
                limit=20,
                similarity_threshold=0.6
            )
            
            if not relevant_chunks:
                return ""
            
            # Sort by similarity score (highest first)
            relevant_chunks.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            
            # Build context within token limit
            context_parts = []
            total_length = 0
            
            for chunk in relevant_chunks:
                content = chunk.get('content', '')
                chunk_meta = chunk.get('metadata', {})
                filename = chunk_meta.get('filename', 'Unknown')
                
                # Estimate token usage (rough: 4 chars per token)
                chunk_tokens = len(content) // 4
                
                if total_length + chunk_tokens > max_context_length // 4:
                    break
                
                context_parts.append(f"[{filename}] {content}")
                total_length += len(content)
            
            context = "\n\n".join(context_parts)
            logger.info(f"Built relevant context from {len(context_parts)} chunks ({len(context)} characters)")
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            return ""
    
    def get_embedding_status(self) -> Dict[str, Any]:
        """Get status of the embedding system."""
        return {
            'langchain_available': LANGCHAIN_AVAILABLE,
            'embeddings_available': self.embedding_manager.is_available(),
            'model': 'mistral-embed' if self.embedding_manager.is_available() else 'None',
            'dimensions': 1024
        }


# Global RAG instance
conversation_rag = ConversationRAG()

# Convenience functions
async def process_document(conversation_id: str, user_id: str, filename: str,
                         file_content: str, file_type: str, file_size: int) -> Tuple[bool, str, Optional[str]]:
    """Process a document for RAG."""
    return await conversation_rag.process_document(
        conversation_id, user_id, filename, file_content, file_type, file_size
    )

async def search_conversation(query: str, conversation_id: str, user_id: str) -> List[Dict]:
    """Search within conversation documents."""
    return await conversation_rag.search_conversation_documents(
        query, conversation_id, user_id
    )

async def get_conversation_context(conversation_id: str, user_id: str) -> str:
    """Get full conversation document context."""
    return await conversation_rag.get_conversation_context(conversation_id, user_id)

async def get_relevant_context(query: str, conversation_id: str, user_id: str) -> str:
    """Get relevant context for a query."""
    return await conversation_rag.get_relevant_context(query, conversation_id, user_id)

def get_rag_status() -> Dict[str, Any]:
    """Get RAG system status."""
    return conversation_rag.get_embedding_status()