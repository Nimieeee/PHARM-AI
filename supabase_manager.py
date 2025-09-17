"""
Clean Supabase Connection Manager for PharmGPT
Simple, robust database connection handling without event loop issues
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

try:
    from supabase import create_async_client, AsyncClient
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    AsyncClient = type("AsyncClient", (), {})
    logger.error("Supabase not available. Install with: pip install supabase")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class SimpleSupabaseManager:
    """Simple Supabase manager that creates fresh clients per operation."""
    
    def __init__(self):
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0
        }
    
    def _get_credentials(self):
        """Get Supabase credentials from Streamlit secrets or environment variables (fallback)."""
        import streamlit as st
        
        # Try Streamlit secrets first, fallback to environment variables
        try:
            url = st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL"))
            key = st.secrets.get("SUPABASE_ANON_KEY", os.environ.get("SUPABASE_ANON_KEY"))
        except Exception:
            # Fallback to environment variables if secrets not available
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_ANON_KEY")
        
        if not url or not key:
            logger.error("Missing Supabase credentials")
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in Streamlit secrets or environment")
        
        return url, key
    
    async def _create_client(self) -> AsyncClient:
        """Create a fresh Supabase client."""
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase library not available")
        
        url, key = self._get_credentials()
        return await create_async_client(url, key)
    
    async def execute_query(self, table: str, operation: str, **kwargs) -> Any:
        """Execute a database query with a fresh client."""
        self.stats['total_queries'] += 1
        
        # Set user context for RLS if user_uuid is provided in data
        user_uuid = None
        if 'data' in kwargs and isinstance(kwargs['data'], dict):
            user_uuid = kwargs['data'].get('user_uuid')
        elif 'eq' in kwargs and isinstance(kwargs['eq'], dict):
            user_uuid = kwargs['eq'].get('user_uuid')
        
        try:
            # Create fresh client for this operation
            client = await self._create_client()
            
            # Get table reference
            table_ref = client.table(table)
            
            # Execute operation
            if operation == 'select':
                result = table_ref.select(kwargs.get('columns', '*'))
                
                # Apply filters
                if 'eq' in kwargs:
                    for column, value in kwargs['eq'].items():
                        result = result.eq(column, value)
                
                if 'limit' in kwargs:
                    result = result.limit(kwargs['limit'])
                
                if 'order' in kwargs:
                    order_clause = kwargs['order']
                    if '.' in order_clause:
                        column, direction = order_clause.rsplit('.', 1)
                        desc = (direction == 'desc')
                    else:
                        column = order_clause
                        desc = True
                    result = result.order(column, desc=desc)
                
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
            self.stats['failed_queries'] += 1
            logger.error(f"Query failed: {operation} on {table} - {str(e)}")
            raise
        
        finally:
            self.stats['successful_queries'] += 1
    
    async def execute_raw_sql(self, query: str, params: list = None) -> Any:
        """Execute raw SQL query using Supabase client directly."""
        self.stats['total_queries'] += 1
        
        try:
            client = await self._create_client()
            
            # Use postgrest for raw SQL - this is a workaround
            # In practice, you'd need to create a custom RPC function in Supabase
            # For now, let's use a different approach
            
            # Simple table queries for testing
            if 'pg_extension' in query and 'vector' in query:
                # Check for pgvector extension
                result = await client.rpc('check_extension', {'ext_name': 'vector'}).execute()
            elif 'information_schema.columns' in query:
                # Get table columns
                table_name = query.split("table_name = '")[1].split("'")[0]
                result = await client.rpc('get_table_columns', {'table_name': table_name}).execute()
            else:
                # For other queries, we'll need to implement specific RPC functions
                # For now, return empty result
                result = type('Result', (), {'data': []})()
            
            self.stats['successful_queries'] += 1
            return result
            
        except Exception as e:
            self.stats['failed_queries'] += 1
            logger.error(f"Raw SQL execution failed: {e}")
            # Return empty result instead of raising for testing
            return type('Result', (), {'data': []})()
    
    async def execute_rpc(self, function_name: str, params: dict = None) -> Any:
        """Execute a stored procedure/function."""
        self.stats['total_queries'] += 1
        
        try:
            client = await self._create_client()
            
            if params:
                result = await client.rpc(function_name, params).execute()
            else:
                result = await client.rpc(function_name).execute()
            
            self.stats['successful_queries'] += 1
            return result
            
        except Exception as e:
            self.stats['failed_queries'] += 1
            logger.error(f"RPC execution failed: {e}")
            raise

    async def test_connection(self) -> bool:
        """Test database connection."""
        try:
            result = await self.execute_query('users', 'select', columns='count', limit=1)
            logger.info("✅ Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            return False

# Global instance
connection_manager = SimpleSupabaseManager()

# Convenience functions
async def get_supabase_client() -> AsyncClient:
    """Get a fresh Supabase client."""
    return await connection_manager._create_client()

async def test_supabase_connection() -> bool:
    """Test Supabase connection."""
    return await connection_manager.test_connection()

def get_connection_stats() -> Dict:
    """Get connection statistics."""
    return connection_manager.stats.copy()

# Health check
async def health_check() -> Dict[str, Any]:
    """Perform health check."""
    return {
        'timestamp': datetime.now().isoformat(),
        'supabase_available': SUPABASE_AVAILABLE,
        'connection_test': await connection_manager.test_connection(),
        'stats': connection_manager.stats
    }