# PharmGPT Implementation Guide

## Overview
This guide provides step-by-step instructions to set up and verify the PharmGPT application using Supabase + pgvector for embeddings.

## Prerequisites
1. Supabase account and project
2. Mistral AI API key
3. Python 3.8+
4. Required dependencies installed

## Step 1: Database Setup

### Execute Database Schema
1. Open your Supabase Dashboard
2. Select your project
3. Go to "SQL Editor"
4. Copy and paste the entire contents of `complete_database_setup.sql`
5. Click "Run"

This will create:
- Tables: users, sessions, conversations, messages, documents, document_chunks
- Functions for authentication, session management, and RAG
- Indexes for performance optimization
- Row Level Security (RLS) policies for user isolation
- pgvector extension with 1024-dimensional embeddings

## Step 2: Environment Configuration

Ensure your `.env` file contains:
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
MISTRAL_API_KEY=your_mistral_api_key
```

## Step 3: Dependency Installation

Install required packages:
```bash
pip install -r requirements.txt
```

## Step 4: Verification

Run the verification script:
```bash
python verify_implementation.py
```

## Troubleshooting

### Common Issues:
1. **Database connection failed**: Check your SUPABASE_URL and SUPABASE_ANON_KEY.
2. **Embedding generation failed**: Check your MISTRAL_API_KEY and that the embedding service is reachable.
3. **Table not found**: Ensure you've executed the database setup script.

### Function overloading / migration errors
If you encounter errors about functions already existing, duplicate signatures, or argument type conflicts when running the SQL setup:
- Run the provided fix_all_functions.sql script to resolve common function conflicts:
  1. Open Supabase -> SQL Editor.
  2. Paste and run `fix_all_functions.sql`.
  3. Re-run `complete_database_setup.sql`.
- If the problem persists, inspect the existing functions (pg_proc) for duplicate signatures and remove or rename the conflicting versions carefully.

### Other troubleshooting tips
- RLS / permissions: Verify Row Level Security policies and that your anon/service keys have the required permissions for the operations you're performing.
- pgvector dimension mismatch: Ensure the pgvector column dimension (e.g., 1024) matches the embedding vector size produced by your model; adjust the column or embedding settings if needed.
- Logs: Check Supabase logs and your application logs for detailed error messages and stack traces to help pinpoint issues.
- Still stuck: Collect error messages and SQL logs, then re-run the migration steps in a fresh schema or reach out for support with the collected logs.
4. **RLS policy violations**: Make sure you're using authenticated requests

### Testing:
1. Run the application: `streamlit run app.py`
2. Create a test user account
3. Create a conversation
4. Upload a document
5. Ask questions about the document content