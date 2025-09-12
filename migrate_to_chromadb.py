#!/usr/bin/env python3
"""
Migration Script - Migrate from Pinecone to ChromaDB
"""

import os
import json
import shutil
from datetime import datetime
from config import USER_DATA_DIR

def backup_existing_data():
    """Create backup of existing user data."""
    if not os.path.exists(USER_DATA_DIR):
        print("ℹ️  No existing user data to backup")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"{USER_DATA_DIR}_backup_{timestamp}"
    
    try:
        shutil.copytree(USER_DATA_DIR, backup_dir)
        print(f"✅ Backup created: {backup_dir}")
        return backup_dir
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def migrate_user_data():
    """Migrate user data structure for ChromaDB."""
    print("🔄 Migrating user data structure...")
    
    if not os.path.exists(USER_DATA_DIR):
        print("ℹ️  No user data to migrate")
        return
    
    # Load users
    users_file = os.path.join(USER_DATA_DIR, "users.json")
    if not os.path.exists(users_file):
        print("ℹ️  No users file found")
        return
    
    try:
        with open(users_file, 'r') as f:
            users = json.load(f)
    except Exception as e:
        print(f"❌ Error loading users: {e}")
        return
    
    # Migrate each user's data
    for username, user_data in users.items():
        user_id = user_data["user_id"]
        print(f"   Migrating user: {username} ({user_id})")
        
        # Ensure user directories exist
        conv_dir = os.path.join(USER_DATA_DIR, f"conversations_{user_id}")
        rag_dir = os.path.join(USER_DATA_DIR, f"rag_{user_id}")
        
        os.makedirs(conv_dir, exist_ok=True)
        os.makedirs(rag_dir, exist_ok=True)
        
        # Migrate conversations if they exist in old format
        old_conv_file = os.path.join(USER_DATA_DIR, f"{user_id}_conversations.json")
        new_conv_file = os.path.join(conv_dir, "conversations.json")
        
        if os.path.exists(old_conv_file) and not os.path.exists(new_conv_file):
            try:
                shutil.move(old_conv_file, new_conv_file)
                print(f"     ✅ Migrated conversations")
            except Exception as e:
                print(f"     ❌ Failed to migrate conversations: {e}")
        
        # Clean up old Pinecone data if it exists
        old_pinecone_dir = os.path.join(USER_DATA_DIR, f"pinecone_{user_id}")
        if os.path.exists(old_pinecone_dir):
            try:
                shutil.rmtree(old_pinecone_dir)
                print(f"     🗑️  Removed old Pinecone data")
            except Exception as e:
                print(f"     ❌ Failed to remove old Pinecone data: {e}")
    
    print("✅ User data migration completed")

def clean_old_files():
    """Clean up old migration files and temporary data."""
    print("🧹 Cleaning up old files...")
    
    if not os.path.exists(USER_DATA_DIR):
        return
    
    # Files to remove
    old_files = [
        "migration_log.txt",
        "pinecone_backup.json",
        "temp_migration_data.json"
    ]
    
    removed_count = 0
    for filename in old_files:
        filepath = os.path.join(USER_DATA_DIR, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                removed_count += 1
                print(f"   🗑️  Removed: {filename}")
            except Exception as e:
                print(f"   ❌ Failed to remove {filename}: {e}")
    
    # Remove old user-specific files with old naming pattern
    for item in os.listdir(USER_DATA_DIR):
        if item.endswith("_conversations.json") or item.startswith("pinecone_"):
            filepath = os.path.join(USER_DATA_DIR, item)
            try:
                if os.path.isfile(filepath):
                    os.remove(filepath)
                elif os.path.isdir(filepath):
                    shutil.rmtree(filepath)
                removed_count += 1
                print(f"   🗑️  Removed: {item}")
            except Exception as e:
                print(f"   ❌ Failed to remove {item}: {e}")
    
    if removed_count > 0:
        print(f"✅ Cleaned up {removed_count} old files")
    else:
        print("ℹ️  No old files to clean up")

def verify_migration():
    """Verify that migration was successful."""
    print("🔍 Verifying migration...")
    
    if not os.path.exists(USER_DATA_DIR):
        print("❌ User data directory not found")
        return False
    
    # Load users
    users_file = os.path.join(USER_DATA_DIR, "users.json")
    if not os.path.exists(users_file):
        print("❌ Users file not found")
        return False
    
    try:
        with open(users_file, 'r') as f:
            users = json.load(f)
    except Exception as e:
        print(f"❌ Error loading users: {e}")
        return False
    
    # Check each user's directory structure
    all_good = True
    for username, user_data in users.items():
        user_id = user_data["user_id"]
        
        conv_dir = os.path.join(USER_DATA_DIR, f"conversations_{user_id}")
        rag_dir = os.path.join(USER_DATA_DIR, f"rag_{user_id}")
        
        if not os.path.exists(conv_dir):
            print(f"❌ Missing conversations directory for user {username}")
            all_good = False
        
        if not os.path.exists(rag_dir):
            print(f"❌ Missing RAG directory for user {username}")
            all_good = False
        
        if all_good:
            print(f"   ✅ User {username}: directories OK")
    
    if all_good:
        print("✅ Migration verification passed")
    else:
        print("❌ Migration verification failed")
    
    return all_good

def main():
    """Main migration function."""
    print("🚀 PharmBot ChromaDB Migration Tool")
    print("=" * 40)
    print("This tool migrates your PharmBot data to use ChromaDB")
    print("instead of Pinecone for better reliability and performance.")
    print()
    
    # Check if migration is needed
    if not os.path.exists(USER_DATA_DIR):
        print("ℹ️  No existing data found. No migration needed.")
        return
    
    print("Migration steps:")
    print("1. Backup existing data")
    print("2. Migrate user data structure")
    print("3. Clean up old files")
    print("4. Verify migration")
    print()
    
    confirm = input("Do you want to proceed with migration? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Migration cancelled")
        return
    
    # Step 1: Backup
    print("\n" + "="*50)
    print("STEP 1: Creating backup...")
    backup_dir = backup_existing_data()
    if not backup_dir:
        print("❌ Migration aborted due to backup failure")
        return
    
    # Step 2: Migrate
    print("\n" + "="*50)
    print("STEP 2: Migrating data structure...")
    migrate_user_data()
    
    # Step 3: Clean up
    print("\n" + "="*50)
    print("STEP 3: Cleaning up old files...")
    clean_old_files()
    
    # Step 4: Verify
    print("\n" + "="*50)
    print("STEP 4: Verifying migration...")
    success = verify_migration()
    
    # Final status
    print("\n" + "="*50)
    if success:
        print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print(f"   Backup saved to: {backup_dir}")
        print("   Your PharmBot is now using ChromaDB for better performance!")
        print("\nNext steps:")
        print("1. Install ChromaDB dependencies: pip install chromadb")
        print("2. Test your application to ensure everything works")
        print("3. If everything works well, you can delete the backup directory")
    else:
        print("❌ MIGRATION FAILED!")
        print(f"   Your original data is backed up in: {backup_dir}")
        print("   Please check the errors above and try again")
        print("   You can restore from backup if needed")

if __name__ == "__main__":
    main()