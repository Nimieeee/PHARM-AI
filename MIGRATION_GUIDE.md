# 🔄 PharmGPT Migration Guide

## From Old System to Clean v2.0 Architecture

This guide helps you migrate from the previous PharmGPT implementation to the new clean architecture.

---

## 📊 **What Changed**

### **🏗️ Architecture Changes**
- **Before**: Scattered files, mixed responsibilities
- **After**: Clean modular architecture in `core/` directory

### **🗄️ Database Changes**
- **Before**: Multiple setup files, inconsistent schema
- **After**: Single `database/schema.sql` with complete setup

### **🔐 Authentication Changes**
- **Before**: Session issues, logout on refresh
- **After**: Persistent 30-day sessions with automatic refresh

### **📚 RAG System Changes**
- **Before**: Pinecone or inconsistent vector storage
- **After**: Supabase + pgvector with conversation isolation

### **👥 User Isolation Changes**  
- **Before**: Potential data leakage between users
- **After**: Database-level RLS ensuring complete isolation

---

## 🚀 **Migration Steps**

### **Step 1: Backup Current System**
```bash
# Backup your current codebase
cp -r pharmgpt pharmgpt_backup_$(date +%Y%m%d)

# Export any important data from your current database
# (This depends on your current setup)
```

### **Step 2: Database Migration**

#### **Option A: Fresh Start (Recommended)**
```sql
-- In Supabase SQL Editor
-- ⚠️ This will delete ALL existing data
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

-- Then run the new schema
-- Copy/paste entire database/schema.sql file
```

#### **Option B: Preserve User Data**
```sql
-- Export existing users first
COPY users TO '/tmp/users_backup.csv' CSV HEADER;

-- Then follow Option A and re-import users
-- (You'll need to adapt the import to new schema)
```

### **Step 3: Update Environment Variables**
Update your `.env` file:
```env
# Old variables (remove if not needed)
# PINECONE_API_KEY=...
# OLD_DATABASE_URL=...

# New required variables
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
MISTRAL_API_KEY=your_mistral_api_key
OPENAI_API_KEY=your_openai_api_key
```

### **Step 4: Install New Dependencies**
```bash
# Uninstall old dependencies that might conflict
pip uninstall pinecone-client

# Install new requirements
pip install -r requirements.txt
```

### **Step 5: Test New System**
```bash
# Run verification
python tests/quick_verification.py

# Should show all tests passing
```

### **Step 6: Update Streamlit Secrets (Production)**
Update `.streamlit/secrets.toml`:
```toml
# Remove old secrets
# [pinecone]
# api_key = "..."

# Add new secrets
SUPABASE_URL = "your_url"
SUPABASE_ANON_KEY = "your_key" 
MISTRAL_API_KEY = "your_key"
```

---

## 🗃️ **File Migration Mapping**

### **Files to Replace**
| Old File | New File | Action |
|----------|----------|---------|
| `auth.py` | `core/auth.py` | ✅ Replace completely |
| `supabase_manager.py` | `core/supabase_client.py` | ✅ Replace completely |
| `rag_service.py` | `core/rag.py` | ✅ Replace completely |
| `conversation_service.py` | `core/conversations.py` | ✅ Replace completely |
| Various setup SQLs | `database/schema.sql` | ✅ Replace with single file |

### **Files to Keep**
| File | Action |
|------|--------|
| `prompts.py` | ✅ Keep and integrate with new chat |
| `config.py` | ⚠️ Check compatibility with `core/config.py` |
| Custom styling/CSS | ✅ Integrate into new pages |

### **Files to Remove**
- `DATABASE_SETUP_GUIDE.md`
- `EMBEDDING_FIX_INSTRUCTIONS.md` 
- `FIXED_DATABASE_SETUP_GUIDE.md`
- `complete_database_setup.sql`
- `fix_*.sql` files
- `test_*.py` (replace with new test suite)
- Old debug/diagnostic scripts

---

## 🔄 **Data Migration**

### **User Data**
If you want to preserve existing users:

```sql
-- 1. Export from old system
SELECT username, email, created_at FROM old_users;

-- 2. Import to new system (adapt as needed)
-- Note: Passwords will need to be reset due to new hashing
INSERT INTO users (username, email, created_at) 
VALUES (...);
```

