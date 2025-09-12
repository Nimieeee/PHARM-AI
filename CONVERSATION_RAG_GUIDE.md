# Conversation-Specific RAG System Guide (ChromaDB)

## 🎯 Overview

PharmBot now uses **ChromaDB-powered conversation-specific RAG (Retrieval-Augmented Generation)** systems, meaning each chat conversation has its own isolated knowledge base. Documents uploaded in one conversation will not interfere with or appear in other conversations.

## 🚀 **NEW: ChromaDB Integration**

We've migrated from Pinecone to **ChromaDB** for better performance and unlimited usage:

✅ **No API limits** - unlimited documents and conversations  
✅ **Faster performance** - local vector database  
✅ **No API costs** - completely free  
✅ **Better reliability** - no network dependencies  
✅ **Enhanced privacy** - all data stays local

## 🔒 Key Benefits

### **Complete Isolation**
- Each conversation maintains its own document collection
- No cross-conversation data leakage
- Perfect for organizing different topics or projects

### **Better Context Management**
- Documents are only relevant to their specific conversation
- More focused and accurate AI responses
- Cleaner knowledge organization

### **Enhanced Privacy**
- Sensitive documents stay within their intended conversation
- Better control over information access
- Reduced risk of context confusion

## 🏗️ Technical Architecture

### **Directory Structure (ChromaDB)**
```
user_data/
├── rag_{user_id}/
│   ├── conversation_{conv_id_1}/
│   │   ├── documents_metadata.json
│   │   └── chroma_db/
│   │       ├── chroma.sqlite3
│   │       └── [ChromaDB files]
│   ├── conversation_{conv_id_2}/
│   │   ├── documents_metadata.json
│   │   └── chroma_db/
│   │       ├── chroma.sqlite3
│   │       └── [ChromaDB files]
│   └── conversation_global/
│       ├── documents_metadata.json
│       └── chroma_db/
│           ├── chroma.sqlite3
│           └── [ChromaDB files]
```

### **RAG System Components (ChromaDB)**
- **User-level directory**: `rag_{user_id}/`
- **Conversation-level directories**: `conversation_{conversation_id}/`
- **Metadata tracking**: Per-conversation document metadata
- **ChromaDB storage**: `chroma_db/` directory with SQLite database
- **Vector collections**: Conversation-specific ChromaDB collections
- **Embeddings**: SentenceTransformers all-MiniLM-L6-v2 model

## 📚 How It Works

### **Document Upload**
1. User uploads document in a specific conversation
2. Document is processed and stored in that conversation's RAG directory
3. Vector embeddings are created and stored separately for that conversation
4. Document only affects AI responses within that conversation

### **AI Response Generation**
1. User asks a question in a conversation
2. System searches only that conversation's knowledge base
3. Relevant documents from that conversation enhance the response
4. No interference from documents in other conversations

### **Conversation Management**
- **Document Count Display**: Each conversation shows its document count (📚2)
- **Isolated Processing**: Documents are processed per-conversation
- **Clean Deletion**: Deleting a conversation removes its RAG data

## 🎮 User Experience

### **Sidebar Indicators**
- Conversations with documents show: `Chat Title... 📚3`
- Empty conversations show: `Chat Title...`
- Total document count displayed at bottom

### **Upload Behavior**
- Upload button appears in each conversation
- Documents are added to the current conversation only
- Success message confirms conversation-specific upload

### **AI Responses**
- AI only uses documents from the current conversation
- Source citations reference conversation-specific documents
- No confusion from unrelated documents

## 🔧 Management Tools

### **Migration Script**
```bash
python migrate_to_conversation_rag.py
```
- Migrates existing user-level RAG data to conversation-specific structure
- Assigns existing documents to the most recent conversation
- Preserves all document data and metadata

### **Privacy Verification**
```bash
python verify_privacy.py
```
- Checks conversation-specific RAG isolation
- Reports conversation RAG directory counts
- Ensures no cross-user data leaks

### **Upload Management**
```bash
python reset_upload_limit.py
```
- Manages upload limits (still user-level, not conversation-level)
- Prevents abuse while allowing conversation-specific uploads

## 📊 Example Use Cases

### **Research Projects**
- **Conversation 1**: "Cardiovascular Pharmacology" - Upload heart drug papers
- **Conversation 2**: "Neuropharmacology" - Upload brain drug research
- **Conversation 3**: "Drug Interactions" - Upload interaction studies

Each conversation maintains its own focused knowledge base.

### **Study Sessions**
- **Conversation 1**: "Exam Prep Chapter 1" - Upload chapter materials
- **Conversation 2**: "Exam Prep Chapter 2" - Upload different chapter
- **Conversation 3**: "Practice Questions" - Upload question banks

No confusion between different study materials.

### **Clinical Cases**
- **Conversation 1**: "Patient Case A" - Upload relevant case files
- **Conversation 2**: "Patient Case B" - Upload different case files
- **Conversation 3**: "General Guidelines" - Upload treatment protocols

Each case maintains its own context.

## 🚀 Getting Started

### **For New Users**
1. Create account and sign in
2. Start a new conversation
3. Upload relevant documents
4. Ask questions - AI will use only those documents

### **For Existing Users**
1. Existing documents have been migrated to your most recent conversation
2. Create new conversations for different topics
3. Upload topic-specific documents to each conversation
4. Enjoy isolated, focused AI assistance

## 🔍 Troubleshooting

### **Documents Not Found**
- Check you're in the correct conversation
- Documents are conversation-specific
- Use the document count indicator (📚) to verify uploads

### **AI Not Using Documents**
- Ensure documents are uploaded to the current conversation
- Check document count shows > 0 for the conversation
- Try more specific questions related to your documents

### **Migration Issues**
- Run `python migrate_to_conversation_rag.py` if needed
- Check `python verify_privacy.py` for system health
- Contact support if issues persist

## 🎉 Benefits Summary

✅ **Perfect Isolation**: Each conversation has its own knowledge base  
✅ **Better Organization**: Documents grouped by topic/conversation  
✅ **Enhanced Privacy**: No cross-conversation data access  
✅ **Focused Responses**: AI uses only relevant documents  
✅ **Clean Management**: Easy to organize and delete conversation data  
✅ **Scalable**: Support unlimited conversations with documents  

The conversation-specific RAG system provides a much better user experience with complete data isolation and focused AI assistance for each conversation topic.