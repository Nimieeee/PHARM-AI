# PharmBot Modular Application Guide

## 🏗️ New Modular Structure

The PharmBot application has been completely modularized into separate pages with clean navigation and proper separation of concerns.

### **📁 Directory Structure**

```
PharmBot/
├── app.py                          # Main application entry point
├── pages/                          # Page components
│   ├── __init__.py
│   ├── homepage.py                 # Landing page (public)
│   ├── signin.py                   # Sign in/Sign up page (public)
│   └── chatbot.py                  # Main chat interface (authenticated)
├── utils/                          # Utility modules
│   ├── __init__.py
│   ├── session_manager.py          # Session state management
│   ├── navigation.py               # Page routing and navigation
│   ├── conversation_manager.py     # Conversation CRUD operations
│   └── sidebar.py                  # Sidebar for authenticated users
├── rag_interface_chromadb.py       # RAG system interface
├── rag_system_chromadb.py          # ChromaDB RAG implementation
├── auth.py                         # Authentication system
├── openai_client.py                # API client
├── prompts.py                      # System prompts
├── config.py                       # Configuration
└── requirements.txt                # Dependencies
```

## 🎯 Page Structure

### **🏠 Homepage (`pages/homepage.py`)**
- **Purpose**: Landing page for unauthenticated users
- **Features**:
  - Welcome message and feature showcase
  - Call-to-action to sign in
  - Example questions
  - Feature cards with animations
  - Educational disclaimer

### **🔐 Sign In Page (`pages/signin.py`)**
- **Purpose**: Authentication for users
- **Features**:
  - Sign In tab with login form
  - Sign Up tab with registration form
  - Form validation and error handling
  - Demo credentials information
  - Account requirements

### **💬 Chatbot Page (`pages/chatbot.py`)**
- **Purpose**: Main chat interface for authenticated users
- **Features**:
  - Welcome screen when no conversation exists
  - Full chat interface with message history
  - File upload functionality
  - RAG-enhanced responses
  - Streaming chat responses

## 🧭 Navigation System

### **Public Navigation (Unauthenticated)**
- **Homepage Button**: Navigate to landing page
- **Sign In Button**: Navigate to authentication page
- **Sidebar Info**: About PharmBot and features

### **Authenticated Navigation**
- **Full Sidebar**: Conversation management, search, document counts
- **Sign Out Button**: Logout and return to homepage
- **Conversation List**: Switch between chats
- **Upload Status**: Document and limit tracking

## 🔄 Page Flow

### **User Journey**
1. **Homepage** → User sees features and benefits
2. **Sign In** → User creates account or logs in
3. **Chatbot** → User interacts with AI and uploads documents
4. **Sign Out** → User logs out and returns to homepage

### **State Management**
- **Session State**: Managed by `utils/session_manager.py`
- **Page Routing**: Handled by `utils/navigation.py`
- **Authentication**: Persistent across page navigation
- **Conversations**: Loaded and managed per user

## 🚀 How to Run

### **Start the Modular App**
```bash
streamlit run app.py
```

### **Development Mode**
```bash
# Run with auto-reload
streamlit run app.py --server.runOnSave=true
```

## 🎨 Features

### **Responsive Design**
- ✅ Clean, modern interface
- ✅ System-aware color scheme (light/dark mode)
- ✅ Mobile-responsive layout
- ✅ Smooth animations and transitions

### **Authentication Flow**
- ✅ Secure sign in/sign up
- ✅ Form validation
- ✅ Session persistence
- ✅ Demo credentials for testing

### **Chat Interface**
- ✅ Real-time streaming responses
- ✅ File upload with drag & drop
- ✅ RAG-enhanced answers
- ✅ Conversation management

### **Document Management**
- ✅ Upload limits (5 per day)
- ✅ Multiple file types supported
- ✅ OCR for images
- ✅ Conversation-specific knowledge bases

## 🔧 Component Details

### **`app.py` - Main Entry Point**
- Initializes session state
- Handles page routing
- Applies global CSS
- Manages navigation flow

### **`utils/session_manager.py`**
- Initializes all session state variables
- Manages authentication state
- Handles conversation state
- Sets up page navigation

### **`utils/navigation.py`**
- Routes users to appropriate pages
- Handles authentication flow
- Manages public vs authenticated navigation
- Controls page transitions

### **`utils/conversation_manager.py`**
- Creates and manages conversations
- Handles message storage
- Manages conversation metadata
- Integrates with file storage

### **`utils/sidebar.py`**
- Renders authenticated user sidebar
- Manages conversation list
- Handles search functionality
- Shows document and upload status

## 🐛 Debugging Guide

### **Page Navigation Issues**
- **Check**: `utils/navigation.py`
- **Debug**: `st.session_state.current_page` value
- **Common Issues**: Page state not updating, authentication flow

### **Authentication Problems**
- **Check**: `pages/signin.py` and `auth.py`
- **Debug**: `st.session_state.authenticated` value
- **Common Issues**: Session not persisting, user creation errors

### **Chat Interface Issues**
- **Check**: `pages/chatbot.py`
- **Debug**: Conversation creation, message handling
- **Common Issues**: No conversation ID, message not saving

### **File Upload Problems**
- **Check**: File upload handling in `pages/chatbot.py`
- **Debug**: Upload limits, file processing
- **Common Issues**: RAG system initialization, duplicate detection

## 📊 Benefits of Modular Structure

### **Before (Monolithic)**
- ❌ 800+ lines in single file
- ❌ Mixed authentication and chat logic
- ❌ Hard to debug specific features
- ❌ Difficult to maintain and extend

### **After (Modular)**
- ✅ ~100-200 lines per module
- ✅ Clear separation of concerns
- ✅ Easy to debug specific pages
- ✅ Simple to add new features

### **Development Benefits**
- ✅ **Faster Development**: Work on specific pages independently
- ✅ **Better Testing**: Test individual components
- ✅ **Easier Maintenance**: Locate and fix issues quickly
- ✅ **Team Collaboration**: Multiple developers can work on different pages

## 🎯 Next Steps

### **Adding New Pages**
1. Create new file in `pages/` directory
2. Add page function (e.g., `render_new_page()`)
3. Update `utils/navigation.py` to include routing
4. Add navigation buttons as needed

### **Extending Features**
1. **New Utilities**: Add to `utils/` directory
2. **New Components**: Create reusable components
3. **Enhanced Navigation**: Add more page types
4. **Advanced Features**: Settings page, profile management

**The modular structure makes PharmBot much easier to develop, debug, and maintain!** 🎉