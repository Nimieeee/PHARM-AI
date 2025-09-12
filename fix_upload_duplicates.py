#!/usr/bin/env python3
"""
Fix Upload Duplicates Script
Removes duplicate upload records that occurred within seconds of each other
"""

import json
from pathlib import Path
from datetime import datetime, timedelta

def fix_upload_duplicates():
    """Remove duplicate upload records."""
    user_data_dir = Path("user_data")
    uploads_file = user_data_dir / "uploads.json"
    
    if not uploads_file.exists():
        print("✅ No uploads file found - nothing to fix")
        return
    
    print("🔍 Checking for duplicate uploads...")
    
    with open(uploads_file, 'r') as f:
        uploads = json.load(f)
    
    total_removed = 0
    
    for user_id, user_uploads in uploads.items():
        if not user_uploads:
            continue
        
        print(f"👤 Checking user {user_id[:8]}... ({len(user_uploads)} uploads)")
        
        # Sort uploads by timestamp
        user_uploads.sort(key=lambda x: x["timestamp"])
        
        # Remove duplicates (same file within 10 seconds)
        cleaned_uploads = []
        
        for upload in user_uploads:
            # Check if this is a duplicate of the last added upload
            is_duplicate = False
            
            if cleaned_uploads:
                last_upload = cleaned_uploads[-1]
                
                # Same filename and size
                if (upload["filename"] == last_upload["filename"] and 
                    upload["file_size"] == last_upload["file_size"]):
                    
                    # Within 10 seconds
                    upload_time = datetime.fromisoformat(upload["timestamp"])
                    last_time = datetime.fromisoformat(last_upload["timestamp"])
                    
                    if abs((upload_time - last_time).total_seconds()) <= 10:
                        is_duplicate = True
                        total_removed += 1
                        print(f"  🗑️  Removed duplicate: {upload['filename']}")
            
            if not is_duplicate:
                cleaned_uploads.append(upload)
        
        uploads[user_id] = cleaned_uploads
        print(f"  ✅ Kept {len(cleaned_uploads)} unique uploads")
    
    # Save cleaned uploads
    with open(uploads_file, 'w') as f:
        json.dump(uploads, f, indent=2)
    
    print(f"✅ Cleanup complete! Removed {total_removed} duplicate uploads")
    
    # Show current status
    for user_id, user_uploads in uploads.items():
        if user_uploads:
            print(f"👤 User {user_id[:8]}... now has {len(user_uploads)} uploads")

if __name__ == "__main__":
    fix_upload_duplicates()