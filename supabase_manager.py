"""
Supabase Connection Manager for PharmGPT
Handles all database connections, pooling, and error management
"""

import os
import time
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from supabase import create_async_client, AsyncClient
    from postgrest.exceptions import APIError
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.error("Supabase async not available. Install with: pip install supabase")
    AsyncClient = type("AsyncClient", (), {})


def validate_order_clause(order_clause: str) -> str:
    """Validate and fix order clause format."""
    if not order_clause:
        return 'created_at.desc'

    original_clause = order_clause

    # Remove any duplicate direction specifiers
    if '.desc.asc' in order_clause:
        order_clause = order_clause.replace('.desc.asc', '.desc')
        logger.warning(f"Fixed malformed order clause: {original_clause} -> {order_clause}")
    elif '.asc.desc' in order_clause:
        order_clause = order_clause.replace('.asc.desc', '.asc')
        logger.warning(f"Fixed malformed order clause: {original_clause} -> {order_clause}")
    elif '.desc.desc' in order_clause:
        order_clause = order_clause.replace('.desc.desc', '.desc')
        logger.warning(f"Fixed malformed order clause: {original_clause} -> {order_clause}")
    elif '.asc.asc' in order_clause:
        order_clause = order_clause.replace('.asc.asc', '.asc')
        logger.warning(f"Fixed malformed order clause: {original_clause} -> {order_clause}")

    # Ensure proper format
    if '.' not in order_clause:
        order_clause = f"{order_clause}.desc"

    return order_clause


