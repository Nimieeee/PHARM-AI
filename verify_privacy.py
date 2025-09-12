#!/usr/bin/env python3
"""
Privacy Verification Tool - Verify user data isolation and privacy
"""

import json
import os
from typing import Dict, List, Tuple
from config import USER_DATA_DIR

def load_users() -> Dict:
    """Load users from file."""
    users_file = os.path.join(USER_DATA_DIR, "users.json")
    try:
        if os.path.exists(users_file):
            with open(users_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"❌ Error loading users: {e}")
    return {}

def get_user_directories() -> List[str]:
    """Get all user-specific directories."""
    user_dirs = []
    
    if os.path.exists(USER_DATA_DIR):
        for item in os.listdir(USER_DATA_DIR):
            if item.startswith("conversations_") or item.startswith("rag_"):
                user_dirs.append(item)
    
    return user_dirs

def verify_directory_ownership() -> Tuple[bool, List[str]]:
    """Verify that all user directories belong to valid users."""
    users = load_users()
    valid_user_ids = set()
    
    # Get all valid user IDs
    for username, user_data in users.items():
        valid_user_ids.add(user_data["user_id"])
    
    # Check all user directories
    user_dirs = get_user_directories()
    orphaned_dirs = []
    
    for dir_name in user_dirs:
        if dir_name.startswith("conversations_"):
            user_id = dir_name.replace("conversations_", "")
        elif dir_name.startswith("rag_"):
            user_id = dir_name.replace("rag_", "")
        else:
            continue
        
        if user_id not in valid_user_ids:
            orphaned_dirs.append(dir_name)
    
    return len(orphaned_dirs) == 0, orphaned_dirs

def check_conversation_isolation() -> Tuple[bool, List[str]]:
    """Check that conversations are properly isolated per user."""
    issues = []
    users = load_users()
    
    for username, user_data in users.items():
        user_id = user_data["user_id"]
        conv_dir = os.path.join(USER_DATA_DIR, f"conversations_{user_id}")
        
        if os.path.exists(conv_dir):
            conv_file = os.path.join(conv_dir, "conversations.json")
            if os.path.exists(conv_file):
                try:
                    with open(conv_file, 'r') as f:
                        conversations = json.load(f)
                    
                    # Check that all conversations belong to this user
                    for conv_id, conv_data in conversations.items():
                        if conv_data.get("user_id") and conv_data["user_id"] != user_id:
                            issues.append(f"Conversation {conv_id} in user {user_id}'s directory belongs to user {conv_data['user_id']}")
                
                except Exception as e:
                    issues.append(f"Error reading conversations for user {user_id}: {e}")
    
    return len(issues) == 0, issues

def check_rag_isolation() -> Tuple[bool, List[str]]:
    """Check that RAG data is properly isolated per user and conversation."""
    issues = []
    users = load_users()
    
    for username, user_data in users.items():
        user_id = user_data["user_id"]
        rag_dir = os.path.join(USER_DATA_DIR, f"rag_{user_id}")
        
        if os.path.exists(rag_dir):
            # Check each conversation directory
            for item in os.listdir(rag_dir):
                if item.startswith("conversation_"):
                    conv_rag_dir = os.path.join(rag_dir, item)
                    metadata_file = os.path.join(conv_rag_dir, "documents_metadata.json")
                    
                    if os.path.exists(metadata_file):
                        try:
                            with open(metadata_file, 'r') as f:
                                metadata = json.load(f)
                            
                            # Check that all documents belong to the correct conversation
                            expected_conv_id = item.replace("conversation_", "")
                            for doc_hash, doc_data in metadata.items():
                                if doc_data.get("conversation_id") and doc_data["conversation_id"] != expected_conv_id:
                                    issues.append(f"Document {doc_hash} in conversation {expected_conv_id} belongs to conversation {doc_data['conversation_id']}")
                        
                        except Exception as e:
                            issues.append(f"Error reading RAG metadata for user {user_id}, conversation {item}: {e}")
    
    return len(issues) == 0, issues

def check_upload_tracking() -> Tuple[bool, List[str]]:
    """Check upload tracking data for consistency."""
    issues = []
    uploads_file = os.path.join(USER_DATA_DIR, "uploads.json")
    
    if os.path.exists(uploads_file):
        try:
            with open(uploads_file, 'r') as f:
                uploads = json.load(f)
            
            users = load_users()
            valid_user_ids = set()
            for username, user_data in users.items():
                valid_user_ids.add(user_data["user_id"])
            
            # Check that all upload records belong to valid users
            for user_id in uploads.keys():
                if user_id not in valid_user_ids:
                    issues.append(f"Upload tracking data exists for invalid user: {user_id}")
        
        except Exception as e:
            issues.append(f"Error reading upload tracking data: {e}")
    
    return len(issues) == 0, issues

