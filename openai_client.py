"""
Clean OpenAI-compatible API client for PharmGPT
Simple, reliable chat completions with Groq and OpenRouter
"""

import openai
from groq import Groq
import os
import logging
import time
import re
from typing import Iterator, Dict, List

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_api_keys():
    """Get API keys from Streamlit secrets or environment variables (fallback)."""
    import streamlit as st
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Try Streamlit secrets first, fallback to environment variables
    try:
        logger.info("Attempting to get API keys from Streamlit secrets...")
        
        # Check if secrets are available
        if hasattr(st, 'secrets'):
            logger.info("st.secrets is available")
            groq_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY"))
            openrouter_key = st.secrets.get("OPENROUTER_API_KEY", os.environ.get("OPENROUTER_API_KEY"))
            
            logger.info(f"Keys from secrets - Groq: {'Found' if groq_key else 'Missing'}, OpenRouter: {'Found' if openrouter_key else 'Missing'}")
        else:
            logger.warning("st.secrets not available, using environment variables")
            groq_key = os.environ.get("GROQ_API_KEY")
            openrouter_key = os.environ.get("OPENROUTER_API_KEY")
            
    except Exception as e:
        logger.error(f"Error accessing secrets: {e}")
        # Fallback to environment variables if secrets not available
        groq_key = os.environ.get("GROQ_API_KEY")
        openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        logger.info("Using environment variables as fallback")
    
    return groq_key, openrouter_key

def get_model_configs():
    """Get model configurations with API keys - 2 optimized modes."""
    groq_key, openrouter_key = get_api_keys()
    
    return {
        "fast": {
            "model": "gemma2-9b-it",
            "api_key": groq_key,
            "base_url": "https://api.groq.com/openai/v1",
            "description": "Fast Mode",
        },
        "premium": {
            "model": "qwen/qwen3-32b",
            "api_key": openrouter_key,
            "base_url": "https://openrouter.ai/api/v1", 
            "description": "Premium Mode",
        }
    }

def get_available_model_modes() -> Dict:
    """Get available model modes based on API key availability."""
    available_modes = {}
    model_configs = get_model_configs()
    
    for mode, config in model_configs.items():
        if config["api_key"]:
            available_modes[mode] = config
    
    return available_modes

def get_model_token_limits() -> Dict:
    """Get unified token limits for all models."""
    return {
        "unified": {
            "max_tokens": 8192,
            "context_window": 131072,
            "description": "Unified high-capacity output for all models"
        }
    }

def get_optimal_max_tokens(model: str) -> int:
    """Get optimized max_tokens for speed."""
    if "gemma" in model:
        return 8192
    elif "qwen" in model:
        return 8192
    else:
        return 8192

def _get_client_for_model(model: str):
    """Get appropriate client for specific model."""
    model_configs = get_model_configs()
    
    for mode, config in model_configs.items():
        if config["model"] == model:
            if not config["api_key"]:
                raise ValueError(f"API key not configured for {mode} mode")
            
            return openai.OpenAI(
                api_key=config["api_key"],
                base_url=config["base_url"]
            )
    
    raise ValueError(f"Unknown model: {model}")

