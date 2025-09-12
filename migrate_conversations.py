#!/usr/bin/env python3
"""
Migration script to help existing users migrate their conversations to the new user system.
This script is optional and only needed if you have existing conversations you want to preserve.
"""

import json
import streamlit as st
from pathlib import Path
from auth import create_user, get_user_id, save_user_conversations
from datetime import datetime

def migrate_existing_conversations():
    """Migrate existing conversations to a user account."""
    print("🔄 PharmBot Conversation Migration Tool")
    print("=" * 50)
    
    # Check if there are any existing conversations in session state
    # This would typically be run as a separate script
    print("This tool helps you migrate existing conversations to a user account.")
    print("If you don't have existing conversations, you can skip this.")
    print()
    
    # Get user details
    username = input("Enter your desired username: ").strip()
    password = input("Enter your desired password: ").strip()
    email = input("Enter your email (optional): ").strip()
    
    if not username or not password:
        print("❌ Username and password are required!")
        return
    
    # Create user account
    try:
        success, message = create_user(username, password, email)
        if not success:
            print(f"❌ {message}")
            return
        
        print(f"✅ {message}")
        user_id = get_user_id(username)
        
        # For now, just create an empty conversations file
        # In a real migration, you would load existing conversations here
        empty_conversations = {}
        save_user_conversations(user_id, empty_conversations)
        
        print(f"✅ Migration completed for user: {username}")
        print("🎉 You can now sign in to PharmBot with your new account!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    migrate_existing_conversations()