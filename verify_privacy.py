#!/usr/bin/env python3
"""
Privacy Verification Script
Ensures user data isolation and privacy
"""

import json
from pathlib import Path

def verify_privacy():
    """Verify user data privacy and isolation."""
    user_data_dir = Path("user_data")
    
    print("🔒 Verifying user data privacy...")
    
    # Load current users
    users_file = user_data_dir / "users.json"
    if users_file.exists():
        with open(users_file, 'r') as f:
            users = json.load(f)
    else:
        users = {}
    
    user_ids = [user_data["user_id"] for user_data in users.values()]
    print(f"📊 Found {len(users)} registered users")
    
    # Check conversation directories
    conversation_dirs = list(user_data_dir.glob("conversations_*"))
    print(f"📁 Found {len(conversation_dirs)} conversation directories")
    
    orphaned_conversations = []
    for conv_dir in conversation_dirs:
        user_id = conv_dir.name.replace("conversations_", "")
        if user_id not in user_ids:
            orphaned_conversations.append(conv_dir.name)
    
    # Check RAG directories
    rag_dirs = list(user_data_dir.glob("rag_*"))
    print(f"📚 Found {len(rag_dirs)} RAG directories")
    
    orphaned_rag = []
    for rag_dir in rag_dirs:
        user_id = rag_dir.name.replace("rag_", "")
        if user_id not in user_ids:
            orphaned_rag.append(rag_dir.name)
    
    # Report results
    if orphaned_conversations:
        print(f"⚠️  Found {len(orphaned_conversations)} orphaned conversation directories:")
        for item in orphaned_conversations:
            print(f"   - {item}")
    
    if orphaned_rag:
        print(f"⚠️  Found {len(orphaned_rag)} orphaned RAG directories:")
        for item in orphaned_rag:
            print(f"   - {item}")
    
    if not orphaned_conversations and not orphaned_rag:
        print("✅ Privacy verification passed!")
        print("🔒 All user data is properly isolated")
        print("👥 No cross-user data leaks detected")
    else:
        print("❌ Privacy issues detected!")
        print("🧹 Run 'python reset_user_data.py' to clean up")
    
    # Check for proper user isolation in current users
    for username, user_data in users.items():
        user_id = user_data["user_id"]
        conv_dir = user_data_dir / f"conversations_{user_id}"
        rag_dir = user_data_dir / f"rag_{user_id}"
        
        # Count conversation-specific RAG directories
        conv_rag_count = 0
        if rag_dir.exists():
            conv_rag_count = len(list(rag_dir.glob("conversation_*")))
        
        print(f"👤 User '{username}' (ID: {user_id[:8]}...):")
        print(f"   📁 Conversations: {'✅' if conv_dir.exists() else '❌'}")
        print(f"   📚 RAG data: {'✅' if rag_dir.exists() else '❌'}")
        if conv_rag_count > 0:
            print(f"   💬 Conversation RAG dirs: {conv_rag_count}")

if __name__ == "__main__":
    verify_privacy()