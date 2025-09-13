#!/usr/bin/env python3
"""
Comprehensive System Test for PharmGPT
Tests all components to identify issues with message sending and document processing
"""

import asyncio
import os
import sys
import traceback
from datetime import datetime

def test_imports():
    """Test all required imports."""
    print("🔍 Testing imports...")
    
    imports = {
        'streamlit': 'streamlit',
        'openai': 'openai', 
        'supabase': 'supabase',
        'chromadb': 'chromadb',
        'sentence_transformers': 'sentence_transformers',
        'PIL': 'PIL',
        'pandas': 'pandas',
        'PyPDF2': 'PyPDF2',
        'docx': 'docx'
    }
    
    results = {}
    for name, module in imports.items():
        try:
            __import__(module)
            results[name] = True
            print(f"  ✅ {name}")
        except ImportError as e:
            results[name] = False
            print(f"  ❌ {name}: {e}")
    
    return results

def test_config():
    """Test configuration loading."""
    print("\n🔧 Testing configuration...")
    
    try:
        from config import get_api_keys, get_model_configs, get_supabase_config
        
        # Test API keys
        groq_key, openrouter_key = get_api_keys()
        print(f"  ✅ API Keys - Groq: {bool(groq_key)}, OpenRouter: {bool(openrouter_key)}")
        
        # Test model configs
        model_configs = get_model_configs()
        print(f"  ✅ Model configs: {list(model_configs.keys())}")
        
        for mode, config in model_configs.items():
            has_key = bool(config.get('api_key'))
            print(f"    {mode}: {config['model']} - API Key: {'✅' if has_key else '❌'}")
        
        # Test Supabase config
        supabase_url, supabase_key = get_supabase_config()
        print(f"  ✅ Supabase config - URL: {bool(supabase_url)}, Key: {bool(supabase_key)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Config test failed: {e}")
        traceback.print_exc()
        return False

def test_api_connections():
    """Test API connections."""
    print("\n🌐 Testing API connections...")
    
    try:
        from openai_client import get_available_model_modes, test_api_connection
        
        modes = get_available_model_modes()
        print(f"  ✅ Available modes: {list(modes.keys())}")
        
        results = {}
        for mode, config in modes.items():
            try:
                connected = test_api_connection(config['model'])
                results[mode] = connected
                print(f"    {mode}: {'✅' if connected else '❌'} {config['model']}")
            except Exception as e:
                results[mode] = False
                print(f"    {mode}: ❌ Error - {e}")
        
        return results
        
    except Exception as e:
        print(f"  ❌ API connection test failed: {e}")
        traceback.print_exc()
        return {}

async def test_database():
    """Test database connection and operations."""
    print("\n🗄️ Testing database...")
    
    try:
        from supabase_manager import get_supabase_client, test_supabase_connection
        
        # Test client initialization
        client = await get_supabase_client()
        if not client:
            print("  ❌ Failed to initialize Supabase client")
            return False
        
        print("  ✅ Supabase client initialized")
        
        # Test connection
        connected = await test_supabase_connection()
        print(f"  ✅ Connection test: {'passed' if connected else 'failed'}")
        
        # Test basic query
        result = await client.table('users').select('count').limit(1).execute()
        print("  ✅ Basic query successful")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        traceback.print_exc()
        return False

async def test_user_service():
    """Test user service operations."""
    print("\n👤 Testing user service...")
    
    try:
        from services.user_service import user_service
        
        # Test getting a user (this should work if database is set up)
        test_username = "test_user_for_system_check"
        user = await user_service.get_user_by_username(test_username)
        
        if user:
            print(f"  ✅ Found test user: {test_username}")
        else:
            print(f"  ℹ️ Test user not found (this is normal): {test_username}")
        
        print("  ✅ User service operational")
        return True
        
    except Exception as e:
        print(f"  ❌ User service test failed: {e}")
        traceback.print_exc()
        return False

def test_rag_system():
    """Test RAG system for document processing."""
    print("\n📄 Testing RAG system...")
    
    try:
        from rag_system_chromadb import _check_dependencies, ConversationRAGSystem
        
        # Test dependencies
        deps_available = _check_dependencies()
        print(f"  ✅ RAG dependencies: {'available' if deps_available else 'missing'}")
        
        if not deps_available:
            return False
        
        # Test initialization
        rag_system = ConversationRAGSystem('test_user', 'test_conversation')
        initialized = rag_system._initialize_components()
        print(f"  ✅ RAG initialization: {'successful' if initialized else 'failed'}")
        
        if initialized:
            # Test document list (should be empty for test conversation)
            docs = rag_system.get_documents_list()
            print(f"  ✅ Document list: {len(docs)} documents")
        
        return initialized
        
    except Exception as e:
        print(f"  ❌ RAG system test failed: {e}")
        traceback.print_exc()
        return False

def test_message_flow():
    """Test message flow components."""
    print("\n💬 Testing message flow...")
    
    try:
        # Test conversation manager
        from utils.conversation_manager import run_async
        print("  ✅ Conversation manager imported")
        
        # Test OpenAI client streaming
        from openai_client import chat_completion_stream, chat_completion
        print("  ✅ OpenAI client imported")
        
        # Test prompts
        from prompts import pharmacology_system_prompt
        print("  ✅ Prompts imported")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Message flow test failed: {e}")
        traceback.print_exc()
        return False

async def test_full_message_simulation():
    """Simulate a complete message flow."""
    print("\n🎯 Testing full message simulation...")
    
    try:
        from openai_client import chat_completion
        from config import get_model_configs
        
        # Get a working model
        model_configs = get_model_configs()
        working_model = None
        
        for mode, config in model_configs.items():
            if config.get('api_key'):
                working_model = config['model']
                break
        
        if not working_model:
            print("  ❌ No working model found")
            return False
        
        print(f"  🤖 Testing with model: {working_model}")
        
        # Test message
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, system test successful!' and nothing else."}
        ]
        
        response = chat_completion(working_model, messages)
        print(f"  ✅ AI Response: {response[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Full message simulation failed: {e}")
        traceback.print_exc()
        return False

async def main():
    """Run comprehensive system test."""
    print("🚀 PharmGPT Comprehensive System Test")
    print("=" * 50)
    
    # Track results
    results = {}
    
    # Test imports
    results['imports'] = test_imports()
    
    # Test configuration
    results['config'] = test_config()
    
    # Test API connections
    results['api_connections'] = test_api_connections()
    
    # Test database
    results['database'] = await test_database()
    
    # Test user service
    results['user_service'] = await test_user_service()
    
    # Test RAG system
    results['rag_system'] = test_rag_system()
    
    # Test message flow
    results['message_flow'] = test_message_flow()
    
    # Test full message simulation
    results['full_simulation'] = await test_full_message_simulation()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    all_passed = True
    
    for test_name, result in results.items():
        if isinstance(result, dict):
            # For API connections, check if any passed
            passed = any(result.values()) if result else False
        else:
            passed = bool(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("The system should be working correctly.")
    else:
        print("⚠️ SOME TESTS FAILED")
        print("Issues identified that need to be fixed.")
    
    print("=" * 50)
    
    return results

if __name__ == "__main__":
    asyncio.run(main())