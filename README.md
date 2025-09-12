# PharmBot - AI Pharmacology Assistant 💊

A beautiful, ChatGPT-style pharmacology chatbot built with Streamlit that provides educational information about drugs, mechanisms of action, interactions, and clinical pharmacology concepts.

![PharmBot](https://img.shields.io/badge/PharmBot-AI%20Pharmacology%20Assistant-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- **🔐 User Authentication**: Secure sign-in/sign-up with private, separated conversations
- **🤖 AI-Powered**: Uses Groq API with Llama 4 Maverick model for fast, expert pharmacology responses
- **💬 ChatGPT-Style Interface**: Modern conversation management with search and organization
- **🎨 Beautiful UI**: System-aware design that adapts to light/dark mode preferences
- **📚 Educational Focus**: Specialized for pharmacology learning and research
- **🔍 Smart Conversations**: Persistent chat history with context awareness
- **👥 Multi-User Support**: Each user has completely private and separated conversations
- **💾 Persistent Storage**: Conversations are saved locally and restored on login
- **📚 RAG System**: Upload documents and images for enhanced, context-aware responses
- **🔍 Document Search**: Semantic search through your uploaded knowledge base
- **🖼️ OCR Support**: Extract text from images using advanced OCR technology
- **📱 Responsive Design**: Works perfectly on desktop and mobile devices

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Groq API key ([Get one here](https://console.groq.com/keys))

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/pharmbot.git
   cd pharmbot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your Groq API key
   ```

4. **Run the application**:
   ```bash
   streamlit run streamlit_app.py
   ```

5. **Set up RAG system (optional)**:
   ```bash
   python setup_rag.py
   ```

6. **Create your account**:
   - Open the app in your browser
   - Click "Sign Up" to create a new account
   - Sign in and start chatting!
   - Upload documents to enhance your conversations

## 🔐 Authentication System

### User Accounts
- **Secure Registration**: Create accounts with username and password
- **Password Security**: Passwords are hashed and salted for maximum security
- **Private Data**: Each user's conversations are completely separated and private
- **Persistent Storage**: Conversations are saved locally and restored on login

### Privacy & Security
- **Local Storage**: All user data is stored locally on your server
- **No Data Sharing**: User conversations are never shared between accounts
- **Secure Hashing**: Passwords use SHA-256 with random salts
- **Session Management**: Secure session handling with timeout protection
- **Data Isolation**: Each user's data is completely isolated in separate directories
- **Privacy Verification**: Built-in tools to verify and maintain data privacy

### Multi-User Support
- **Separated Conversations**: Each user sees only their own conversations
- **Individual Settings**: Personal preferences and conversation history
- **Account Management**: Easy sign-in/sign-out functionality

## 📚 Conversation-Specific RAG System

### Document Support
- **PDF Documents**: Extract and process PDF content
- **Word Documents**: Support for .docx and .doc files
- **Text Files**: Plain text and CSV files
- **Images**: OCR text extraction from PNG, JPG, JPEG files
- **Semantic Search**: Find relevant information using AI embeddings

### Knowledge Base Features
- **Conversation Isolation**: Each chat has its own isolated document collection
- **No Cross-Chat Interference**: Documents in one conversation don't affect others
- **Chunked Processing**: Documents are intelligently split for better retrieval
- **Vector Search**: Uses Pinecone/local storage for fast, semantic document search
- **Context Integration**: Automatically enhances conversations with relevant document content
- **Document Management**: Upload, view, search, and delete documents per conversation

### RAG-Enhanced Conversations
- **Conversation-Specific Context**: Only documents from the current chat are used
- **Perfect Isolation**: No interference from documents in other conversations
- **Source Citations**: Responses include references to conversation-specific documents
- **Fallback Handling**: Works with or without uploaded documents
- **Real-time Search**: Searches only the current conversation's knowledge base

### Technical Implementation
- **LangChain**: Document processing and text splitting
- **Pinecone/Local Storage**: Vector database for semantic search
- **HuggingFace Embeddings**: Sentence transformers for document embeddings
- **OCR**: Tesseract for image text extraction
- **Conversation Isolation**: Each chat maintains separate document storage

## 🎯 Usage Examples

### Ask Complex Questions
- "Explain the mechanism of action of ACE inhibitors in detail"
- "What are the major drug interactions with warfarin and why do they occur?"
- "Describe the pharmacokinetics of digoxin and its clinical implications"

### Explore Drug Categories
- "Tell me about NSAIDs and their side effects"
- "How do beta-blockers work in cardiovascular disease?"
- "What are the differences between ACE inhibitors and ARBs?"

### Clinical Scenarios
- "How would you manage digoxin toxicity?"
- "What monitoring is required for patients on warfarin?"
- "Explain the contraindications for NSAIDs"

## 🏗️ Project Structure

```
pharmbot/
├── streamlit_app.py              # Main Streamlit application
├── rag_system_chromadb.py        # ChromaDB-based RAG system
├── rag_interface_chromadb.py     # RAG interface layer
├── config.py                     # Configuration and API setup
├── openai_client.py              # Groq API client
├── prompts.py                    # AI system prompts
├── auth.py                       # Authentication & user management
├── drug_database.py              # Drug reference database
├── reset_upload_limit.py         # Upload limit management
├── verify_privacy.py             # Privacy verification
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── README.md                     # This file
└── user_data/                    # User data storage
    ├── users.json
    ├── sessions.json
    ├── uploads.json
    └── rag_{user_id}/
        └── conversation_{conv_id}/
            ├── chroma_db/        # ChromaDB vector database
            └── documents_metadata.json
```

## 🎨 Features Showcase

### Modern Interface
- Clean, professional design
- System-aware color scheme (light/dark mode)
- Smooth animations and hover effects
- Mobile-responsive layout

### Conversation Management
- Create multiple chat sessions
- Search through conversation history
- Rename and organize conversations
- Duplicate conversations for related topics

### Educational Tools
- Quick example questions to get started
- Comprehensive drug information
- Evidence-based responses
- Clinical context and explanations

## 🔧 Configuration

The app uses Groq's Llama 4 Maverick model by default. You can modify the model in `streamlit_app.py`:

```python
FIXED_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
```

Available Groq models:
- `meta-llama/llama-4-maverick-17b-128e-instruct` (Current - Latest Llama 4 model)
- `llama-3.1-70b-versatile` (Alternative - Best balance of speed and quality)
- `llama-3.1-8b-instant` (Fastest)
- `mixtral-8x7b-32768` (Good for longer contexts)

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Commit your changes**: `git commit -m 'Add amazing feature'`
5. **Push to the branch**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

### Ideas for Contributions
- Add more drugs to the database
- Improve the AI prompts
- Add new features (export, sharing, etc.)
- Enhance the UI/UX
- Add tests
- Improve documentation

## ⚠️ Important Disclaimer

**Educational Use Only**: PharmBot is designed for educational purposes only. The information provided should not replace professional medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals for clinical decisions and patient care.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [Groq](https://groq.com/)
- Icons and emojis from various sources
- Inspired by modern AI chat interfaces

## 🔒 Privacy & Data Management

### Verification Tools
Run these commands to ensure your data privacy:

```bash
# Verify user data isolation
python verify_privacy.py

# Clean up any orphaned data
python reset_user_data.py
```

### Data Structure
Each user's data is stored in isolated directories:
- `user_data/conversations_{user_id}/` - Private conversations
- `user_data/rag_{user_id}/` - Private document uploads
- `user_data/users.json` - User accounts (passwords hashed)

### Privacy Guarantee
- **Complete Isolation**: Users can never see each other's data
- **Automatic Cleanup**: System automatically removes orphaned data
- **Local Storage**: All data stays on your server
- **No Cross-User Access**: Technical safeguards prevent data leaks

## 📞 Support

If you have questions or need help:
- Open an issue on GitHub
- Check the documentation
- Review the example usage
- Run `python verify_privacy.py` for data privacy verification

---

**Made with ❤️ for the pharmacology community**