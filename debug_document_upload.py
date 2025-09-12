#!/usr/bin/env python3
"""
Debug document upload process
"""

import asyncio
from services.document_service import document_service
from services.user_service import user_service

async def test_document_creation():
    """Test document creation directly"""
    try:
        # Test user lookup
        print("Testing user lookup...")
        user_data = user_service.get_user_by_id("e4443c52948edad6132f34b6378a9901")
        print(f"User data: {user_data}")
        
        if not user_data:
            print("❌ User not found!")
            return
        
        # Test document creation
        print("Testing document creation...")
        doc_data = {
            "document_hash": "test_doc_123",
            "filename": "test.txt",
            "file_type": "text/plain",
            "file_size": 100,
            "content": "This is a test document",
            "chunk_count": 1,
            "processing_method": "test",
            "is_processed": True
        }
        result = await document_service.save_document_metadata(
            user_uuid=user_data['id'],
            conversation_id="05506e11-d250-40f4-9f8a-d236cd03596a",
            doc_data=doc_data
        )
        print(f"Document creation result: {result}")
        
        # Test document retrieval
        print("Testing document retrieval...")
        docs = await document_service.get_conversation_documents(
            user_data['id'],
            "05506e11-d250-40f4-9f8a-d236cd03596a"
        )
        print(f"Retrieved documents: {docs}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_document_creation())