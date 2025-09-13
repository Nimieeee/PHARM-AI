#!/usr/bin/env python3
"""
Debug script to test the complete message flow in PharmGPT
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_api_keys():
    """Test API key configuration and connectivity."""
    logger.info("🔑 Testing API key configuration...")
    
    # Check environment variables
    groq_key = os.environ.get("GROQ_API_KEY")
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    
    logger.info(f"GROQ_API_KEY: {'✅ Set' if groq_key else '❌ Missing'}")
    logger.info(f"OPENROUTER_API_KEY: {'✅ Set' if openrouter_key else '❌ Missing'}")
    
    if not groq_key or not openrouter_key:
        logger.error("❌ API keys are missing!")
        return False
    
    # Test API connections
    try:
        from openai_client import test_api_connection
        
        # Test Groq API
        groq_model = "meta-llama/llama-4-maverick-17b-128e-instruct"
        groq_works = test_api_connection(groq_model)
        logger.info(f"Groq API ({groq_model}): {'✅ Working' if groq_works else '❌ Failed'}")
        
        # Test OpenRouter API
        openrouter_model = "openrouter/sonoma-sky-alpha"
        openrouter_works = test_api_connection(openrouter_model)
        logger.info(f"OpenRouter API ({openrouter_model}): {'✅ Working' if openrouter_works else '❌ Failed'}")
        
        return groq_works or openrouter_works
        
    except Exception as e:
        logger.error(f"❌ Error testing API connections: {e}")
        return False

async def test_database_connection():
    """Test database connection and user lookup."""
    logger.info("🗄️ Testing database connection...")
    
    try:
        from services.user_service import user_service
        
        # Test user lookup
        test_user_id = "e4443c52948edad6132f34b6378a9901"
        user = await user_service.get_user_by_id(test_user_id)
        
        if user:
            logger.info(f"✅ Database connection working - Found user: {user.get('username')}")
            return True, user
        else:
            logger.error(f"❌ User not found: {test_user_id}")
            return False, None
            
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False, None

async def test_conversation_creation():
    """Test conversation creation."""
    logger.info("💬 Testing conversation creation...")
    
    try:
        from services.conversation_service import conversation_service
        
        # Get test user
        db_works, user = await test_database_connection()
        if not db_works or not user:
            logger.error("❌ Cannot test conversation creation - database issues")
            return False, None
        
        # Create test conversation
        conversation_id = await conversation_service.create_conversation(
            user['id'], 
            "Debug Test Conversation", 
            "meta-llama/llama-4-maverick-17b-128e-instruct"
        )
        
        if conversation_id:
            logger.info(f"✅ Conversation created successfully: {conversation_id}")
            return True, conversation_id
        else:
            logger.error("❌ Failed to create conversation")
            return False, None
            
    except Exception as e:
        logger.error(f"❌ Conversation creation failed: {e}")
        return False, None

async def test_message_addition():
    """Test adding messages to conversation."""
    logger.info("📝 Testing message addition...")
    
    try:
        from services.conversation_service import conversation_service
        
        # Get test user and conversation
        db_works, user = await test_database_connection()
        if not db_works or not user:
            logger.error("❌ Cannot test message addition - database issues")
            return False
        
        conv_works, conversation_id = await test_conversation_creation()
        if not conv_works or not conversation_id:
            logger.error("❌ Cannot test message addition - conversation creation failed")
            return False
        
        # Test adding user message
        test_message = {
            "role": "user",
            "content": "Hello, this is a test message",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        success = await conversation_service.add_message(
            user['id'],
            conversation_id,
            test_message
        )
        
        if success:
            logger.info("✅ Message added successfully")
            
            # Test adding assistant message
            assistant_message = {
                "role": "assistant", 
                "content": "Hello! This is a test response.",
                "timestamp": "2024-01-01T00:00:01Z"
            }
            
            success2 = await conversation_service.add_message(
                user['id'],
                conversation_id,
                assistant_message
            )
            
            if success2:
                logger.info("✅ Assistant message added successfully")
                return True
            else:
                logger.error("❌ Failed to add assistant message")
                return False
        else:
            logger.error("❌ Failed to add user message")
            return False
            
    except Exception as e:
        logger.error(f"❌ Message addition failed: {e}")
        return False

async def test_ai_response_generation():
    """Test AI response generation."""
    logger.info("🤖 Testing AI response generation...")
    
    try:
        from openai_client import chat_completion
        
        # Test message
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in exactly 5 words."}
        ]
        
        # Test with Groq model
        try:
            groq_model = "meta-llama/llama-4-maverick-17b-128e-instruct"
            response = chat_completion(groq_model, test_messages)
            logger.info(f"✅ Groq response: {response[:100]}...")
            return True
        except Exception as groq_error:
            logger.error(f"❌ Groq failed: {groq_error}")
            
            # Try OpenRouter as fallback
            try:
                openrouter_model = "openrouter/sonoma-sky-alpha"
                response = chat_completion(openrouter_model, test_messages)
                logger.info(f"✅ OpenRouter response: {response[:100]}...")
                return True
            except Exception as or_error:
                logger.error(f"❌ OpenRouter also failed: {or_error}")
                return False
                
    except Exception as e:
        logger.error(f"❌ AI response generation failed: {e}")
        return False

async def test_streaming_response():
    """Test streaming AI response."""
    logger.info("📡 Testing streaming response...")
    
    try:
        from openai_client import chat_completion_stream
        
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Count from 1 to 5, one number per line."}
        ]
        
        # Test streaming with Groq
        try:
            groq_model = "meta-llama/llama-4-maverick-17b-128e-instruct"
            response_chunks = []
            
            for chunk in chat_completion_stream(groq_model, test_messages):
                response_chunks.append(chunk)
                if len(response_chunks) > 10:  # Limit for testing
                    break
            
            full_response = ''.join(response_chunks)
            logger.info(f"✅ Streaming response: {full_response[:100]}...")
            return True
            
        except Exception as stream_error:
            logger.error(f"❌ Streaming failed: {stream_error}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Streaming test failed: {e}")
        return False

async def run_comprehensive_test():
    """Run all tests in sequence."""
    logger.info("🚀 Starting comprehensive message flow test...")
    
    results = {}
    
    # Test 1: API Keys
    results['api_keys'] = await test_api_keys()
    
    # Test 2: Database
    results['database'] = (await test_database_connection())[0]
    
    # Test 3: Conversation Creation
    results['conversation'] = (await test_conversation_creation())[0]
    
    # Test 4: Message Addition
    results['messages'] = await test_message_addition()
    
    # Test 5: AI Response
    results['ai_response'] = await test_ai_response_generation()
    
    # Test 6: Streaming
    results['streaming'] = await test_streaming_response()
    
    # Summary
    logger.info("📊 Test Results Summary:")
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
    
    # Overall result
    all_passed = all(results.values())
    logger.info(f"🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if not all_passed:
        logger.info("💡 Troubleshooting suggestions:")
        if not results['api_keys']:
            logger.info("  - Check API keys in .env file")
        if not results['database']:
            logger.info("  - Check Supabase connection and user data")
        if not results['conversation']:
            logger.info("  - Check conversation service and database schema")
        if not results['messages']:
            logger.info("  - Check message storage and RLS policies")
        if not results['ai_response']:
            logger.info("  - Check API connectivity and model availability")
        if not results['streaming']:
            logger.info("  - Check streaming implementation and network")
    
    return all_passed

def main():
    """Main function."""
    logger.info("🧪 PharmGPT Message Flow Debug Tool")
    logger.info("=" * 50)
    
    # Run async tests
    result = asyncio.run(run_comprehensive_test())
    
    logger.info("=" * 50)
    logger.info(f"🏁 Debug session completed: {'SUCCESS' if result else 'ISSUES FOUND'}")

if __name__ == "__main__":
    main()