"""
Quick Setup Verification for PharmGPT
Tests basic functionality and configuration
"""

import asyncio
import logging
import sys
import os
from typing import Dict, List

# Add current directory to path
sys.path.insert(0, '.')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def check_environment():
    """Check environment setup."""
    print("🔍 Checking Environment Setup...")
    
    checks = {
        "Python Version": sys.version_info >= (3, 8),
        "SUPABASE_URL": bool(os.getenv("SUPABASE_URL")),
        "SUPABASE_ANON_KEY": bool(os.getenv("SUPABASE_ANON_KEY")),
        "MISTRAL_API_KEY": bool(os.getenv("MISTRAL_API_KEY"))
    }
    
    for check, status in checks.items():
        print(f"  {'✅' if status else '❌'} {check}: {'OK' if status else 'MISSING'}")
    
    return all(checks.values())


def check_dependencies():
    """Check required dependencies."""
    print("\n📦 Checking Dependencies...")
    
    dependencies = {
        "streamlit": "streamlit",
        "supabase": "supabase",
        "langchain": "langchain",
        "langchain-mistralai": "langchain_mistralai",
        "PyPDF2": "PyPDF2",
        "docx2txt": "docx2txt",
        "pandas": "pandas",
        "PIL": "PIL"
    }
    
    results = {}
    for name, module in dependencies.items():
        try:
            __import__(module)
            results[name] = True
            print(f"  ✅ {name}: Available")
        except ImportError:
            results[name] = False
            print(f"  ❌ {name}: Missing")
    
    return results


async def test_database_connection():
    """Test database connection."""
    print("\n🗄️ Testing Database Connection...")
    
    try:
        from core.supabase_client import supabase_manager
        
        success = await supabase_manager.test_connection()
        if success:
            print("  ✅ Database connection: SUCCESS")
        else:
            print("  ❌ Database connection: FAILED")
        
        return success
        
    except Exception as e:
        print(f"  ❌ Database connection error: {e}")
        return False


async def test_authentication():
    """Test authentication functionality."""
    print("\n🔐 Testing Authentication...")
    
    try:
        from core.supabase_client import supabase_manager
        import uuid
        
        # Create test user
        test_username = f"quicktest_{uuid.uuid4().hex[:8]}"
        test_password = "TestPass123!"
        
        success, message, user_data = await supabase_manager.create_user(
            test_username, test_password
        )
        
        if success:
            print(f"  ✅ User creation: SUCCESS")
            
            # Test authentication
            auth_success, auth_message, auth_data = await supabase_manager.authenticate_user(
                test_username, test_password
            )
            
            if auth_success:
                print(f"  ✅ Authentication: SUCCESS")
                return True
            else:
                print(f"  ❌ Authentication: FAILED - {auth_message}")
                return False
        else:
            print(f"  ❌ User creation: FAILED - {message}")
            return False
            
    except Exception as e:
        print(f"  ❌ Authentication error: {e}")
        return False


def test_file_processing():
    """Test document processing."""
    print("\n📄 Testing Document Processing...")
    
    try:
        from core.utils import DocumentProcessor
        
        # Create a test text file
        test_content = b"This is a test document for PharmGPT. It contains pharmacology information."
        
        class MockFile:
            def __init__(self, name, content):
                self.name = name
                self._content = content
            
            def getvalue(self):
                return self._content
        
        mock_file = MockFile("test.txt", test_content)
        
        success, text, message, metadata = DocumentProcessor.process_uploaded_file(mock_file)
        
        if success and text:
            print(f"  ✅ Document processing: SUCCESS")
            print(f"    - Extracted {len(text)} characters")
            return True
        else:
            print(f"  ❌ Document processing: FAILED - {message}")
            return False
            
    except Exception as e:
        print(f"  ❌ Document processing error: {e}")
        return False


