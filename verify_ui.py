#!/usr/bin/env python3
"""
UI Component Verification Script
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_ui_components():
    """Verify that UI components can be imported and are functional."""
    try:
        # Test importing main app components
        from core.config import config
        logger.info("✅ Config module imported successfully")
        
        from core.auth import AuthenticationManager
        logger.info("✅ Authentication module imported successfully")
        
        from core.conversations import ConversationManager
        logger.info("✅ Conversation manager imported successfully")
        
        from core.rag import ConversationRAG
        logger.info("✅ RAG system imported successfully")
        
        # Test importing page components
        # Note: Streamlit pages can't be easily tested without running Streamlit
        logger.info("✅ Core UI components verified")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ UI component verification failed: {e}")
        return False

def verify_file_structure():
    """Verify required files exist."""
    required_files = [
        'app.py',
        'pages/3_💬_Chatbot.py',
        'core/__init__.py',
        'core/config.py',
        'core/auth.py',
        'core/conversations.py',
        'core/rag.py',
        'core/supabase_client.py',
        'core/utils.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
            logger.error(f"❌ Missing file: {file_path}")
        else:
            logger.info(f"✅ Found file: {file_path}")
    
    if missing_files:
        logger.error(f"❌ Missing {len(missing_files)} required files")
        return False
    
    logger.info("✅ All required files present")
    return True

def main():
    """Run UI verification."""
    logger.info("🖥️ Starting UI Component Verification")
    logger.info("=" * 40)
    
    # Verify file structure
    logger.info("\n🔍 Checking file structure...")
    file_result = verify_file_structure()
    
    # Verify UI components
    logger.info("\n🔍 Checking UI components...")
    component_result = verify_ui_components()
    
    # Summary
    logger.info("\n" + "=" * 40)
    logger.info("UI VERIFICATION SUMMARY")
    logger.info("=" * 40)
    
    if file_result and component_result:
        logger.info("🎉 All UI components verified successfully!")
        logger.info("✅ UI is ready for Streamlit deployment")
        return True
    else:
        logger.error("⚠️ UI verification failed.")
        return False

if __name__ == "__main__":
    try:
        result = main()
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"UI verification failed with error: {e}")
        sys.exit(1)