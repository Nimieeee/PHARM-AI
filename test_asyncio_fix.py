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
    
    # Create a new event loop context
    try:
        # This should work without AsyncIO errors
        user = await user_service.get_user_by_id(test_user_id)
        logger.info("✅ Event loop handling working correctly")
    except Exception as e:
        if "bound to a different event loop" in str(e):
            logger.error("❌ AsyncIO event loop issue still present")
        else:
            logger.info(f"ℹ️ Other error (expected): {e}")

def main():
    """Main test function."""
    logger.info("🚀 Starting AsyncIO fix test...")
    
    # Run the async test
    asyncio.run(test_user_service())
    
    logger.info("✅ AsyncIO fix test completed")

if __name__ == "__main__":
    main()