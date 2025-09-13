#!/usr/bin/env python3
"""
Streamlit Cloud Document Processing Test
Quick verification that document processing works on Streamlit Cloud
"""

import streamlit as st
import asyncio
from io import BytesIO

def main():
    st.title("🔧 Streamlit Cloud Document Processing Test")
    st.write("This tool verifies that document processing works correctly on your Streamlit Cloud deployment.")
    
    # Test 1: Configuration Loading
    st.write("## 1. 📋 Configuration Test")
    try:
        from config import get_api_keys, get_model_configs, get_supabase_config
        
        # Test API keys
        groq_key, openrouter_key = get_api_keys()
        st.write(f"**GROQ API Key**: {'✅ Available' if groq_key else '❌ Missing'}")
        st.write(f"**OpenRouter API Key**: {'✅ Available' if openrouter_key else '❌ Missing'}")
        
        # Test model configs
        model_configs = get_model_configs()
        st.write(f"**Model Configurations**: ✅ Loaded ({len(model_configs)} models)")
        
        # Test Supabase config
        supabase_url, supabase_key = get_supabase_config()
        st.write(f"**Supabase URL**: {'✅ Available' if supabase_url else '❌ Missing'}")
        st.write(f"**Supabase Key**: {'✅ Available' if supabase_key else '❌ Missing'}")
        
    except Exception as e:
        st.error(f"❌ Configuration test failed: {e}")
        return
    
    # Test 2: RAG System Dependencies
    st.write("## 2. 🤖 RAG System Dependencies")
    try:
        from rag_system_chromadb import _check_dependencies
        
        if _check_dependencies():
            st.success("✅ All RAG dependencies available")
        else:
            st.error("❌ Some RAG dependencies missing")
            return
            
    except Exception as e:
        st.error(f"❌ RAG dependency check failed: {e}")
        return
    
    # Test 3: RAG System Initialization
    st.write("## 3. 🔧 RAG System Initialization")
    
    # Set up session state for testing
    if 'user_id' not in st.session_state:
        st.session_state.user_id = 'test-user'
        st.session_state.authenticated = True
    
    try:
        from rag_system_chromadb import initialize_rag_system
        
        test_conversation_id = 'test-conversation-streamlit-cloud'
        rag_system = initialize_rag_system(test_conversation_id)
        
        if rag_system:
            st.success("✅ RAG system initialized successfully")
            
            # Test component initialization
            if rag_system._initialize_components():
                st.success("✅ RAG components initialized")
                
                # Test document list
                docs = rag_system.get_documents_list()
                st.write(f"**Document List**: ✅ Working ({len(docs)} documents)")
                
            else:
                st.error("❌ RAG component initialization failed")
                return
        else:
            st.error("❌ RAG system initialization failed")
            return
            
    except Exception as e:
        st.error(f"❌ RAG system test failed: {e}")
        return
    
    # Test 4: Document Processing
    st.write("## 4. 📄 Document Processing Test")
    
    # Create a test document
    test_content = """
    PharmGPT Test Document
    
    This is a test document for verifying document processing functionality.
    It contains information about medications and drug interactions.
    
    Key topics:
    - Drug interactions
    - Medication dosages
    - Side effects
    - Contraindications
    """
    
    if st.button("🧪 Test Document Processing"):
        with st.spinner("Testing document processing..."):
            try:
                # Test document processing
                result = asyncio.run(test_document_processing(rag_system, test_content))
                
                if result:
                    st.success("✅ Document processing test passed!")
                    
                    # Test search
                    search_results = rag_system.search_documents("drug interactions")
                    if search_results:
                        st.success(f"✅ Document search working ({len(search_results)} results)")
                        
                        # Show search results
                        with st.expander("Search Results"):
                            for i, result in enumerate(search_results):
                                st.write(f"**Result {i+1}:**")
                                st.write(f"- **File**: {result['filename']}")
                                st.write(f"- **Relevance**: {result['relevance_score']:.3f}")
                                st.write(f"- **Content**: {result['content'][:200]}...")
                                st.write("---")
                    else:
                        st.warning("⚠️ Document search returned no results")
                else:
                    st.error("❌ Document processing test failed")
                    
            except Exception as e:
                st.error(f"❌ Document processing test failed: {e}")
    
    # Test 5: Database Connection
    st.write("## 5. 🗄️ Database Connection Test")
    try:
        from utils.database_status import quick_database_health_check
        
        if st.button("🔍 Test Database Connection"):
            with st.spinner("Testing database connection..."):
                health = asyncio.run(quick_database_health_check())
                
                if health['database_connected']:
                    st.success("✅ Database connected")
                else:
                    st.error("❌ Database connection failed")
                
                if health['core_tables_accessible']:
                    st.success("✅ Core tables accessible")
                else:
                    st.error("❌ Core tables not accessible")
                
                if health['errors']:
                    st.write("**Issues found:**")
                    for error in health['errors']:
                        st.warning(f"⚠️ {error}")
                        
    except Exception as e:
        st.error(f"❌ Database test failed: {e}")
    
    # Summary
    st.write("## 📊 Summary")
    st.info("""
    **If all tests pass, your document processing should work correctly on Streamlit Cloud.**
    
    **Next steps:**
    1. Try uploading a real document in your main app
    2. Check that it processes successfully
    3. Verify that you can search and get relevant results
    4. Test with different file types (PDF, DOCX, TXT, CSV)
    """)

async def test_document_processing(rag_system, test_content):
    """Test document processing with sample content."""
    try:
        # Convert string to bytes
        content_bytes = test_content.encode('utf-8')
        
        # Test document processing
        result = await rag_system.add_document(
            file_content=content_bytes,
            filename="test_document.txt",
            file_type="text/plain"
        )
        
        return result == True
        
    except Exception as e:
        st.error(f"Document processing error: {e}")
        return False

if __name__ == "__main__":
    main()