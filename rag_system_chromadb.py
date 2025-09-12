"""
RAG System using ChromaDB for conversation-specific document storage
"""

import os
import json
import hashlib
import tempfile
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import streamlit as st

# SQLite upgrade for Streamlit Cloud compatibility
import sys
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

# Document processing imports
try:
    import chromadb
    from chromadb.config import Settings
    import PyPDF2
    import docx
    import pandas as pd
    from PIL import Image
    import pytesseract
    from sentence_transformers import SentenceTransformer
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    st.error(f"RAG dependencies not available: {e}")

from config import USER_DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP, MAX_SEARCH_RESULTS

class ConversationRAGSystem:
    """RAG system for conversation-specific document storage and retrieval."""
    
    def __init__(self, user_id: str, conversation_id: str):
        self.user_id = user_id
        self.conversation_id = conversation_id
        self.rag_dir = os.path.join(USER_DATA_DIR, f"rag_{user_id}", f"conversation_{conversation_id}")
        self.chroma_dir = os.path.join(self.rag_dir, "chroma_db")
        self.metadata_file = os.path.join(self.rag_dir, "documents_metadata.json")
        
        # Ensure directories exist
        os.makedirs(self.rag_dir, exist_ok=True)
        os.makedirs(self.chroma_dir, exist_ok=True)
        
        # Initialize components
        self.client = None
        self.collection = None
        self.embeddings_model = None
        self.text_splitter = None
        
        if DEPENDENCIES_AVAILABLE:
            self._initialize_components()
    
    def _initialize_components(self):
        """Initialize ChromaDB and other components."""
        try:
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.chroma_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            collection_name = f"conv_{self.conversation_id}"
            try:
                self.collection = self.client.get_collection(collection_name)
            except:
                self.collection = self.client.create_collection(collection_name)
            
            # Initialize embeddings model
            self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
        except Exception as e:
            st.error(f"Error initializing RAG system: {e}")
            self.client = None
            self.collection = None
    
    def _load_metadata(self) -> Dict:
        """Load document metadata."""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            st.error(f"Error loading metadata: {e}")
        return {}
    
    def _save_metadata(self, metadata: Dict):
        """Save document metadata."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            st.error(f"Error saving metadata: {e}")
    
    def _generate_document_hash(self, content: str, filename: str) -> str:
        """Generate unique hash for document content in this conversation."""
        # Include conversation ID in hash to ensure conversation-specific uniqueness
        hash_input = f"{self.conversation_id}_{filename}_{content}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file."""
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
    
    def _extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from image using OCR."""
        try:
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            st.error(f"Error extracting text from image: {e}")
            return ""
    
    def add_document(self, file_content: bytes, filename: str, file_type: str) -> bool:
        """Add document to the RAG system."""
        if not DEPENDENCIES_AVAILABLE or not self.collection:
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
            
            # Check if document already exists in this conversation
            metadata = self._load_metadata()
            if doc_hash in metadata:
                return "duplicate"
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            if not chunks:
                st.error("Document could not be split into chunks")
                return False
            
            # Generate embeddings and add to ChromaDB
            chunk_ids = []
            chunk_texts = []
            chunk_metadatas = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_hash}_chunk_{i}"
                chunk_ids.append(chunk_id)
                chunk_texts.append(chunk)
                chunk_metadatas.append({
                    "filename": filename,
                    "chunk_index": i,
                    "document_hash": doc_hash,
                    "file_type": file_type,
                    "conversation_id": self.conversation_id
                })
            
            # Add to ChromaDB
            self.collection.add(
                ids=chunk_ids,
                documents=chunk_texts,
                metadatas=chunk_metadatas
            )
            
            # Update metadata
            metadata[doc_hash] = {
                "filename": filename,
                "file_type": file_type,
                "chunk_count": len(chunks),
                "added_at": datetime.now().isoformat(),
                "conversation_id": self.conversation_id
            }
            self._save_metadata(metadata)
            
            return True
            
        except Exception as e:
            st.error(f"Error adding document: {e}")
            return False
    
    def add_image(self, image: Image.Image, filename: str) -> bool:
        """Add image to the RAG system using OCR."""
        if not DEPENDENCIES_AVAILABLE or not self.collection:
            return False
        
        try:
            # Extract text using OCR
            text = self._extract_text_from_image(image)
            
            if not text.strip():
                st.error("No text could be extracted from the image")
                return False
            
            # Generate document hash
            doc_hash = self._generate_document_hash(text, filename)
            
            # Check if document already exists in this conversation
            metadata = self._load_metadata()
            if doc_hash in metadata:
                return "duplicate"
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(text)
            
            if not chunks:
                st.error("Image text could not be split into chunks")
                return False
            
            # Generate embeddings and add to ChromaDB
            chunk_ids = []
            chunk_texts = []
            chunk_metadatas = []
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_hash}_chunk_{i}"
                chunk_ids.append(chunk_id)
                chunk_texts.append(chunk)
                chunk_metadatas.append({
                    "filename": filename,
                    "chunk_index": i,
                    "document_hash": doc_hash,
                    "file_type": "image/ocr",
                    "conversation_id": self.conversation_id
                })
            
            # Add to ChromaDB
            self.collection.add(
                ids=chunk_ids,
                documents=chunk_texts,
                metadatas=chunk_metadatas
            )
            
            # Update metadata
            metadata[doc_hash] = {
                "filename": filename,
                "file_type": "image/ocr",
                "chunk_count": len(chunks),
                "added_at": datetime.now().isoformat(),
                "conversation_id": self.conversation_id
            }
            self._save_metadata(metadata)
            
            return True
            
        except Exception as e:
            st.error(f"Error adding image: {e}")
            return False
    
    def search_documents(self, query: str, max_results: int = MAX_SEARCH_RESULTS) -> List[Dict]:
        """Search documents for relevant content."""
        if not DEPENDENCIES_AVAILABLE or not self.collection:
            return []
        
        try:
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=max_results
            )
            
            search_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    search_results.append({
                        "content": doc,
                        "filename": metadata.get("filename", "Unknown"),
                        "chunk_index": metadata.get("chunk_index", 0),
                        "relevance_score": 1 - distance,  # Convert distance to similarity
                        "file_type": metadata.get("file_type", "Unknown")
                    })
            
            return search_results
            
        except Exception as e:
            st.error(f"Error searching documents: {e}")
            return []
    
    def get_documents_list(self) -> List[Dict]:
        """Get list of all documents in this conversation."""
        metadata = self._load_metadata()
        documents = []
        
        for doc_hash, doc_info in metadata.items():
            documents.append({
                "filename": doc_info["filename"],
                "file_type": doc_info["file_type"],
                "chunk_count": doc_info["chunk_count"],
                "added_at": doc_info["added_at"],
                "document_hash": doc_hash
            })
        
        return documents
    
    def delete_document(self, document_hash: str) -> bool:
        """Delete a document from the RAG system."""
        if not DEPENDENCIES_AVAILABLE or not self.collection:
            return False
        
        try:
            # Get document metadata
            metadata = self._load_metadata()
            if document_hash not in metadata:
                return False
            
            # Delete chunks from ChromaDB
            chunk_count = metadata[document_hash]["chunk_count"]
            chunk_ids = [f"{document_hash}_chunk_{i}" for i in range(chunk_count)]
            
            self.collection.delete(ids=chunk_ids)
            
            # Remove from metadata
            del metadata[document_hash]
            self._save_metadata(metadata)
            
            return True
            
        except Exception as e:
            st.error(f"Error deleting document: {e}")
            return False
    
    def get_context_for_query(self, query: str) -> str:
        """Get relevant context for a query."""
        search_results = self.search_documents(query)
        
        if not search_results:
            return ""
        
        context_parts = []
        for result in search_results:
            context_parts.append(f"From {result['filename']}:\n{result['content']}")
        
        return "\n\n".join(context_parts)

def initialize_rag_system(conversation_id: str) -> Optional[ConversationRAGSystem]:
    """Initialize RAG system for a conversation."""
    if not st.session_state.authenticated or not st.session_state.user_id:
        return None
    
    if not DEPENDENCIES_AVAILABLE:
        return None
    
    try:
        rag_system = ConversationRAGSystem(st.session_state.user_id, conversation_id)
        return rag_system
    except Exception as e:
        st.error(f"Error initializing RAG system: {e}")
        return None