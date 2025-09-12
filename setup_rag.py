#!/usr/bin/env python3
"""
Setup script for RAG system dependencies
Helps install system-level dependencies like Tesseract OCR
"""

import subprocess
import sys
import platform
import os

def run_command(command):
    """Run a shell command and return success status."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def install_tesseract():
    """Install Tesseract OCR based on the operating system."""
    system = platform.system().lower()
    
    print("🔍 Installing Tesseract OCR...")
    
    if system == "darwin":  # macOS
        print("📱 Detected macOS - Installing via Homebrew...")
        success, stdout, stderr = run_command("brew install tesseract")
        if success:
            print("✅ Tesseract installed successfully!")
        else:
            print("❌ Failed to install Tesseract via Homebrew")
            print("Please install Homebrew first: https://brew.sh/")
            print("Then run: brew install tesseract")
    
    elif system == "linux":
        print("🐧 Detected Linux - Installing via apt...")
        success, stdout, stderr = run_command("sudo apt-get update && sudo apt-get install -y tesseract-ocr")
        if success:
            print("✅ Tesseract installed successfully!")
        else:
            print("❌ Failed to install Tesseract via apt")
            print("Please run: sudo apt-get install tesseract-ocr")
    
    elif system == "windows":
        print("🪟 Detected Windows")
        print("Please install Tesseract manually:")
        print("1. Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. Install the executable")
        print("3. Add Tesseract to your PATH")
    
    else:
        print(f"❓ Unknown system: {system}")
        print("Please install Tesseract OCR manually for your system")

def check_tesseract():
    """Check if Tesseract is installed and working."""
    print("🔍 Checking Tesseract installation...")
    success, stdout, stderr = run_command("tesseract --version")
    
    if success:
        version = stdout.split('\n')[0] if stdout else "Unknown version"
        print(f"✅ Tesseract found: {version}")
        return True
    else:
        print("❌ Tesseract not found or not working")
        return False

def install_python_dependencies():
    """Install Python dependencies."""
    print("🐍 Installing Python dependencies...")
    
    # Install requirements
    success, stdout, stderr = run_command(f"{sys.executable} -m pip install -r requirements.txt")
    
    if success:
        print("✅ Python dependencies installed successfully!")
    else:
        print("❌ Failed to install Python dependencies")
        print("Error:", stderr)
        return False
    
    return True

def test_rag_system():
    """Test if the RAG system can be imported and initialized."""
    print("🧪 Testing RAG system...")
    
    try:
        from rag_system import RAGSystem
        from rag_interface import initialize_rag_system
        print("✅ RAG system imports successful!")
        
        # Test basic functionality
        rag = RAGSystem("test_user")
        print("✅ RAG system initialization successful!")
        
        return True
    except Exception as e:
        print(f"❌ RAG system test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 PharmBot RAG System Setup")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found. Please run this script from the PharmBot directory.")
        return
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Setup failed at Python dependencies step")
        return
    
    # Check/install Tesseract
    if not check_tesseract():
        install_tesseract()
        
        # Check again after installation
        if not check_tesseract():
            print("⚠️  Tesseract installation may have failed. Image OCR might not work.")
            print("You can continue without it, but image processing will be limited.")
    
    # Test RAG system
    if test_rag_system():
        print("\n🎉 RAG system setup completed successfully!")
        print("\n📚 You can now:")
        print("- Upload PDF, Word, CSV, and text documents")
        print("- Upload images for OCR text extraction")
        print("- Use RAG-enhanced conversations")
        print("- Search through your document knowledge base")
        print("\n🚀 Run: streamlit run streamlit_app.py")
    else:
        print("\n❌ Setup completed with errors. Some features may not work.")

if __name__ == "__main__":
    main()