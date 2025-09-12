# Supabase Setup Guide for PharmGPT

## When to Use Supabase

### ✅ Use Supabase if you have:
- **Multiple concurrent users** (>10 users)
- **Large datasets** (>50 conversations, >1000 messages)
- **Need for real-time features** (collaboration, notifications)
- **Scaling requirements** (growing user base)
- **Advanced search needs** (complex queries, filtering)
- **Multi-device sync requirements**

### ❌ Stick with files if you have:
- **Single user or small team** (<5 users)
- **Small datasets** (<20 conversations)
- **Offline requirements** (no internet dependency)
- **Simple use case** (basic chat functionality)
- **Prefer simplicity** (fewer dependencies)

## Performance Comparison

Based on testing, here's when each system performs better:

| Scenario | File-based | Supabase | Winner |
|----------|------------|----------|---------|
| Single user, <10 conversations | ~0.001s | ~0.050s | **Files** |
| Single user, 10-50 conversations | ~0.005s | ~0.040s | **Files** |
| Single user, >50 conversations | ~0.020s | ~0.035s | **Supabase** |
| Multiple users, any size | Race conditions | ~0.040s | **Supabase** |
| Complex queries/search | Not supported | ~0.100s | **Supabase** |
| Offline usage | ✅ Works | ❌ Fails | **Files** |

## Setup Instructions

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note your project URL and anon key

### 2. Set up Database Schema

Run this SQL in your Supabase SQL editor:

```sql
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
```

### 3. Configure Streamlit Secrets

Add to your `.streamlit/secrets.toml`:

```toml
# Existing API keys
GROQ_API_KEY = "your_groq_key"
OPENROUTER_API_KEY = "your_openrouter_key"

# Supabase configuration
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your_anon_key"
```

### 4. Enable Supabase in Config

In `config.py`, change:

```python
# Database settings
USE_SUPABASE = True  # Set to True to use Supabase
```

### 5. Install Dependencies

```bash
pip install supabase
```

### 6. Test Performance

Use the built-in performance comparison tool:

```python
from performance_comparison import run_performance_comparison
run_performance_comparison()
```

## Migration from Files to Supabase

### Automatic Migration

The system includes automatic migration capabilities:

1. Enable Supabase in config
2. Run the app - it will detect existing file data
3. Data will be automatically migrated on first run
4. File-based data remains as backup

### Manual Migration

If you prefer manual control:

```python
from supabase_integration import migrate_file_data_to_supabase
migrate_file_data_to_supabase()
```

## Performance Optimization Tips

### For Supabase:

1. **Use Connection Pooling**: Enable in Supabase dashboard
2. **Optimize Queries**: Use indexes and limit results
3. **Cache Frequently Accessed Data**: Use session state caching
4. **Batch Operations**: Group multiple operations together
5. **Use RLS Policies**: For security and performance

### For Files:

1. **Regular Cleanup**: Remove old session state data
2. **Optimize File Size**: Keep conversation files small
3. **Use Caching**: Cache frequently accessed conversations
4. **Minimize I/O**: Batch file operations

## Monitoring Performance

### Built-in Metrics

The app includes performance monitoring for both systems:

```python
from performance_monitor import show_performance_sidebar
show_performance_sidebar()
```

### Key Metrics to Watch

- **Response Time**: <100ms for queries
- **Memory Usage**: <500MB total
- **Cache Hit Rate**: >80% for optimal performance
- **Database Connections**: <10 concurrent

## Troubleshooting

### Common Issues

1. **Slow Queries**: Add indexes, optimize WHERE clauses
2. **Connection Timeouts**: Check network, increase timeout
3. **High Memory Usage**: Clear caches, optimize queries
4. **Migration Errors**: Check data format, run validation

### Performance Debugging

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Monitor query performance
from supabase_integration import supabase_manager
# Queries will be logged with timing information
```

## Cost Considerations

### Supabase Pricing (as of 2024):
- **Free Tier**: 500MB database, 2GB bandwidth
- **Pro Tier**: $25/month, 8GB database, 250GB bandwidth
- **Team Tier**: $599/month, 100GB database, 1TB bandwidth

### File-based Costs:
- **Storage**: Minimal (few MB for typical usage)
- **Bandwidth**: None (local storage)
- **Maintenance**: Manual backups recommended

## Recommendation

For most PharmGPT users, **start with the file-based system** and migrate to Supabase when you experience:

- Slow performance with large datasets
- Need for multi-user access
- Requirements for advanced features
- Scaling beyond single-user usage

The hybrid approach allows you to switch seamlessly based on your needs.