class SupabaseConnectionManager:
    """Manages Supabase database connections with pooling and error handling."""

    _instance = None
    _client: Optional[AsyncClient] = None
    _initialization_attempted = False
    _initialization_successful = False
    _connection_stats = {
        'total_queries': 0,
        'successful_queries': 0,
        'failed_queries': 0,
        'avg_response_time': 0.0,
        'last_connection_test': None,
        'connection_errors': []
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseConnectionManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._event_loop_id = None
            # Don't initialize client here - do it lazily

    def _check_event_loop(self):
        """Check if we're in a different event loop and reset if needed."""
        try:
            current_loop = asyncio.get_running_loop()
            current_loop_id = id(current_loop)
            
            if self._event_loop_id is not None and self._event_loop_id != current_loop_id:
                logger.warning(f"Event loop changed in connection manager (old: {self._event_loop_id}, new: {current_loop_id}), resetting client")
                # Force complete reset
                self._client = None
                self._initialization_attempted = False
                self._initialization_successful = False
                # Clear any cached connection state
                if hasattr(self, '_connection_pool'):
                    self._connection_pool = None
            
            self._event_loop_id = current_loop_id
        except RuntimeError:
            # No event loop running, reset everything to be safe
            if self._event_loop_id is not None:
                logger.warning("No event loop running, resetting client state")
                self._client = None
                self._initialization_attempted = False
                self._initialization_successful = False
                self._event_loop_id = None

    async def _initialize_client(self) -> bool:
        """Initialize Supabase client with error handling."""
        logger.info("🚀 SUPABASE._INITIALIZE_CLIENT called")
        
        # Check for event loop changes
        self._check_event_loop()

        if not SUPABASE_AVAILABLE:
            logger.error("❌ Supabase library not available")
            return False

        try:
            # Get credentials from Streamlit secrets or environment variables
            if 'STREAMLIT_CLOUD' in os.environ or '.streamlit.app' in os.environ.get('HOSTNAME', ''):
                supabase_url = st.secrets.get("SUPABASE_URL")
                supabase_key = st.secrets.get("SUPABASE_ANON_KEY")
            else:
                from dotenv import load_dotenv
                load_dotenv()
                supabase_url = os.environ.get("SUPABASE_URL")
                supabase_key = os.environ.get("SUPABASE_ANON_KEY")
                logger.info(f"Loaded from .env: URL found: {bool(supabase_url)}, Key found: {bool(supabase_key)}")

            if not supabase_url or not supabase_key:
                logger.error("❌ Supabase credentials not found")
                st.error("❌ Supabase credentials not configured. Please set SUPABASE_URL and SUPABASE_ANON_KEY.")
                return False

            # Create client with connection pooling
            logger.info("🔧 Creating Supabase client")
            try:
                self._client = await create_async_client(supabase_url, supabase_key)
            except Exception as client_error:
                if "bound to a different event loop" in str(client_error):
                    logger.warning("AsyncIO issue during client creation, retrying...")
                    # Wait a moment and try again
                    await asyncio.sleep(0.1)
                    self._client = await create_async_client(supabase_url, supabase_key)
                else:
                    raise client_error

            # Test connection
            logger.info("🧪 Testing connection during initialization")
            if await self.test_connection():
                logger.info("✅ Supabase client initialized successfully")
                return True
            else:
                logger.error("❌ Supabase connection test failed")
                return False

        except Exception as e:
            logger.error(f"💥 Failed to initialize Supabase client: {e}")
            st.error(f"❌ Failed to connect to Supabase: {str(e)}")
            return False

    async def get_client(self) -> Optional[AsyncClient]:
        """Get Supabase client instance with smart caching."""
        logger.info(f"🔍 SUPABASE.GET_CLIENT called - client exists: {self._client is not None}, init_attempted: {self._initialization_attempted}")

        # Check for event loop changes first
        self._check_event_loop()

        # Initialize if needed (including after event loop changes)
        if self._client is None:
            if not self._initialization_attempted:
                logger.info("🚀 First initialization attempt...")
            else:
                logger.info("🔄 Reinitializing client (likely due to event loop change)...")
            
            self._initialization_attempted = True
            success = await self._initialize_client()
            self._initialization_successful = success

        return self._client

    async def test_connection(self) -> bool:
        """Test database connection health."""
        logger.info("🧪 SUPABASE.TEST_CONNECTION called")

        if not self._client:
            logger.warning("❌ No client available for connection test")
            return False

        try:
            start_time = time.time()

            # Simple query to test connection
            logger.info("📊 Executing connection test query")
            result = await self._client.table('users').select('count').limit(1).execute()

            response_time = time.time() - start_time
            self._connection_stats['last_connection_test'] = datetime.now()
            self._connection_stats['avg_response_time'] = response_time

            logger.info(f"✅ Connection test successful ({response_time:.3f}s)")
            return True

        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            self._connection_stats['connection_errors'].append({
                'timestamp': datetime.now(),
                'error': str(e)
            })
            return False

    async def set_user_context(self, user_id: str) -> bool:
        """Set user context for RLS policies."""
        try:
            if self._client:
                # Use the custom set_user_context function defined in the database
                await self._client.rpc('set_user_context', {
                    'user_identifier': user_id
                }).execute()
                logger.info(f"User context set for RLS: {user_id}")
                return True
        except Exception as e:
            # This is optional functionality - don't fail if the function doesn't exist
            if "PGRST202" in str(e) or "not found" in str(e).lower():
                logger.info(f"RLS context function not available (this is optional): {e}")
            else:
                logger.warning(f"Failed to set user context: {e}")
        return False

    async def execute_query(self, table: str, operation: str, **kwargs) -> Any:
        """Execute database query with error handling and stats tracking."""
        # Check event loop before executing query
        self._check_event_loop()
        
        # Ensure client is available (this will initialize if needed)
        client = await self.get_client()
        if not client:
            raise ConnectionError("Supabase client not initialized")

        start_time = time.time()
        self._connection_stats['total_queries'] += 1

        try:
            # Get table reference
            table_ref = client.table(table)

            # Execute operation based on type
            if operation == 'select':
                columns = kwargs.get('columns', '*')
                result = table_ref.select(columns)

                # Apply filters
                if 'eq' in kwargs:
                    for column, value in kwargs['eq'].items():
                        result = result.eq(column, value)

                if 'limit' in kwargs:
                    result = result.limit(kwargs['limit'])

                if 'order' in kwargs:
                    order_param = kwargs['order']
                    logger.info(f"Original order parameter: '{order_param}'")

                    # Parse column and direction
                    if '.' in str(order_param):
                        column, direction = str(order_param).rsplit('.', 1)
                        # Ensure only valid directions
                        if direction not in ['asc', 'desc']:
                            direction = 'desc'
                    else:
                        column = str(order_param)
                        direction = 'desc'

                    # Reconstruct clean order
                    clean_order = f"{column}.{direction}"
                    logger.info(f"Clean order clause: '{clean_order}'")

                    # Use the order method with explicit column and direction
                    result = result.order(column, desc=(direction == 'desc'))

                return await result.execute()

            elif operation == 'insert':
                data = kwargs.get('data', {})
                return await table_ref.insert(data).execute()

            elif operation == 'update':
                data = kwargs.get('data', {})
                result = table_ref.update(data)

                if 'eq' in kwargs:
                    for column, value in kwargs['eq'].items():
                        result = result.eq(column, value)

                return await result.execute()

            elif operation == 'delete':
                result = table_ref.delete()

                if 'eq' in kwargs:
                    for column, value in kwargs['eq'].items():
                        result = result.eq(column, value)

                return await result.execute()

            elif operation == 'upsert':
                data = kwargs.get('data', {})
                return await table_ref.upsert(data).execute()

            else:
                raise ValueError(f"Unsupported operation: {operation}")

        except Exception as e:
            self._connection_stats['failed_queries'] += 1
            
            # Handle AsyncIO event loop binding issues
            if "bound to a different event loop" in str(e) or "asyncio" in str(e).lower():
                logger.warning(f"AsyncIO event loop issue detected, reinitializing client: {str(e)}")
                # Force client reinitialization
                self._client = None
                self._initialization_attempted = False
                self._initialization_successful = False
                
                # Try to reinitialize and retry the query once
                try:
                    fresh_client = await self.get_client()
                    if fresh_client:
                        logger.info("Client reinitialized, retrying query...")
                        # Retry the query with fresh client
                        table_ref = fresh_client.table(table)
                        
                        if operation == 'select':
                            columns = kwargs.get('columns', '*')
                            result = table_ref.select(columns)
                            
                            if 'eq' in kwargs:
                                for column, value in kwargs['eq'].items():
                                    result = result.eq(column, value)
                            
                            if 'limit' in kwargs:
                                result = result.limit(kwargs['limit'])
                                
                            return await result.execute()
                        
                        # Add other operations as needed
                        elif operation == 'insert':
                            data = kwargs.get('data', {})
                            return await table_ref.insert(data).execute()
                        
                        elif operation == 'update':
                            data = kwargs.get('data', {})
                            result = table_ref.update(data)
                            if 'eq' in kwargs:
                                for column, value in kwargs['eq'].items():
                                    result = result.eq(column, value)
                            return await result.execute()
                        
                        elif operation == 'delete':
                            result = table_ref.delete()
                            if 'eq' in kwargs:
                                for column, value in kwargs['eq'].items():
                                    result = result.eq(column, value)
                            return await result.execute()
                        
                        elif operation == 'upsert':
                            data = kwargs.get('data', {})
                            return await table_ref.upsert(data).execute()
                            
                except Exception as retry_e:
                    logger.error(f"Retry after client reinitialization failed: {str(retry_e)}")
                    raise retry_e
            
            logger.error(f"Query failed: {operation} on {table} - {str(e)}")
            raise

        finally:
            # Update stats
            response_time = time.time() - start_time
            self._connection_stats['successful_queries'] += 1

            # Update average response time
            total_successful = self._connection_stats['successful_queries']
            current_avg = self._connection_stats['avg_response_time']
            self._connection_stats['avg_response_time'] = (
                (current_avg * (total_successful - 1) + response_time) / total_successful
            )

    def force_client_reset(self):
        """Force complete client reset - useful for event loop issues."""
        logger.warning("🔄 Forcing complete client reset")
        self._client = None
        self._initialization_attempted = False
        self._initialization_successful = False
        self._event_loop_id = None
        
        # Clear connection stats errors
        if 'connection_errors' in self._connection_stats:
            self._connection_stats['connection_errors'].clear()

    async def execute_raw_sql(self, query: str, params: Dict = None) -> Any:
        """Execute raw SQL query."""
        if not self._client:
            raise ConnectionError("Supabase client not initialized")

        try:
            return await self._client.rpc('execute_sql', {'query': query, 'params': params or {}}).execute()
        except Exception as e:
            logger.error(f"Raw SQL query failed: {str(e)}")
            raise

    def get_connection_stats(self) -> Dict:
        """Get connection statistics."""
        return self._connection_stats.copy()

    def reset_stats(self):
        """Reset connection statistics."""
        self._connection_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'avg_response_time': 0.0,
            'last_connection_test': None,
            'connection_errors': []
        }

    def close_connections(self):
        """Close database connections."""
        # Supabase client doesn't require explicit connection closing
        # But we can reset the client if needed
        self._client = None
        logger.info("Supabase connections closed")

