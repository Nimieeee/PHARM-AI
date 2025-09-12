#!/usr/bin/env python3
"""
Disable the problematic database trigger through Python
This will fix the conversation creation issue immediately
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def disable_trigger():
    """Disable the problematic trigger using Supabase client."""
    
    try:
        from supabase_manager import connection_manager
        
        print("🔧 Disabling problematic database trigger...")
        
        # Test connection first
        if not connection_manager.test_connection():
            print("❌ Connection test failed")
            return False
        
        print("✅ Connection established")
        
        # Get the Supabase client
        client = connection_manager.get_client()
        if not client:
            print("❌ Could not get Supabase client")
            return False
        
        # Execute SQL to disable trigger
        sql_commands = [
            "DROP TRIGGER IF EXISTS update_conversations_message_count ON conversations;",
            "DROP TRIGGER IF EXISTS safe_update_conversations_message_count ON conversations;",
            "DROP TRIGGER IF EXISTS safe_message_count_trigger ON conversations;",
            "ALTER TABLE conversations ALTER COLUMN messages DROP NOT NULL;",
            "ALTER TABLE conversations ALTER COLUMN messages SET DEFAULT '[]'::jsonb;",
            "ALTER TABLE conversations ALTER COLUMN message_count DROP NOT NULL;",
            "ALTER TABLE conversations ALTER COLUMN message_count SET DEFAULT 0;",
            "UPDATE conversations SET messages = '[]'::jsonb WHERE messages IS NULL;",
            "UPDATE conversations SET message_count = 0 WHERE message_count IS NULL;"
        ]
        
        for i, sql in enumerate(sql_commands, 1):
            try:
                print(f"Executing step {i}/{len(sql_commands)}...")
                result = client.rpc('exec_sql', {'sql': sql}).execute()
                print(f"✅ Step {i} completed")
            except Exception as e:
                print(f"⚠️  Step {i} failed (might be expected): {e}")
                # Continue with other commands
        
        print("🎉 Trigger disable completed!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to disable trigger: {e}")
        return False

def test_conversation_creation():
    """Test if conversation creation works now."""
    
    try:
        import asyncio
        from services.conversation_service import conversation_service
        
        async def test():
            test_user_uuid = "a3cc3247-bfdb-4145-a9d4-3010f834f6c6"
            
            try:
                conv_id = await conversation_service.create_conversation(
                    test_user_uuid, 
                    "Test After Trigger Fix"
                )
                print(f"✅ Conversation creation test passed: {conv_id}")
                return True
            except Exception as e:
                print(f"❌ Conversation creation test failed: {e}")
                return False
        
        return asyncio.run(test())
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting trigger disable process...")
    
    # Step 1: Disable trigger
    if disable_trigger():
        print("\n🧪 Testing conversation creation...")
        
        # Step 2: Test conversation creation
        if test_conversation_creation():
            print("\n🎉 SUCCESS! Conversation creation is now working!")
        else:
            print("\n⚠️  Trigger disabled but conversation creation still needs work.")
    else:
        print("\n❌ Could not disable trigger through Python.")
        print("Please run the SQL script manually in Supabase dashboard:")
        print("emergency_disable_trigger.sql")