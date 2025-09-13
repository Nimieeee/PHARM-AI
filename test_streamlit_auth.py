#!/usr/bin/env python3
"""
Test authentication in Streamlit context
"""

import streamlit as st

st.title("🧪 Authentication Test")

# Test authentication functions
try:
    st.write("Testing authentication imports...")
    from auth import authenticate_user, login_user, create_user
    st.success("✅ Authentication functions imported successfully")
    
    # Test authenticate_user
    st.write("Testing authenticate_user function...")
    result = authenticate_user('test_user', 'test_pass')
    st.success(f"✅ authenticate_user result: {result}")
    
    # Test login_user
    st.write("Testing login_user function...")
    result = login_user('test_user', 'test_pass')
    st.success(f"✅ login_user result: {result}")
    
    # Test create_user
    st.write("Testing create_user function...")
    result = create_user('test_user_new', 'test_pass')
    st.success(f"✅ create_user result: {result}")
    
    st.balloons()
    st.success("🎉 All authentication tests passed! No asyncio errors!")
    
except Exception as e:
    st.error(f"❌ Error: {e}")
    st.code(str(e))
    
    # Check if it's an asyncio error
    if "asyncio" in str(e).lower() or "coroutine" in str(e).lower():
        st.error("🔍 ASYNCIO ERROR DETECTED!")
        st.write("This indicates there's still an async/await issue somewhere.")
        
        # Show detailed error
        import traceback
        st.code(traceback.format_exc())
    else:
        st.info("This appears to be a different type of error, not asyncio-related.")