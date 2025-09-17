"""
OCR Manager for PharmGPT
Handles text extraction from images using Google Vision API and Tesseract OCR
Optimized for Streamlit Cloud deployment with multiple OCR backends
"""

import logging
import tempfile
import os
import base64
from PIL import Image

# Configure logging
logger = logging.getLogger(__name__)

class OCRManager:
    """Manages OCR operations using Google Vision API and Tesseract fallback."""
    
    def __init__(self):
        self.google_vision_available = self._check_google_vision()
        self.tesseract_available = self._check_tesseract()
        
        if self.google_vision_available:
            logger.info("✅ Google Vision API available (primary)")
        elif self.tesseract_available:
            logger.info("✅ Tesseract OCR available (fallback)")
        else:
            logger.warning("⚠️ No OCR engines available")
    
    def _check_google_vision(self) -> bool:
        """Check if Google Vision API is available and configured."""
        try:
            from google.cloud import vision
            import json
            
            # Check for credentials in Streamlit secrets or environment
            import streamlit as st
            
            try:
                google_creds = st.secrets.get("GOOGLE_APPLICATION_CREDENTIALS_JSON", 
                                            os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON"))
                google_creds_file = st.secrets.get("GOOGLE_APPLICATION_CREDENTIALS", 
                                                 os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
            except Exception:
                # Fallback to environment variables if secrets not available
                google_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
                google_creds_file = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
            
            if google_creds:
                # Credentials provided as JSON string
                return True
            elif google_creds_file:
                # Credentials provided as file path
                return True
            else:
                logger.debug("Google Vision API credentials not configured")
                return False
                
        except ImportError:
            logger.debug("Google Vision API client not installed")
            return False
        except Exception as e:
            logger.debug(f"Google Vision API not available: {e}")
            return False
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract OCR is available."""
        try:
            import pytesseract
            # Try to get version to verify it's working
            pytesseract.get_tesseract_version()
            logger.info("✅ Tesseract OCR available")
            return True
        except ImportError:
            logger.debug("Tesseract OCR not installed")
            return False
        except Exception:
            logger.debug("Tesseract OCR not available")
            return False
    
    def extract_text_from_image(self, image_path: str, image_info: str = "") -> str:
        """Extract text from image using Google Vision API (primary) or Tesseract OCR (fallback)."""
        
        # Try Google Vision API first
        if self.google_vision_available:
            try:
                text = self._extract_with_google_vision(image_path)
                if text and text.strip():
                    logger.info(f"✅ Google Vision extracted: {len(text)} characters")
                    return f"{image_info}📄 Extracted Text (Google Vision):\n{text.strip()}"
            except Exception as e:
                logger.warning(f"Google Vision failed, falling back to Tesseract: {e}")
        
        # Fallback to Tesseract OCR
        if self.tesseract_available:
            try:
                text = self._extract_with_tesseract(image_path)
                if text and text.strip():
                    logger.info(f"✅ Tesseract extracted: {len(text)} characters")
                    return f"{image_info}📄 Extracted Text (Tesseract):\n{text.strip()}"
            except Exception as e:
                logger.error(f"Tesseract extraction failed: {e}")
        
        # No OCR available or all failed
        if not self.google_vision_available and not self.tesseract_available:
            return f"{image_info}OCR not available. Please configure Google Vision API or install Tesseract OCR."
        else:
            return f"{image_info}📷 This image appears to contain visual content but no readable text was detected."
    
    def _extract_with_google_vision(self, image_path: str) -> str:
        """Extract text using Google Vision API."""
        from google.cloud import vision
        import json
        
        # Initialize the client
        client = self._get_vision_client()
        
        # Read the image file
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        # Perform text detection
        response = client.text_detection(image=image)
        texts = response.text_annotations
        
        if texts:
            # The first annotation contains all detected text
            return texts[0].description
        
        # Check for errors
        if response.error.message:
            raise Exception(f"Google Vision API error: {response.error.message}")
        
        return ""
    
    def _get_vision_client(self):
        """Get Google Vision client with proper authentication."""
        from google.cloud import vision
        import json
        import streamlit as st
        
        # Check for JSON credentials in Streamlit secrets or environment variable
        try:
            google_creds_json = st.secrets.get("GOOGLE_APPLICATION_CREDENTIALS_JSON", 
                                             os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON"))
        except Exception:
            google_creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        
        if google_creds_json:
            # Parse JSON credentials and create client
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(google_creds_json)
                temp_creds_path = f.name
            
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_creds_path
            client = vision.ImageAnnotatorClient()
            
            # Clean up temp file
            os.unlink(temp_creds_path)
            return client
        else:
            # Use default credentials (file path or service account)
            return vision.ImageAnnotatorClient()
    
    def _extract_with_tesseract(self, image_path: str) -> str:
        """Extract text using Tesseract OCR with optimized settings."""
        import pytesseract
        from PIL import Image
        
        # Open and process image
        image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Try different OCR configurations for better results
        configs = [
            '--psm 6',  # Uniform block of text
            '--psm 8',  # Single word
            '--psm 13', # Raw line. Treat the image as a single text line
            '--psm 3',  # Fully automatic page segmentation (default)
        ]
        
        best_text = ""
        max_length = 0
        
        for config in configs:
            try:
                text = pytesseract.image_to_string(image, config=config)
                if text and len(text.strip()) > max_length:
                    best_text = text
                    max_length = len(text.strip())
            except Exception as e:
                logger.debug(f"Config {config} failed: {e}")
                continue
        
        return best_text
    
    def process_image_file(self, uploaded_file, file_content: bytes) -> str:
        """Process an uploaded image file and extract text."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name
            
            try:
                # Open and get image info
                image = Image.open(tmp_path)
                image_info = f"Image: {uploaded_file.name}\nSize: {image.size[0]}x{image.size[1]} pixels\nFormat: {image.format}\n\n"
                
                # Extract text using OCR
                result = self.extract_text_from_image(tmp_path, image_info)
                
                return result
                
            finally:
                # Clean up temporary file
                os.unlink(tmp_path)
                
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return f"[Image: {uploaded_file.name} - {len(file_content)} bytes - Processing failed: {e}]"
    
    def get_ocr_status(self) -> dict:
        """Get status of Tesseract OCR engine."""
        return {
            'tesseract_available': self.tesseract_available,
            'ocr_working': self.tesseract_available,
            'engine': 'tesseract',
            'note': 'Only text content will be extracted from images for processing'
        }

# Global OCR manager instance
ocr_manager = OCRManager()

def extract_text_from_image(image_path: str, image_info: str = "") -> str:
    """Extract text from image using available OCR engines."""
    return ocr_manager.extract_text_from_image(image_path, image_info)

def process_image_file(uploaded_file, file_content: bytes) -> str:
    """Process uploaded image file and extract text."""
    return ocr_manager.process_image_file(uploaded_file, file_content)

def get_ocr_status() -> dict:
    """Get OCR engine availability status."""
    return ocr_manager.get_ocr_status()