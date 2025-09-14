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
    """Advanced RAG service with LangChain and pgvector - Full Document Processing by Default."""
    
    def __init__(self, default_full_document_mode: bool = True):
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
        
        # Initialize text splitter optimized for full document knowledge base
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # Much larger chunks to preserve more context
            chunk_overlap=300,  # Substantial overlap to maintain continuity
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]
        )
        
        # Alternative splitter for very large documents
        self.large_doc_splitter = RecursiveCharacterTextSplitter(
            chunk_size=3000,  # Very large chunks for comprehensive context
            chunk_overlap=500,  # Large overlap for continuity
            length_function=len,
            separators=["\n\n\n", "\n\n", "\n", ". ", "! ", "? "]
        )
        
        # Set default processing mode
        self.default_full_document_mode = default_full_document_mode
        logger.info("RAG Service initialized")
        
        # Import Supabase connection
        from supabase_manager import connection_manager
        self.db = connection_manager
    
    async def process_document(
        self, 
        document_content: str, 
        document_id: str,
        conversation_id: str,
        user_uuid: str,
        metadata: Dict = None,
        use_full_document_mode: bool = True  # Default to full document processing
    ) -> bool:
        """Process document for full knowledge base (default) or similarity search."""
        try:
            logger.info(f"Processing document {document_id}")
            
            # Create LangChain document with enhanced metadata
            enhanced_metadata = metadata or {}
            enhanced_metadata.update({
                'processing_mode': 'full_document_knowledge_base',
                'processed_at': datetime.now().isoformat(),
                'document_id': document_id,
                'conversation_id': conversation_id
            })
            
            doc = LangChainDocument(
                page_content=document_content,
                metadata=enhanced_metadata
            )
            
            # Choose splitter based on document size and mode
            doc_length = len(document_content)
            
            if use_full_document_mode:
                if doc_length > 10000:  # Large documents get very large chunks
                    splitter = self.large_doc_splitter
                    logger.info(f"Using large document splitter for {doc_length} character document")
                else:
                    splitter = self.text_splitter
                    logger.info(f"Using standard splitter for {doc_length} character document")
            else:
                # Fallback to smaller chunks for similarity search
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=800,
                    chunk_overlap=200,
                    length_function=len,
                    separators=["\n\n", "\n", ". ", "! ", "? ", "; ", ", ", " ", ""]
                )
            
            # Split document into chunks
            chunks = splitter.split_documents([doc])
            logger.info(f"Split document into {len(chunks)} chunks")
            
            # Process chunks in batches
            batch_size = 10
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                await self._process_chunk_batch(
                    batch, document_id, conversation_id, user_uuid, i
                )
            
            logger.info(f"Successfully processed {len(chunks)} chunks")
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
        """Process a batch of chunks with enhanced error handling."""
        try:
            # Extract text content from chunks
            texts = [chunk.page_content for chunk in chunks]
            
            # Generate embeddings for the batch
            embeddings = await self._generate_embeddings(texts)
            
            # Store chunks with embeddings
            successful_inserts = 0
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                try:
                    chunk_data = {
                        'document_uuid': document_id,
                        'conversation_id': conversation_id,
                        'user_uuid': user_uuid,
                        'chunk_index': start_index + idx,
                        'content': chunk.page_content,
                        'embedding': embedding,
                        'metadata': json.dumps(chunk.metadata)
                    }
                    
                    # Insert into database with retry logic
                    result = await self._insert_chunk_with_retry(chunk_data)
                    
                    if result:
                        successful_inserts += 1
                    else:
                        logger.warning(f"Failed to insert chunk {start_index + idx}")
                        
                except Exception as chunk_error:
                    logger.error(f"Error inserting chunk {start_index + idx}: {chunk_error}")
                    # Continue with other chunks
            
            logger.info(f"Successfully inserted {successful_inserts}/{len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Error processing chunk batch: {e}")
            raise
    
    async def _insert_chunk_with_retry(self, chunk_data: dict, max_retries: int = 3) -> bool:
        """Insert chunk with retry logic for RLS issues."""
        for attempt in range(max_retries):
            try:
                result = await self.db.execute_query(
                    'document_chunks',
                    'insert',
                    data=chunk_data
                )
                
                if result.data:
                    return True
                else:
                    logger.warning(f"Insert attempt {attempt + 1} failed - no data returned")
                    
            except Exception as e:
                error_msg = str(e)
                
                # Check for RLS policy violation
                if "row-level security policy" in error_msg.lower():
                    logger.error(f"RLS policy violation on attempt {attempt + 1}: {error_msg}")
                    
                    # Try to fix user_uuid format
                    if attempt < max_retries - 1:
                        # Ensure user_uuid is properly formatted
                        if isinstance(chunk_data['user_uuid'], str):
                            try:
                                import uuid
                                # Validate and reformat UUID
                                uuid_obj = uuid.UUID(chunk_data['user_uuid'])
                                chunk_data['user_uuid'] = str(uuid_obj)
                                logger.info(f"Reformatted user_uuid for retry {attempt + 2}")
                                continue
                            except ValueError:
                                logger.error(f"Invalid UUID format: {chunk_data['user_uuid']}")
                                break
                else:
                    logger.error(f"Insert attempt {attempt + 1} failed: {error_msg}")
                
                if attempt == max_retries - 1:
                    logger.error(f"All {max_retries} insert attempts failed for chunk")
                    return False
                    
                # Wait before retry
                await asyncio.sleep(0.5 * (attempt + 1))
        
        return False
    
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
        similarity_threshold: float = 0.5,  # Lower threshold for more results
        max_chunks: int = 10  # More chunks for thorough analysis
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
    
    async def get_full_document_context(
        self,
        conversation_id: str,
        user_uuid: str,
        max_context_length: int = 15000  # Much larger for full document context
    ) -> str:
        """Get complete document context for conversation (entire documents as knowledge base)."""
        try:
            logger.info(f"Getting document context for conversation {conversation_id}")
            
            # Get ALL chunks for this conversation (not just similar ones)
            result = await self.db.execute_rpc(
                'get_conversation_chunks',
                {
                    'target_conversation_id': conversation_id,
                    'target_user_uuid': user_uuid
                }
            )
            
            if not result.data:
                logger.info("No document chunks found for conversation")
                return ""
            
            # Group chunks by document
            documents = {}
            for chunk in result.data:
                doc_uuid = chunk['document_uuid']
                if doc_uuid not in documents:
                    documents[doc_uuid] = {
                        'chunks': [],
                        'metadata': chunk.get('metadata', {})
                    }
                documents[doc_uuid]['chunks'].append(chunk)
            
            # Build complete document context
            context_parts = []
            current_length = 0
            
            for doc_uuid, doc_data in documents.items():
                # Sort chunks by index to maintain document order
                sorted_chunks = sorted(doc_data['chunks'], key=lambda x: x['chunk_index'])
                
                # Reconstruct full document content
                doc_content = ""
                doc_filename = "Unknown Document"
                
                # Try to get filename from metadata
                try:
                    if isinstance(doc_data['metadata'], str):
                        import json
                        metadata = json.loads(doc_data['metadata'])
                    else:
                        metadata = doc_data['metadata']
                    
                    doc_filename = metadata.get('filename', doc_filename)
                except:
                    pass
                
                # Combine all chunks to reconstruct full document
                for chunk in sorted_chunks:
                    doc_content += chunk['content'] + "\n"
                
                # Add document to context if it fits
                doc_section = f"\n=== DOCUMENT: {doc_filename} ===\n{doc_content.strip()}\n"
                
                if current_length + len(doc_section) <= max_context_length:
                    context_parts.append(doc_section)
                    current_length += len(doc_section)
                else:
                    # If document is too long, include as much as possible
                    remaining_space = max_context_length - current_length - 100  # Leave some buffer
                    if remaining_space > 500:  # Only add if meaningful space left
                        truncated_content = doc_content[:remaining_space] + "\n[... document continues ...]"
                        doc_section = f"\n=== DOCUMENT: {doc_filename} ===\n{truncated_content}\n"
                        context_parts.append(doc_section)
                    break
            
            full_context = "".join(context_parts)
            logger.info(f"Built document context: {len(full_context)} chars from {len(documents)} documents")
            
            return full_context
            
        except Exception as e:
            logger.error(f"Error getting full document context: {e}")
            return ""
    
    async def get_conversation_context(
        self,
        query: str,
        conversation_id: str,
        user_uuid: str,
        max_context_length: int = 4000  # Increased for more thorough context
    ) -> str:
        """Get relevant context from conversation documents for a query."""
        try:
            # Search for relevant chunks with multiple strategies
            # Strategy 1: High similarity chunks
            high_sim_chunks = await self.search_similar_chunks(
                query, conversation_id, user_uuid, similarity_threshold=0.7, max_chunks=5
            )
            
            # Strategy 2: Medium similarity chunks for broader context
            med_sim_chunks = await self.search_similar_chunks(
                query, conversation_id, user_uuid, similarity_threshold=0.5, max_chunks=10
            )
            
            # Combine and deduplicate
            seen_chunks = set()
            similar_chunks = []
            
            for chunk in high_sim_chunks + med_sim_chunks:
                chunk_id = f"{chunk['document_uuid']}_{chunk['chunk_index']}"
                if chunk_id not in seen_chunks:
                    seen_chunks.add(chunk_id)
                    similar_chunks.append(chunk)
            
            # Sort by similarity score
            similar_chunks.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            
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