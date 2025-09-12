# Design Document

## Overview

This design outlines the complete migration of PharmGPT from file-based storage to Supabase as the exclusive database backend. The migration will be implemented as a seamless transition that preserves all existing functionality while providing improved performance, scalability, and reliability.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   Supabase       │    │   ChromaDB      │
│   Frontend      │◄──►│   Database       │    │   (RAG Store)   │
│                 │    │                  │    │                 │
│ - Chat UI       │    │ - Users          │    │ - Documents     │
│ - Auth Pages    │    │ - Conversations  │    │ - Embeddings    │
│ - File Upload   │    │ - Documents      │    │ - Search Index  │
│ - Settings      │    │ - Sessions       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Database Schema Design

#### Core Tables

1. **users** - User account management
2. **sessions** - Authentication sessions
3. **conversations** - Chat conversations with messages
4. **documents** - Document metadata for RAG system
5. **uploads** - File upload tracking
6. **user_preferences** - User settings and preferences

#### Detailed Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE
);

-- Sessions table
CREATE TABLE sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    username VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    messages JSONB NOT NULL DEFAULT '[]',
    model VARCHAR(255) DEFAULT 'meta-llama/llama-4-maverick-17b-128e-instruct',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    message_count INTEGER DEFAULT 0,
    is_archived BOOLEAN DEFAULT FALSE,
    UNIQUE(conversation_id, user_id)
);

-- Documents table for RAG
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_hash VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    chunk_count INTEGER NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    is_processed BOOLEAN DEFAULT FALSE,
    processing_error TEXT,
    UNIQUE(document_hash, conversation_id)
);

-- Uploads tracking
CREATE TABLE uploads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(255),
    upload_status VARCHAR(50) DEFAULT 'completed',
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_time_ms INTEGER
);

-- User preferences
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    preference_key VARCHAR(255) NOT NULL,
    preference_value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, preference_key)
);
```

## Components and Interfaces

### 1. Database Connection Manager

**Purpose**: Manage Supabase connections with pooling and error handling

**Interface**:
```python
class SupabaseConnectionManager:
    def get_client() -> Client
    def test_connection() -> bool
    def close_connections() -> None
    def get_connection_stats() -> Dict
```

### 2. User Management Service

**Purpose**: Handle all user-related database operations

**Interface**:
```python
class UserService:
    async def create_user(username: str, password: str) -> Tuple[bool, str]
    async def authenticate_user(username: str, password: str) -> Tuple[bool, str]
    async def get_user_by_id(user_id: str) -> Optional[Dict]
    async def update_user_profile(user_id: str, data: Dict) -> bool
    async def delete_user(user_id: str) -> bool
```

### 3. Session Management Service

**Purpose**: Handle authentication sessions with Supabase

**Interface**:
```python
class SessionService:
    async def create_session(username: str) -> str
    async def validate_session(session_id: str) -> Optional[str]
    async def refresh_session(session_id: str) -> bool
    async def logout_session(session_id: str) -> None
    async def cleanup_expired_sessions() -> int
```

### 4. Conversation Service

**Purpose**: Manage conversations and messages in Supabase

**Interface**:
```python
class ConversationService:
    async def create_conversation(user_id: str, title: str) -> str
    async def get_user_conversations(user_id: str) -> Dict
    async def get_conversation(user_id: str, conv_id: str) -> Optional[Dict]
    async def update_conversation(user_id: str, conv_id: str, data: Dict) -> bool
    async def delete_conversation(user_id: str, conv_id: str) -> bool
    async def add_message(user_id: str, conv_id: str, message: Dict) -> bool
    async def get_messages(user_id: str, conv_id: str, limit: int = 50) -> List[Dict]
```

### 5. Document Service

**Purpose**: Manage document metadata for RAG system

**Interface**:
```python
class DocumentService:
    async def save_document_metadata(user_id: str, conv_id: str, doc_data: Dict) -> bool
    async def get_conversation_documents(user_id: str, conv_id: str) -> List[Dict]
    async def delete_document(user_id: str, doc_hash: str) -> bool
    async def update_document_status(doc_hash: str, status: str) -> bool
```

### 6. Migration Service

**Purpose**: Handle migration from file-based storage to Supabase

**Interface**:
```python
class MigrationService:
    async def detect_existing_data() -> Dict
    async def migrate_users() -> Tuple[int, List[str]]
    async def migrate_conversations(user_mapping: Dict) -> Tuple[int, List[str]]
    async def migrate_documents(user_mapping: Dict) -> Tuple[int, List[str]]
    async def verify_migration() -> Dict
    async def create_backup() -> str
