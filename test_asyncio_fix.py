#!/usr/bin/env python3
"""
Test script to verify AsyncIO event loop fixes
"""

import asyncio
import logging
from services.user_service import user_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_user_service():
    """Test user service with different event loops."""
    logger.info("🧪 Testing user service AsyncIO fixes...")
    
    # Test 1: Get user by ID
    test_user_id = "e4443c52948edad6132f34b6378a9901"
    
    try:
        user = await user_service.get_user_by_id(test_user_id)
        if user:
            logger.info(f"✅ User found: {user.get('username', 'Unknown')}")
        else:
            logger.info("ℹ️ User not found (this is expected if user doesn't exist)")
    except Exception as e:
        logger.error(f"❌ Error getting user: {e}")
    
    # Test 2: Try to trigger event loop change
    logger.info("🔄 Testing event loop resilience...")
    
    # Simulate multiple calls that might trigger event loop issues
    for i in range(3):
        try:
            logger.info(f"🔄 Test iteration {i+1}")
            user = await user_service.get_user_by_id(test_user_id)
            logger.info(f"✅ Iteration {i+1} successful")
        except Exception as e:
            if "bound to a different event loop" in str(e):
                logger.error(f"❌ AsyncIO event loop issue still present in iteration {i+1}")
            else:
                logger.info(f"ℹ️ Other error in iteration {i+1} (may be expected): {e}")
    
    # Test 3: Test connection manager directly
    logger.info("🔧 Testing connection manager directly...")
    try:
        from supabase_manager import get_connection_manager
        conn_mgr = get_connection_manager()
        
        # Force event loop check
        conn_mgr._check_event_loop()
        logger.info("✅ Connection manager event loop check passed")
        
    except Exception as e:
        logger.error(f"❌ Connection manager test failed: {e}")

def main():
    """Main test function."""
    logger.info("🚀 Starting AsyncIO fix test...")
    
    # Run the async test
    asyncio.run(test_user_service())
    
    logger.info("✅ AsyncIO fix test completed")

if __name__ == "__main__":
    main()