#!/usr/bin/env python3
"""
Simple script to manually toggle testing mode on/off
Useful if you need to run manual tests or if automated tests fail to cleanup
"""

import os
import asyncio
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def toggle_testing_mode(enable: bool):
    """Enable or disable testing mode."""
    
    try:
        from supabase import create_async_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            print("❌ Missing Supabase credentials")
            return False
        
        client = await create_async_client(supabase_url, supabase_key)
        
        if enable:
            await client.rpc('enable_testing_mode').execute()
            print("✅ Testing mode ENABLED - RLS policies bypassed")
            print("⚠️  Remember to disable testing mode when done!")
        else:
            await client.rpc('disable_testing_mode').execute()
            print("✅ Testing mode DISABLED - RLS policies active")
            print("🔒 Database is now secure for production use")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to toggle testing mode: {e}")
        return False

async def main():
    """Main function to handle command line arguments."""
    
    if len(sys.argv) != 2 or sys.argv[1] not in ['on', 'off']:
        print("Usage:")
        print("  python toggle_testing_mode.py on   # Enable testing mode")
        print("  python toggle_testing_mode.py off  # Disable testing mode")
        sys.exit(1)
    
    enable = sys.argv[1] == 'on'
    
    print("🔧 PharmGPT Testing Mode Toggle")
    print("=" * 40)
    
    success = await toggle_testing_mode(enable)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())