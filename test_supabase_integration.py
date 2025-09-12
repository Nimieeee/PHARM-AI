#!/usr/bin/env python3
"""
Test script to verify Supabase integration is working properly
Run this to test all core functionality
"""

import asyncio
import streamlit as st
from services.user_service import user_service
from services.session_service import session_service
from services.conversation_service import conversation_service
from services.document_service import document_service

async def test_user_operations():
    """Test user creation and authentication"""
    print("🧪 Testing User Operations...")
    
    # Test user creation
    success, message = await user_service.create_user("testuser123", "testpass123", "test@example.com")
    print(f"  User creation: {'✅' if success else '❌'} {message}")
    
    # Test authentication
    success, message, user_data = await user_service.authenticate_user("testuser123", "testpass123")
    print(f"  Authentication: {'✅' if success else '❌'} {message}")
    
    return user_data

async def test_session_operations(user_data):
    """Test session management"""
    print("🧪 Testing Session Operations...")
    
    if not user_data:
        print("  ❌ Skipping session tests - no user data")
        return None
    
    # Test session creation
    session_data = await session_service.create_session(user_data['id'], user_data['username'])
    print(f"  Session creation: {'✅' if session_data else '❌'}")
    
    if session_data:
        # Test session validation
        is_valid = await session_service.validate_session(session_data['session_id'])
        print(f"  Session validation: {'✅' if is_valid else '❌'}")
    
    return session_data

async def test_conversation_operations(user_data):
    """Test conversation management"""
    print("🧪 Testing Conversation Operations...")
    
    if not user_data:
        print("  ❌ Skipping conversation tests - no user data")
        return
    
    # Test conversation creation
    conv_id = await conversation_service.create_conversation(
        user_data['id'], 
        "Test Conversation",
        "gpt-3.5-turbo"
    )
    print(f"  Conversation creation: {'✅' if conv_id else '❌'}")
    
    if conv_id:
        # Test adding messages
        success = await conversation_service.add_message(
            conv_id,
            {"role": "user", "content": "Hello, this is a test message"}
        )
        print(f"  Add message: {'✅' if success else '❌'}")
        
        # Test loading conversation
        conversation = await conversation_service.get_conversation(conv_id)
        print(f"  Load conversation: {'✅' if conversation else '❌'}")

async def test_document_operations(user_data):
    """Test document metadata operations"""
    print("🧪 Testing Document Operations...")
    
    if not user_data:
        print("  ❌ Skipping document tests - no user data")
        return
    
    # Test document metadata creation
    doc_id = await document_service.add_document(
        user_data['id'],
        "test_conversation_id",
        "test_document.pdf",
        "application/pdf",
        1024,
        5,
        "test_hash_123"
    )
    print(f"  Document creation: {'✅' if doc_id else '❌'}")

async def main():
    """Run all tests"""
    print("🚀 Starting Supabase Integration Tests...\n")
    
    try:
        # Test user operations
        user_data = await test_user_operations()
        print()
        
        # Test session operations
        session_data = await test_session_operations(user_data)
        print()
        
        # Test conversation operations
        await test_conversation_operations(user_data)
        print()
        
        # Test document operations
        await test_document_operations(user_data)
        print()
        
        print("✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    # This script needs to be run in a Streamlit context
    print("To run this test, use: streamlit run test_supabase_integration.py")
    print("Or run individual tests in your Streamlit app")