### **Conversation Data**
```sql
-- Export conversations with user mapping
SELECT user_id, title, created_at, updated_at 
FROM old_conversations;

-- Import to new system
INSERT INTO conversations (user_id, title, created_at, updated_at)
VALUES (...);
```

### **Document Data**
- Old document embeddings will need to be regenerated
- New system uses 1024-dimensional Mistral embeddings
- Documents will need to be re-processed through new RAG system

---

## ⚙️ **Configuration Migration**

### **Old Config Pattern**
```python
# config.py (old)
APP_TITLE = "PharmGPT"
DATABASE_URL = "..."
PINECONE_KEY = "..."
```

### **New Config Pattern** 
```python
# core/config.py (new)
class Config:
    APP_TITLE = "PharmGPT"
    # Environment-based configuration
    # Streamlit secrets integration
    # Validation and health checks
```

**Migration Steps:**
1. Review your old `config.py`
2. Port custom settings to `core/config.py`
3. Update imports in your custom code

---

## 🧪 **Testing Migration**

### **Pre-Migration Testing**
```bash
# Test current system works
streamlit run app.py

# Export any critical data
# Take screenshots of important conversations
```

### **Post-Migration Testing**
```bash
# Run new verification
python tests/quick_verification.py

# Test core functionality
python tests/test_comprehensive.py

# Manual testing
streamlit run app.py
# - Create account
# - Create conversation  
# - Upload document
# - Test RAG functionality
# - Verify data isolation
```

---

## 🚨 **Common Migration Issues**

### **Import Errors**
```python
# Old import
from auth import authenticate_user

# New import  
from core.auth import sign_in
```

### **Database Connection Issues**
- Update connection strings
- Verify Supabase credentials
- Check RLS policies are active

### **Session Issues**
- Clear browser storage
- Users will need to log in again
- Sessions from old system won't work

### **Document Processing**
- Old documents need re-upload
- Embeddings will be regenerated
- File processing has new validation

---

## 💡 **Best Practices for Migration**

### **1. Staged Migration**
```bash
# Week 1: Setup new system in parallel
# Week 2: Test with limited users  
# Week 3: Full migration
# Week 4: Remove old system
```

### **2. User Communication**
- Notify users about migration
- Explain they'll need to re-login
- Inform about re-uploading documents

### **3. Rollback Plan**
- Keep old system running initially
- Have database backups
- Test rollback procedure

### **4. Monitoring**
- Monitor error rates after migration
- Check user adoption
- Performance metrics

---

## 📈 **Post-Migration Benefits**

Users will immediately notice:

✅ **No more logout on refresh**  
✅ **Better performance** - cleaner queries  
✅ **Improved security** - proper user isolation  
✅ **Better document processing** - multiple file types  
✅ **Conversation-specific knowledge** - better context  
✅ **Cleaner UI** - modern interface design  

---

## 🆘 **Migration Support**

### **Rollback Procedure**
If you need to rollback:

```bash
# 1. Stop new system
# 2. Restore old codebase
cp -r pharmgpt_backup_* pharmgpt

# 3. Restore old database (if you have backups)
# 4. Update environment variables back
# 5. Restart old system
```

### **Common Issues & Solutions**

| Issue | Solution |
|-------|----------|
| Users can't login | Clear browser storage, re-signup |
| Documents not found | Re-upload through new system |
| Performance slow | Check database indexes, run `ANALYZE` |
| Conversations empty | Check RLS policies, verify user_id mapping |

---

## ✅ **Migration Checklist**

- [ ] Backup current system and data
- [ ] Setup new Supabase database
- [ ] Run `database/schema.sql`
- [ ] Update environment variables
- [ ] Install new dependencies
- [ ] Run verification tests
- [ ] Test core functionality
- [ ] Migrate user accounts (if needed)
- [ ] Update production secrets
- [ ] Deploy new system
- [ ] Communicate to users
- [ ] Monitor for issues
- [ ] Remove old system (after verification)

---

**🎉 Congratulations on migrating to PharmGPT v2.0!**

Your users will love the improved experience and you'll benefit from the cleaner, more maintainable architecture.