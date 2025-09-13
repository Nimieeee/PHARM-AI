#!/usr/bin/env python3
"""
Streamlit Cloud compatibility fixes
Run this to apply fixes for common cloud deployment issues
"""

import os
import sys

def fix_sqlite_for_chromadb():
    """Fix SQLite compatibility for ChromaDB on Streamlit Cloud"""
    try:
        # This is needed for ChromaDB on Streamlit Cloud
        __import__('pysqlite3')
        import sys
        sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
        print("✅ SQLite fix applied for ChromaDB compatibility")
    except ImportError:
        print("⚠️  pysqlite3-binary not installed, ChromaDB may not work")

def check_environment():
    """Check if we're running on Streamlit Cloud"""
    is_cloud = any([
        'STREAMLIT_CLOUD' in os.environ,
        'STREAMLIT_SHARING' in os.environ,
        '.streamlit.app' in os.environ.get('HOSTNAME', ''),
        'streamlit.app' in os.environ.get('SERVER_NAME', '')
    ])
    
    if is_cloud:
        print("🌐 Running on Streamlit Cloud")
    else:
        print("🏠 Running locally")
    
    return is_cloud

def fix_asyncio_for_cloud():
    """Fix asyncio event loop issues on Streamlit Cloud"""
    import asyncio
    
    try:
        # Try to get existing loop
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Loop is closed")
        # Don't create new loop if one is already running
        if not loop.is_running():
            print("✅ Using existing asyncio event loop")
        return loop
    except RuntimeError:
        # Create new event loop if none exists or is closed
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            print("✅ New asyncio event loop created")
            return loop
        except Exception as e:
            print(f"⚠️  Could not create event loop: {e}")
            return None

def apply_all_fixes():
    """Apply all Streamlit Cloud compatibility fixes"""
    print("🔧 Applying Streamlit Cloud fixes...")
    
    # Check environment
    is_cloud = check_environment()
    
    # Fix SQLite for ChromaDB
    fix_sqlite_for_chromadb()
    
    # Fix asyncio
    fix_asyncio_for_cloud()
    
    print("✅ All fixes applied successfully")
    return is_cloud

if __name__ == "__main__":
    apply_all_fixes()