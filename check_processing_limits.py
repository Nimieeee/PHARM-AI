#!/usr/bin/env python3
"""
Check LangChain + pgvector Processing Limits
"""

import asyncio
import logging
from supabase_manager import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_processing_limits():
    """Check current processing limits and usage."""
    try:
        logger.info("🔍 Checking LangChain + pgvector processing limits...")
        
        # Get Supabase client
        supabase = get_supabase_client()
        if not supabase:
            logger.error("❌ Failed to connect to Supabase")
            return
        
        # Check document_chunks table
        try:
            chunks_result = supabase.table('document_chunks').select('id, content, embedding').execute()
            chunk_count = len(chunks_result.data) if chunks_result.data else 0
            
            # Calculate storage usage
            total_content_size = 0
            total_embedding_size = 0
            
            for chunk in chunks_result.data[:10]:  # Sample first 10
                if chunk.get('content'):
                    total_content_size += len(chunk['content'])
                if chunk.get('embedding'):
                    total_embedding_size += len(str(chunk['embedding']))
            
            # Estimate total sizes
            if chunk_count > 0:
                avg_content_size = total_content_size / min(10, chunk_count)
                avg_embedding_size = total_embedding_size / min(10, chunk_count)
                estimated_total_content = avg_content_size * chunk_count
                estimated_total_embeddings = avg_embedding_size * chunk_count
            else:
                estimated_total_content = 0
                estimated_total_embeddings = 0
            
            logger.info(f"📊 Current Usage Statistics:")
            logger.info(f"   • Document Chunks: {chunk_count:,}")
            logger.info(f"   • Estimated Content Size: {estimated_total_content/1024/1024:.2f} MB")
            logger.info(f"   • Estimated Embedding Size: {estimated_total_embeddings/1024/1024:.2f} MB")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not check document_chunks: {e}")
        
        # Check documents table
        try:
            docs_result = supabase.table('documents').select('id, filename, file_size').execute()
            doc_count = len(docs_result.data) if docs_result.data else 0
            
            total_file_size = 0
            for doc in docs_result.data:
                if doc.get('file_size'):
                    total_file_size += doc['file_size']
            
            logger.info(f"📁 Document Statistics:")
            logger.info(f"   • Total Documents: {doc_count:,}")
            logger.info(f"   • Total File Size: {total_file_size/1024/1024:.2f} MB")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not check documents: {e}")
        
        # Provide recommendations
        logger.info(f"\n💡 Processing Limit Recommendations:")
        
        if chunk_count < 1000:
            logger.info(f"   ✅ Chunk count ({chunk_count}) is within optimal range")
        elif chunk_count < 10000:
            logger.info(f"   ⚠️ Chunk count ({chunk_count}) is moderate - monitor performance")
        else:
            logger.info(f"   ❌ Chunk count ({chunk_count}) is high - consider cleanup")
        
        if estimated_total_content < 100 * 1024 * 1024:  # 100MB
            logger.info(f"   ✅ Content size is manageable")
        else:
            logger.info(f"   ⚠️ Content size is large - consider chunking strategy")
        
        logger.info(f"\n📋 Recommended Limits:")
        logger.info(f"   • Max Document Size: 10MB per file")
        logger.info(f"   • Max Chunk Size: 1000 characters")
        logger.info(f"   • Max Total Chunks: 10,000 for good performance")
        logger.info(f"   • Max Vector Dimensions: 1536 (OpenAI) or 384 (sentence-transformers)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error checking processing limits: {e}")
        return False

def main():
    """Main function."""
    print("🔍 LangChain + pgvector Processing Limits Check")
    print("=" * 60)
    
    success = asyncio.run(check_processing_limits())
    
    if success:
        print("\n✅ Processing limits check completed!")
    else:
        print("\n❌ Processing limits check failed.")

if __name__ == "__main__":
    main()