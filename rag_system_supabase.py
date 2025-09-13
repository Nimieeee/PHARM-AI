"""
RAG System using Supabase pgvector for conversation-specific document storage
"""

import os
import json
import hashlib
import tempfile
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import streamlit as st
import sys
import logging

from supabase_manager import get_supabase_client

logger = logging.getLogger(__name__)

# Import Supabase services (only when in Streamlit context)
def _get_supabase_services():
    """Get Supabase services if available and in Streamlit context."""
    try:
        # Only import if we're in a Streamlit context
        if 'streamlit' in sys.modules:
            from services.document_service import document_service
            from services.user_service import user_service
            return document_service, user_service, True
    except ImportError:
        pass
    return None, None, False

# Import PIL Image at module level
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

# Import pytesseract for OCR
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    pytesseract = None

# Import pandas for CSV processing
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

# Import PyPDF2 for PDF processing
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    PyPDF2 = None

# Import docx for Word document processing
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    docx = None

# Lazy import flag - dependencies loaded only when needed
DEPENDENCIES_AVAILABLE = None

def _check_dependencies():
    """Check if RAG dependencies are available (lazy loading)."""
    global DEPENDENCIES_AVAILABLE
    if DEPENDENCIES_AVAILABLE is None:
        try:
            from sentence_transformers import SentenceTransformer
            import PyPDF2
            import docx
            import pandas as pd
            from PIL import Image
            DEPENDENCIES_AVAILABLE = True
        except ImportError as e:
            DEPENDENCIES_AVAILABLE = False
            # Only show warning if in Streamlit context
            if 'streamlit' in sys.modules:
                st.warning(f"RAG system unavailable: {e}")
    return DEPENDENCIES_AVAILABLE

# Simple text splitter class to avoid heavy dependencies
class RecursiveCharacterTextSplitter:
    """Simple text splitter for chunking documents."""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, 
                 length_function=len, separators=None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function
        self.separators = separators or ["\n\n", "\n", " ", ""]
    
    def split_text(self, text: str) -> List[str]:
        """Split text into chunks."""
        if not text:
            return []
            
        chunks = []
        current_chunk = ""
        
        # Split by separators in order of preference
        for separator in self.separators:
            if separator in text:
                parts = text.split(separator)
                for part in parts:
                    if self.length_function(current_chunk + separator + part) <= self.chunk_size:
                        current_chunk += separator + part if current_chunk else part
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                        current_chunk = part
                        
                        # Handle oversized parts
                        while self.length_function(current_chunk) > self.chunk_size:
                            chunks.append(current_chunk[:self.chunk_size])
                            current_chunk = current_chunk[self.chunk_size - self.chunk_overlap:]
                
                if current_chunk:
                    chunks.append(current_chunk)
                return chunks
        
        # Fallback: split by character count
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunks.append(text[i:i + self.chunk_size])
        
        return chunks

from config import CHUNK_SIZE, CHUNK_OVERLAP, MAX_SEARCH_RESULTS

# Helper function to run async functions in Streamlit
def run_async(coro):
    """Run async function in Streamlit context."""
    try:
        import asyncio
        loop = asyncio.get_event_loop()
    except RuntimeError:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

# Default user data directory for RAG system (no longer used for ChromaDB)
USER_DATA_DIR = "user_data"

