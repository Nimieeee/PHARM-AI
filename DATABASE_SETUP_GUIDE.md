# 🗄️ Complete Database Setup Guide

Since you've deleted all your Supabase tables, here's how to recreate everything from scratch with all the fixes applied.

## 📋 Step-by-Step Instructions

### 1. Run the Complete Database Setup

Go to your **Supabase Dashboard** → **SQL Editor** and run the entire contents of `complete_database_setup.sql`:

```sql
-- Copy and paste the entire complete_database_setup.sql file
-- This will create all tables, indexes, RLS policies, and functions
```

This script will:
- ✅ Create all 6 required tables (users, sessions, conversations, messages, documents, document_chunks)
- ✅ Set up 1024-dimensional vector support for Mistral AI embeddings
- ✅ Create all required indexes for performance
- ✅ Enable Row Level Security (RLS) with proper policies
- ✅ Create all RAG system functions (search_document_chunks, get_conversation_chunks, etc.)
- ✅ Set up triggers for automatic timestamp updates

### 2. Verify the Setup

After running the SQL script, test that everything works:

```bash
python verify_database_setup.py
```

This will test:
- Database structure (all tables exist)
- 1024-dimensional vector functionality
- RAG system functions
- User isolation setup

### 3. Test Embedding Functionality

Once the database is set up, test the embedding system:

```bash
python test_embedding_fix.py
```

This should now work perfectly with:
- ✅ 1024-dimensional Mistral AI embeddings
- ✅ Document processing and storage
- ✅ Semantic search functionality

## 🔧 What This Setup Includes

### Database Tables:
- **users**: User accounts and profiles
- **sessions**: User session management  
- **conversations**: Chat conversations
- **messages**: Individual chat messages
- **documents**: Uploaded files metadata
- **document_chunks**: Text chunks with 1024-D embeddings for RAG

### RAG System Functions:
- **search_document_chunks**: Semantic search across user's documents
- **get_conversation_chunks**: Retrieve chunks for a specific conversation
- **set_user_context**: Set user context for RLS policies
- **get_user_stats**: Get user statistics (conversations, messages, etc.)

### Security Features:
- **Row Level Security**: Users can only access their own data
- **Proper RLS Policies**: Enforced at database level
- **User Isolation**: Complete separation of user data

## 🚀 Ready to Deploy

After successful setup and testing:

1. Your database supports **1024-dimensional Mistral AI embeddings**
2. **User isolation** is properly enforced
3. **RAG system** is fully functional
4. **All security policies** are in place

You can now deploy your PharmGPT application to **Streamlit Cloud** - everything should work perfectly!

## 🆘 Troubleshooting

If you get any errors:

1. **"vector extension not found"**: Make sure you have the vector extension enabled in Supabase
2. **"function does not exist"**: Re-run the complete_database_setup.sql script
3. **RLS policy errors**: Check that your Supabase project has RLS enabled
4. **Embedding dimension errors**: Ensure you ran the complete setup (not just the old fix script)

The `verify_database_setup.py` script will help identify any issues and guide you to fix them.