"""
Advanced RAG Service using LangChain + Supabase pgvector
Handles document processing, embeddings, and semantic search
"""

import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
try:
    from langchain_huggingface import HuggingFaceEmbeddings as SentenceTransformerEmbeddings
except ImportError:
    from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.docstore.document import Document as LangChainDocument

# Configure logging
logger = logging.getLogger(__name__)

class RAGService:
    """Advanced RAG service with LangChain and pgvector."""
    
    def __init__(self):
        # Initialize embeddings model (384 dimensions) - using new import
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2"
            )
        except ImportError:
            # Fallback to old import for compatibility
            from langchain_community.embeddings import HuggingFaceEmbeddings as SentenceTransformerEmbeddings
            self.embeddings = SentenceTransformerEmbeddings(
                model_name="all-MiniLM-L6-v2"
            )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # Smaller chunks for better precision
            chunk_overlap=50,  # Some overlap to maintain context
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Import Supabase connection
        from supabase_manager import connection_manager
        self.db = connection_manager
    
    async def process_document(
        self, 
        document_content: str, 
        document_id: str,
        conversation_id: str,
        user_uuid: str,
        metadata: Dict = None
    ) -> bool:
        """Process document into chunks and store embeddings."""
        try:
            logger.info(f"Processing document {document_id} for RAG")
            
            # Create LangChain document
            doc = LangChainDocument(
                page_content=document_content,
                metadata=metadata or {}
            )
            
            # Split document into chunks
            chunks = self.text_splitter.split_documents([doc])
            logger.info(f"Split document into {len(chunks)} chunks")
            
            # Process chunks in batches
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                await self._process_chunk_batch(
                    batch, document_id, conversation_id, user_uuid, i
                )
            
            logger.info(f"✅ Successfully processed {len(chunks)} chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            return False
    
    async def _process_chunk_batch(
        self,
        chunks: List[LangChainDocument],
        document_id: str,
        conversation_id: str,
        user_uuid: str,
        start_index: int
    ):
        """Process a batch of chunks."""
        try:
            # Extract text content from chunks
            texts = [chunk.page_content for chunk in chunks]
            
            # Generate embeddings for the batch
            embeddings = await self._generate_embeddings(texts)
            
            # Store chunks with embeddings
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_data = {
                    'document_uuid': document_id,
                    'conversation_id': conversation_id,
                    'user_uuid': user_uuid,
                    'chunk_index': start_index + idx,
                    'content': chunk.page_content,
                    'embedding': embedding,
                    'metadata': json.dumps(chunk.metadata)
                }
                
                # Insert into database
                result = await self.db.execute_query(
                    'document_chunks',
                    'insert',
                    data=chunk_data
                )
                
                if not result.data:
                    logger.warning(f"Failed to insert chunk {start_index + idx}")
            
        except Exception as e:
            logger.error(f"Error processing chunk batch: {e}")
            raise
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        try:
            # Run embedding generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, 
                self.embeddings.embed_documents, 
                texts
            )
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    async def search_similar_chunks(
        self,
        query: str,
        conversation_id: str,
        user_uuid: str,
        similarity_threshold: float = 0.7,
        max_chunks: int = 5
    ) -> List[Dict]:
        """Search for similar document chunks using semantic similarity."""
        try:
            logger.info(f"Searching for similar chunks: '{query[:50]}...'")
            
            # Generate embedding for query
            loop = asyncio.get_event_loop()
            query_embedding = await loop.run_in_executor(
                None,
                self.embeddings.embed_query,
                query
            )
            
            # Search using pgvector function
            result = await self.db.execute_rpc(
                'search_document_chunks',
                {
                    'query_embedding': query_embedding,
                    'target_conversation_id': conversation_id,
                    'target_user_uuid': user_uuid,
                    'similarity_threshold': similarity_threshold,
                    'match_count': max_chunks
                }
            )
            
            if result.data:
                logger.info(f"Found {len(result.data)} similar chunks")
                return result.data
            else:
                logger.info("No similar chunks found")
                return []
                
        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}")
            return []
    
    async def get_conversation_context(
        self,
        query: str,
        conversation_id: str,
        user_uuid: str,
        max_context_length: int = 2000
    ) -> str:
        """Get relevant context from conversation documents for a query."""
        try:
            # Search for relevant chunks
            similar_chunks = await self.search_similar_chunks(
                query, conversation_id, user_uuid, similarity_threshold=0.6, max_chunks=8
            )
            
            if not similar_chunks:
                return ""
            
            # Build context from similar chunks
            context_parts = []
            current_length = 0
            
            for chunk in similar_chunks:
                content = chunk['content']
                similarity = chunk['similarity']
                
                # Add chunk if it fits within length limit
                if current_length + len(content) <= max_context_length:
                    context_parts.append(f"[Similarity: {similarity:.2f}] {content}")
                    current_length += len(content)
                else:
                    # Truncate last chunk if needed
                    remaining_space = max_context_length - current_length
                    if remaining_space > 100:  # Only add if meaningful space left
                        truncated = content[:remaining_space - 20] + "..."
                        context_parts.append(f"[Similarity: {similarity:.2f}] {truncated}")
                    break
            
            context = "\n\n".join(context_parts)
            logger.info(f"Built context: {len(context)} chars from {len(context_parts)} chunks")
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return ""
    
    async def delete_document_chunks(
        self,
        document_id: str,
        user_uuid: str
    ) -> bool:
        """Delete all chunks for a document."""
        try:
            result = await self.db.execute_query(
                'document_chunks',
                'delete',
                eq={
                    'document_uuid': document_id,
                    'user_uuid': user_uuid
                }
            )
            
            logger.info(f"Deleted chunks for document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document chunks: {e}")
            return False
    
    async def get_conversation_documents_summary(
        self,
        conversation_id: str,
        user_uuid: str
    ) -> Dict:
        """Get summary of documents in a conversation."""
        try:
            result = await self.db.execute_rpc(
                'get_conversation_chunks',
                {
                    'target_conversation_id': conversation_id,
                    'target_user_uuid': user_uuid
                }
            )
            
            if not result.data:
                return {'total_chunks': 0, 'documents': {}}
            
            # Group chunks by document
            documents = {}
            for chunk in result.data:
                doc_id = chunk['document_uuid']
                if doc_id not in documents:
                    documents[doc_id] = {
                        'chunk_count': 0,
                        'total_content_length': 0,
                        'created_at': chunk['created_at']
                    }
                
                documents[doc_id]['chunk_count'] += 1
                documents[doc_id]['total_content_length'] += len(chunk['content'])
            
            return {
                'total_chunks': len(result.data),
                'documents': documents
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation documents summary: {e}")
            return {'total_chunks': 0, 'documents': {}}

# Global RAG service instance
rag_service = RAGService()

# Async wrapper functions for easier use
async def process_document_for_rag(
    content: str,
    document_id: str,
    conversation_id: str,
    user_uuid: str,
    metadata: Dict = None
) -> bool:
    """Process document for RAG (async wrapper)."""
    return await rag_service.process_document(
        content, document_id, conversation_id, user_uuid, metadata
    )

async def search_conversation_context(
    query: str,
    conversation_id: str,
    user_uuid: str
) -> str:
    """Search for relevant context in conversation documents."""
    return await rag_service.get_conversation_context(
        query, conversation_id, user_uuid
    )

async def delete_document_from_rag(
    document_id: str,
    user_uuid: str
) -> bool:
    """Delete document from RAG system."""
    return await rag_service.delete_document_chunks(document_id, user_uuid)