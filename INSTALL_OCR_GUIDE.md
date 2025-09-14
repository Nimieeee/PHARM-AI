# OCR Installation Guide for Image Processing

## Overview
To enable text extraction from images (OCR), you need to install Tesseract OCR on your system.

## Installation Instructions

### For Local Development

#### macOS (using Homebrew)
```bash
brew install tesseract
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

#### Windows
1. Download Tesseract installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer
3. Add Tesseract to your PATH environment variable

#### CentOS/RHEL/Fedora
```bash
sudo yum install tesseract
# or for newer versions:
sudo dnf install tesseract
```

### For Streamlit Cloud Deployment

Streamlit Cloud doesn't support system package installation, so OCR functionality will be limited. The app will gracefully handle this by:

1. Attempting OCR if tesseract is available
2. Falling back to image metadata extraction if OCR fails
3. Providing clear error messages about OCR availability

### Verification

Test if Tesseract is properly installed:

```bash
tesseract --version
```

You should see version information if installation was successful.

## Supported Image Formats

With OCR enabled, the following image formats are supported:
- PNG
- JPG/JPEG
- GIF
- BMP
- TIFF
- WebP

## Features

### Image Processing Capabilities
- **Image Metadata**: Size, format, dimensions
- **OCR Text Extraction**: Extracts readable text from images
- **Error Handling**: Graceful fallback when OCR is unavailable
- **Multiple Formats**: Support for common image formats

### PPTX Processing Capabilities
- **Slide Text**: Extracts text from all slides
- **Table Content**: Processes tables within slides
- **Speaker Notes**: Includes presentation notes
- **Structured Output**: Organizes content by slide number

## Troubleshooting

### Common Issues

1. **"tesseract not found" error**
   - Ensure Tesseract is installed and in PATH
   - Restart your terminal/IDE after installation

2. **Poor OCR accuracy**
   - Ensure images have good contrast and resolution
   - OCR works best with clear, high-contrast text

3. **Streamlit Cloud limitations**
   - OCR may not work on Streamlit Cloud
   - App will still process images for metadata
   - Consider using local deployment for full OCR functionality

## Usage in PharmGPT

Once installed, you can:
1. Upload images containing text (screenshots, scanned documents, etc.)
2. Upload PowerPoint presentations (.pptx files)
3. The RAG system will extract and index the text content
4. Ask questions about the content in uploaded images/presentations