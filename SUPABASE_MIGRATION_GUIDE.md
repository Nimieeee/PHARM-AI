# PharmGPT Supabase Migration Guide

## Overview

This guide will help you migrate your PharmGPT application from file-based storage to Supabase exclusively. The migration is designed to be safe, with automatic backups and rollback capabilities.

## Prerequisites

1. **Existing PharmGPT Installation**: You should have a working PharmGPT installation with file-based storage
2. **Supabase Account**: Create a free account at [supabase.com](https://supabase.com)
3. **Python Environment**: Ensure you have Python 3.8+ with pip

## Step 1: Set Up Supabase Project

### 1.1 Create New Project
1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Choose your organization
4. Enter project name (e.g., "pharmgpt-production")
5. Enter a strong database password
6. Select a region close to your users
7. Click "Create new project"

### 1.2 Get Project Credentials
1. Go to Project Settings → API
2. Copy your **Project URL** (looks like `https://xxxxx.supabase.co`)
3. Copy your **anon/public key** (starts with `eyJ...`)

### 1.3 Set Up Database Schema
1. Go to SQL Editor in your Supabase dashboard
2. Copy the contents of `supabase_schema.sql` from your project
3. Paste and run the SQL script
4. Verify all tables were created successfully

## Step 2: Configure PharmGPT

### 2.1 Install Dependencies
```bash
pip install supabase>=2.0.0
```

### 2.2 Configure Streamlit Secrets

**For Streamlit Cloud (Recommended):**
1. Go to your Streamlit Cloud app dashboard
2. Click on "Settings" → "Secrets"
3. Add your secrets in the web interface:

```toml
# Existing API keys
GROQ_API_KEY = "your_groq_key_here"
OPENROUTER_API_KEY = "your_openrouter_key_here"

# Supabase configuration
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your_anon_key_here"
```

**For Local Development:**
Create `.streamlit/secrets.toml` (this file is gitignored for security):

```toml
# Existing API keys
GROQ_API_KEY = "your_groq_key_here"
OPENROUTER_API_KEY = "your_openrouter_key_here"

# Supabase configuration
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your_anon_key_here"
```

**⚠️ IMPORTANT**: Never commit secrets to GitHub. The `.streamlit/` folder is automatically gitignored.

### 2.3 Test Connection
Run this test to verify your Supabase connection:

```python
import streamlit as st
from supabase_manager import health_check

# Test connection
health = health_check()
print(f"Supabase available: {health['supabase_available']}")
print(f"Client initialized: {health['client_initialized']}")
print(f"Connection test: {health['connection_test']}")
```

## Step 3: Run Migration

### 3.1 Automatic Migration (Recommended)
Run the migration script:

```bash
python migrate_to_supabase.py
```

The script will:
1. ✅ Check Supabase connection
2. 🔍 Detect existing file-based data
3. ✅ Validate data integrity
4. 💾 Create automatic backup
5. 🚀 Migrate all data to Supabase
6. ✅ Verify migration success
7. 📊 Generate migration report

### 3.2 Manual Migration (Advanced)
If you prefer manual control:

```python
from services.migration_service import migrate_all_data

# Run migration
result = await migrate_all_data()

if result['success']:
    print(f"Migration successful!")
    print(f"Users: {result['users_migrated']}")
    print(f"Conversations: {result['conversations_migrated']}")
    print(f"Documents: {result['documents_migrated']}")
else:
    print(f"Migration failed: {result['error']}")
```

## Step 4: Verify Migration

### 4.1 Start Your Application
```bash
streamlit run app.py
```

### 4.2 Test Core Functionality
1. **Authentication**: Try logging in with existing credentials
2. **Conversations**: Verify all conversations are visible
3. **Messages**: Check that message history is intact
4. **Documents**: Confirm uploaded documents are accessible
5. **New Features**: Test creating new conversations and uploading files

### 4.3 Performance Check
- Page load times should be similar or better
- File uploads should work normally
- Search functionality should be responsive

## Step 5: Post-Migration Cleanup

### 5.1 Verify Everything Works
Use your application for a few days to ensure everything functions correctly.

### 5.2 Clean Up Backup (Optional)
After confirming everything works, you can delete the backup:

```bash
# The backup directory will be named something like:
# user_data_backup_20241201_143022
rm -rf user_data_backup_*
```

### 5.3 Remove Old Files (Optional)
Once you're confident in the migration, you can remove the old file-based data:

```bash
# CAUTION: Only do this after thorough testing
rm -rf user_data/
```

## Troubleshooting

### Common Issues

#### 1. Connection Errors
**Error**: "Supabase client not initialized"
**Solution**: 
- Check your `SUPABASE_URL` and `SUPABASE_ANON_KEY` in secrets
- Verify the URL format: `https://xxxxx.supabase.co`
- Ensure the anon key is correct (starts with `eyJ`)

#### 2. Schema Errors
**Error**: "Table 'users' doesn't exist"
**Solution**:
- Run the `supabase_schema.sql` script in your Supabase SQL editor
- Check that all tables were created successfully
- Verify RLS policies are enabled

#### 3. Migration Validation Errors
**Error**: "Data validation failed"
**Solution**:
- Check the specific validation errors in the output
- Fix any corrupted JSON files in your `user_data` directory
- You can choose to continue migration despite warnings

#### 4. Performance Issues
**Issue**: Slow response times
**Solution**:
- Check your Supabase project region (should be close to users)
- Verify database indexes are created (included in schema)
- Monitor your Supabase dashboard for query performance

### Rollback Procedure

If something goes wrong, you can rollback:

#### Automatic Rollback
The migration script will offer to rollback if verification fails.

#### Manual Rollback
```python
from services.migration_service import migration_service

# Rollback to backup
success = await migration_service.rollback_migration("user_data_backup_20241201_143022")
```

#### Emergency Rollback
If the automatic rollback fails:

1. Stop your application
2. Rename your current `user_data` directory: `mv user_data user_data_failed`
3. Restore from backup: `mv user_data_backup_* user_data`
4. Update `config.py`: Set `USE_SUPABASE = False`
5. Restart your application

## Performance Comparison

### Before Migration (File-based)
- ✅ Fast for single user
- ❌ No concurrent user support
- ❌ Limited search capabilities
- ❌ Manual backup required
- ❌ No real-time features

### After Migration (Supabase)
- ✅ Supports multiple concurrent users
- ✅ Advanced search and filtering
- ✅ Automatic backups and point-in-time recovery
- ✅ Real-time capabilities
- ✅ Better data integrity and consistency
- ✅ Scalable architecture

## Support

### Getting Help
1. Check the migration logs for specific error messages
2. Review the generated migration report
3. Test with a small dataset first
4. Ensure all prerequisites are met

### Migration Report
The migration generates a detailed report including:
- Migration timestamp
- Data counts (users, conversations, documents)
- Error messages and warnings
- Performance metrics
- Backup location

### Best Practices
1. **Test First**: Run migration on a copy of your data first
2. **Backup**: Always create backups before migration
3. **Verify**: Thoroughly test all functionality after migration
4. **Monitor**: Watch Supabase dashboard for performance metrics
5. **Gradual**: Consider migrating users in batches for large datasets

## Advanced Configuration

### Custom Migration Settings
You can customize migration behavior in `services/migration_service.py`:

```python
# Custom backup directory
migration_service = MigrationService(user_data_dir="custom_data_dir")

# Custom batch sizes for large datasets
BATCH_SIZE = 100  # Process 100 items at a time
```

### Production Deployment
For production deployments:

1. **Use Supabase Pro**: For better performance and support
2. **Set up monitoring**: Use Supabase dashboard and alerts
3. **Configure backups**: Set up automated daily backups
4. **Use connection pooling**: Already configured in the migration
5. **Monitor performance**: Set up query performance monitoring

This migration will transform your PharmGPT from a single-user file-based application to a scalable, multi-user, cloud-based solution with enterprise-grade features.