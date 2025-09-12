"""
Document Service for PharmGPT
Handles document metadata for RAG system with Supabase
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import streamlit as st
import logging

from supabase_manager import connection_manager, SupabaseError, ErrorHandler

logger = logging.getLogger(__name__)

class DocumentService:
    """Service class for document metadata management in RAG system."""
    
    def __init__(self):
        self.connection_manager = connection_manager
    
    def _generate_document_hash(self, content: str, filename: str, conversation_id: str) -> str:
        """Generate unique hash for document content in conversation context."""
        hash_input = f"{conversation_id}_{filename}_{content}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    async def save_document_metadata(self, user_uuid: str, conversation_id: str, doc_data: Dict) -> bool:
        """
        Save document metadata to Supabase.
        
        Args:
            user_uuid: User's UUID
            conversation_id: Conversation ID
            doc_data: Document metadata dictionary
            
        Returns:
            bool: Success status
        """
        try:
            # Validate required fields
            required_fields = ['document_hash', 'filename', 'file_type', 'file_size', 'chunk_count']
            if not all(field in doc_data for field in required_fields):
                logger.error(f"Missing required fields in document data: {doc_data}")
                return False
            
            # Create document metadata with only confirmed schema fields
            document_metadata = {
                'user_uuid': user_uuid,
                'conversation_id': conversation_id,
                'document_id': doc_data['document_hash'],  # Use existing document_id field
                'filename': doc_data['filename'],
                'file_type': doc_data['file_type'],
                'file_size': doc_data['file_size'],
                'content': doc_data.get('content', ''),
                'metadata': json.dumps({
                    'chunk_count': doc_data['chunk_count'],
                    'processing_method': doc_data.get('processing_method', 'unknown'),
                    **doc_data.get('metadata', {})
                }),
                'is_processed': doc_data.get('is_processed', True)
            }
            
            result = self.connection_manager.execute_query(
                table='documents',
                operation='upsert',
                data=document_metadata
            )
            
            if result.data:
                logger.info(f"Document metadata saved: {doc_data['filename']} in conversation {conversation_id}")
                return True
            else:
                logger.error(f"Failed to save document metadata: {doc_data['filename']}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving document metadata: {str(e)}")
            return False
    
    async def get_conversation_documents(self, user_uuid: str, conversation_id: str) -> List[Dict]:
        """
        Get all documents for a specific conversation.
        
        Args:
            user_uuid: User's UUID
            conversation_id: Conversation ID
            
        Returns:
            List[Dict]: List of document metadata
        """
        try:
            result = self.connection_manager.execute_query(
                table='documents',
                operation='select',
                eq={
                    'user_id': user_uuid,
                    'conversation_id': conversation_id
                },
                order='added_at.desc'
            )
            
            documents = []
            if result.data:
                for doc in result.data:
                    # Parse metadata JSON
                    metadata = json.loads(doc['metadata']) if doc['metadata'] else {}
                    
                    documents.append({
                        'document_hash': doc['document_hash'],
                        'filename': doc['filename'],
                        'file_type': doc['file_type'],
                        'file_size': doc['file_size'],
                        'chunk_count': doc['chunk_count'],
                        'added_at': doc['added_at'],
                        'metadata': metadata,
                        'is_processed': doc.get('is_processed', True),
                        'processing_error': doc.get('processing_error')
                    })
            
            logger.info(f"Retrieved {len(documents)} documents for conversation {conversation_id}")
            return documents
            
        except Exception as e:
            logger.error(f"Error getting documents for conversation {conversation_id}: {str(e)}")
            return []
    
    async def get_user_documents(self, user_uuid: str, limit: int = 100) -> List[Dict]:
        """
        Get all documents for a user across all conversations.
        
        Args:
            user_uuid: User's UUID
            limit: Maximum number of documents to return
            
        Returns:
            List[Dict]: List of document metadata
        """
        try:
            result = self.connection_manager.execute_query(
                table='documents',
                operation='select',
                eq={'user_id': user_uuid},
                limit=limit,
                order='added_at.desc'
            )
            
            documents = []
            if result.data:
                for doc in result.data:
                    metadata = json.loads(doc['metadata']) if doc['metadata'] else {}
                    
                    documents.append({
                        'document_hash': doc['document_hash'],
                        'conversation_id': doc['conversation_id'],
                        'filename': doc['filename'],
                        'file_type': doc['file_type'],
                        'file_size': doc['file_size'],
                        'chunk_count': doc['chunk_count'],
                        'added_at': doc['added_at'],
                        'metadata': metadata,
                        'is_processed': doc.get('is_processed', True),
                        'processing_error': doc.get('processing_error')
                    })
            
            logger.info(f"Retrieved {len(documents)} documents for user {user_uuid}")
            return documents
            
        except Exception as e:
            logger.error(f"Error getting documents for user {user_uuid}: {str(e)}")
            return []
    
    async def get_document_by_hash(self, user_uuid: str, document_hash: str) -> Optional[Dict]:
        """
        Get document metadata by hash.
        
        Args:
            user_uuid: User's UUID
            document_hash: Document hash
            
        Returns:
            Optional[Dict]: Document metadata or None if not found
        """
        try:
            result = self.connection_manager.execute_query(
                table='documents',
                operation='select',
                eq={
                    'user_id': user_uuid,
                    'document_hash': document_hash
                }
            )
            
            if result.data:
                doc = result.data[0]
                metadata = json.loads(doc['metadata']) if doc['metadata'] else {}
                
                return {
                    'document_hash': doc['document_hash'],
                    'conversation_id': doc['conversation_id'],
                    'filename': doc['filename'],
                    'file_type': doc['file_type'],
                    'file_size': doc['file_size'],
                    'chunk_count': doc['chunk_count'],
                    'added_at': doc['added_at'],
                    'metadata': metadata,
                    'is_processed': doc.get('is_processed', True),
                    'processing_error': doc.get('processing_error')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting document by hash {document_hash}: {str(e)}")
            return None
    
    async def delete_document(self, user_uuid: str, document_hash: str) -> bool:
        """
        Delete document metadata.
        
        Args:
            user_uuid: User's UUID
            document_hash: Document hash to delete
            
        Returns:
            bool: Success status
        """
        try:
            result = self.connection_manager.execute_query(
                table='documents',
                operation='delete',
                eq={
                    'user_id': user_uuid,
                    'document_hash': document_hash
                }
            )
            
            logger.info(f"Document metadata deleted: {document_hash}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting document {document_hash}: {str(e)}")
            return False
    
    async def delete_conversation_documents(self, user_uuid: str, conversation_id: str) -> int:
        """
        Delete all documents for a conversation.
        
        Args:
            user_uuid: User's UUID
            conversation_id: Conversation ID
            
        Returns:
            int: Number of documents deleted
        """
        try:
            # First get the documents to count them
            documents = await self.get_conversation_documents(user_uuid, conversation_id)
            
            result = self.connection_manager.execute_query(
                table='documents',
                operation='delete',
                eq={
                    'user_id': user_uuid,
                    'conversation_id': conversation_id
                }
            )
            
            count = len(documents)
            logger.info(f"Deleted {count} documents for conversation {conversation_id}")
            return count
            
        except Exception as e:
            logger.error(f"Error deleting documents for conversation {conversation_id}: {str(e)}")
            return 0
    
    async def update_document_status(self, user_uuid: str, document_hash: str, is_processed: bool, processing_error: str = None) -> bool:
        """
        Update document processing status.
        
        Args:
            user_uuid: User's UUID
            document_hash: Document hash
            is_processed: Processing status
            processing_error: Error message if processing failed
            
        Returns:
            bool: Success status
        """
        try:
            update_data = {
                'is_processed': is_processed,
                'processing_error': processing_error
            }
            
            result = self.connection_manager.execute_query(
                table='documents',
                operation='update',
                data=update_data,
                eq={
                    'user_id': user_uuid,
                    'document_hash': document_hash
                }
            )
            
            if result.data:
                logger.info(f"Document status updated: {document_hash}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating document status {document_hash}: {str(e)}")
            return False
    
    async def search_documents(self, user_uuid: str, query: str, conversation_id: str = None, limit: int = 20) -> List[Dict]:
        """
        Search documents by filename or metadata.
        
        Args:
            user_uuid: User's UUID
            query: Search query
            conversation_id: Optional conversation filter
            limit: Maximum results
            
        Returns:
            List[Dict]: Matching documents
        """
        try:
            # Get documents to search
            if conversation_id:
                documents = await self.get_conversation_documents(user_uuid, conversation_id)
            else:
                documents = await self.get_user_documents(user_uuid)
            
            # Search in filenames and metadata (client-side for now)
            results = []
            query_lower = query.lower()
            
            for doc in documents:
                # Search in filename
                if query_lower in doc['filename'].lower():
                    results.append({
                        **doc,
                        'match_type': 'filename'
                    })
                    continue
                
                # Search in file type
                if query_lower in doc['file_type'].lower():
                    results.append({
                        **doc,
                        'match_type': 'file_type'
                    })
                    continue
                
                # Search in metadata
                metadata_str = json.dumps(doc['metadata']).lower()
                if query_lower in metadata_str:
                    results.append({
                        **doc,
                        'match_type': 'metadata'
                    })
                
                if len(results) >= limit:
                    break
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching documents for user {user_uuid}: {str(e)}")
            return []
    
    async def get_document_stats(self, user_uuid: str) -> Dict:
        """Get document statistics for a user."""
        try:
            documents = await self.get_user_documents(user_uuid)
            
            total_documents = len(documents)
            total_size = sum(doc['file_size'] for doc in documents)
            total_chunks = sum(doc['chunk_count'] for doc in documents)
            
            # Group by file type
            file_types = {}
            for doc in documents:
                file_type = doc['file_type']
                if file_type not in file_types:
                    file_types[file_type] = {'count': 0, 'size': 0}
                file_types[file_type]['count'] += 1
                file_types[file_type]['size'] += doc['file_size']
            
            # Processing status
            processed_count = sum(1 for doc in documents if doc.get('is_processed', True))
            failed_count = sum(1 for doc in documents if doc.get('processing_error'))
            
            return {
                'total_documents': total_documents,
                'total_size_bytes': total_size,
                'total_chunks': total_chunks,
                'avg_chunks_per_document': total_chunks / total_documents if total_documents > 0 else 0,
                'file_types': file_types,
                'processed_documents': processed_count,
                'failed_documents': failed_count,
                'processing_success_rate': processed_count / total_documents if total_documents > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting document stats for user {user_uuid}: {str(e)}")
            return {}
    
    async def get_conversation_document_count(self, user_uuid: str, conversation_id: str) -> int:
        """Get document count for a specific conversation."""
        try:
            documents = await self.get_conversation_documents(user_uuid, conversation_id)
            return len(documents)
            
        except Exception as e:
            logger.error(f"Error getting document count for conversation {conversation_id}: {str(e)}")
            return 0
    
    async def check_document_exists(self, user_uuid: str, document_hash: str, conversation_id: str) -> bool:
        """Check if a document already exists in a conversation."""
        try:
            result = self.connection_manager.execute_query(
                table='documents',
                operation='select',
                columns='document_hash',
                eq={
                    'user_id': user_uuid,
                    'document_hash': document_hash,
                    'conversation_id': conversation_id
                }
            )
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error checking document existence {document_hash}: {str(e)}")
            return False
    
    async def update_document_metadata(self, user_uuid: str, document_hash: str, metadata: Dict) -> bool:
        """Update document metadata."""
        try:
            result = self.connection_manager.execute_query(
                table='documents',
                operation='update',
                data={'metadata': json.dumps(metadata)},
                eq={
                    'user_id': user_uuid,
                    'document_hash': document_hash
                }
            )
            
            if result.data:
                logger.info(f"Document metadata updated: {document_hash}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error updating document metadata {document_hash}: {str(e)}")
            return False
    
    async def batch_delete_documents(self, user_uuid: str, document_hashes: List[str]) -> int:
        """
        Batch delete multiple documents.
        
        Args:
            user_uuid: User's UUID
            document_hashes: List of document hashes to delete
            
        Returns:
            int: Number of successfully deleted documents
        """
        success_count = 0
        
        for doc_hash in document_hashes:
            if await self.delete_document(user_uuid, doc_hash):
                success_count += 1
        
        logger.info(f"Batch deleted {success_count}/{len(document_hashes)} documents")
        return success_count

# Global document service instance
document_service = DocumentService()

# Convenience functions for backward compatibility
async def save_document_metadata(user_uuid: str, conversation_id: str, doc_data: Dict) -> bool:
    """Save document metadata."""
    return await document_service.save_document_metadata(user_uuid, conversation_id, doc_data)

async def get_conversation_documents(user_uuid: str, conversation_id: str) -> List[Dict]:
    """Get conversation documents."""
    return await document_service.get_conversation_documents(user_uuid, conversation_id)

async def delete_document(user_uuid: str, document_hash: str) -> bool:
    """Delete document."""
    return await document_service.delete_document(user_uuid, document_hash)