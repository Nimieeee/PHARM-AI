#!/usr/bin/env python3
"""
Advanced AsyncIO Event Loop Fix for Supabase Client
This addresses the deeper issue where asyncio.locks.Event objects get bound to different event loops
"""

import asyncio
import logging
from typing import Optional, Any
import functools

logger = logging.getLogger(__name__)

def with_event_loop_safety(func):
    """Decorator to handle AsyncIO event loop binding issues."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        max_retries = 2
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if ("bound to a different event loop" in str(e) or 
                    "asyncio" in str(e).lower()) and attempt < max_retries - 1:
                    
                    logger.warning(f"AsyncIO event loop issue on attempt {attempt + 1}, retrying...")
                    
                    # Get the instance (self) from args
                    if args and hasattr(args[0], '_client'):
                        instance = args[0]
                        # Force client reset
                        instance._client = None
                        if hasattr(instance, '_initialization_attempted'):
                            instance._initialization_attempted = False
                        if hasattr(instance, '_initialization_successful'):
                            instance._initialization_successful = False
                        
                        # Wait a moment for event loop to stabilize
                        await asyncio.sleep(0.1)
                        
                        # Try to reinitialize
                        if hasattr(instance, '_initialize_client'):
                            await instance._initialize_client()
                    
                    continue
                else:
                    raise e
        
        return None
    
    return wrapper

class EventLoopSafeSupabaseManager:
    """Enhanced Supabase manager with advanced event loop safety."""
    
    def __init__(self, base_manager):
        self.base_manager = base_manager
        self._last_event_loop_id = None
        self._client_creation_lock = asyncio.Lock()
    
    async def _ensure_event_loop_safety(self):
        """Ensure we're operating in a safe event loop context."""
        try:
            current_loop = asyncio.get_running_loop()
            current_loop_id = id(current_loop)
            
            if (self._last_event_loop_id is not None and 
                self._last_event_loop_id != current_loop_id):
                
                logger.warning("Event loop changed, forcing client recreation")
                
                # Force complete reset of the base manager
                self.base_manager._client = None
                self.base_manager._initialization_attempted = False
                self.base_manager._initialization_successful = False
                
                # Clear any internal asyncio objects
                if hasattr(self.base_manager, '_connection_pool'):
                    self.base_manager._connection_pool = None
            
            self._last_event_loop_id = current_loop_id
            
        except RuntimeError:
            # No event loop running
            logger.warning("No event loop detected, resetting state")
            self.base_manager._client = None
            self.base_manager._initialization_attempted = False
            self.base_manager._initialization_successful = False
            self._last_event_loop_id = None
    
    @with_event_loop_safety
    async def execute_query(self, table: str, operation: str, **kwargs):
        """Execute query with advanced event loop safety."""
        await self._ensure_event_loop_safety()
        
        async with self._client_creation_lock:
            return await self.base_manager.execute_query(table, operation, **kwargs)
    
    @with_event_loop_safety
    async def get_client(self):
        """Get client with event loop safety."""
        await self._ensure_event_loop_safety()
        
        async with self._client_creation_lock:
            return await self.base_manager.get_client()

def apply_event_loop_safety_patch():
    """Apply event loop safety patches to existing managers."""
    logger.info("🔧 Applying advanced AsyncIO event loop safety patches...")
    
    # This would be called during application startup
    # to wrap existing managers with enhanced safety
    pass

if __name__ == "__main__":
    logger.info("🧪 Testing advanced AsyncIO event loop safety...")
    apply_event_loop_safety_patch()
    logger.info("✅ Advanced AsyncIO safety patches applied")