class ConversationRAGSystem:
    """RAG system for conversation-specific document storage and retrieval using Supabase pgvector."""
    
    def __init__(self, user_id: str, conversation_id: str):
        self.user_id = user_id
        self.conversation_id = conversation_id
        
        # Initialize components lazily
        self.supabase = None
        self.embeddings_model = None
        self.text_splitter = None
        self._initialized = False
        
        # Cache key for session state
        self._cache_key = f"rag_system_{user_id}_{conversation_id}"
    
    async def _initialize_components(self):
        """Initialize Supabase client and other components lazily."""
        if self._initialized:
            return True
            
        # Check if already cached in session state
        if self._cache_key in st.session_state:
            cached = st.session_state[self._cache_key]
            self.supabase = cached.get('supabase')
            self.embeddings_model = cached.get('embeddings_model')
            self.text_splitter = cached.get('text_splitter')
            self._initialized = True
            return True
            
        try:
            # Import dependencies here to catch specific errors
            from sentence_transformers import SentenceTransformer
            
            self.supabase = await get_supabase_client()
            
            # Initialize embeddings model (cached globally)
            if 'global_embeddings_model' not in st.session_state:
                with st.spinner("🤖 Loading AI model for document processing..."):
                    st.session_state.global_embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.embeddings_model = st.session_state.global_embeddings_model
            
            # Initialize text splitter (lightweight, can be recreated)
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            # Cache in session state
            st.session_state[self._cache_key] = {
                'supabase': self.supabase,
                'embeddings_model': self.embeddings_model,
                'text_splitter': self.text_splitter
            }
            
            self._initialized = True
            return True
            
        except ImportError as e:
            st.error(f"❌ RAG system dependencies missing: {e}")
            st.info("💡 Some document processing features may not be available.")
            return False
        except Exception as e:
            st.error(f"❌ Error initializing RAG system: {e}")
            self.supabase = None
            return False
    
    async def _get_conversation_db_id(self, user_uuid: str, conversation_id: str) -> Optional[str]:
        """Get the actual database ID for a conversation from its conversation_id field."""
        try:
            # Only try if we're in Streamlit context
            if 'streamlit' in sys.modules:
                supabase = await get_supabase_client()
                
                # Query conversations table to find the actual ID
                result = await supabase.table('conversations').select('id').eq('user_uuid', user_uuid).eq('conversation_id', conversation_id).execute()
                
                if result.data and len(result.data) > 0:
                    return result.data[0]['id']
                else:
                    # Fallback: maybe the conversation_id is already the database ID
                    result = await supabase.table('conversations').select('id').eq('user_uuid', user_uuid).eq('id', conversation_id).execute()
                    if result.data and len(result.data) > 0:
                        return result.data[0]['id']
            
            return None
        except Exception as e:
            if 'streamlit' in sys.modules:
                st.warning(f"Error looking up conversation ID: {e}")
            return None
    
    def _generate_document_hash(self, content: str, filename: str) -> str:
        """Generate unique hash for document content in this conversation."""
        # Include conversation ID in hash to ensure conversation-specific uniqueness
        hash_input = f"{self.conversation_id}_{filename}_{content}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file."""
        if not PYPDF2_AVAILABLE:
            st.error("PDF processing not available. Please install PyPDF2.")
            return ""
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(file_content)
                tmp_file.flush()
                
                text = ""
                with open(tmp_file.name, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                
                os.unlink(tmp_file.name)
                return text.strip()
        except Exception as e:
            st.error(f"Error extracting PDF text: {e}")
            return ""
    
    def _extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file."""
        if not DOCX_AVAILABLE:
            st.error("DOCX processing not available. Please install python-docx.")
            return ""
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                tmp_file.write(file_content)
                tmp_file.flush()
                
                doc = docx.Document(tmp_file.name)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                
                os.unlink(tmp_file.name)
                return text.strip()
        except Exception as e:
            st.error(f"Error extracting DOCX text: {e}")
            return ""
    
    def _extract_text_from_csv(self, file_content: bytes) -> str:
        """Extract text from CSV file."""
        if not PANDAS_AVAILABLE:
            st.error("CSV processing not available. Please install pandas.")
            return ""
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                tmp_file.write(file_content)
                tmp_file.flush()
                
                df = pd.read_csv(tmp_file.name)
                text = df.to_string(index=False)
                
                os.unlink(tmp_file.name)
                return text.strip()
        except Exception as e:
            st.error(f"Error extracting CSV text: {e}")
            return ""
    
    def _extract_text_from_image(self, image) -> str:
        """Extract text from image using OCR."""
        if not PYTESSERACT_AVAILABLE:
            st.error("OCR functionality not available. Please install pytesseract.")
            return ""
        
        try:
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            st.error(f"Error extracting text from image: {e}")
            return ""
    
    async def add_document(self, file_content: bytes, filename: str, file_type: str) -> bool:
        """Add document to the RAG system."""
        if not _check_dependencies():
            return False
            
        if not await self._initialize_components(): # Await the async init
            return False
        
        try:
            # Extract text based on file type
            text = ""
            if file_type == "application/pdf":
                text = self._extract_text_from_pdf(file_content)
            elif file_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
                text = self._extract_text_from_docx(file_content)
            elif file_type == "text/csv":
                text = self._extract_text_from_csv(file_content)
            elif file_type == "text/plain":
                text = file_content.decode('utf-8', errors='ignore')
            else:
                st.error(f"Unsupported file type: {file_type}")
                return False
            
            if not text.strip():
                st.error("No text could be extracted from the document")
                return False
            
            # Generate document hash
            doc_hash = self._generate_document_hash(text, filename)
            
            # Get user UUID from legacy user_id
            document_service, user_service, supabase_available = _get_supabase_services()
            if not supabase_available:
                st.error("Supabase services not available for document processing.")
                return False
            
            user_data = await user_service.get_user_by_id(self.user_id)
            if not user_data:
                st.error("User not found for document processing.")
                return False
            user_uuid = user_data['id']

            # Get the actual conversation database ID from conversation_id
            actual_conversation_id = await self._get_conversation_db_id(user_uuid, self.conversation_id)
            if not actual_conversation_id:
                st.warning(f"Could not find conversation {self.conversation_id} in database for document processing.")
                return False

            # Check if document already exists in this conversation (using Supabase)
            existing_doc = await document_service.check_document_exists(user_uuid, doc_hash, actual_conversation_id)
            if existing_doc:
                return "duplicate"
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            if not chunks:
                st.error("Document could not be split into chunks")
                return False
            
            # Generate embeddings and add to Supabase document_chunks table
            chunks_to_insert = []
            for i, chunk in enumerate(chunks):
                embedding = self.embeddings_model.encode(chunk).tolist() # Convert numpy array to list
                chunks_to_insert.append({
                    "user_uuid": user_uuid,
                    "conversation_id": actual_conversation_id,
                    "document_hash": doc_hash,
                    "chunk_index": i,
                    "content": chunk,
                    "embedding": embedding,
                    "metadata": {
                        "filename": filename,
                        "file_type": file_type,
                        "original_file_size": len(file_content)
                    }
                })
            
            # Insert chunks into Supabase
            insert_result = await self.supabase.table('document_chunks').insert(chunks_to_insert).execute()
            if insert_result.data is None:
                logger.error(f"Failed to insert document chunks into Supabase: {insert_result.error}")
                st.error(f"Failed to store document chunks: {insert_result.error}")
                return False

            # Save high-level document metadata to the 'documents' table
            doc_data = {
                "document_hash": doc_hash,
                "filename": filename,
                "file_type": file_type,
                "file_size": len(file_content),
                "content": text[:10000],  # Store first 10k chars as preview
                "chunk_count": len(chunks),
                "processing_method": "supabase_pgvector_rag",
                "is_processed": True
            }
            
            # Generate embedding for the entire document (or its preview)
            document_embedding = self.embeddings_model.encode(text[:10000]).tolist()

            from services.document_service import save_document_metadata_sync
            save_document_metadata_sync(
                user_uuid=user_uuid,
                conversation_id=actual_conversation_id,
                doc_data=doc_data,
                embedding=document_embedding
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            st.error(f"Error adding document: {e}")
            return False
    
    async def add_image(self, image, filename: str) -> bool:
        """Add image to the RAG system using OCR."""
        if not _check_dependencies():
            return False
        
        if not await self._initialize_components(): # Await the async init
            return False
        
        try:
            # Extract text using OCR
            text = self._extract_text_from_image(image)
            
            if not text.strip():
                st.error("No text could be extracted from the image")
                return False
            
            # Generate document hash
            doc_hash = self._generate_document_hash(text, filename)
            
            # Get user UUID from legacy user_id
            document_service, user_service, supabase_available = _get_supabase_services()
            if not supabase_available:
                st.error("Supabase services not available for image processing.")
                return False
            
            user_data = await user_service.get_user_by_id(self.user_id)
            if not user_data:
                st.error("User not found for image processing.")
                return False
            user_uuid = user_data['id']

            # Get the actual conversation database ID from conversation_id
            actual_conversation_id = await self._get_conversation_db_id(user_uuid, self.conversation_id)
            if not actual_conversation_id:
                st.warning(f"Could not find conversation {self.conversation_id} in database for image processing.")
                return False

            # Check if document already exists in this conversation (using Supabase)
            existing_doc = await document_service.check_document_exists(user_uuid, doc_hash, actual_conversation_id)
            if existing_doc:
                return "duplicate"
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            if not chunks:
                st.error("Image text could not be split into chunks")
                return False
            
            # Generate embeddings and add to Supabase document_chunks table
            chunks_to_insert = []
            for i, chunk in enumerate(chunks):
                embedding = self.embeddings_model.encode(chunk).tolist() # Convert numpy array to list
                chunks_to_insert.append({
                    "user_uuid": user_uuid,
                    "conversation_id": actual_conversation_id,
                    "document_hash": doc_hash,
                    "chunk_index": i,
                    "content": chunk,
                    "embedding": embedding,
                    "metadata": {
                        "filename": filename,
                        "file_type": "image/ocr",
                        "original_file_size": 0 # Image size not available here
                    }
                })
            
            # Insert chunks into Supabase
            insert_result = await self.supabase.table('document_chunks').insert(chunks_to_insert).execute()
            if insert_result.data is None:
                logger.error(f"Failed to insert image chunks into Supabase: {insert_result.error}")
                st.error(f"Failed to store image chunks: {insert_result.error}")
                return False

            # Save high-level document metadata to the 'documents' table
            doc_data = {
                "document_hash": doc_hash,
                "filename": filename,
                "file_type": "image/ocr",
                "file_size": 0,  # Image size not available here
                "content": text[:10000],  # Store first 10k chars as preview
                "chunk_count": len(chunks),
                "processing_method": "supabase_pgvector_rag",
                "is_processed": True
            }
            
            # Generate embedding for the entire document (or its preview)
            document_embedding = self.embeddings_model.encode(text[:10000]).tolist()

            from services.document_service import save_document_metadata_sync
            save_document_metadata_sync(
                user_uuid=user_uuid,
                conversation_id=actual_conversation_id,
                doc_data=doc_data,
                embedding=document_embedding
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding image: {e}")
            st.error(f"Error adding image: {e}")
            return False
    
    async def search_documents(self, query: str, max_results: int = MAX_SEARCH_RESULTS) -> List[Dict]:
        """Search documents for relevant content using Supabase pgvector."""
        if not _check_dependencies():
            return []
            
        if not await self._initialize_components(): # Await the async init
            return []
        
        try:
            query_embedding = self.embeddings_model.encode(query).tolist()
            
            # Perform vector similarity search using Supabase RPC function
            # This assumes you have a Supabase function named 'match_documents'
            # that takes query_embedding, match_threshold, match_count, user_id, and conversation_id
            # and returns relevant document chunks.
            
            # Example of the SQL function in Supabase:
            # CREATE OR REPLACE FUNCTION match_documents(
            #   query_embedding vector(1536), -- Adjust dimension based on your model
            #   match_threshold float,
            #   match_count int,
            #   user_id uuid,
            #   conversation_id uuid
            # )
            # RETURNS TABLE (
            #   id bigint,
            #   document_hash text,
            #   content text,
            #   similarity float
            # ) 
            # LANGUAGE plpgsql
            # AS $$
            # BEGIN
            #   RETURN QUERY
            #   SELECT
            #     document_chunks.id,
            #     document_chunks.document_hash,
            #     document_chunks.content,
            #     (document_chunks.embedding <#> query_embedding) * -1 AS similarity
            #   FROM document_chunks
            #   WHERE document_chunks.user_uuid = user_id
            #     AND document_chunks.conversation_id = conversation_id
            #     AND (document_chunks.embedding <#> query_embedding) * -1 > match_threshold
            #   ORDER BY similarity DESC
            #   LIMIT match_count;
            # END;
            # $$

            # Call the Supabase RPC function
            rpc_result = await self.supabase.rpc('match_documents', {
                'query_embedding': query_embedding,
                'match_threshold': 0.7, # Adjust threshold as needed
                'match_count': max_results,
                'user_id': self.user_id,
                'conversation_id': self.conversation_id
            }).execute()

            if rpc_result.data:
                # Fetch full document metadata for the matched chunks
                # This is a simplified approach. In a real app, you might join tables in the RPC function.
                matched_document_hashes = list(set([item['document_hash'] for item in rpc_result.data]))
                
                document_service, _, supabase_available = _get_supabase_services()
                if not supabase_available:
                    st.error("Supabase services not available for document search.")
                    return []

                # Get full document details for the matched hashes
                # This assumes document_service has a method to get documents by hash list
                # For now, we'll iterate and get them one by one (less efficient but works)
                full_documents = []
                for doc_hash in matched_document_hashes:
                    doc = await document_service.get_document_by_hash(self.user_id, doc_hash)
                    if doc:
                        # Add the content from the matched chunk to the document for context
                        for chunk_data in rpc_result.data:
                            if chunk_data['document_hash'] == doc_hash:
                                doc['content'] = chunk_data['content'] # Override with chunk content
                                doc['similarity'] = chunk_data['similarity'] # Add similarity score
                                break
                        full_documents.append(doc)
                
                # Sort by similarity (highest first)
                full_documents.sort(key=lambda x: x.get('similarity', 0), reverse=True)

                return full_documents
            else:
                logger.info("No matching documents found for query.")
                return []
            
        except Exception as e:
            logger.error(f"Error searching documents with Supabase pgvector: {e}")
            st.error(f"Error searching documents: {e}")
            return []
    
    async def get_documents_list(self) -> List[Dict]:
        """Get list of all documents in this conversation from Supabase 'documents' table."""
        if not await self._initialize_components():
            return []
        
        document_service, user_service, supabase_available = _get_supabase_services()
        if not supabase_available:
            st.error("Supabase services not available to get document list.")
            return []
        
        user_data = await user_service.get_user_by_id(self.user_id)
        if not user_data:
            st.error("User not found to get document list.")
            return []
        user_uuid = user_data['id']

        actual_conversation_id = await self._get_conversation_db_id(user_uuid, self.conversation_id)
        if not actual_conversation_id:
            return []

        documents = await document_service.get_conversation_documents(user_uuid, actual_conversation_id)
        return documents
    
    async def delete_document(self, document_hash: str) -> bool:
        """Delete a document from the RAG system (Supabase 'documents' and 'document_chunks')."""
        if not await self._initialize_components():
            return False
        
        document_service, user_service, supabase_available = _get_supabase_services()
        if not supabase_available:
            st.error("Supabase services not available to delete document.")
            return False
        
        user_data = await user_service.get_user_by_id(self.user_id)
        if not user_data:
            st.error("User not found to delete document.")
            return False
        user_uuid = user_data['id']

        actual_conversation_id = await self._get_conversation_db_id(user_uuid, self.conversation_id)
        if not actual_conversation_id:
            st.warning(f"Could not find conversation {self.conversation_id} in database to delete document.")
            return False

        try:
            # Delete from document_chunks table
            delete_chunks_result = await self.supabase.table('document_chunks').delete().filter(
                'user_uuid', 'eq', user_uuid
            ).filter(
                'conversation_id', 'eq', actual_conversation_id
            ).filter(
                'document_hash', 'eq', document_hash
            ).execute()

            if delete_chunks_result.data is None:
                logger.error(f"Failed to delete document chunks for hash {document_hash}: {delete_chunks_result.error}")
                st.error(f"Failed to delete document chunks: {delete_chunks_result.error}")
                return False

            # Delete from documents table (high-level metadata)
            success = await document_service.delete_document(user_uuid, document_hash)
            
            if success:
                logger.info(f"Document {document_hash} and its chunks deleted from Supabase.")
                return True
            else:
                logger.error(f"Failed to delete high-level document metadata for hash {document_hash}.")
                return False
            
        except Exception as e:
            logger.error(f"Error deleting document {document_hash}: {e}")
            st.error(f"Error deleting document: {e}")
            return False
    
    def get_context_for_query(self, query: str) -> str:
        """Get relevant context for a query."""
        # This method needs to be async now because search_documents is async
        # For now, we'll make it a synchronous call to the async search_documents
        # This is not ideal but works within Streamlit's synchronous flow for now.
        search_results = run_async(self.search_documents(query))
        
        if not search_results:
            return ""
        
        context_parts = []
        for result in search_results:
            context_parts.append(f"From {result['filename']}:\n{result['content']}")
        
        return "\n\n".join(context_parts)

async def initialize_rag_system(conversation_id: str) -> Optional[ConversationRAGSystem]:
    """Initialize RAG system for a conversation."""
    if not st.session_state.authenticated or not st.session_state.user_id:
        return None
    
    if not _check_dependencies():
        return None
    
    try:
        rag_system = ConversationRAGSystem(st.session_state.user_id, conversation_id)
        if await rag_system._initialize_components(): # Await the async init
            return rag_system
        return None
    except Exception as e:
        st.error(f"Error initializing RAG system: {e}")
        return None