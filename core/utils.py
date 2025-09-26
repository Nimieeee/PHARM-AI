"""
Utility functions for PharmGPT
Document processing, error handling, and common operations
"""

import logging
import asyncio
import hashlib
import mimetypes
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
import io
import os
import tempfile

import streamlit as st

# Configure logging
logger = logging.getLogger(__name__)

# Document processing imports
try:
    import PyPDF2
    import docx2txt
    from PIL import Image
    import pandas as pd
    DOCUMENT_PROCESSING_AVAILABLE = True
except ImportError:
    DOCUMENT_PROCESSING_AVAILABLE = False
    logger.warning("Document processing libraries not available")


def run_async(coro) -> Any:
    """Helper to run async functions in Streamlit context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        logger.error(f"Error running async operation: {e}")
        raise


def safe_execute(func, *args, default=None, **kwargs) -> Any:
    """Safely execute a function with error handling."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Error executing {func.__name__}: {e}")
        return default


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    import uuid
    unique_id = str(uuid.uuid4())
    return f"{prefix}_{unique_id}" if prefix else unique_id


def format_timestamp(timestamp: Union[str, datetime], format_str: str = "%Y-%m-%d %H:%M") -> str:
    """Format timestamp for display."""
    try:
        if isinstance(timestamp, str):
            # Parse ISO format
            if 'T' in timestamp:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        else:
            dt = timestamp
        
        return dt.strftime(format_str)
    except Exception:
        return str(timestamp)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'[^\w\s.-]', '', filename)
    # Limit length
    if len(filename) > 100:
        name, ext = os.path.splitext(filename)
        filename = name[:95] + ext
    
    return filename


def get_file_hash(file_content: bytes) -> str:
    """Generate hash for file content."""
    return hashlib.sha256(file_content).hexdigest()


def validate_file_size(file_size: int, max_size_mb: int = 50) -> Tuple[bool, str]:
    """Validate file size."""
    max_bytes = max_size_mb * 1024 * 1024
    if file_size > max_bytes:
        return False, f"File size ({file_size / 1024 / 1024:.1f} MB) exceeds limit ({max_size_mb} MB)"
    return True, "Valid size"


def validate_file_type(filename: str, allowed_types: Dict[str, str]) -> Tuple[bool, str]:
    """Validate file type based on extension."""
    if not filename:
        return False, "No filename provided"
    
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    if ext in allowed_types:
        return True, f"Valid {ext} file"
    
    return False, f"File type '{ext}' not supported. Allowed: {', '.join(allowed_types.keys())}"


