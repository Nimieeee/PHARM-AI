#!/usr/bin/env python3
"""
Quick Start Guide Generator for PharmGPT
"""

def generate_quick_start():
    """Generate a quick start guide."""
    guide = """
# PharmGPT Quick Start Guide

## 1. Prerequisites
- Supabase account (free tier available)
- Mistral AI API key
- Python 3.8+

## 2. Setup Steps

### Step 1: Database Setup
1. Open your Supabase Dashboard
2. Select your project
3. Go to "SQL Editor"
4. Copy and paste the entire contents of `complete_database_setup.sql`
5. Click "Run"

### Step 2: Environment Configuration
Create a `.env` file with:
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
MISTRAL_API_KEY=your_mistral_api_key
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run Verification
```bash
python verify_implementation.py
```

### Step 5: Start the Application
```bash
streamlit run app.py
```

## 3. First Time Usage

1. Open the application in your browser
2. Go to the Sign In page
3. Create a new account
4. Start a new conversation
5. Upload a document (optional)
6. Ask pharmacology-related questions

## 4. Key Features

- 💬 ChatGPT-style conversation interface
- 📚 Document upload and RAG integration
- 🔐 Secure user authentication
- 🧠 Mistral AI-powered responses
- 🗃️ Conversation-specific knowledge bases
- 📱 Responsive design for all devices

## 5. Troubleshooting

If you encounter issues:

1. **Database Connection Failed**: 
   - Check your SUPABASE_URL and SUPABASE_ANON_KEY
   - Ensure you've executed the database setup script

2. **Embedding Generation Failed**:
   - Check your MISTRAL_API_KEY
   - Ensure you have internet connectivity

3. **Tables Not Found**:
   - Re-run the complete_database_setup.sql script
   - Check for any error messages during execution

4. **Authentication Issues**:
   - Clear browser cookies and cache
   - Ensure you're using the correct credentials

## 6. Support

For additional help:
- Check the detailed documentation in README.md
- Review the implementation guide in IMPLEMENTATION_GUIDE.md
- Contact support through the application's contact page
"""
    
    with open("QUICK_START.md", "w") as f:
        f.write(guide)
    
    print("✅ Quick Start Guide generated: QUICK_START.md")

if __name__ == "__main__":
    generate_quick_start()