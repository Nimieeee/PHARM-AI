# PharmGPT - AI Pharmacology Assistant 💊

A beautiful, ChatGPT-style pharmacology chatbot built with Streamlit and Supabase that provides educational information about drugs, mechanisms of action, interactions, and clinical pharmacology concepts.

## 🚀 Live Demo

[**https://ptt-ai.streamlit.app/**](https://ptt-ai.streamlit.app/)

## ✨ Features

- **🔐 Secure Authentication**: Enterprise-grade user authentication with Supabase.
- **🤖 AI-Powered**: Uses Mistral AI models for expert pharmacology responses.
- **💬 ChatGPT-Style Interface**: Modern conversation management with search and organization.
- **📚 RAG System with pgvector**: Upload documents and images for enhanced, context-aware responses using Supabase and pgvector.
- **📱 Responsive Design**: Works perfectly on desktop and mobile devices.
- **⚡ High Performance**: Optimized queries with connection pooling.
- **🔒 Enterprise Security**: Row-level security and encrypted data storage.

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Supabase account ([Get one here](https://supabase.com))
- API keys for Mistral AI models

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

3. **Set up Supabase & pgvector**:
   - Create a Supabase project at [supabase.com](https://supabase.com)
   - Enable the `pgvector` extension in your Supabase project.
   - Go to SQL Editor and run the necessary schema to create your tables.
   - Get your project URL and anon key from Settings → API

4. **Configure secrets**:
   Create `.streamlit/secrets.toml`:
   ```toml
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_ANON_KEY = "your_anon_key_here"
   MISTRAL_API_KEY = "your_mistral_api_key_here"
   ```

5. **Run the application**:
   ```bash
   streamlit run app.py
   ```

### Streamlit Cloud Deployment

For deployment on Streamlit Cloud, you need to include a `packages.txt` file in the root of your repository with the following content:

```
tesseract-ocr
```

This will ensure that Tesseract OCR is installed in the Streamlit Cloud environment.

## 🏗️ Project Structure

```
pharmgpt/
├── app.py                        # Main Streamlit application
├── config.py                     # Configuration settings
├── auth.py                       # Authentication wrapper
├── openai_client.py              # AI model integration
├── prompts.py                    # System prompts and templates
├── supabase_manager.py           # Database connection management
├── services/                     # Service layer
│   ├── user_service.py           # User management
│   ├── session_service.py        # Session handling
│   ├── conversation_service.py   # Conversation management
│   ├── document_service.py       # Document metadata
│   └── migration_service.py      # Data migration
├── pages/                        # Streamlit pages
│   ├── 2_🔐_Sign_In.py
│   ├── 3_💬_Chatbot.py
│   └── 4_📞_Contact_Support.py
├── utils/                        # Utility modules
│   ├── session_manager.py        # Session state management
│   ├── conversation_manager.py   # Conversation handling
│   ├── navigation.py             # Page navigation
│   ├── sidebar.py                # Sidebar components
│   └── theme.py                  # UI theming
├── requirements.txt              # Python dependencies
├── packages.txt                  # System-level dependencies for Streamlit Cloud
└── README.md                     # This file
```

## ⚠️ Important Disclaimer

**Educational Use Only**: PharmGPT is designed for educational purposes only. The information provided should not replace professional medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals for clinical decisions and patient care.

## 📄 License

This project is licensed under the MIT License.