#!/usr/bin/env python3
"""
Quick Streamlit Cloud Test
Simple test to verify core functionality works
"""

import streamlit as st

def main():
    st.title("🚀 Quick Streamlit Cloud Test")
    
    # Test 1: Basic imports
    st.write("## 1. Testing Imports")
    
    try:
        from config import get_api_keys, get_model_configs
        st.success("✅ Config imports working")
        
        # Test API keys
        groq_key, openrouter_key = get_api_keys()
        if groq_key or openrouter_key:
            st.success("✅ API keys available")
        else:
            st.warning("⚠️ No API keys found")
        
        # Test model configs
        configs = get_model_configs()
        st.success(f"✅ Model configs loaded ({len(configs)} models)")
        
    except Exception as e:
        st.error(f"❌ Config test failed: {e}")
        return
    
    # Test 2: RAG System
    st.write("## 2. Testing RAG System")
    
    try:
        from rag_system_chromadb import _check_dependencies
        
        if _check_dependencies():
            st.success("✅ RAG dependencies available")
            
            # Test initialization
            if 'user_id' not in st.session_state:
                st.session_state.user_id = 'test-user'
                st.session_state.authenticated = True
            
            from rag_system_chromadb import initialize_rag_system
            rag_system = initialize_rag_system('test-conversation')
            
            if rag_system:
                st.success("✅ RAG system initialized")
            else:
                st.error("❌ RAG system initialization failed")
        else:
            st.error("❌ RAG dependencies missing")
            
    except Exception as e:
        st.error(f"❌ RAG test failed: {e}")
    
    # Test 3: Database
    st.write("## 3. Testing Database")
    
    try:
        from supabase_manager import get_supabase_client
        import asyncio
        
        async def test_db():
            client = await get_supabase_client()
            return client is not None
        
        if asyncio.run(test_db()):
            st.success("✅ Database connection working")
        else:
            st.error("❌ Database connection failed")
            
    except Exception as e:
        st.error(f"❌ Database test failed: {e}")
    
    # Test 4: Document Processing
    st.write("## 4. Testing Document Processing")
    
    if st.button("🧪 Test Document Upload"):
        try:
            # Create test content
            test_content = b"This is a test document for PharmGPT."
            
            # Test RAG system
            from rag_system_chromadb import initialize_rag_system
            rag_system = initialize_rag_system('test-conversation')
            
            if rag_system:
                with st.spinner("Testing document processing..."):
                    import asyncio
                    result = asyncio.run(rag_system.add_document(
                        test_content, 
                        "test.txt", 
                        "text/plain"
                    ))
                
                if result == True:
                    st.success("✅ Document processing works!")
                    
                    # Test search
                    search_results = rag_system.search_documents("test")
                    if search_results:
                        st.success(f"✅ Document search works ({len(search_results)} results)")
                    else:
                        st.warning("⚠️ No search results found")
                        
                elif result == "duplicate":
                    st.info("ℹ️ Document already exists (this is normal)")
                else:
                    st.error("❌ Document processing failed")
            else:
                st.error("❌ Could not initialize RAG system")
                
        except Exception as e:
            st.error(f"❌ Document test failed: {e}")
    
    # Summary
    st.write("## 📊 Summary")
    st.info("""
    **If all tests pass, your Streamlit Cloud app should work correctly!**
    
    **What to test next:**
    1. Try the main chat interface
    2. Upload a real document
    3. Ask questions about the document
    4. Check that responses include document context
    """)

if __name__ == "__main__":
    main()