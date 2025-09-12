# PharmBot Project Structure

## 📁 Core Application Files

### **Main Application**
- `streamlit_app.py` - Main Streamlit application with complete functionality
- `config.py` - Configuration and API key management
- `.env` - Environment variables (API keys)
- `requirements.txt` - Python dependencies

### **Authentication & User Management**
- `auth.py` - User authentication, session management, upload limits
- `drug_database.py` - Drug information database and search functionality

### **AI & Chat System**
- `openai_client.py` - OpenAI/Groq API client for chat completions
- `prompts.py` - System prompts and AI behavior configuration

### **RAG System (ChromaDB)**
- `rag_system_chromadb.py` - ChromaDB-based RAG system with conversation isolation
- `rag_interface_chromadb.py` - Interface layer for RAG system integration

## 📁 Utilities & Management

### **Data Management**
- `reset_upload_limit.py` - Reset user upload limits
- `reset_user_data.py` - Clean up user data while preserving accounts
- `verify_privacy.py` - Verify user data isolation and privacy

### **Migration & Setup**
- `migrate_to_chromadb.py` - Migration script from Pinecone to ChromaDB

## 📁 Documentation

### **User Guides**
- `README.md` - Main project documentation and setup instructions
- `CONVERSATION_RAG_GUIDE.md` - Guide to conversation-specific RAG system
- `CHROMADB_MIGRATION_SUMMARY.md` - ChromaDB migration details

### **Technical Documentation**
- `CODEBASE_STRUCTURE.md` - Detailed codebase structure and architecture
- `PROJECT_STRUCTURE.md` - This file - clean project overview

## 📁 Configuration Files

- `.env.example` - Example environment variables file
- `.gitignore` - Git ignore patterns
- `requirements.txt` - Python package dependencies

## 📁 Data Directory

- `user_data/` - User data storage (conversations, RAG data, uploads)
  - `users.json` - User accounts
  - `sessions.json` - Active sessions
  - `uploads.json` - Upload tracking
  - `conversations_{user_id}/` - User-specific conversations
  - `rag_{user_id}/` - User-specific RAG data
    - `conversation_{conv_id}/` - Conversation-specific knowledge bases
      - `chroma_db/` - ChromaDB vector database
      - `documents_metadata.json` - Document metadata

## 🚀 How to Run

### **Start the Application:**
```bash
streamlit run streamlit_app.py
```

### **Reset User Data:**
```bash
python reset_user_data.py
```

### **Reset Upload Limits:**
```bash
python reset_upload_limit.py
```

### **Verify Privacy:**
```bash
python verify_privacy.py
```

## 🎯 Key Features

- ✅ **ChromaDB-powered RAG** with unlimited document storage
- ✅ **Perfect conversation isolation** - each chat has its own knowledge base
- ✅ **User authentication** with secure session management
- ✅ **Upload limits** (5 documents per 24 hours per user)
- ✅ **Multiple file types** (PDF, TXT, CSV, DOCX, images with OCR)
- ✅ **Drug database** with comprehensive pharmaceutical information
- ✅ **Privacy-focused** with complete user data isolation

## 📊 File Count Summary

- **Core files**: 8
- **Utilities**: 4
- **Documentation**: 5
- **Configuration**: 3
- **Total**: 20 files (clean and organized)

**The project is now clean, organized, and production-ready!** 🎉