#!/usr/bin/env python3
"""
Test script for Supabase integration
Run this to verify that your Supabase setup is working correctly.
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from supabase_manager import get_supabase_client, test_supabase_connection
from services.user_service import UserService

def test_connection():
    """Test basic Supabase connection."""
    print("🔗 Testing Supabase connection...")
    
    client = get_supabase_client()
    if not client:
        print("❌ Failed to get Supabase client")
        return False
    
    if test_supabase_connection():
        print("✅ Supabase connection successful")
        return True
    else:
        print("❌ Supabase connection failed")
        return False

def test_user_service():
    """Test user service operations."""
    print("\n👤 Testing User Service...")
    
    user_service = UserService()
    
    # Test user creation
    test_username = f"testuser_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_password = "testpass123"
    test_email = f"{test_username}@example.com"
    
    print(f"Creating test user: {test_username}")
    success, message = user_service.create_user(test_username, test_password, test_email)
    
    if success:
        print("✅ User creation successful")
        
        # Test authentication
        print("Testing authentication...")
        auth_success, auth_message, user_data = user_service.authenticate_user(test_username, test_password)
        
        if auth_success:
            print("✅ User authentication successful")
            print(f"User data: {user_data['username']} (ID: {user_data['user_id']})")
            
            # Test getting user by username
            print("Testing get user by username...")
            retrieved_user = user_service.get_user_by_username(test_username)
            if retrieved_user:
                print("✅ Get user by username successful")
            else:
                print("❌ Get user by username failed")
            
            # Test getting user by ID
            print("Testing get user by ID...")
            retrieved_user_by_id = user_service.get_user_by_id(user_data['user_id'])
            if retrieved_user_by_id:
                print("✅ Get user by ID successful")
            else:
                print("❌ Get user by ID failed")
            
            return True
        else:
            print(f"❌ User authentication failed: {auth_message}")
            return False
    else:
        print(f"❌ User creation failed: {message}")
        return False

def test_database_tables():
    """Test that all required tables exist and are accessible."""
    print("\n🗄️  Testing database tables...")
    
    client = get_supabase_client()
    if not client:
        print("❌ No Supabase client available")
        return False
    
    tables = ['users', 'sessions', 'conversations', 'messages', 'documents']
    
    for table in tables:
        try:
            result = client.table(table).select('count').limit(1).execute()
            print(f"✅ Table '{table}' is accessible")
        except Exception as e:
            print(f"❌ Table '{table}' failed: {e}")
            return False
    
    # Test the user_stats view
    try:
        result = client.table('user_stats').select('*').limit(1).execute()
        print("✅ View 'user_stats' is accessible")
    except Exception as e:
        print(f"❌ View 'user_stats' failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("🧪 PharmGPT Supabase Integration Test")
    print("=" * 40)
    
    # Test connection
    if not test_connection():
        print("\n❌ Connection test failed. Please check your Supabase configuration.")
        sys.exit(1)
    
    # Test database tables
    if not test_database_tables():
        print("\n❌ Database table test failed. Please run setup_supabase.py first.")
        sys.exit(1)
    
    # Test user service
    if not test_user_service():
        print("\n❌ User service test failed.")
        sys.exit(1)
    
    print("\n🎉 All tests passed!")
    print("Your Supabase integration is working correctly.")

if __name__ == "__main__":
    main()