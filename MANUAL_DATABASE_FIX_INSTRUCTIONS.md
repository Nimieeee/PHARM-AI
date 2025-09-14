# Manual Database Fix Instructions for RAG RLS Issue

## Overview
The RAG system is encountering RLS (Row Level Security) policy violations when trying to store document chunks. This requires manual intervention through the Supabase dashboard.

## 🚨 Current Error
```
Query failed: insert on document_chunks - 
{'message': 'new row violates row-level security policy for table "document_chunks"', 
 'code': '42501', 'hint': None, 'details': None}
```

## 🛠️ Manual Fix Options

### Option 1: Disable RLS Temporarily (Recommended for Testing)

1. **Go to Supabase Dashboard**
   - Visit: https://supabase.com/dashboard
   - Select your project: `ayjqeatcijvzeynmkqki`

2. **Navigate to Database**
   - Click "Database" in the left sidebar
   - Click "Tables" 
   - Find the `document_chunks` table

3. **Disable RLS**
   - Click on the `document_chunks` table
   - Click "Settings" or "RLS" tab
   - Toggle "Enable RLS" to OFF
   - Click "Save"

### Option 2: Fix RLS Policies (Recommended for Production)

1. **Go to Authentication > Policies**
   - In Supabase Dashboard, click "Authentication"
   - Click "Policies"
   - Find policies for `document_chunks` table

2. **Create New Policy**
   - Click "New Policy"
   - Select `document_chunks` table
   - Policy name: "Allow authenticated users full access"
   - Policy definition:
   ```sql
   -- For INSERT
   WITH CHECK (auth.uid() IS NOT NULL)
   
   -- For SELECT, UPDATE, DELETE  
   USING (auth.uid() IS NOT NULL)
   ```

3. **Or Use SQL Editor**
   - Go to "SQL Editor" in dashboard
   - Run this SQL:
   ```sql
   -- Drop existing policies
   DROP POLICY IF EXISTS "Users can manage their own document chunks" ON document_chunks;
   
   -- Create permissive policy for authenticated users
   CREATE POLICY "Allow authenticated users" ON document_chunks
   FOR ALL TO authenticated USING (true) WITH CHECK (true);
   
   -- Grant permissions
   GRANT ALL ON document_chunks TO authenticated;
   GRANT USAGE ON SEQUENCE document_chunks_id_seq TO authenticated;
   ```

### Option 3: Use Provided Scripts

If you have access to run Python scripts with Supabase admin access:

```bash
# Try the simple fix
python simple_rag_fix.py

# Or the comprehensive fix
python fix_rag_database_issues.py

# Emergency option (disables all security)
python disable_rls_completely.py
```

## 🔍 Verification Steps

After applying any fix:

1. **Test Document Upload**
   - Go to your app: https://ptt-ai.streamlit.app/Chatbot
   - Upload a document (PDF, DOCX, etc.)
   - Check if you see: "✅ Document processed successfully"

2. **Check Logs**
   - Look for: "✅ Successfully processed X chunks for document"
   - Should NOT see: "⚠️ RAG processing failed"

3. **Test RAG Search**
   - Ask a question about your uploaded document
   - The AI should reference the document content in its response

## 🎯 Expected Results

### Before Fix:
- ❌ Document upload shows processing but fails silently
- ❌ RAG search doesn't find document content
- ❌ Error logs show RLS policy violations

### After Fix:
- ✅ Document upload shows "Document processed successfully"
- ✅ RAG search finds and uses document content
- ✅ No RLS policy errors in logs

## 🔧 Alternative: Local Development

If you can't fix the Supabase RLS policies, you can:

1. **Use Local PostgreSQL**
   - Install PostgreSQL with pgvector extension
   - Update connection strings to local database
   - No RLS restrictions on local development

2. **Use Different Vector Store**
   - Switch to ChromaDB (file-based)
   - Update RAG service to use ChromaDB instead of Supabase
   - No database permissions needed

## 📞 Support

If manual fixes don't work:

1. **Check Supabase Project Settings**
   - Ensure you have Owner/Admin access
   - Check if RLS is enforced at project level

2. **Contact Supabase Support**
   - Provide error message and project ID
   - Ask about RLS policy configuration

3. **Use Alternative Approach**
   - Temporarily store documents in session state only
   - Skip pgvector storage until RLS is resolved
   - Use simple text matching instead of semantic search

## ⚠️ Security Note

**Option 1 (Disable RLS)** removes all security from the document_chunks table. This is fine for testing but should not be used in production with real user data.

**Option 2 (Fix Policies)** maintains security while allowing proper functionality.

Choose the option that matches your current development stage and security requirements.