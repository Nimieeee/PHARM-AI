#!/usr/bin/env python3
"""
Migration Script for PharmGPT
Migrate from file-based storage to Supabase
"""

import asyncio
import sys
import os
from datetime import datetime
import streamlit as st

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.migration_service import migration_service, migrate_all_data
from supabase_manager import connection_manager, health_check

def print_banner():
    """Print migration banner."""
    print("=" * 60)
    print("PharmGPT Migration to Supabase")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()

def print_step(step_num: int, description: str):
    """Print migration step."""
    print(f"Step {step_num}: {description}")
    print("-" * 40)

async def main():
    """Main migration function."""
    print_banner()
    
    try:
        # Step 1: Health check
        print_step(1, "Checking Supabase connection")
        health = health_check()
        
        if not health['supabase_available']:
            print("❌ Supabase library not available. Please install: pip install supabase")
            return False
        
        if not health['client_initialized']:
            print("❌ Supabase client not initialized. Please check your credentials.")
            return False
        
        if not health['connection_test']:
            print("❌ Supabase connection test failed. Please check your configuration.")
            return False
        
        print("✅ Supabase connection successful")
        print()
        
        # Step 2: Detect existing data
        print_step(2, "Detecting existing file-based data")
        analysis = await migration_service.detect_existing_data()
        
        if analysis.get('errors'):
            print("❌ Errors detected in existing data:")
            for error in analysis['errors']:
                print(f"   - {error}")
            return False
        
        print(f"✅ Found {analysis['user_count']} users")
        print(f"✅ Found {analysis['conversation_count']} conversations")
        print(f"✅ Found {analysis['document_count']} documents")
        print(f"✅ Total data size: {analysis['total_size_mb']} MB")
        print()
        
        if analysis['user_count'] == 0:
            print("ℹ️  No existing data to migrate")
            return True
        
        # Step 3: Validate data integrity
        print_step(3, "Validating data integrity")
        validation = await migration_service.validate_data_integrity(analysis)
        
        if not validation['valid']:
            print("❌ Data validation failed:")
            for error in validation['errors']:
                print(f"   - {error}")
            
            if validation['warnings']:
                print("⚠️  Warnings:")
                for warning in validation['warnings']:
                    print(f"   - {warning}")
            
            response = input("\nContinue with migration despite validation issues? (y/N): ")
            if response.lower() != 'y':
                print("Migration cancelled")
                return False
        else:
            print("✅ Data validation passed")
            if validation['warnings']:
                print("⚠️  Warnings:")
                for warning in validation['warnings']:
                    print(f"   - {warning}")
        print()
        
        # Step 4: Create backup
        print_step(4, "Creating backup of existing data")
        backup_path = await migration_service.create_backup()
        print(f"✅ Backup created at: {backup_path}")
        print()
        
        # Step 5: Confirm migration
        print("Migration Summary:")
        print(f"  Users to migrate: {analysis['user_count']}")
        print(f"  Conversations to migrate: {analysis['conversation_count']}")
        print(f"  Documents to migrate: {analysis['document_count']}")
        print(f"  Backup location: {backup_path}")
        print()
        
        response = input("Proceed with migration? (y/N): ")
        if response.lower() != 'y':
            print("Migration cancelled")
            return False
        
        # Step 6: Execute migration
        print_step(6, "Executing migration")
        
        # Migrate users
        print("Migrating users...")
        user_count, user_errors = await migration_service.migrate_users()
        print(f"✅ Migrated {user_count} users")
        if user_errors:
            print("❌ User migration errors:")
            for error in user_errors:
                print(f"   - {error}")
        
        # Migrate conversations
        print("Migrating conversations...")
        conv_count, conv_errors = await migration_service.migrate_conversations(
            migration_service.user_mapping
        )
        print(f"✅ Migrated {conv_count} conversations")
        if conv_errors:
            print("❌ Conversation migration errors:")
            for error in conv_errors:
                print(f"   - {error}")
        
        # Migrate documents
        print("Migrating documents...")
        doc_count, doc_errors = await migration_service.migrate_documents(
            migration_service.user_mapping
        )
        print(f"✅ Migrated {doc_count} documents")
        if doc_errors:
            print("❌ Document migration errors:")
            for error in doc_errors:
                print(f"   - {error}")
        
        print()
        
        # Step 7: Verify migration
        print_step(7, "Verifying migration")
        verification = await migration_service.verify_migration()
        
        if verification['success']:
            print("✅ Migration verification passed")
            print(f"   Users verified: {verification['users_verified']}")
            print(f"   Conversations verified: {verification['conversations_verified']}")
            print(f"   Documents verified: {verification['documents_verified']}")
        else:
            print("❌ Migration verification failed:")
            for discrepancy in verification['discrepancies']:
                print(f"   - {discrepancy}")
            
            response = input("\nRollback migration? (y/N): ")
            if response.lower() == 'y':
                print("Rolling back migration...")
                rollback_success = await migration_service.rollback_migration(backup_path)
                if rollback_success:
                    print("✅ Migration rolled back successfully")
                else:
                    print("❌ Rollback failed")
                return False
        
        print()
        
        # Step 8: Save migration report
        print_step(8, "Saving migration report")
        report_path = migration_service.save_migration_report()
        print(f"✅ Migration report saved: {report_path}")
        print()
        
        # Success summary
        print("=" * 60)
        print("MIGRATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"Users migrated: {user_count}")
        print(f"Conversations migrated: {conv_count}")
        print(f"Documents migrated: {doc_count}")
        print(f"Backup location: {backup_path}")
        print(f"Report location: {report_path}")
        print()
        print("Your PharmGPT application now uses Supabase exclusively!")
        print("You can safely delete the backup after verifying everything works.")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def run_migration():
    """Run migration with proper async handling."""
    try:
        # Set up Streamlit secrets for command line usage
        if not hasattr(st, 'secrets'):
            # Try to load secrets from file
            secrets_file = ".streamlit/secrets.toml"
            if os.path.exists(secrets_file):
                import toml
                secrets = toml.load(secrets_file)
                st.secrets = type('Secrets', (), secrets)()
            else:
                print("❌ Streamlit secrets not found. Please ensure .streamlit/secrets.toml exists")
                return False
        
        # Run migration
        return asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n❌ Migration cancelled by user")
        return False
    except Exception as e:
        print(f"❌ Migration setup failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)