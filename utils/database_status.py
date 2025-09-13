"""
Database Status Utilities for PharmGPT
Quick health checks and status monitoring for Streamlit Cloud
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime
import streamlit as st
from supabase_manager import get_supabase_client, get_connection_stats

logger = logging.getLogger(__name__)

async def quick_database_health_check() -> Dict[str, Any]:
    """Perform a quick database health check."""
    health_status = {
        'timestamp': datetime.now().isoformat(),
        'database_connected': False,
        'core_tables_accessible': False,
        'rls_functions_available': False,
        'connection_stats': {},
        'errors': []
    }
    
    try:
        # Test connection
        client = await get_supabase_client()
        if client:
            health_status['database_connected'] = True
            
            # Test core tables
            try:
                await client.table('users').select('count').limit(1).execute()
                await client.table('conversations').select('count').limit(1).execute()
                health_status['core_tables_accessible'] = True
            except Exception as e:
                health_status['errors'].append(f"Core tables error: {str(e)}")
            
            # Test RLS functions (optional)
            try:
                await client.rpc('set_user_context', {
                    'user_identifier': 'health-check'
                }).execute()
                health_status['rls_functions_available'] = True
            except Exception as e:
                if "PGRST202" not in str(e):
                    health_status['errors'].append(f"RLS function error: {str(e)}")
            
            # Get connection stats
            health_status['connection_stats'] = get_connection_stats()
            
        else:
            health_status['errors'].append("Could not establish database connection")
            
    except Exception as e:
        health_status['errors'].append(f"Health check failed: {str(e)}")
        logger.error(f"Database health check failed: {e}")
    
    return health_status

def display_database_status_sidebar():
    """Display database status in Streamlit sidebar."""
    with st.sidebar:
        st.write("### 🔧 Database Status")
        
        # Run health check
        try:
            health = asyncio.run(quick_database_health_check())
            
            # Display status
            if health['database_connected']:
                st.success("✅ Database Connected")
            else:
                st.error("❌ Database Disconnected")
            
            if health['core_tables_accessible']:
                st.success("✅ Tables Accessible")
            else:
                st.error("❌ Tables Inaccessible")
            
            if health['rls_functions_available']:
                st.success("✅ RLS Functions Available")
            else:
                st.info("ℹ️ RLS Functions Optional")
            
            # Show connection stats if available
            stats = health.get('connection_stats', {})
            if stats.get('total_queries', 0) > 0:
                st.write(f"📊 Queries: {stats['successful_queries']}/{stats['total_queries']}")
                if stats.get('avg_response_time'):
                    st.write(f"⏱️ Avg Response: {stats['avg_response_time']:.3f}s")
            
            # Show errors if any
            if health['errors']:
                with st.expander("⚠️ Issues"):
                    for error in health['errors']:
                        st.write(f"• {error}")
                        
        except Exception as e:
            st.error(f"❌ Status Check Failed: {str(e)}")

def display_database_status_main():
    """Display database status in main area."""
    st.write("### 🔧 Database Health Status")
    
    col1, col2, col3 = st.columns(3)
    
    try:
        health = asyncio.run(quick_database_health_check())
        
        with col1:
            if health['database_connected']:
                st.success("✅ **Connected**")
            else:
                st.error("❌ **Disconnected**")
        
        with col2:
            if health['core_tables_accessible']:
                st.success("✅ **Tables OK**")
            else:
                st.error("❌ **Tables Error**")
        
        with col3:
            if health['rls_functions_available']:
                st.success("✅ **RLS Available**")
            else:
                st.info("ℹ️ **RLS Optional**")
        
        # Show detailed stats
        stats = health.get('connection_stats', {})
        if stats.get('total_queries', 0) > 0:
            st.write("**Connection Statistics:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Queries", stats['total_queries'])
            
            with col2:
                success_rate = (stats['successful_queries'] / stats['total_queries']) * 100
                st.metric("Success Rate", f"{success_rate:.1f}%")
            
            with col3:
                if stats.get('avg_response_time'):
                    st.metric("Avg Response", f"{stats['avg_response_time']:.3f}s")
        
        # Show errors if any
        if health['errors']:
            st.write("**Issues:**")
            for error in health['errors']:
                st.warning(f"⚠️ {error}")
                
    except Exception as e:
        st.error(f"❌ Status check failed: {str(e)}")

# Utility function for other modules
async def is_database_healthy() -> bool:
    """Quick check if database is healthy."""
    try:
        health = await quick_database_health_check()
        return health['database_connected'] and health['core_tables_accessible']
    except:
        return False