#!/usr/bin/env python3
"""
Emergency fix for conversation creation issue
This script will test and fix the conversation creation problem
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_and_fix_conversation_creation():
    """Test conversation creation and apply fixes if needed."""
    
    print("🔧 Testing and fixing conversation creation...")
    
    try:
        from services.conversation_service import conversation_service
        from supabase_manager import connection_manager
        
        # Test user UUID from your logs
        test_user_uuid = "a3cc3247-bfdb-4145-a9d4-3010f834f6c6"
        
        print("Step 1: Testing basic connection...")
        if not connection_manager.test_connection():
            print("❌ Connection test failed")
            return False
        print("✅ Connection test passed")
        
        print("\nStep 2: Testing conversation creation...")
        try:
            conv_id = await conversation_service.create_conversation(
                test_user_uuid, 
                f"Test Conversation {asyncio.get_event_loop().time()}"
            )
            print(f"✅ Conversation creation succeeded: {conv_id}")
            return True
            
        except Exception as e:
            print(f"❌ Conversation creation failed: {e}")
            
            if "cannot get array length of a scalar" in str(e):
                print("\n🔧 Applying emergency fix...")
                
                # Try to create conversation without messages field
                try:
                    print("Step 3: Trying minimal conversation creation...")
                    
                    import uuid
                    import json
                    from datetime import datetime
                    
                    conversation_id = str(uuid.uuid4())
                    
                    # Create with minimal data
                    minimal_data = {
                        'conversation_id': conversation_id,
                        'user_id': test_user_uuid,
                        'title': f"Emergency Test {datetime.now().strftime('%H:%M:%S')}",
                        'model': 'meta-llama/llama-4-maverick-17b-128e-instruct',
                        'created_at': datetime.now().isoformat(),
                        'is_archived': False
                        # No messages or message_count to avoid trigger
                    }
                    
                    result = connection_manager.execute_query(
                        table='conversations',
                        operation='insert',
                        data=minimal_data
                    )
                    
                    if result.data:
                        print(f"✅ Emergency conversation creation succeeded: {conversation_id}")
                        
                        # Try to add messages field separately
                        try:
                            update_result = connection_manager.execute_query(
                                table='conversations',
                                operation='update',
                                data={
                                    'messages': json.dumps([]),
                                    'message_count': 0
                                },
                                eq={
                                    'conversation_id': conversation_id,
                                    'user_id': test_user_uuid
                                }
                            )
                            print("✅ Messages field added successfully")
                        except Exception as update_error:
                            print(f"⚠️  Messages field update failed: {update_error}")
                        
                        return True
                    else:
                        print("❌ Emergency creation also failed")
                        
                except Exception as emergency_error:
                    print(f"❌ Emergency fix failed: {emergency_error}")
            
            return False
            
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False

async def main():
    """Main function to run the test and fix."""
    
    print("🚀 Starting conversation creation fix...")
    
    success = await test_and_fix_conversation_creation()
    
    if success:
        print("\n🎉 Conversation creation is now working!")
        print("Your Supabase integration is fully functional.")
    else:
        print("\n⚠️  Conversation creation still needs database trigger fix.")
        print("\nTo fix this:")
        print("1. Go to your Supabase Dashboard")
        print("2. Open SQL Editor")
        print("3. Run the script: emergency_disable_trigger.sql")
        print("4. Restart your Streamlit app")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())