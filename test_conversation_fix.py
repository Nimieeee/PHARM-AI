#!/usr/bin/env python3
"""
Test conversation creation after applying the database trigger fix
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_conversation_creation():
    """Test conversation creation with different approaches."""
    
    try:
        from services.conversation_service import conversation_service
        
        print("Testing conversation creation...")
        
        # Test user UUID (from your logs)
        test_user_uuid = "a3cc3247-bfdb-4145-a9d4-3010f834f6c6"
        
        # Test 1: Try main conversation creation
        try:
            conv_id = await conversation_service.create_conversation(
                test_user_uuid, 
                "Test Conversation - Main Method"
            )
            print(f"✅ Main conversation creation succeeded: {conv_id}")
            return True
        except Exception as e:
            print(f"❌ Main conversation creation failed: {e}")
        
        # Test 2: Try fallback method if it exists
        try:
            if hasattr(conversation_service, 'create_conversation_simple'):
                conv_id = await conversation_service.create_conversation_simple(
                    test_user_uuid, 
                    "Test Conversation - Fallback Method"
                )
                print(f"✅ Fallback conversation creation succeeded: {conv_id}")
                return True
            else:
                print("⚠️  Fallback method not available")
        except Exception as e:
            print(f"❌ Fallback conversation creation failed: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing conversation creation fixes...")
    success = asyncio.run(test_conversation_creation())
    
    if success:
        print("\n🎉 Conversation creation is working!")
    else:
        print("\n⚠️  Conversation creation still needs the database trigger fix.")
        print("Please run the SQL script: immediate_trigger_fix.sql")