def test_rag_system():
    """Test RAG system initialization."""
    print("\n🤖 Testing RAG System...")
    
    try:
        from core.rag import ConversationRAG, get_rag_status
        
        rag_status = get_rag_status()
        
        print(f"  {'✅' if rag_status['langchain_available'] else '❌'} LangChain: {'Available' if rag_status['langchain_available'] else 'Missing'}")
        print(f"  {'✅' if rag_status['embeddings_available'] else '❌'} Embeddings: {'Available' if rag_status['embeddings_available'] else 'Missing'}")
        print(f"  📏 Model: {rag_status['model']} ({rag_status['dimensions']} dimensions)")
        
        return rag_status['langchain_available']
        
    except Exception as e:
        print(f"  ❌ RAG system error: {e}")
        return False


async def quick_integration_test():
    """Quick end-to-end test."""
    print("\n🚀 Running Integration Test...")

    client = None
    try:
        from core.supabase_client import supabase_manager
        from core.conversations import ConversationManager
        import uuid

        # Enable testing mode to bypass RLS
        try:
            client = await supabase_manager.get_client()
            await client.rpc('enable_testing_mode').execute()
        except Exception as e:
            print(f"  ⚠️ Could not enable testing mode: {e}")
            # Proceed anyway; some setups may not provide this RPC

        # Create test user
        test_username = f"integration_{uuid.uuid4().hex[:8]}"
        test_password = "TestPass123!"

        success, message, user_data = await supabase_manager.create_user(
            test_username, test_password
        )

        if not success:
            print(f"  ❌ Integration test failed at user creation: {message}")
            return False

        user_id = user_data['user_id']

        # Create conversation
        conversation_id = await supabase_manager.create_conversation(
            user_id=user_id,
            title="Integration Test Conversation"
        )

        if not conversation_id:
            print(f"  ❌ Integration test failed at conversation creation")
            return False

        # Add message
        message_id = await supabase_manager.add_message(
            conversation_id=conversation_id,
            user_id=user_id,
            role="user",
            content="Test message for integration"
        )

        if not message_id:
            print(f"  ❌ Integration test failed at message creation")
            return False

        # Verify message retrieval
        messages = await supabase_manager.get_conversation_messages(
            conversation_id, user_id
        )

        if len(messages) != 1:
            print(f"  ❌ Integration test failed at message retrieval")
            return False

        print(f"  ✅ Integration test: SUCCESS")
        print(f"    - Created user: {test_username}")
        print(f"    - Created conversation: {conversation_id[:8]}...")
        print(f"    - Added and retrieved 1 message")

        return True

    except Exception as e:
        print(f"  ❌ Integration test error: {e}")
        return False
    finally:
        # Always disable testing mode if it was enabled
        try:
            if client is None:
                from core.supabase_client import supabase_manager
                client = await supabase_manager.get_client()
            await client.rpc('disable_testing_mode').execute()
        except Exception:
            pass  # Ignore errors when disabling testing mode


async def main():
    """Run quick setup verification."""
    print("🏥 PharmGPT Quick Setup Verification")
    print("=" * 50)
    
    results = {}
    
    # Environment checks
    results['environment'] = check_environment()
    results['dependencies'] = check_dependencies()
    
    # Database tests
    results['database'] = await test_database_connection()
    
    # Core functionality tests
    results['auth'] = await test_authentication()
    results['file_processing'] = test_file_processing()
    results['rag_system'] = test_rag_system()
    
    # Integration test
    results['integration'] = await quick_integration_test()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for success in results.values() if success)
    failed_tests = total_tests - passed_tests
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\n📈 Results: {passed_tests}/{total_tests} tests passed")
    
    if failed_tests == 0:
        print("🎉 All verifications passed! PharmGPT is ready to use!")
        print("\n🚀 Next steps:")
        print("  1. Run: streamlit run app.py")
        print("  2. Open your browser to the Streamlit URL")
        print("  3. Sign up for a new account")
        print("  4. Start chatting!")
    else:
        print("⚠️  Some verifications failed. Please check:")
        
        if not results.get('environment'):
            print("  - Environment variables (check .env file)")
        if not results.get('dependencies'):
            print("  - Install missing dependencies with pip")
        if not results.get('database'):
            print("  - Supabase database setup (run database/schema.sql)")
        if not results.get('rag_system'):
            print("  - LangChain and Mistral API setup")
    
    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        exit_code = 0 if all(results.values()) else 1
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Verification cancelled by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Verification failed with error: {e}")
        exit(1)