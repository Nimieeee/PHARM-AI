#!/usr/bin/env python3
"""
Reset Upload Limit Script
Resets upload count for a specific user or all users
"""

import json
from pathlib import Path
import sys

def reset_upload_limit(user_id=None):
    """Reset upload limit for a user or all users."""
    user_data_dir = Path("user_data")
    uploads_file = user_data_dir / "uploads.json"
    
    if not uploads_file.exists():
        print("✅ No uploads file found - creating empty one")
        with open(uploads_file, 'w') as f:
            json.dump({}, f, indent=2)
        return
    
    with open(uploads_file, 'r') as f:
        uploads = json.load(f)
    
    if user_id:
        # Reset specific user
        if user_id in uploads:
            count = len(uploads[user_id])
            uploads[user_id] = []
            print(f"✅ Reset upload count for user {user_id[:8]}... (removed {count} uploads)")
        else:
            print(f"❌ User {user_id} not found in uploads")
    else:
        # Reset all users
        total_removed = 0
        for uid in uploads:
            total_removed += len(uploads[uid])
            uploads[uid] = []
        print(f"✅ Reset upload count for all users (removed {total_removed} uploads)")
    
    # Save updated uploads
    with open(uploads_file, 'w') as f:
        json.dump(uploads, f, indent=2)

def list_users_with_uploads():
    """List all users with their upload counts."""
    user_data_dir = Path("user_data")
    uploads_file = user_data_dir / "uploads.json"
    users_file = user_data_dir / "users.json"
    
    if not uploads_file.exists():
        print("No uploads file found")
        return
    
    # Load users for username mapping
    users = {}
    if users_file.exists():
        with open(users_file, 'r') as f:
            users_data = json.load(f)
            users = {data["user_id"]: username for username, data in users_data.items()}
    
    with open(uploads_file, 'r') as f:
        uploads = json.load(f)
    
    print("📊 Users with uploads:")
    for user_id, user_uploads in uploads.items():
        username = users.get(user_id, "Unknown")
        print(f"  👤 {username} ({user_id[:8]}...): {len(user_uploads)} uploads")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_users_with_uploads()
        else:
            reset_upload_limit(sys.argv[1])
    else:
        print("Usage:")
        print("  python reset_upload_limit.py list          # List users with uploads")
        print("  python reset_upload_limit.py <user_id>     # Reset specific user")
        print("  python reset_upload_limit.py all           # Reset all users")
        
        if input("Reset all users' upload limits? (y/N): ").lower() == 'y':
            reset_upload_limit()