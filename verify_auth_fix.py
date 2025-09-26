#!/usr/bin/env python3
"""
Final verification that the authentication fix is working
"""

import os
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_auth_fix():
    """Verify that the authentication fix is working"""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")

        if not supabase_url or not supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_ANON_KEY environment variables")

        # Import supabase inside the function to handle import errors gracefully
        try:
            from supabase import create_client
        except ImportError as e:
            logger.error(f"Supabase library not available: {e}")
            logger.info("Please install supabase: pip install supabase")
            return False

        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)

        # Test 1: Database connection
        logger.info("Testing database connection...")
        result = supabase.table('users').select('count').limit(1).execute()
        logger.info(f"✅ Database connection successful")

        # Test 2: Create a test user
        logger.info("Testing user creation...")
        test_username = "test_user_fix_verification"
        test_password = "test_password_123"
        test_email = "test@example.com"

        # Try to create a user
        try:
            result = supabase.rpc('create_user_account', {
                'p_username': test_username,
                'p_password': test_password,
                'p_email': test_email
            }).execute()
            
            if result.data and len(result.data) > 0:
                user_data = result.data[0]
                if user_data.get('success'):
                    logger.info("✅ User creation successful")
                    user_id = user_data.get('user_id')
                else:
                    # Check if it's a "user already exists" error (which is OK)
                    if "already exists" in user_data.get('message', ''):
                        logger.info("✅ User already exists (which is OK)")
                        # Get the user ID for authentication test
                        user_result = supabase.table('users').select('id').eq('username', test_username).execute()
                        if user_result.data and len(user_result.data) > 0:
                            user_id = user_result.data[0]['id']
                        else:
                            raise Exception("Could not find user")
                    else:
                        raise Exception(f"User creation failed: {user_data.get('message')}")
            else:
                raise Exception("Unexpected response from create_user_account")
                
        except Exception as e:
            if "already exists" in str(e):
                logger.info("✅ User already exists (which is OK)")
                # Get the user ID for authentication test
                user_result = supabase.table('users').select('id').eq('username', test_username).execute()
                if user_result.data and len(user_result.data) > 0:
                    user_id = user_result.data[0]['id']
                else:
                    raise Exception("Could not find user")
            else:
                raise e
        
        # Test 3: Authenticate the user
        logger.info("Testing user authentication...")
        auth_result = supabase.rpc('authenticate_user', {
            'p_username': test_username,
            'p_password': test_password
        }).execute()
        
        if auth_result.data and len(auth_result.data) > 0:
            auth_data = auth_result.data[0]
            if auth_data.get('success'):
                logger.info("✅ User authentication successful")
                logger.info(f"   User ID: {auth_data.get('user_id')}")
                logger.info(f"   Username: {auth_data.get('username')}")
                logger.info(f"   Display Name: {auth_data.get('display_name')}")
            else:
                raise Exception(f"Authentication failed: {auth_data.get('message')}")
        else:
            raise Exception("Unexpected response from authenticate_user")
        
        logger.info("🎉 All authentication tests passed!")
        logger.info("✅ The authentication fix is working correctly!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Authentication verification failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(verify_auth_fix())
    exit(0 if result else 1)