def generate_privacy_report() -> Dict:
    """Generate comprehensive privacy report."""
    print("🔍 Generating Privacy Report...")
    print("=" * 50)
    
    report = {
        "timestamp": str(os.path.getctime(USER_DATA_DIR)) if os.path.exists(USER_DATA_DIR) else "N/A",
        "checks": {}
    }
    
    # Check 1: Directory ownership
    print("1. Checking directory ownership...")
    is_clean, orphaned = verify_directory_ownership()
    report["checks"]["directory_ownership"] = {
        "passed": is_clean,
        "issues": orphaned
    }
    
    if is_clean:
        print("   ✅ All directories belong to valid users")
    else:
        print(f"   ❌ Found {len(orphaned)} orphaned directories: {orphaned}")
    
    # Check 2: Conversation isolation
    print("2. Checking conversation isolation...")
    is_isolated, issues = check_conversation_isolation()
    report["checks"]["conversation_isolation"] = {
        "passed": is_isolated,
        "issues": issues
    }
    
    if is_isolated:
        print("   ✅ Conversations are properly isolated")
    else:
        print(f"   ❌ Found {len(issues)} conversation isolation issues")
        for issue in issues:
            print(f"      - {issue}")
    
    # Check 3: RAG data isolation
    print("3. Checking RAG data isolation...")
    is_rag_clean, rag_issues = check_rag_isolation()
    report["checks"]["rag_isolation"] = {
        "passed": is_rag_clean,
        "issues": rag_issues
    }
    
    if is_rag_clean:
        print("   ✅ RAG data is properly isolated")
    else:
        print(f"   ❌ Found {len(rag_issues)} RAG isolation issues")
        for issue in rag_issues:
            print(f"      - {issue}")
    
    # Check 4: Upload tracking
    print("4. Checking upload tracking consistency...")
    is_upload_clean, upload_issues = check_upload_tracking()
    report["checks"]["upload_tracking"] = {
        "passed": is_upload_clean,
        "issues": upload_issues
    }
    
    if is_upload_clean:
        print("   ✅ Upload tracking is consistent")
    else:
        print(f"   ❌ Found {len(upload_issues)} upload tracking issues")
        for issue in upload_issues:
            print(f"      - {issue}")
    
    # Overall status
    all_passed = all(check["passed"] for check in report["checks"].values())
    report["overall_status"] = "PASSED" if all_passed else "FAILED"
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 PRIVACY VERIFICATION PASSED")
        print("   All user data is properly isolated and secure!")
    else:
        print("⚠️  PRIVACY VERIFICATION FAILED")
        print("   Some issues were found that need attention.")
    
    return report

def cleanup_orphaned_data():
    """Clean up orphaned data directories."""
    print("🧹 Cleaning up orphaned data...")
    
    users = load_users()
    valid_user_ids = set()
    for username, user_data in users.items():
        valid_user_ids.add(user_data["user_id"])
    
    user_dirs = get_user_directories()
    cleaned = []
    
    for dir_name in user_dirs:
        if dir_name.startswith("conversations_"):
            user_id = dir_name.replace("conversations_", "")
        elif dir_name.startswith("rag_"):
            user_id = dir_name.replace("rag_", "")
        else:
            continue
        
        if user_id not in valid_user_ids:
            import shutil
            dir_path = os.path.join(USER_DATA_DIR, dir_name)
            try:
                shutil.rmtree(dir_path)
                cleaned.append(dir_name)
                print(f"   🗑️  Removed orphaned directory: {dir_name}")
            except Exception as e:
                print(f"   ❌ Failed to remove {dir_name}: {e}")
    
    if cleaned:
        print(f"✅ Cleaned up {len(cleaned)} orphaned directories")
    else:
        print("ℹ️  No orphaned directories found")
    
    return cleaned

def main():
    """Main function."""
    print("🔒 PharmBot Privacy Verification Tool")
    print("=" * 40)
    
    if not os.path.exists(USER_DATA_DIR):
        print("ℹ️  No user data directory found. Nothing to verify.")
        return
    
    while True:
        print("\nOptions:")
        print("1. Run full privacy verification")
        print("2. Clean up orphaned data")
        print("3. Show user statistics")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            report = generate_privacy_report()
            
            # Save report
            report_file = os.path.join(USER_DATA_DIR, "privacy_report.json")
            try:
                with open(report_file, 'w') as f:
                    json.dump(report, f, indent=2)
                print(f"\n📄 Report saved to: {report_file}")
            except Exception as e:
                print(f"❌ Failed to save report: {e}")
        
        elif choice == "2":
            confirm = input("Are you sure you want to clean up orphaned data? (y/N): ").strip().lower()
            if confirm == 'y':
                cleanup_orphaned_data()
            else:
                print("❌ Operation cancelled")
        
        elif choice == "3":
            users = load_users()
            user_dirs = get_user_directories()
            
            print(f"\n📊 User Statistics:")
            print(f"   Total users: {len(users)}")
            print(f"   User directories: {len(user_dirs)}")
            
            for username, user_data in users.items():
                user_id = user_data["user_id"]
                conv_dir = os.path.join(USER_DATA_DIR, f"conversations_{user_id}")
                rag_dir = os.path.join(USER_DATA_DIR, f"rag_{user_id}")
                
                conv_count = 0
                if os.path.exists(conv_dir):
                    conv_file = os.path.join(conv_dir, "conversations.json")
                    if os.path.exists(conv_file):
                        try:
                            with open(conv_file, 'r') as f:
                                conversations = json.load(f)
                            conv_count = len(conversations)
                        except:
                            pass
                
                rag_count = 0
                if os.path.exists(rag_dir):
                    rag_count = len([d for d in os.listdir(rag_dir) if d.startswith("conversation_")])
                
                print(f"   {username}: {conv_count} conversations, {rag_count} RAG collections")
        
        elif choice == "4":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()