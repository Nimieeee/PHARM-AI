# PharmGPT - AI Pharmacology Assistant 💊

A beautiful, ChatGPT-style pharmacology chatbot built with Streamlit and Supabase that provides educational information about drugs, mechanisms of action, interactions, and clinical pharmacology concepts.

![PharmGPT](https://img.shields.io/badge/PharmGPT-AI%20Pharmacology%20Assistant-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![Supabase](https://img.shields.io/badge/Supabase-Database-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

- **🔐 Secure Authentication**: Enterprise-grade user authentication with Supabase
- **🤖 AI-Powered**: Uses Groq API with Llama 4 Maverick model for fast, expert pharmacology responses
- **💬 ChatGPT-Style Interface**: Modern conversation management with search and organization
- **🎨 Beautiful UI**: System-aware design that adapts to light/dark mode preferences
- **📚 Educational Focus**: Specialized for pharmacology learning and research
- **🔍 Smart Conversations**: Persistent chat history with context awareness
- **👥 Multi-User Support**: Concurrent users with real-time capabilities
- **💾 Cloud Database**: Supabase PostgreSQL with automatic backups
- **📚 RAG System**: Upload documents and images for enhanced, context-aware responses
- **🔍 Document Search**: Semantic search through your uploaded knowledge base
- **🖼️ OCR Support**: Extract text from images using advanced OCR technology
- **📱 Responsive Design**: Works perfectly on desktop and mobile devices
- **⚡ High Performance**: Optimized queries with connection pooling
- **🔒 Enterprise Security**: Row-level security and encrypted data storage

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Supabase account ([Get one here](https://supabase.com))
- Groq API key ([Get one here](https://console.groq.com/keys))
- OpenRouter API key ([Get one here](https://openrouter.ai/keys))

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/pharmgpt.git
   cd pharmgpt
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Supabase**:
   - Create a Supabase project at [supabase.com](https://supabase.com)
   - Go to SQL Editor and run the contents of `supabase_schema.sql`
   - Get your project URL and anon key from Settings → API

4. **Configure secrets**:
   Create `.streamlit/secrets.toml`:
   ```toml
   GROQ_API_KEY = "your_groq_api_key_here"
   OPENROUTER_API_KEY = "your_openrouter_api_key_here"
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_ANON_KEY = "your_anon_key_here"
   ```

5. **Run the application**:
   ```bash
   streamlit run app.py
   ```

6. **Create your account**:
   - Open the app in your browser
   - Click "Sign Up" to create a new account
   - Sign in and start chatting!
   - Upload documents to enhance your conversations

### 🌐 Streamlit Cloud Deployment

1. **Fork this repository** to your GitHub account

2. **Set up Supabase**:
   - Create your Supabase project
   - Run the database schema from `supabase_schema.sql`
   - Note your project URL and anon key

3. **Deploy to Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select your forked repository
   - Choose `app.py` as the main file

4. **Add secrets in Streamlit Cloud**:
   - In your Streamlit Cloud dashboard, go to your app settings
   - Click on "Secrets" in the left sidebar
   - Add your credentials:
     ```toml
     GROQ_API_KEY = "your_groq_api_key_here"
     OPENROUTER_API_KEY = "your_openrouter_api_key_here"
     SUPABASE_URL = "https://your-project.supabase.co"
     SUPABASE_ANON_KEY = "your_anon_key_here"
     ```

5. **Deploy**: Your app will automatically deploy and be available at your Streamlit Cloud URL

### 🔐 Security Notes
- **Never commit API keys** to GitHub
- **Use Streamlit secrets** for both local development and cloud deployment
- **The .streamlit/ folder is automatically gitignored** for security

## 🗄️ Database Architecture

### Supabase PostgreSQL
- **Row Level Security (RLS)**: Users can only access their own data
- **Automatic Backups**: Point-in-time recovery and daily backups
- **Real-time Capabilities**: Built-in real-time subscriptions
- **Connection Pooling**: Optimized database connections
- **ACID Transactions**: Data consistency and integrity

### Database Tables
- **users**: User accounts and authentication data
- **sessions**: Authentication sessions with expiration
- **conversations**: Chat conversations with message history
- **documents**: Document metadata for RAG system
- **uploads**: File upload tracking and statistics

### Migration from File-Based Storage
If you have existing data from a previous version:

```bash
python migrate_to_supabase.py
```

This tool will:
- ✅ Detect and validate existing file-based data
- 💾 Create automatic backup of your current data
- 🚀 Migrate all users, conversations, and documents to Supabase
- ✅ Verify migration integrity
- 📊 Generate detailed migration report

## 🔐 Authentication & Security

### Enterprise-Grade Security
- **Supabase Auth**: Industry-standard authentication
- **Password Security**: Proper hashing with salt
- **Session Management**: Secure session handling with timeout
- **Row Level Security**: Database-level access control
- **Encrypted Connections**: All data transmitted over HTTPS/TLS

### Multi-User Support
- **Concurrent Users**: Support for multiple simultaneous users
- **Data Isolation**: Complete separation of user data
- **Real-time Capabilities**: Future support for collaborative features
- **Scalable Architecture**: Handles growing user base efficiently

## 📚 Conversation-Specific RAG System

### Document Support
- **PDF Documents**: Extract and process PDF content
- **Word Documents**: Support for .docx and .doc files
- **Text Files**: Plain text and CSV files
- **Images**: OCR text extraction from PNG, JPG, JPEG files
- **Semantic Search**: Find relevant information using AI embeddings

### Knowledge Base Features
- **Conversation Isolation**: Each chat has its own isolated document collection
- **Metadata Storage**: Document information stored in Supabase
- **Vector Search**: ChromaDB for fast, semantic document search
- **Context Integration**: Automatically enhances conversations with relevant content
- **Document Management**: Upload, view, search, and delete documents per conversation

### RAG-Enhanced Conversations
- **Conversation-Specific Context**: Only documents from the current chat are used
- **Perfect Isolation**: No interference from documents in other conversations
- **Source Citations**: Responses include references to conversation-specific documents
- **Fallback Handling**: Works with or without uploaded documents
- **Real-time Search**: Searches only the current conversation's knowledge base

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
pharmgpt/
├── app.py                        # Main Streamlit application
├── config.py                     # Configuration settings
├── auth.py                       # Authentication wrapper
├── openai_client.py              # AI model integration
├── prompts.py                    # System prompts and templates
├── supabase_manager.py           # Database connection management
├── supabase_schema.sql           # Database schema
├── migrate_to_supabase.py        # Migration tool
├── services/                     # Service layer
│   ├── user_service.py           # User management
│   ├── session_service.py        # Session handling
│   ├── conversation_service.py   # Conversation management
│   ├── document_service.py       # Document metadata
│   └── migration_service.py      # Data migration
├── pages/                        # Streamlit pages
│   ├── homepage.py               # Landing page
│   ├── signin.py                 # Authentication page
│   └── chatbot.py                # Main chat interface
├── utils/                        # Utility modules
│   ├── session_manager.py        # Session state management
│   ├── conversation_manager.py   # Conversation handling
│   ├── navigation.py             # Page navigation
│   ├── sidebar.py                # Sidebar components
│   └── theme.py                  # UI theming
├── rag_system_chromadb.py        # RAG implementation
├── rag_interface_chromadb.py     # RAG interface
├── drug_database.py              # Drug information database
├── requirements.txt              # Python dependencies
└── SUPABASE_MIGRATION_GUIDE.md   # Complete setup guide
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

The app uses Groq's Llama 4 Maverick model by default. You can modify the model in `config.py`:

```python
FIXED_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"
```

Available models:
- `meta-llama/llama-4-maverick-17b-128e-instruct` (Groq - Current)
- `openrouter/sonoma-sky-alpha` (OpenRouter - Turbo mode)

## ⚡ Performance Features

### Database Optimizations
- **Connection Pooling**: Efficient database connections
- **Query Optimization**: Proper indexing and efficient queries
- **Caching**: Intelligent caching with TTL values
- **Batch Operations**: Grouped database operations for efficiency

### Application Performance
- **Lazy Loading**: Components load only when needed
- **Optimized Streaming**: Reduced UI update frequency
- **Memory Management**: Automatic cleanup and optimization
- **Error Handling**: Comprehensive error handling with retry logic

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
- Performance optimizations

## ⚠️ Important Disclaimer

**Educational Use Only**: PharmGPT is designed for educational purposes only. The information provided should not replace professional medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals for clinical decisions and patient care.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Database powered by [Supabase](https://supabase.com/)
- AI models from [Groq](https://groq.com/) and [OpenRouter](https://openrouter.ai/)
- RAG system using [ChromaDB](https://www.trychroma.com/)
- Modern, secure, and scalable architecture

## 📞 Support

If you have questions or need help:
- Check the [Supabase Migration Guide](SUPABASE_MIGRATION_GUIDE.md)
- Open an issue on GitHub
- Review the documentation
- Run the migration tool for existing data

---

**Made with ❤️ for the pharmacology community**

*Now powered by enterprise-grade Supabase infrastructure for better performance, security, and scalability.*