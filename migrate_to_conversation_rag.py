#!/usr/bin/env python3
"""
Migrate to Conversation-Specific RAG Script
Migrates existing user-level RAG data to conversation-specific structure
"""

import json
import shutil
from pathlib import Path

def migrate_to_conversation_rag():
    """Migrate existing RAG data to conversation-specific structure."""
    user_data_dir = Path("user_data")
    
    print("🔄 Migrating to conversation-specific RAG system...")
    
    # Find all existing user RAG directories
    old_rag_dirs = list(user_data_dir.glob("rag_*"))
    
    if not old_rag_dirs:
        print("✅ No existing RAG data found - nothing to migrate")
        return
    
    migrated_count = 0
    
    for old_rag_dir in old_rag_dirs:
        # Extract user ID from directory name
        user_id = old_rag_dir.name.replace("rag_", "")
        
        print(f"👤 Processing user {user_id[:8]}...")
        
        # Check if this is already the new structure (has conversation subdirectories)
        has_conversations = any(item.is_dir() and item.name.startswith("conversation_") 
                              for item in old_rag_dir.iterdir())
        
        if has_conversations:
            print(f"   ✅ Already using new structure")
            continue
        
        # Check if user has any documents
        metadata_file = old_rag_dir / "documents_metadata.json"
        if not metadata_file.exists():
            print(f"   ℹ️  No documents found")
            continue
        
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            if not metadata:
                print(f"   ℹ️  No documents in metadata")
                continue
            
            # Load user's conversations to find the most recent one
            users_file = user_data_dir / "users.json"
            conversations_file = None
            
            if users_file.exists():
                with open(users_file, 'r') as f:
                    users = json.load(f)
                
                # Find username for this user_id
                username = None
                for uname, udata in users.items():
                    if udata.get("user_id") == user_id:
                        username = uname
                        break
                
                if username:
                    conv_file = user_data_dir / f"conversations_{user_id}" / "conversations.json"
                    if conv_file.exists():
                        conversations_file = conv_file
            
            # Determine target conversation
            target_conversation_id = "global"  # Default fallback
            
            if conversations_file and conversations_file.exists():
                try:
                    with open(conversations_file, 'r') as f:
                        conversations = json.load(f)
                    
                    if conversations:
                        # Use the most recent conversation
                        most_recent = max(conversations.items(), 
                                        key=lambda x: x[1].get('created_at', ''))
                        target_conversation_id = most_recent[0]
                        print(f"   📁 Migrating to conversation: {most_recent[1].get('title', 'Untitled')}")
                except:
                    pass
            
            # Create new conversation-specific directory
            new_conv_dir = old_rag_dir / f"conversation_{target_conversation_id}"
            new_conv_dir.mkdir(exist_ok=True)
            
            # Move files to conversation directory
            files_moved = 0
            for item in old_rag_dir.iterdir():
                if item.is_file():
                    target_path = new_conv_dir / item.name
                    shutil.move(str(item), str(target_path))
                    files_moved += 1
            
            print(f"   ✅ Migrated {len(metadata)} documents ({files_moved} files)")
            migrated_count += 1
            
        except Exception as e:
            print(f"   ❌ Error migrating user {user_id[:8]}: {e}")
    
    print(f"✅ Migration complete! Migrated {migrated_count} users to conversation-specific RAG")
    print("🔒 Each conversation now has its own isolated knowledge base")

if __name__ == "__main__":
    migrate_to_conversation_rag()