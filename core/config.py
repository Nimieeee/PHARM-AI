"""
Configuration Management for PharmGPT
Centralized configuration with environment variable support
"""

import os
import logging
from typing import Dict, Any, Optional
import streamlit as st

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    """Application configuration manager."""
    
    # Application Settings
    APP_TITLE = "PharmGPT"
    APP_ICON = "💊"
    APP_VERSION = "2.0.0"
    APP_DESCRIPTION = "AI Pharmacology Assistant with Supabase + pgvector"
    
    # Page Configuration
    PAGE_CONFIG = {
        'page_title': APP_TITLE,
        'page_icon': APP_ICON,
        'layout': 'wide',
        'initial_sidebar_state': 'collapsed',
        'menu_items': {
            'Get Help': 'https://github.com/yourusername/pharmgpt',
            'Report a bug': 'https://github.com/yourusername/pharmgpt/issues',
            'About': f'{APP_TITLE} v{APP_VERSION} - AI Pharmacology Assistant'
        }
    }
    
    # Database Configuration
    MAX_RETRIES = 3
    QUERY_TIMEOUT = 30
    CONNECTION_POOL_SIZE = 10
    
    # RAG Configuration
    EMBEDDING_MODEL = "mistral-embed"
    EMBEDDING_DIMENSIONS = 1024
    DEFAULT_SIMILARITY_THRESHOLD = 0.7
    MAX_CONTEXT_LENGTH = 8000
    MAX_SEARCH_RESULTS = 20
    
    # Chunking Configuration
    CHUNK_SIZES = {
        'small': {'size': 500, 'overlap': 50},
        'medium': {'size': 1000, 'overlap': 100},
        'large': {'size': 1500, 'overlap': 150}
    }
    DEFAULT_CHUNK_SIZE = 'medium'
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB = 50
    ALLOWED_FILE_TYPES = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'txt': 'text/plain',
        'md': 'text/markdown',
        'csv': 'text/csv',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    
    # UI Configuration
    THEME = {
        'primary_color': '#1f77b4',
        'background_color': '#ffffff',
        'secondary_background_color': '#f0f2f6',
        'text_color': '#262730',
        'font': 'sans serif'
    }
    
    # Session Configuration
    SESSION_TIMEOUT_DAYS = 30
    SESSION_CLEANUP_INTERVAL_HOURS = 24
    
    # AI Model Configuration
    DEFAULT_MODEL = 'mistral-medium'
    AVAILABLE_MODELS = {
        'normal': 'mistral-medium',
        'advanced': 'mistral-large',
        'fast': 'mistral-small'
    }
    
    # Rate Limiting
    RATE_LIMITS = {
        'messages_per_minute': 20,
        'files_per_hour': 10,
        'queries_per_minute': 30
    }
    
    @classmethod
    def get_supabase_url(cls) -> str:
        """Get Supabase URL from secrets or environment."""
        try:
            return st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
        except:
            return os.getenv("SUPABASE_URL", "")
    
    @classmethod
    def get_supabase_key(cls) -> str:
        """Get Supabase key from secrets or environment."""
        try:
            return st.secrets.get("SUPABASE_ANON_KEY", os.getenv("SUPABASE_ANON_KEY", ""))
        except:
            return os.getenv("SUPABASE_ANON_KEY", "")
    
    @classmethod
    def get_mistral_key(cls) -> str:
        """Get Mistral API key from secrets or environment."""
        try:
            return st.secrets.get("MISTRAL_API_KEY", os.getenv("MISTRAL_API_KEY", ""))
        except:
            return os.getenv("MISTRAL_API_KEY", "")
    
    @classmethod
    def get_openai_key(cls) -> str:
        """Get OpenAI API key from secrets or environment."""
        try:
            return st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        except:
            return os.getenv("OPENAI_API_KEY", "")
    
    @classmethod
    def validate_configuration(cls) -> Dict[str, bool]:
        """Validate all configuration requirements."""
        checks = {
            'supabase_url': bool(cls.get_supabase_url()),
            'supabase_key': bool(cls.get_supabase_key()),
            'mistral_key': bool(cls.get_mistral_key()),
            'openai_key': bool(cls.get_openai_key())
        }
        
        return checks
    
    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """Get configuration summary for debugging."""
        validation = cls.validate_configuration()
        
        return {
            'app': {
                'title': cls.APP_TITLE,
                'version': cls.APP_VERSION,
                'description': cls.APP_DESCRIPTION
            },
            'database': {
                'max_retries': cls.MAX_RETRIES,
                'query_timeout': cls.QUERY_TIMEOUT,
                'connection_pool_size': cls.CONNECTION_POOL_SIZE
            },
            'rag': {
                'model': cls.EMBEDDING_MODEL,
                'dimensions': cls.EMBEDDING_DIMENSIONS,
                'similarity_threshold': cls.DEFAULT_SIMILARITY_THRESHOLD,
                'max_context_length': cls.MAX_CONTEXT_LENGTH
            },
            'files': {
                'max_size_mb': cls.MAX_FILE_SIZE_MB,
                'allowed_types': list(cls.ALLOWED_FILE_TYPES.keys())
            },
            'validation': validation,
            'ready': all(validation.values())
        }


# Environment-specific configurations
class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    LOG_LEVEL = logging.DEBUG
    SESSION_TIMEOUT_DAYS = 7
    MAX_FILE_SIZE_MB = 10


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    LOG_LEVEL = logging.INFO
    SESSION_TIMEOUT_DAYS = 30
    MAX_FILE_SIZE_MB = 50


class TestingConfig(Config):
    """Testing environment configuration."""
    DEBUG = True
    LOG_LEVEL = logging.DEBUG
    SESSION_TIMEOUT_DAYS = 1
    MAX_FILE_SIZE_MB = 5
    MAX_SEARCH_RESULTS = 5


def get_config() -> Config:
    """Get configuration based on environment."""
    env = os.getenv('PHARMGPT_ENV', 'production').lower()
    
    if env == 'development':
        return DevelopmentConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return ProductionConfig()


# Global configuration instance
config = get_config()

# Export commonly used values
APP_TITLE = config.APP_TITLE
APP_ICON = config.APP_ICON
APP_VERSION = config.APP_VERSION
MAX_FILE_SIZE_MB = config.MAX_FILE_SIZE_MB
ALLOWED_FILE_TYPES = config.ALLOWED_FILE_TYPES
DEFAULT_SIMILARITY_THRESHOLD = config.DEFAULT_SIMILARITY_THRESHOLD