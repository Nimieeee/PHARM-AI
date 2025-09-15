"""
OCR Manager for PharmGPT
Handles text extraction from images using multiple OCR engines
"""

import logging
from typing import Optional, Tuple
import tempfile
import os
from PIL import Image

# Configure logging
logger = logging.getLogger(__name__)

class OCRManager:
    """Manages OCR operations with multiple fallback engines."""
    
    def __init__(self):
        self.available_engines = []
        self._check_available_engines()
    
    def _check_available_engines(self):
        """Check which OCR engines are available."""
        # Check EasyOCR (no system dependencies)
        try:
            import easyocr
            self.available_engines.append('easyocr')
            logger.info("✅ EasyOCR available")
        except ImportError:
            logger.info("⚠️ EasyOCR not available")
        
        # Check Tesseract
        try:
            import pytesseract
            # Try to run tesseract to see if it's installed
            pytesseract.get_tesseract_version()
            self.available_engines.append('tesseract')
            logger.info("✅ Tesseract OCR available")
        except (ImportError, Exception) as e:
            logger.info(f"⚠️ Tesseract OCR not available: {e}")
        
        logger.info(f"Available OCR engines: {self.available_engines}")
    
    def extract_text_from_image(self, image_path: str, image_info: str = "") -> str:
        """Extract text from image using the best available OCR engine."""
        if not self.available_engines:
            return f"{image_info}OCR engines not available. Please install tesseract-ocr system package or easyocr Python package for text extraction from images."
        
        # Try each available engine
        for engine in self.available_engines:
            try:
                if engine == 'easyocr':
                    text = self._extract_with_easyocr(image_path)
                elif engine == 'tesseract':
                    text = self._extract_with_tesseract(image_path)
                else:
                    continue
                
                if text and text.strip():
                    logger.info(f"✅ Text extracted using {engine}: {len(text)} characters")
                    return f"{image_info}OCR Extracted Text (using {engine}):\n{text.strip()}"
                
            except Exception as e:
                logger.warning(f"OCR engine {engine} failed: {e}")
                continue
        
        # No text found with any engine
        return f"{image_info}This image appears to contain visual content (charts, graphs, or diagrams) but no readable text was detected by OCR engines."
    
    def _extract_with_easyocr(self, image_path: str) -> str:
        """Extract text using EasyOCR."""
        import easyocr
        
        # Initialize EasyOCR reader (supports multiple languages)
        reader = easyocr.Reader(['en'])  # English only for now, can add more languages
        
        # Extract text
        results = reader.readtext(image_path)
        
        # Combine all detected text
        extracted_text = []
        for (bbox, text, confidence) in results:
            if confidence > 0.5:  # Only include text with reasonable confidence
                extracted_text.append(text)
        
        return ' '.join(extracted_text)
    
    def _extract_with_tesseract(self, image_path: str) -> str:
        """Extract text using Tesseract OCR."""
        import pytesseract
        from PIL import Image
        
        # Open and process image
        image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Extract text using different PSM modes for better results
        psm_modes = [6, 8, 13]  # Different page segmentation modes
        
        for psm in psm_modes:
            try:
                config = f'--psm {psm}'
                text = pytesseract.image_to_string(image, config=config)
                if text and text.strip():
                    return text
            except:
                continue
        
        return ""
    
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
        """Get status of available OCR engines."""
        return {
            'available_engines': self.available_engines,
            'easyocr_available': 'easyocr' in self.available_engines,
            'tesseract_available': 'tesseract' in self.available_engines,
            'ocr_working': len(self.available_engines) > 0
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