class DocumentProcessor:
    """Handle various document types for text extraction."""
    
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> Tuple[bool, str, str]:
        """Extract text from PDF file."""
        if not DOCUMENT_PROCESSING_AVAILABLE:
            return False, "", "PDF processing not available"
        
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num + 1}: {e}")
            
            full_text = "\n\n".join(text_parts)
            
            if not full_text.strip():
                return False, "", "No readable text found in PDF"
            
            return True, full_text, f"Extracted text from {len(pdf_reader.pages)} pages"
            
        except Exception as e:
            return False, "", f"Error processing PDF: {str(e)}"
    
    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> Tuple[bool, str, str]:
        """Extract text from DOCX file."""
        if not DOCUMENT_PROCESSING_AVAILABLE:
            return False, "", "DOCX processing not available"
        
        try:
            # Save to temporary file for docx2txt
            with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            try:
                text = docx2txt.process(tmp_file_path)
                if text.strip():
                    return True, text, "Successfully extracted text from DOCX"
                else:
                    return False, "", "No text content found in DOCX"
            finally:
                # Clean up temporary file
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
                    
        except Exception as e:
            return False, "", f"Error processing DOCX: {str(e)}"
    
    @staticmethod
    def extract_text_from_txt(file_content: bytes) -> Tuple[bool, str, str]:
        """Extract text from plain text file."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    text = file_content.decode(encoding)
                    return True, text, f"Successfully decoded as {encoding}"
                except UnicodeDecodeError:
                    continue
            
            return False, "", "Could not decode text file"
            
        except Exception as e:
            return False, "", f"Error processing text file: {str(e)}"
    
    @staticmethod
    def extract_text_from_csv(file_content: bytes) -> Tuple[bool, str, str]:
        """Extract text from CSV file."""
        if not DOCUMENT_PROCESSING_AVAILABLE:
            return False, "", "CSV processing not available"
        
        try:
            csv_file = io.StringIO(file_content.decode('utf-8'))
            df = pd.read_csv(csv_file)
            
            # Convert DataFrame to readable text format
            text_parts = [f"CSV Data ({len(df)} rows, {len(df.columns)} columns)\n"]
            text_parts.append("Columns: " + ", ".join(df.columns))
            text_parts.append("\nData Preview:")
            text_parts.append(df.head(10).to_string())
            
            if len(df) > 10:
                text_parts.append(f"\n... and {len(df) - 10} more rows")
            
            full_text = "\n".join(text_parts)
            return True, full_text, f"Processed CSV with {len(df)} rows"
            
        except Exception as e:
            return False, "", f"Error processing CSV: {str(e)}"
    
    @classmethod
    def process_uploaded_file(cls, uploaded_file) -> Tuple[bool, str, str, Dict]:
        """Process uploaded file and extract text content."""
        if not uploaded_file:
            return False, "", "No file uploaded", {}
        
        try:
            # Get file info
            filename = sanitize_filename(uploaded_file.name)
            file_size = len(uploaded_file.getvalue())
            file_type = filename.split('.')[-1].lower() if '.' in filename else ''
            
            # Create metadata
            metadata = {
                'filename': filename,
                'file_type': file_type,
                'file_size': file_size,
                'upload_time': datetime.now().isoformat(),
                'file_hash': get_file_hash(uploaded_file.getvalue())
            }
            
            # Process based on file type
            file_content = uploaded_file.getvalue()
            
            if file_type == 'pdf':
                success, text, message = cls.extract_text_from_pdf(file_content)
            elif file_type == 'docx':
                success, text, message = cls.extract_text_from_docx(file_content)
            elif file_type in ['txt', 'md']:
                success, text, message = cls.extract_text_from_txt(file_content)
            elif file_type == 'csv':
                success, text, message = cls.extract_text_from_csv(file_content)
            else:
                # Try as plain text
                success, text, message = cls.extract_text_from_txt(file_content)
                if not success:
                    return False, "", f"Unsupported file type: {file_type}", metadata
            
            if success and text.strip():
                metadata['text_length'] = len(text)
                metadata['word_count'] = len(text.split())
                return True, text, message, metadata
            else:
                return False, "", message, metadata
                
        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}")
            return False, "", f"Error processing file: {str(e)}", {}


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def create_download_link(content: str, filename: str, mime_type: str = "text/plain") -> str:
    """Create a download link for content."""
    import base64
    
    b64_content = base64.b64encode(content.encode()).decode()
    href = f'<a href="data:{mime_type};base64,{b64_content}" download="{filename}">Download {filename}</a>'
    return href


class ErrorHandler:
    """Centralized error handling and logging."""
    
    @staticmethod
    def log_error(error: Exception, context: str = "", user_id: str = None):
        """Log error with context."""
        error_info = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.error(f"Error in {context}: {error}", extra=error_info)
    
    @staticmethod
    def handle_streamlit_error(error: Exception, context: str = "", show_details: bool = False):
        """Handle and display error in Streamlit interface."""
        ErrorHandler.log_error(error, context)
        
        if show_details:
            st.error(f"Error in {context}: {str(error)}")
        else:
            st.error("An error occurred. Please try again or contact support if the issue persists.")
    
    @staticmethod
    def create_error_report(error: Exception, context: Dict = None) -> Dict:
        """Create detailed error report."""
        return {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'timestamp': datetime.now().isoformat(),
            'stack_trace': str(error) if hasattr(error, '__traceback__') else None
        }


def validate_environment() -> Dict[str, Any]:
    """Validate environment setup and dependencies."""
    checks = {
        'document_processing': DOCUMENT_PROCESSING_AVAILABLE,
        'streamlit_version': st.__version__ if hasattr(st, '__version__') else 'Unknown',
        'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
        'temp_directory': os.path.exists(tempfile.gettempdir()),
        'write_permissions': os.access('.', os.W_OK)
    }
    
    return checks


# Export commonly used functions
__all__ = [
    'run_async', 'safe_execute', 'generate_id', 'format_timestamp',
    'truncate_text', 'sanitize_filename', 'get_file_hash',
    'validate_file_size', 'validate_file_type', 'DocumentProcessor',
    'format_file_size', 'create_download_link', 'ErrorHandler',
    'validate_environment'
]