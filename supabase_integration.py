"""
Supabase Integration for PharmGPT
Optional high-performance database backend
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import streamlit as st

# Supabase integration (optional)
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    st.warning("Supabase not available. Install with: pip install supabase")

class SupabaseManager:
    """Supabase database manager for PharmGPT."""
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Supabase client."""
        if not SUPABASE_AVAILABLE:
            return
        
        try:
            # Get Supabase credentials from Streamlit secrets
            supabase_url = st.secrets.get("SUPABASE_URL")
            supabase_key = st.secrets.get("SUPABASE_ANON_KEY")
            
            if supabase_url and supabase_key:
                self.client = create_client(supabase_url, supabase_key)
            else:
                st.info("Supabase credentials not configured. Using file-based storage.")
                
        except Exception as e:
            st.warning(f"Supabase initialization failed: {e}. Using file-based storage.")
    
    def is_available(self) -> bool:
        """Check if Supabase is available and configured."""
        return self.client is not None
    
    # User Management
    async def create_user(self, username: str, password: str) -> Tuple[bool, str]:
        """Create user in Supabase."""
        if not self.is_available():
            return False, "Supabase not available"
        
        try:
            # Check if user exists
            result = self.client.table('users').select('username').eq('username', username).execute()
            if result.data:
                return False, "Username already exists"
            
            # Hash password
            salt = secrets.token_hex(32)
            password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            user_id = hashlib.md5(username.encode()).hexdigest()
            
            # Insert user
            self.client.table('users').insert({
                'username': username,
                'password_hash': password_hash,
                'salt': salt,
                'user_id': user_id,
                'created_at': datetime.now().isoformat()
            }).execute()
            
            return True, "Account created successfully"
            
        except Exception as e:
            return False, f"Error creating account: {str(e)}"
    
    async def authenticate_user(self, username: str, password: str) -> Tuple[bool, str]:
        """Authenticate user with Supabase."""
        if not self.is_available():
            return False, "Supabase not available"
        
        try:
            result = self.client.table('users').select('password_hash', 'salt').eq('username', username).execute()
            
            if not result.data:
                return False, "Username not found"
            
            user_data = result.data[0]
            password_hash = hashlib.sha256((password + user_data['salt']).encode()).hexdigest()
            
            if password_hash == user_data['password_hash']:
                return True, "Authentication successful"
            else:
                return False, "Invalid password"
                
        except Exception as e:
            return False, f"Authentication error: {str(e)}"
    
    # Conversation Management
    async def load_user_conversations(self, user_id: str) -> Dict:
        """Load conversations from Supabase with caching."""
        if not self.is_available():
            return {}
        
        # Check cache first
        cache_key = f"supabase_conversations_{user_id}"
        if cache_key in st.session_state:
            cached_data = st.session_state[cache_key]
            # Check if cache is still valid (5 minutes)
            if datetime.now() - cached_data['timestamp'] < timedelta(minutes=5):
                return cached_data['conversations']
        
        try:
            result = self.client.table('conversations').select('*').eq('user_id', user_id).execute()
            
            conversations = {}
            for row in result.data:
                conversations[row['conversation_id']] = {
                    'title': row['title'],
                    'messages': json.loads(row['messages']),
                    'created_at': row['created_at'],
                    'model': row.get('model', 'meta-llama/llama-4-maverick-17b-128e-instruct')
                }
            
            # Cache the result
            st.session_state[cache_key] = {
                'conversations': conversations,
                'timestamp': datetime.now()
            }
            
            return conversations
            
        except Exception as e:
            st.error(f"Error loading conversations: {e}")
            return {}
    
    async def save_user_conversations(self, user_id: str, conversations: Dict):
        """Save conversations to Supabase with batching."""
        if not self.is_available():
            return
        
        try:
            # Prepare batch operations
            operations = []
            
            for conv_id, conv_data in conversations.items():
                operations.append({
                    'conversation_id': conv_id,
                    'user_id': user_id,
                    'title': conv_data['title'],
                    'messages': json.dumps(conv_data['messages']),
                    'created_at': conv_data['created_at'],
                    'model': conv_data.get('model', 'meta-llama/llama-4-maverick-17b-128e-instruct'),
                    'updated_at': datetime.now().isoformat()
                })
            
            # Batch upsert
            if operations:
                self.client.table('conversations').upsert(operations).execute()
            
            # Update cache
            cache_key = f"supabase_conversations_{user_id}"
            st.session_state[cache_key] = {
                'conversations': conversations,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            st.error(f"Error saving conversations: {e}")
    
    # Document Management for RAG
    async def save_document_metadata(self, user_id: str, conversation_id: str, doc_hash: str, metadata: Dict):
        """Save document metadata to Supabase."""
        if not self.is_available():
            return
        
        try:
            self.client.table('documents').upsert({
                'document_hash': doc_hash,
                'user_id': user_id,
                'conversation_id': conversation_id,
                'filename': metadata['filename'],
                'file_type': metadata['file_type'],
                'chunk_count': metadata['chunk_count'],
                'added_at': metadata['added_at'],
                'metadata': json.dumps(metadata)
            }).execute()
            
        except Exception as e:
            st.error(f"Error saving document metadata: {e}")
    
    async def get_conversation_documents(self, user_id: str, conversation_id: str) -> List[Dict]:
        """Get documents for a conversation."""
        if not self.is_available():
            return []
        
        try:
            result = self.client.table('documents').select('*').eq('user_id', user_id).eq('conversation_id', conversation_id).execute()
            
            documents = []
            for row in result.data:
                documents.append({
                    'filename': row['filename'],
                    'file_type': row['file_type'],
                    'chunk_count': row['chunk_count'],
                    'added_at': row['added_at'],
                    'document_hash': row['document_hash']
                })
            
            return documents
            
        except Exception as e:
            st.error(f"Error loading documents: {e}")
            return []

# Global Supabase manager instance
supabase_manager = SupabaseManager()

# Hybrid approach: Use Supabase if available, fallback to files
async def hybrid_load_conversations(user_id: str) -> Dict:
    """Load conversations using Supabase if available, otherwise files."""
    if supabase_manager.is_available():
        return await supabase_manager.load_user_conversations(user_id)
    else:
        # Fallback to file-based system
        from auth import load_user_conversations
        return load_user_conversations(user_id)

async def hybrid_save_conversations(user_id: str, conversations: Dict):
    """Save conversations using Supabase if available, otherwise files."""
    if supabase_manager.is_available():
        await supabase_manager.save_user_conversations(user_id, conversations)
    else:
        # Fallback to file-based system
        from auth import save_user_conversations
        save_user_conversations(user_id, conversations)

# Performance comparison utilities
class PerformanceComparison:
    """Compare performance between file-based and Supabase storage."""
    
    @staticmethod
    def benchmark_load_conversations(user_id: str, iterations: int = 10):
        """Benchmark conversation loading performance."""
        import time
        
        # File-based timing
        file_times = []
        for _ in range(iterations):
            start = time.time()
            from auth import load_user_conversations
            load_user_conversations(user_id)
            file_times.append(time.time() - start)
        
        # Supabase timing (if available)
        supabase_times = []
        if supabase_manager.is_available():
            for _ in range(iterations):
                start = time.time()
                import asyncio
                asyncio.run(supabase_manager.load_user_conversations(user_id))
                supabase_times.append(time.time() - start)
        
        return {
            'file_avg': sum(file_times) / len(file_times) if file_times else 0,
            'supabase_avg': sum(supabase_times) / len(supabase_times) if supabase_times else 0,
            'file_times': file_times,
            'supabase_times': supabase_times
        }

# SQL Schema for Supabase setup
SUPABASE_SCHEMA = """
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sessions table
CREATE TABLE sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL
);

-- Conversations table
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    title TEXT NOT NULL,
    messages JSONB NOT NULL,
    model VARCHAR(255) DEFAULT 'meta-llama/llama-4-maverick-17b-128e-instruct',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(conversation_id, user_id)
);

-- Documents table for RAG
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    document_hash VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    conversation_id VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(255) NOT NULL,
    chunk_count INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    UNIQUE(document_hash, conversation_id)
);

-- Uploads tracking
CREATE TABLE uploads (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at);
CREATE INDEX idx_documents_user_conversation ON documents(user_id, conversation_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX idx_uploads_user_date ON uploads(user_id, uploaded_at);

-- Row Level Security (RLS)
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE uploads ENABLE ROW LEVEL SECURITY;

-- RLS Policies (users can only access their own data)
CREATE POLICY "Users can only access their own conversations" ON conversations
    FOR ALL USING (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can only access their own documents" ON documents
    FOR ALL USING (user_id = current_setting('app.current_user_id'));

CREATE POLICY "Users can only access their own uploads" ON uploads
    FOR ALL USING (user_id = current_setting('app.current_user_id'));
"""