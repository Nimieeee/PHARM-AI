# Embedding Dimension Fix Instructions

## Problem
Your PharmGPT application is failing to insert document chunks because of a dimension mismatch:
- **Database expects**: 384-dimensional vectors
- **Mistral AI produces**: 1024-dimensional vectors

## Solution Steps

### Step 1: Apply Database Migration
1. Go to your Supabase dashboard
2. Navigate to the SQL Editor
3. Copy and paste the contents of `fix_embedding_dimensions.sql`
4. Run the SQL script

This will:
- Drop the existing `document_chunks` table (if any)
- Create a new table with 1024-dimensional vector support
- Set up proper indexes and RLS policies
- Create search functions optimized for Mistral AI embeddings

### Step 2: Verify the Fix
Run the test script to ensure everything works:

```bash
python test_embedding_fix.py
```

This will:
- Test basic 1024-dimensional embedding insertion
- Test the RAG service integration
- Verify document processing and search functionality

### Step 3: Restart Your Application
After applying the database changes:
1. Restart your Streamlit application
2. Try uploading a document
3. The embedding dimension errors should be resolved

## What Changed
- **Database schema**: Updated to support `vector(1024)` instead of `vector(384)`
- **Embedding model**: Confirmed to use Mistral AI (1024 dimensions)
- **Search function**: Updated to work with 1024-dimensional vectors
- **Indexes**: Optimized for the new vector dimensions

## Expected Results
After applying this fix:
- ✅ Document uploads will work without dimension errors
- ✅ RAG system will function properly
- ✅ Semantic search will return relevant results
- ✅ No more "expected 384 dimensions, not 1024" errors

## Troubleshooting
If you still see issues:
1. Verify the SQL script ran without errors
2. Check that the `vector` extension is enabled in Supabase
3. Ensure your Mistral AI API key is properly configured
4. Run the test script to identify specific problems

## Files Created
- `fix_embedding_dimensions.sql` - Database migration script
- `test_embedding_fix.py` - Verification test script
- `EMBEDDING_FIX_INSTRUCTIONS.md` - This instruction file