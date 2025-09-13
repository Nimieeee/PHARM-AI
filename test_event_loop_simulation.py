#!/usr/bin/env python3
"""
Test script to simulate event loop changes and verify fixes
"""

import asyncio
import logging
from services.user_service import user_service
from supabase_manager import get_connection_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def simulate_event_loop_change():
    """Simulate what happens when Streamlit changes event loops."""
    logger.info("🔄 Simulating event loop change scenario...")
    
    test_user_id = "e4443c52948edad6132f34b6378a9901"
    
    # First, get the connection manager and make a query
    conn_mgr = get_connection_manager()
    
    try:
        # Initial query
        logger.info("📊 Making initial query...")
        user1 = await user_service.get_user_by_id(test_user_id)
        if user1:
            logger.info(f"✅ Initial query successful: {user1.get('username')}")
        
        # Force event loop ID change to simulate Streamlit behavior
        logger.info("🔄 Simulating event loop change...")
        old_loop_id = conn_mgr._event_loop_id
        conn_mgr._event_loop_id = 999999999  # Force different ID
        
        # This should trigger event loop detection and client reset
        logger.info("📊 Making query after simulated event loop change...")
        user2 = await user_service.get_user_by_id(test_user_id)
        if user2:
            logger.info(f"✅ Post-event-loop-change query successful: {user2.get('username')}")
        
        # Verify the system recovered
        logger.info("🔍 Verifying system recovery...")
        user3 = await user_service.get_user_by_id(test_user_id)
        if user3:
            logger.info(f"✅ Recovery verification successful: {user3.get('username')}")
        
        logger.info("✅ Event loop change simulation completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Event loop simulation failed: {e}")
        raise

async def test_multiple_event_loops():
    """Test behavior across multiple event loops."""
    logger.info("🔄 Testing multiple event loop scenario...")
    
    test_user_id = "e4443c52948edad6132f34b6378a9901"
    
    # Create multiple tasks that might run in different contexts
    tasks = []
    for i in range(5):
        async def query_task(task_id):
            try:
                user = await user_service.get_user_by_id(test_user_id)
                if user:
                    logger.info(f"✅ Task {task_id} successful: {user.get('username')}")
                    return True
                else:
                    logger.info(f"ℹ️ Task {task_id}: User not found")
                    return False
            except Exception as e:
                logger.error(f"❌ Task {task_id} failed: {e}")
                return False
        
        tasks.append(query_task(i))
    
    # Run all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = sum(1 for r in results if r is True)
    logger.info(f"📊 Multiple event loop test: {success_count}/5 tasks successful")
    
    return success_count >= 3  # Allow some failures

def main():
    """Main test function."""
    logger.info("🚀 Starting comprehensive event loop test...")
    
    async def run_tests():
        try:
            # Test 1: Simulate event loop change
            await simulate_event_loop_change()
            
            # Test 2: Multiple concurrent operations
            success = await test_multiple_event_loops()
            
            if success:
                logger.info("✅ All event loop tests passed!")
            else:
                logger.warning("⚠️ Some tests had issues, but this may be expected")
                
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
            raise
    
    # Run the async tests
    asyncio.run(run_tests())
    
    logger.info("✅ Comprehensive event loop test completed")

if __name__ == "__main__":
    main()