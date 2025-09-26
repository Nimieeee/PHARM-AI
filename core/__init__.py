"""
Core PharmGPT modules for clean architecture implementation.
"""

__version__ = "2.0.0"
__author__ = "PharmGPT Team"

# Export main classes for easy imports
from .auth import AuthenticationManager, initialize_auth_session, require_authentication
from .supabase_client import supabase_manager
from .conversations import ConversationManager
from .rag import ConversationRAG
from .config import config, Config
from .utils import DocumentProcessor, ErrorHandler

__all__ = [
    'AuthenticationManager',
    'supabase_manager', 
    'ConversationManager',
    'ConversationRAG',
    'config',
    'Config',
    'DocumentProcessor',
    'ErrorHandler',
    'initialize_auth_session',
    'require_authentication'
]