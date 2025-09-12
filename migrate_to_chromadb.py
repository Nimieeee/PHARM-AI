#!/usr/bin/env python3
"""
Migration Script: Pinecone to ChromaDB
Migrates existing RAG data from Pinecone-based system to ChromaDB
"""

import json
from pathlib import Path
import shutil
from datetime import datetime

def migrate_to_chromadb():
    """Migrate existing Pinecone RAG data to ChromaDB structure."""
    print("🔄 Migrating from Pinecone to ChromaDB...")
    
    user_data_dir = Path("user_data")
    if not user_data_dir.exists():
        print("✅ No user data found - nothing to migrate")
        return
    
    # Find all user RAG directories
    rag_dirs = list(user_data_dir.glob("rag_*"))
    
    if not rag_dirs:
        print("✅ No RAG directories found - nothing to migrate")
        return
    
    print(f"📁 Found {len(rag_dirs)} user RAG directories")
    
    migrated_users = 0
    migrated_conversations = 0
    
    for rag_dir in rag_dirs:
        user_id = rag_dir.name.replace("rag_", "")
        print(f"\n👤 Processing user: {user_id[:8]}...")
        
        # Find conversation directories
        conv_dirs = list(rag_dir.glob("conversation_*"))
        
        if not conv_dirs:
            print("   📂 No conversation directories found")
            continue
        
        user_migrated = False
        
        for conv_dir in conv_dirs:
            conv_id = conv_dir.name.replace("conversation_", "")
            metadata_file = conv_dir / "documents_metadata.json"
            chroma_dir = conv_dir / "chroma_db"
            
            # Skip if already has ChromaDB
            if chroma_dir.exists():
                print(f"   ✅ Conversation {conv_id[:8]}... already has ChromaDB")
                continue
            
            # Check if has documents metadata
            if not metadata_file.exists():
                print(f"   📝 Conversation {conv_id[:8]}... has no documents")
                continue
            
            try:
                # Load metadata
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                if not metadata:
                    print(f"   📝 Conversation {conv_id[:8]}... has empty metadata")
                    continue
                
                print(f"   📚 Conversation {conv_id[:8]}... has {len(metadata)} documents")
                
                # Create ChromaDB directory structure
                chroma_dir.mkdir(parents=True, exist_ok=True)
                
                # Create a migration info file
                migration_info = {
                    "migrated_at": datetime.now().isoformat(),
                    "original_documents": len(metadata),
                    "migration_status": "metadata_only",
                    "note": "Document content needs to be re-uploaded. Only metadata was preserved."
                }
                
                migration_file = conv_dir / "migration_info.json"
                with open(migration_file, 'w') as f:
                    json.dump(migration_info, f, indent=2)
                
                print(f"   ✅ Prepared ChromaDB structure for conversation {conv_id[:8]}...")
                migrated_conversations += 1
                user_migrated = True
                
            except Exception as e:
                print(f"   ❌ Error migrating conversation {conv_id[:8]}...: {e}")
        
        if user_migrated:
            migrated_users += 1
    
    print(f"\n🎯 Migration Summary:")
    print(f"   👥 Users processed: {migrated_users}")
    print(f"   💬 Conversations migrated: {migrated_conversations}")
    
    if migrated_conversations > 0:
        print(f"\n📝 Important Notes:")
        print(f"   • ChromaDB structure has been prepared")
        print(f"   • Document metadata has been preserved")
        print(f"   • ⚠️  You need to re-upload documents for full functionality")
        print(f"   • The app will now use ChromaDB instead of Pinecone")
        print(f"   • No more Pinecone API limits!")
    else:
        print(f"\n✅ No migration needed - all conversations already use ChromaDB")

def cleanup_old_pinecone_files():
    """Clean up old Pinecone-related files (optional)."""
    print("\n🧹 Cleaning up old Pinecone files...")
    
    files_to_check = [
        "test_pinecone.py",
        "rag_system.py",  # Old Pinecone-based system
        "rag_interface.py"  # Old Pinecone-based interface
    ]
    
    cleaned_files = []
    
    for file_path in files_to_check:
        file_obj = Path(file_path)
        if file_obj.exists():
            # Create backup
            backup_path = Path(f"{file_path}.pinecone_backup")
            shutil.copy2(file_obj, backup_path)
            cleaned_files.append(file_path)
            print(f"   📦 Backed up {file_path} to {backup_path}")
    
    if cleaned_files:
        print(f"   ✅ Backed up {len(cleaned_files)} old Pinecone files")
        print(f"   💡 You can delete the backup files once you're sure ChromaDB works well")
    else:
        print(f"   ✅ No old Pinecone files to clean up")

def verify_chromadb_setup():
    """Verify ChromaDB is properly set up."""
    print("\n🔍 Verifying ChromaDB setup...")
    
    try:
        import chromadb
        print("   ✅ ChromaDB package is installed")
        
        # Test basic ChromaDB functionality
        from rag_system_chromadb import ChromaRAGSystem
        
        # Create a test system
        test_rag = ChromaRAGSystem("test-user", "test-conversation")
        health = test_rag.health_check()
        
        if health['chromadb_ready']:
            print("   ✅ ChromaDB is working correctly")
            print(f"   📊 Mode: {health['mode']}")
            
            # Clean up test data
            test_dir = Path("user_data") / "rag_test-user"
            if test_dir.exists():
                shutil.rmtree(test_dir)
                print("   🧹 Cleaned up test data")
            
            return True
        else:
            print("   ❌ ChromaDB setup has issues")
            return False
            
    except ImportError:
        print("   ❌ ChromaDB package not installed")
        print("   💡 Run: pip install chromadb")
        return False
    except Exception as e:
        print(f"   ❌ ChromaDB verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Pinecone to ChromaDB Migration Tool")
    print("=" * 50)
    
    # Verify ChromaDB setup first
    if not verify_chromadb_setup():
        print("\n❌ ChromaDB setup verification failed!")
        print("Please install ChromaDB and fix any issues before migrating.")
        exit(1)
    
    # Perform migration
    migrate_to_chromadb()
    
    # Optional cleanup
    print("\n" + "=" * 50)
    response = input("Do you want to backup old Pinecone files? (y/N): ").lower().strip()
    if response in ['y', 'yes']:
        cleanup_old_pinecone_files()
    
    print("\n🎉 Migration completed!")
    print("Your PharmBot now uses ChromaDB - unlimited, free, and fast!")
    print("Remember to re-upload your documents for full functionality.")