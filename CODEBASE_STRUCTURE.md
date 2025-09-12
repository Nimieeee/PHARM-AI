# PharmBot Codebase Structure

## 🎯 **Core Application Files**

### **Main Application**
- `streamlit_app.py` - Main Streamlit application with chat interface
- `main.py` - Alternative entry point (if needed)

### **Authentication & User Management**
- `auth.py` - User authentication, registration, and session management
- User data stored in `user_data/` directory

### **RAG System (Pinecone-based)**
- `rag_system.py` - Pinecone vector database integration
- `rag_interface.py` - RAG interface for Streamlit integration
- **Features**: Image OCR, document processing, vector search, context generation

### **AI & Knowledge**
- `openai_client.py` - OpenAI/Groq API client for chat completions
- `prompts.py` - System prompts for pharmacology expertise
- `drug_database.py` - Built-in drug information database

### **Configuration**
- `.env` - Environment variables (API keys)
- `config.py` - Application configuration
- `requirements.txt` - Python dependencies

## 📚 **Key Features**

### **RAG-Enhanced Chat**
- ✅ Upload images (📎 button) with OCR text extraction
- ✅ Upload documents (PDF, DOCX, TXT, CSV)
- ✅ Vector storage in Pinecone cloud (no corruption issues)
- ✅ Context-aware responses using uploaded content
- ✅ Scientific content recognition (genetics, pharmacology)

### **User Experience**
- ✅ User authentication and session management
- ✅ Conversation history and management
- ✅ Document upload with progress feedback
- ✅ Health monitoring and error recovery
- ✅ Mobile-responsive interface

### **Production Ready**
- ✅ Pinecone managed vector database
- ✅ Local fallback mode (works without API key)
- ✅ Robust error handling
- ✅ Scalable architecture
- ✅ Clean, maintainable code

## 🔧 **Dependencies**

### **Core**
- `streamlit` - Web application framework
- `openai` - AI completions (compatible with Groq)
- `python-dotenv` - Environment variable management

### **RAG System**
- `pinecone` - Managed vector database
- `langchain` - Document processing and text splitting
- `sentence-transformers` - Text embeddings
- `scikit-learn` - Local vector similarity (fallback)

### **Document Processing**
- `PyPDF2` - PDF text extraction
- `python-docx` - Word document processing
- `pandas` - CSV/Excel processing
- `unstructured` - Advanced document parsing

### **Image Processing**
- `Pillow` - Image manipulation
- `pytesseract` - OCR text extraction

## 🚀 **Getting Started**

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Set API keys** in `.env` file:
   - `GROQ_API_KEY` - For AI completions
   - `PINECONE_API_KEY` - For vector database (optional - has local fallback)
3. **Run application**: `streamlit run streamlit_app.py`

## 📊 **System Status**

- **Vector Database**: Pinecone (cloud) with local fallback
- **AI Provider**: Groq (OpenAI-compatible)
- **Authentication**: File-based user management
- **Storage**: Local file system + Pinecone cloud
- **Status**: Production-ready ✅

## 🎯 **No More Issues**

- ❌ ChromaDB corruption - **SOLVED** (using Pinecone)
- ❌ Database readonly errors - **SOLVED** (managed service)
- ❌ Vector index corruption - **SOLVED** (cloud-based)
- ❌ Silent upload failures - **SOLVED** (robust error handling)
- ❌ RAG context not working - **SOLVED** (proper integration)

**Your PharmBot is now production-ready with a clean, maintainable codebase! 🎉**