def chat_completion_fast(model: str, messages: List[Dict]) -> str:
    """Ultra-fast non-streaming completion for maximum speed."""
    try:
        client = _get_client_for_model(model)
        model_configs = get_model_configs()
        
        # Find model config
        model_config = None
        for mode, config in model_configs.items():
            if config["model"] == model:
                model_config = config
                break
        
        if not model_config:
            raise ValueError(f"Model config not found for: {model}")
        
        # Fast completion without streaming
        max_tokens = get_optimal_max_tokens(model)
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            max_tokens=max_tokens,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stream=False  # No streaming for maximum speed
        )
        
        return response.choices[0].message.content
    except openai.RateLimitError as e:
        logger.warning(f"Rate limit error for {model}: {e}. Attempting fallback.")
        # Fallback logic
        fallback_model = "qwen/qwen2-32b-instruct" if model == "groq/gemma2-9b-it" else "groq/gemma2-9b-it"
        logger.info(f"Falling back to {fallback_model}")
        try:
            client = _get_client_for_model(fallback_model)
            response = client.chat.completions.create(
                model=fallback_model,
                messages=messages,
                temperature=0.5,
                max_tokens=8192,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as fallback_e:
            logger.error(f"Fallback failed: {fallback_e}")
            return f"Error: API service capacity exceeded for all available models. Please try again later."
    except Exception as e:
        logger.error(f"Error in fast completion: {e}")
        return f"Error generating response: {str(e)}"

def chat_completion_stream(model: str, messages: List[Dict]) -> Iterator[str]:
    """Generate ultra-fluid streaming chat completion with advanced features."""
    try:
        client = _get_client_for_model(model)
        model_configs = get_model_configs()
        
        # Find model config
        model_config = None
        for mode, config in model_configs.items():
            if config["model"] == model:
                model_config = config
                break
        
        if not model_config:
            raise ValueError(f"Model config not found for: {model}")
        
        # Optimized streaming for speed
        max_tokens = get_optimal_max_tokens(model)
        logger.info(f"Starting optimized stream with {max_tokens} tokens for model: {model}")
        
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=model_config.get("temperature", 0.3),  # Lower temp for faster, focused responses
            max_tokens=max_tokens,
            top_p=0.9,  # Slightly more focused
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=None # Added stop
        )
        
        # Controlled streaming at ~6 tokens per second
        buffer = ""
        word_count = 0
        last_yield_time = time.time()
        
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                buffer += content
                
                # Controlled yield conditions for ~6 tokens per second:
                current_time = time.time()
                time_since_last_yield = current_time - last_yield_time
                
                # Yield at controlled rate for smooth reading experience
                should_yield = (
                    len(buffer) >= 6 or  # ~6 characters per chunk (roughly 1 token)
                    time_since_last_yield >= 0.167 or  # ~6 tokens per second (1000ms/6 = 167ms)
                    any(punct in buffer for punct in ['. ', '! ', '? ', '\n']) or  # Sentence breaks
                    ' ' in buffer and len(buffer) >= 3  # Word boundaries
                )
                
                if should_yield and buffer.strip():
                    yield buffer
                    buffer = ""
                    word_count += len(re.findall(r'\S+', buffer))
                    last_yield_time = current_time
                    
                    # Small delay for controlled streaming speed
                    time.sleep(0.02)  # 20ms additional delay for smoother appearance
            
            # Silent finish reason handling (no user-visible messages)
            if chunk.choices[0].finish_reason is not None:
                # Yield any remaining buffer content
                if buffer.strip():
                    yield buffer
                
                finish_reason = chunk.choices[0].finish_reason
                logger.info(f"Stream completed: {finish_reason} (total words: ~{word_count})")
                
    except openai.RateLimitError as e:
        logger.warning(f"Rate limit error for {model}: {e}. Attempting fallback.")
        # Fallback logic
        fallback_model = "qwen/qwen2-32b-instruct" if model == "groq/gemma2-9b-it" else "groq/gemma2-9b-it"
        logger.info(f"Falling back to {fallback_model}")
        try:
            yield from chat_completion_stream(fallback_model, messages)
        except Exception as fallback_e:
            logger.error(f"Fallback failed: {fallback_e}")
            yield f"Error: API service capacity exceeded for all available models. Please try again later."

    except Exception as e:
        logger.error(f"Streaming error: {str(e)}")
        yield f"Error: {str(e)}"

def chat_completion(model: str, messages: List[Dict]) -> str:
    """Generate non-streaming chat completion with advanced features."""
    try:
        client = _get_client_for_model(model)
        model_configs = get_model_configs()
        
        # Find model config
        model_config = None
        for mode, config in model_configs.items():
            if config["model"] == model:
                model_config = config
                break
        
        if not model_config:
            raise ValueError(f"Model config not found for: {model}")
        
        # Standard OpenAI-compatible completion
        max_tokens = 8192
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.5,
            max_tokens=max_tokens,
            top_p=0.95,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        
        return response.choices[0].message.content
    except openai.RateLimitError as e:
        logger.warning(f"Rate limit error for {model}: {e}. Attempting fallback.")
        # Fallback logic
        fallback_model = "qwen/qwen2-32b-instruct" if model == "groq/gemma2-9b-it" else "groq/gemma2-9b-it"
        logger.info(f"Falling back to {fallback_.model}")
        try:
            return chat_completion(fallback_model, messages)
        except Exception as fallback_e:
            logger.error(f"Fallback failed: {fallback_e}")
            return f"Error: API service capacity exceeded for all available models. Please try again later."
    except Exception as e:
        logger.error(f"Chat completion error: {str(e)}")
        return f"Error: {str(e)}"

def test_api_connection(model: str) -> bool:
    """Test API connection for a specific model."""
    try:
        client = _get_client_for_model(model)
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.5,
            max_tokens=10
        )
        
        return True
        
    except Exception as e:
        logger.error(f"API connection test failed for {model}: {e}")
        return False
