"""
ChromaDB-based RAG System for PharmBot
Local vector database - unlimited, free, and fast
"""

import streamlit as st
import chromadb
from chromadb.config import Settings
import uuid
from pathlib import Path
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import hashlib
import shutil
import time
import os

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.document_loaders import (
    PyPDFLoader, TextLoader, CSVLoader, 
    UnstructuredWordDocumentLoader
)
from langchain_huggingface import HuggingFaceEmbeddings

# Image processing
from PIL import Image
import pytesseract
import io

class ChromaRAGSystem:
    """Conversation-specific RAG system using ChromaDB - each chat has its own knowledge base."""
    
    def __init__(self, user_id: str, conversation_id: str = None):
        self.user_id = user_id
        self.conversation_id = conversation_id or "global"
        
        # Create conversation-specific directory structure
        self.user_rag_dir = Path("user_data") / f"rag_{user_id}"
        self.user_rag_dir.mkdir(parents=True, exist_ok=True)
        
        self.conversation_rag_dir = self.user_rag_dir / f"conversation_{self.conversation_id}"
        self.conversation_rag_dir.mkdir(parents=True, exist_ok=True)
        
        # ChromaDB directory for this conversation (completely isolated per conversation)
        self.chroma_dir = self.conversation_rag_dir / "chroma_db"
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        
        # Metadata file for tracking documents in this conversation
        self.metadata_file = self.conversation_rag_dir / "documents_metadata.json"
        
        # Collection name for this conversation - use simple name since each conversation has its own DB
        self.collection_name = "documents"  # Simple name since each conversation has its own ChromaDB database
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Load metadata
        self.documents_metadata = self.load_documents_metadata()
        
        # Initialize ChromaDB
        self.client = None
        self.collection = None
        self._initialize_chromadb()
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB client and collection."""
        try:
            # Initialize ChromaDB client with persistent storage
            self.client = chromadb.PersistentClient(
                path=str(self.chroma_dir),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Create or get collection
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name="sentence-transformers/all-MiniLM-L6-v2"
                    )
                )
                print(f"✅ Connected to existing ChromaDB collection: {self.collection_name}")
            except:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
                        model_name="sentence-transformers/all-MiniLM-L6-v2"
                    )
                )
                print(f"✅ Created new ChromaDB collection: {self.collection_name}")
            
            print("✅ ChromaDB client initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing ChromaDB: {e}")
            self.client = None
            self.collection = None
    
    def load_documents_metadata(self) -> Dict:
        """Load documents metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def save_documents_metadata(self):
        """Save documents metadata to file."""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.documents_metadata, f, indent=2, default=str)
    
    def get_file_hash(self, file_content: bytes) -> str:
        """Generate hash for file content."""
        return hashlib.md5(file_content).hexdigest()
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from image using OCR."""
        try:
            # Convert image to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using pytesseract
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return ""
    
    def add_document(self, file_content: bytes, filename: str, file_type: str) -> bool:
        """Add document to the ChromaDB RAG system."""
        try:
            # Check if document already exists
            file_hash = self.get_file_hash(file_content)
            if file_hash in self.documents_metadata:
                try:
                    st.info(f"Document '{filename}' already exists in the knowledge base.")
                except:
                    print(f"Document '{filename}' already exists")
                return True
            
            # Process document based on type
            documents = []
            if file_type == 'application/pdf':
                documents = self.process_pdf(file_content, filename)
            elif file_type == 'text/plain':
                documents = self.process_text(file_content, filename)
            elif file_type == 'text/csv':
                documents = self.process_csv(file_content, filename)
            elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
                documents = self.process_word(file_content, filename)
            else:
                # Treat as text
                documents = self.process_text(file_content, filename)
            
            if not documents:
                return False
            
            # Split into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            # Add chunks to ChromaDB
            added_at = datetime.now().isoformat()
            
            if self.collection:
                # Prepare data for ChromaDB
                ids = []
                documents_text = []
                metadatas = []
                
                for i, chunk in enumerate(chunks):
                    # Create unique ID
                    chunk_id = f"{file_hash}_{i}"
                    ids.append(chunk_id)
                    documents_text.append(chunk.page_content)
                    
                    # Create metadata
                    metadata = {
                        "filename": filename,
                        "file_hash": file_hash,
                        "chunk_index": i,
                        "source": filename,
                        "doc_type": "document",
                        "added_at": added_at
                    }
                    metadatas.append(metadata)
                
                # Add to ChromaDB collection
                self.collection.add(
                    ids=ids,
                    documents=documents_text,
                    metadatas=metadatas
                )
                
                print(f"✅ Added {len(chunks)} chunks to ChromaDB collection")
            
            # Update metadata
            self.documents_metadata[file_hash] = {
                "filename": filename,
                "file_type": "document",
                "chunks_count": len(chunks),
                "added_at": added_at,
                "size_bytes": len(file_content)
            }
            
            self.save_documents_metadata()
            
            return True
            
        except Exception as e:
            try:
                st.error(f"Error adding document: {e}")
            except:
                print(f"Error adding document: {e}")
            return False
    
    def add_image(self, image: Image.Image, filename: str) -> bool:
        """Add image to the ChromaDB RAG system by extracting text."""
        try:
            # Extract text from image
            text = self.extract_text_from_image(image)
            
            # If no text found, create a descriptive entry
            if not text or len(text.strip()) < 10:
                width, height = image.size
                mode = image.mode
                
                content_description = f"Image file: {filename}"
                if any(term in filename.lower() for term in ['gene', 'dna', 'rna']):
                    content_description += " - Appears to be genetics/genomics related"
                elif any(term in filename.lower() for term in ['drug', 'pharm', 'medicine']):
                    content_description += " - Appears to be pharmaceutical/medical related"
                elif any(term in filename.lower() for term in ['chart', 'graph', 'plot']):
                    content_description += " - Appears to be a chart or graph"
                elif any(term in filename.lower() for term in ['diagram', 'figure', 'fig']):
                    content_description += " - Appears to be a diagram or figure"
                
                content_description += f" (Image dimensions: {width}x{height}, Mode: {mode})"
                
                if text and len(text.strip()) > 0:
                    content_description += f"\n\nExtracted text (limited): {text.strip()}"
                
                text = content_description
            
            # Convert image to bytes for hashing
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_bytes = img_byte_arr.getvalue()
            
            # Check if image already exists
            file_hash = self.get_file_hash(img_bytes)
            if file_hash in self.documents_metadata:
                try:
                    st.info(f"Image '{filename}' already exists in the knowledge base.")
                except:
                    print(f"Image '{filename}' already exists")
                return True
            
            # Create document from extracted text
            doc = Document(
                page_content=text,
                metadata={"source": filename, "type": "image"}
            )
            
            # Split into chunks
            chunks = self.text_splitter.split_documents([doc])
            
            # Add chunks to ChromaDB
            added_at = datetime.now().isoformat()
            
            if self.collection:
                # Prepare data for ChromaDB
                ids = []
                documents_text = []
                metadatas = []
                
                for i, chunk in enumerate(chunks):
                    # Create unique ID
                    chunk_id = f"{file_hash}_{i}"
                    ids.append(chunk_id)
                    documents_text.append(chunk.page_content)
                    
                    # Create metadata
                    metadata = {
                        "filename": filename,
                        "file_hash": file_hash,
                        "chunk_index": i,
                        "source": filename,
                        "doc_type": "image",
                        "added_at": added_at
                    }
                    metadatas.append(metadata)
                
                # Add to ChromaDB collection
                self.collection.add(
                    ids=ids,
                    documents=documents_text,
                    metadatas=metadatas
                )
                
                print(f"✅ Added {len(chunks)} image chunks to ChromaDB collection")
            
            # Update metadata
            self.documents_metadata[file_hash] = {
                "filename": filename,
                "file_type": "image",
                "chunks_count": len(chunks),
                "added_at": added_at,
                "size_bytes": len(img_bytes),
                "extracted_text_length": len(text)
            }
            
            self.save_documents_metadata()
            
            return True
            
        except Exception as e:
            try:
                st.error(f"Error adding image: {e}")
            except:
                print(f"Error adding image: {e}")
            return False
    
    def search_documents(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for relevant documents using ChromaDB."""
        try:
            if not self.collection:
                return []
            
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                documents = results['documents'][0]  # First query results
                metadatas = results['metadatas'][0] if results['metadatas'] else []
                distances = results['distances'][0] if results['distances'] else []
                
                for i, doc in enumerate(documents):
                    metadata = metadatas[i] if i < len(metadatas) else {}
                    distance = distances[i] if i < len(distances) else 1.0
                    
                    # Convert distance to similarity score (ChromaDB uses distance, lower is better)
                    similarity_score = 1.0 - distance if distance <= 1.0 else 0.0
                    
                    formatted_results.append({
                        "content": doc,
                        "metadata": {
                            "filename": metadata.get("filename", ""),
                            "file_hash": metadata.get("file_hash", ""),
                            "chunk_index": metadata.get("chunk_index", 0),
                            "source": metadata.get("source", ""),
                            "type": metadata.get("doc_type", "")
                        },
                        "relevance_score": float(similarity_score)
                    })
            
            return formatted_results
            
        except Exception as e:
            try:
                st.error(f"Error searching documents: {e}")
            except:
                print(f"Error searching documents: {e}")
            return []
    
    def get_context_for_query(self, query: str, max_context_length: int = 3000) -> str:
        """Get relevant context for a query."""
        results = self.search_documents(query, n_results=5)
        
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for result in results:
            content = result["content"]
            filename = result["metadata"].get("filename", "Unknown")
            
            # Add source information
            source_info = f"\n[Source: {filename}]\n"
            full_content = source_info + content
            
            if current_length + len(full_content) <= max_context_length:
                context_parts.append(full_content)
                current_length += len(full_content)
            else:
                # Add partial content if it fits
                remaining_space = max_context_length - current_length
                if remaining_space > 100:
                    partial_content = source_info + content[:remaining_space-len(source_info)-3] + "..."
                    context_parts.append(partial_content)
                break
        
        return "\n".join(context_parts)
    
    def get_documents_list(self) -> List[Dict]:
        """Get list of all documents in the knowledge base."""
        return [
            {
                "file_hash": file_hash,
                "filename": info["filename"],
                "file_type": info["file_type"],
                "chunks_count": info["chunks_count"],
                "added_at": info["added_at"],
                "size_bytes": info.get("size_bytes", 0),
                "extracted_text_length": info.get("extracted_text_length", 0)
            }
            for file_hash, info in self.documents_metadata.items()
        ]
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the ChromaDB RAG system."""
        try:
            doc_count = len(self.documents_metadata)
            
            # Check ChromaDB connection
            chromadb_ready = self.collection is not None
            
            # Get vector count
            vector_count = 0
            if self.collection:
                try:
                    vector_count = self.collection.count()
                except:
                    pass
            
            # Test search functionality
            search_works = True
            try:
                self.search_documents("test", n_results=1)
            except:
                search_works = False
            
            return {
                "status": "healthy",
                "documents_count": doc_count,
                "vector_count": vector_count,
                "search_functional": search_works,
                "chromadb_ready": chromadb_ready,
                "mode": "chromadb"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "documents_count": 0,
                "vector_count": 0,
                "search_functional": False,
                "chromadb_ready": False,
                "mode": "error"
            }
    
    def clear_all_documents(self) -> bool:
        """Clear all documents from the ChromaDB RAG system."""
        try:
            if self.collection:
                # Delete all documents from collection
                try:
                    # Get all IDs and delete them
                    all_data = self.collection.get()
                    if all_data['ids']:
                        self.collection.delete(ids=all_data['ids'])
                        print(f"✅ Deleted {len(all_data['ids'])} documents from ChromaDB")
                except Exception as e:
                    print(f"Error clearing ChromaDB collection: {e}")
            
            # Clear metadata
            self.documents_metadata = {}
            self.save_documents_metadata()
            
            return True
            
        except Exception as e:
            try:
                st.error(f"Error clearing documents: {e}")
            except:
                print(f"Error clearing documents: {e}")
            return False
    
    # Document processing methods (same as before)
    def process_pdf(self, file_content: bytes, filename: str) -> List[Document]:
        """Process PDF file and extract text."""
        documents = []
        try:
            temp_file = self.conversation_rag_dir / f"temp_{filename}"
            with open(temp_file, 'wb') as f:
                f.write(file_content)
            
            loader = PyPDFLoader(str(temp_file))
            documents = loader.load()
            
            temp_file.unlink()
            
        except Exception as e:
            print(f"Error processing PDF: {e}")
        
        return documents
    
    def process_text(self, file_content: bytes, filename: str) -> List[Document]:
        """Process text file."""
        try:
            text = file_content.decode('utf-8')
            return [Document(page_content=text, metadata={"source": filename})]
        except Exception as e:
            print(f"Error processing text: {e}")
            return []
    
    def process_csv(self, file_content: bytes, filename: str) -> List[Document]:
        """Process CSV file."""
        try:
            temp_file = self.conversation_rag_dir / f"temp_{filename}"
            with open(temp_file, 'wb') as f:
                f.write(file_content)
            
            loader = CSVLoader(str(temp_file))
            documents = loader.load()
            
            temp_file.unlink()
            
            return documents
        except Exception as e:
            print(f"Error processing CSV: {e}")
            return []
    
    def process_word(self, file_content: bytes, filename: str) -> List[Document]:
        """Process Word document."""
        try:
            temp_file = self.conversation_rag_dir / f"temp_{filename}"
            with open(temp_file, 'wb') as f:
                f.write(file_content)
            
            loader = UnstructuredWordDocumentLoader(str(temp_file))
            documents = loader.load()
            
            temp_file.unlink()
            
            return documents
        except Exception as e:
            print(f"Error processing Word document: {e}")
            return []