class SupabaseError(Exception):
    """Custom exception for Supabase operations."""

    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ErrorHandler:
    """Handle Supabase errors with retry logic."""

    @staticmethod
    def handle_connection_error(error: Exception) -> str:
        """Handle connection-related errors."""
        if "connection" in str(error).lower():
            return "Database connection failed. Please check your internet connection and try again."
        elif "timeout" in str(error).lower():
            return "Database request timed out. Please try again."
        elif "authentication" in str(error).lower():
            return "Database authentication failed. Please check your credentials."
        else:
            return f"Database connection error: {str(error)}"

    @staticmethod
    def handle_auth_error(error: Exception) -> str:
        """Handle authentication-related errors."""
        if "invalid" in str(error).lower():
            return "Invalid credentials. Please check your username and password."
        elif "expired" in str(error).lower():
            return "Session expired. Please log in again."
        elif "unauthorized" in str(error).lower():
            return "Unauthorized access. Please log in."
        else:
            return f"Authentication error: {str(error)}"

    @staticmethod
    def handle_data_error(error: Exception) -> str:
        """Handle data-related errors."""
        if "unique" in str(error).lower():
            return "This data already exists. Please use different values."
        elif "foreign key" in str(error).lower():
            return "Related data not found. Please check your input."
        elif "not null" in str(error).lower():
            return "Required information is missing. Please fill in all required fields."
        else:
            return f"Data error: {str(error)}"

    @staticmethod
    async def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0) -> Any:
        """Retry function with exponential backoff."""
        for attempt in range(max_retries):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func()
                else:
                    return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e

                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}")
                await asyncio.sleep(delay)

# Global connection manager instance (lazy-loaded)
_connection_manager = None

def get_connection_manager():
    """Get global connection manager instance with lazy loading."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = SupabaseConnectionManager()
    return _connection_manager

# For backward compatibility
connection_manager = get_connection_manager()

async def get_supabase_client() -> Optional[AsyncClient]:
    """Get global Supabase client instance."""
    return await get_connection_manager().get_client()

async def test_supabase_connection() -> bool:
    """Test Supabase connection."""
    return await get_connection_manager().test_connection()

def get_connection_stats() -> Dict:
    """Get connection statistics."""
    return get_connection_manager().get_connection_stats()

# Health check function for monitoring
async def health_check() -> Dict[str, Any]:
    """Perform comprehensive health check."""
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'supabase_available': SUPABASE_AVAILABLE,
        'client_initialized': connection_manager._client is not None,
        'connection_test': False,
        'stats': connection_manager.get_connection_stats()
    }

    if health_status['client_initialized']:
        health_status['connection_test'] = await connection_manager.test_connection()

    return health_status