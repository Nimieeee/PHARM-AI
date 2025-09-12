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
    from supabase import create_client, Client
    from postgrest.exceptions import APIError
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.error("Supabase not available. Install with: pip install supabase")


def validate_order_clause(order_clause: str) -> str:
    """Validate and fix order clause format."""
    if not order_clause:
        return 'created_at.desc'
    
    # Remove any duplicate direction specifiers
    if '.desc.asc' in order_clause:
        order_clause = order_clause.replace('.desc.asc', '.desc')
    elif '.asc.desc' in order_clause:
        order_clause = order_clause.replace('.asc.desc', '.asc')
    elif '.desc.desc' in order_clause:
        order_clause = order_clause.replace('.desc.desc', '.desc')
    elif '.asc.asc' in order_clause:
        order_clause = order_clause.replace('.asc.asc', '.asc')
    
    # Ensure proper format
    if '.' not in order_clause:
        order_clause = f"{order_clause}.desc"
    
    return order_clause


class SupabaseConnectionManager:
    """Manages Supabase database connections with pooling and error handling."""
    
    _instance = None
    _client: Optional[Client] = None
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
            self._initialize_client()
    
    def _initialize_client(self) -> bool:
        """Initialize Supabase client with error handling."""
        if not SUPABASE_AVAILABLE:
            logger.error("Supabase library not available")
            return False
        
        try:
            # Get credentials from Streamlit secrets
            supabase_url = st.secrets.get("SUPABASE_URL")
            supabase_key = st.secrets.get("SUPABASE_ANON_KEY")
            
            if not supabase_url or not supabase_key:
                logger.error("Supabase credentials not found in secrets")
                st.error("❌ Supabase credentials not configured. Please add SUPABASE_URL and SUPABASE_ANON_KEY to your Streamlit secrets.")
                return False
            
            # Create client with connection pooling
            self._client = create_client(supabase_url, supabase_key)
            
            # Test connection
            if self.test_connection():
                logger.info("Supabase client initialized successfully")
                return True
            else:
                logger.error("Supabase connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            st.error(f"❌ Failed to connect to Supabase: {str(e)}")
            return False
    
    def get_client(self) -> Optional[Client]:
        """Get Supabase client instance."""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    def test_connection(self) -> bool:
        """Test database connection health."""
        if not self._client:
            return False
        
        try:
            start_time = time.time()
            
            # Simple query to test connection
            result = self._client.table('users').select('count').limit(1).execute()
            
            response_time = time.time() - start_time
            self._connection_stats['last_connection_test'] = datetime.now()
            self._connection_stats['avg_response_time'] = response_time
            
            logger.info(f"Connection test successful ({response_time:.3f}s)")
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            self._connection_stats['connection_errors'].append({
                'timestamp': datetime.now(),
                'error': str(e)
            })
            return False
    
    def execute_query(self, table: str, operation: str, **kwargs) -> Any:
        """Execute database query with error handling and stats tracking."""
        if not self._client:
            raise ConnectionError("Supabase client not initialized")
        
        start_time = time.time()
        self._connection_stats['total_queries'] += 1
        
        try:
            # Get table reference
            table_ref = self._client.table(table)
            
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
                    validated_order = validate_order_clause(kwargs['order'])
                    result = result.order(validated_order)
                
                return result.execute()
            
            elif operation == 'insert':
                data = kwargs.get('data', {})
                return table_ref.insert(data).execute()
            
            elif operation == 'update':
                data = kwargs.get('data', {})
                result = table_ref.update(data)
                
                if 'eq' in kwargs:
                    for column, value in kwargs['eq'].items():
                        result = result.eq(column, value)
                
                return result.execute()
            
            elif operation == 'delete':
                result = table_ref.delete()
                
                if 'eq' in kwargs:
                    for column, value in kwargs['eq'].items():
                        result = result.eq(column, value)
                
                return result.execute()
            
            elif operation == 'upsert':
                data = kwargs.get('data', {})
                return table_ref.upsert(data).execute()
            
            else:
                raise ValueError(f"Unsupported operation: {operation}")
        
        except Exception as e:
            self._connection_stats['failed_queries'] += 1
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
    
    def execute_raw_sql(self, query: str, params: Dict = None) -> Any:
        """Execute raw SQL query."""
        if not self._client:
            raise ConnectionError("Supabase client not initialized")
        
        try:
            return self._client.rpc('execute_sql', {'query': query, 'params': params or {}}).execute()
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

# Global connection manager instance
connection_manager = SupabaseConnectionManager()

def get_supabase_client() -> Optional[Client]:
    """Get global Supabase client instance."""
    return connection_manager.get_client()

def test_supabase_connection() -> bool:
    """Test Supabase connection."""
    return connection_manager.test_connection()

def get_connection_stats() -> Dict:
    """Get connection statistics."""
    return connection_manager.get_connection_stats()

# Health check function for monitoring
def health_check() -> Dict[str, Any]:
    """Perform comprehensive health check."""
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'supabase_available': SUPABASE_AVAILABLE,
        'client_initialized': connection_manager._client is not None,
        'connection_test': False,
        'stats': connection_manager.get_connection_stats()
    }
    
    if health_status['client_initialized']:
        health_status['connection_test'] = connection_manager.test_connection()
    
    return health_status

# Initialize connection on import
if SUPABASE_AVAILABLE:
    try:
        connection_manager._initialize_client()
    except Exception as e:
        logger.warning(f"Failed to initialize Supabase on import: {e}")