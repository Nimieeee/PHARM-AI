#!/usr/bin/env python3
"""
Reset Upload Limit - Clear upload tracking for users
"""

import json
import os
from datetime import datetime
from config import USER_DATA_DIR

UPLOADS_FILE = os.path.join(USER_DATA_DIR, "uploads.json")

def load_uploads():
    """Load upload tracking data."""
    try:
        if os.path.exists(UPLOADS_FILE):
            with open(UPLOADS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading uploads: {e}")
    return {}

def save_uploads(uploads):
    """Save upload tracking data."""
    try:
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        with open(UPLOADS_FILE, 'w') as f:
            json.dump(uploads, f, indent=2)
        print(f"✅ Upload data saved to {UPLOADS_FILE}")
    except Exception as e:
        print(f"❌ Error saving uploads: {e}")

def reset_all_upload_limits():
    """Reset upload limits for all users."""
    print("🔄 Resetting all upload limits...")
    
    uploads = load_uploads()
    
    if not uploads:
        print("ℹ️  No upload data found")
        return
    
    # Clear all upload data
    uploads.clear()
    save_uploads(uploads)
    
    print("✅ All upload limits have been reset")
    print("ℹ️  All users can now upload files again")

def reset_user_upload_limit(user_id):
    """Reset upload limit for a specific user."""
    print(f"🔄 Resetting upload limit for user: {user_id}")
    
    uploads = load_uploads()
    
    if user_id in uploads:
        del uploads[user_id]
        save_uploads(uploads)
        print(f"✅ Upload limit reset for user {user_id}")
    else:
        print(f"ℹ️  No upload data found for user {user_id}")

def show_upload_status():
    """Show current upload status for all users."""
    uploads = load_uploads()
    
    if not uploads:
        print("ℹ️  No upload data found")
        return
    
    print("📊 Current Upload Status:")
    print("-" * 50)
    
    for user_id, user_uploads in uploads.items():
        print(f"User: {user_id}")
        print(f"  Total uploads: {len(user_uploads)}")
        
        if user_uploads:
            latest_upload = max(user_uploads, key=lambda x: x['timestamp'])
            print(f"  Latest upload: {latest_upload['filename']} at {latest_upload['timestamp']}")
        
        print()

def main():
    """Main function."""
    print("🔧 PharmBot Upload Limit Reset Tool")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Show upload status")
        print("2. Reset all upload limits")
        print("3. Reset specific user upload limit")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            show_upload_status()
        
        elif choice == "2":
            confirm = input("Are you sure you want to reset ALL upload limits? (y/N): ").strip().lower()
            if confirm == 'y':
                reset_all_upload_limits()
            else:
                print("❌ Operation cancelled")
        
        elif choice == "3":
            user_id = input("Enter user ID to reset: ").strip()
            if user_id:
                reset_user_upload_limit(user_id)
            else:
                print("❌ Invalid user ID")
        
        elif choice == "4":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()