```

## Data Models

### User Model
```python
@dataclass
class User:
    id: str
    username: str
    user_id: str
    email: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool
```

### Conversation Model
```python
@dataclass
class Conversation:
    id: str
    conversation_id: str
    user_id: str
    title: str
    messages: List[Dict]
    model: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    is_archived: bool
```

### Document Model
```python
@dataclass
class Document:
    id: str
    document_hash: str
    user_id: str
    conversation_id: str
    filename: str
    file_type: str
    file_size: int
    chunk_count: int
    added_at: datetime
    metadata: Dict
    is_processed: bool
```

## Error Handling

### Error Categories

1. **Connection Errors**: Network issues, Supabase unavailable
2. **Authentication Errors**: Invalid credentials, expired sessions
3. **Data Errors**: Constraint violations, invalid data format
4. **Migration Errors**: Data corruption, incomplete migration
5. **Performance Errors**: Slow queries, timeout issues

### Error Handling Strategy

```python
class SupabaseError(Exception):
    def __init__(self, message: str, error_code: str, details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}

class ErrorHandler:
    @staticmethod
    def handle_connection_error(error: Exception) -> str
    @staticmethod
    def handle_auth_error(error: Exception) -> str
    @staticmethod
    def handle_data_error(error: Exception) -> str
    @staticmethod
    def retry_with_backoff(func, max_retries: int = 3) -> Any
```

## Testing Strategy

### Unit Tests
- Test each service class independently
- Mock Supabase client for isolated testing
- Test error handling and edge cases
- Validate data models and serialization

### Integration Tests
- Test complete workflows (user registration, conversation creation)
- Test migration process with sample data
- Test performance under load
- Test error recovery scenarios

### Performance Tests
- Benchmark query performance vs file-based system
- Test concurrent user scenarios
- Measure memory usage and connection pooling
- Test large dataset handling

### Migration Tests
- Test migration with various data sizes
- Test partial migration recovery
- Test data integrity after migration
- Test rollback scenarios

## Performance Optimizations

### Database Optimizations

1. **Indexes**: Strategic indexes on frequently queried columns
2. **Connection Pooling**: Reuse database connections
3. **Query Optimization**: Use efficient queries with proper JOINs
4. **Batch Operations**: Group multiple operations together
5. **Caching**: Cache frequently accessed data in session state

### Application Optimizations

1. **Lazy Loading**: Load data only when needed
2. **Pagination**: Implement pagination for large datasets
3. **Compression**: Compress large JSON data
4. **Background Processing**: Move heavy operations to background
5. **Memory Management**: Regular cleanup of unused data

### Caching Strategy

```python
class CacheManager:
    def __init__(self):
        self.cache_ttl = {
            'conversations': 300,  # 5 minutes
            'documents': 600,     # 10 minutes
            'user_data': 1800,    # 30 minutes
        }
    
    def get_cached_data(self, key: str) -> Optional[Any]
    def set_cached_data(self, key: str, data: Any, ttl: int = None) -> None
    def invalidate_cache(self, pattern: str) -> None
    def cleanup_expired_cache() -> None
```

## Security Considerations

### Row Level Security (RLS)

```sql
-- Enable RLS on all tables
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE uploads ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can only access their own conversations" ON conversations
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY "Users can only access their own documents" ON documents
    FOR ALL USING (user_id = auth.uid());
```

### Data Encryption
- All data transmitted over HTTPS/TLS
- Passwords hashed with bcrypt and salt
- Sensitive data encrypted at rest in Supabase
- API keys stored securely in Streamlit secrets

### Access Control
- User authentication required for all operations
- Session-based access control
- Automatic session expiration
- Rate limiting on API endpoints

## Deployment Strategy

### Phase 1: Infrastructure Setup
1. Create Supabase project and configure database
2. Set up database schema and indexes
3. Configure Row Level Security policies
4. Test connection and basic operations

### Phase 2: Service Implementation
1. Implement core service classes
2. Add comprehensive error handling
3. Implement caching and performance optimizations
4. Add monitoring and logging

### Phase 3: Migration Implementation
1. Build migration service
2. Test migration with sample data
3. Implement rollback capabilities
4. Add migration progress tracking

### Phase 4: Integration and Testing
1. Replace file-based operations with Supabase calls
2. Run comprehensive testing suite
3. Performance testing and optimization
4. User acceptance testing

### Phase 5: Production Deployment
1. Configure production Supabase instance
2. Run migration on production data
3. Monitor performance and errors
4. Gradual rollout to users

This design provides a comprehensive foundation for migrating PharmGPT to use Supabase exclusively while maintaining all existing functionality and improving performance.