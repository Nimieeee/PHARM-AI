"""
OCR Manager for PharmGPT
Handles text extraction from images using Tesseract OCR
Optimized for Streamlit Cloud deployment
"""

import logging
import tempfile
import os
from PIL import Image

# Configure logging
logger = logging.getLogger(__name__)

class OCRManager:
    """Manages OCR operations using Tesseract (pre-installed on Streamlit Cloud)."""
    
    def __init__(self):
        self.tesseract_available = self._check_tesseract()
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract OCR is available."""
        try:
            import pytesseract
            # Try to get version to verify it's working
            pytesseract.get_tesseract_version()
            logger.info("✅ Tesseract OCR available")
            return True
        except (ImportError, Exception) as e:
            logger.warning(f"⚠️ Tesseract OCR not available: {e}")
            return False
    
    def extract_text_from_image(self, image_path: str, image_info: str = "") -> str:
        """Extract text from image using Tesseract OCR."""
        if not self.tesseract_available:
            return f"{image_info}OCR not available. Tesseract OCR is required for text extraction from images."
        
        try:
            text = self._extract_with_tesseract(image_path)
            
            if text and text.strip():
                logger.info(f"✅ Text extracted: {len(text)} characters")
                return f"{image_info}📄 Extracted Text:\n{text.strip()}"
            else:
                return f"{image_info}📷 This image appears to contain visual content (charts, graphs, or diagrams) but no readable text was detected."
                
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return f"{image_info}❌ Text extraction failed: {str(e)}"
    
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