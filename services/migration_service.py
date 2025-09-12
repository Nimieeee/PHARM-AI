"""
Migration Service for PharmGPT
Handles migration from file-based storage to Supabase
"""

import os
import json
import shutil
import asyncio
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import streamlit as st
import logging

from services.user_service import user_service
from services.session_service import session_service
from services.conversation_service import conversation_service
from services.document_service import document_service
from supabase_manager import connection_manager

logger = logging.getLogger(__name__)

class MigrationService:
    """Service class for migrating file-based data to Supabase."""
    
    def __init__(self, user_data_dir: str = "user_data"):
        self.user_data_dir = user_data_dir
        self.backup_dir = f"{user_data_dir}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.migration_log = []
    
    def _log_migration(self, level: str, message: str):
        """Log migration progress."""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {level}: {message}"
        self.migration_log.append(log_entry)
        
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)
    
    async def detect_existing_data(self) -> Dict:
        """
        Detect and analyze existing file-based data.
        
        Returns:
            Dict: Analysis of existing data structure
        """
        try:
            self._log_migration("INFO", "Starting data detection...")
            
            analysis = {
                'users_file_exists': False,
                'sessions_file_exists': False,
                'uploads_file_exists': False,
                'user_count': 0,
                'conversation_count': 0,
                'document_count': 0,
                'total_size_mb': 0,
                'users': [],
                'conversations_by_user': {},
                'documents_by_user': {},
                'errors': []
            }
            
            if not os.path.exists(self.user_data_dir):
                self._log_migration("WARNING", f"User data directory not found: {self.user_data_dir}")
                return analysis
            
            # Check for main data files
            users_file = os.path.join(self.user_data_dir, "users.json")
            sessions_file = os.path.join(self.user_data_dir, "sessions.json")
            uploads_file = os.path.join(self.user_data_dir, "uploads.json")
            
            analysis['users_file_exists'] = os.path.exists(users_file)
            analysis['sessions_file_exists'] = os.path.exists(sessions_file)
            analysis['uploads_file_exists'] = os.path.exists(uploads_file)
            
            # Analyze users
            if analysis['users_file_exists']:
                try:
                    with open(users_file, 'r') as f:
                        users_data = json.load(f)
                    
                    analysis['user_count'] = len(users_data)
                    analysis['users'] = list(users_data.keys())
                    
                    self._log_migration("INFO", f"Found {analysis['user_count']} users")
                    
                    # Analyze each user's data
                    for username, user_info in users_data.items():
                        user_id = user_info.get('user_id')
                        if not user_id:
                            analysis['errors'].append(f"User {username} missing user_id")
                            continue
                        
                        # Check conversations
                        conv_dir = os.path.join(self.user_data_dir, f"conversations_{user_id}")
                        conv_file = os.path.join(conv_dir, "conversations.json")
                        
                        if os.path.exists(conv_file):
                            try:
                                with open(conv_file, 'r') as f:
                                    conversations = json.load(f)
                                
                                analysis['conversations_by_user'][user_id] = len(conversations)
                                analysis['conversation_count'] += len(conversations)
                                
                                # Calculate total messages
                                total_messages = sum(
                                    len(conv.get('messages', [])) 
                                    for conv in conversations.values()
                                )
                                
                                self._log_migration("INFO", 
                                    f"User {username}: {len(conversations)} conversations, {total_messages} messages")
                                
                            except Exception as e:
                                analysis['errors'].append(f"Error reading conversations for {username}: {str(e)}")
                        
                        # Check RAG documents
                        rag_dir = os.path.join(self.user_data_dir, f"rag_{user_id}")
                        if os.path.exists(rag_dir):
                            doc_count = 0
                            for conv_dir in os.listdir(rag_dir):
                                conv_path = os.path.join(rag_dir, conv_dir)
                                if os.path.isdir(conv_path):
                                    metadata_file = os.path.join(conv_path, "documents_metadata.json")
                                    if os.path.exists(metadata_file):
                                        try:
                                            with open(metadata_file, 'r') as f:
                                                metadata = json.load(f)
                                            doc_count += len(metadata)
                                        except Exception as e:
                                            analysis['errors'].append(f"Error reading document metadata for {username}: {str(e)}")
                            
                            analysis['documents_by_user'][user_id] = doc_count
                            analysis['document_count'] += doc_count
                
                except Exception as e:
                    analysis['errors'].append(f"Error reading users file: {str(e)}")
            
            # Calculate total size
            try:
                total_size = 0
                for root, dirs, files in os.walk(self.user_data_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        total_size += os.path.getsize(file_path)
                
                analysis['total_size_mb'] = round(total_size / (1024 * 1024), 2)
                
            except Exception as e:
                analysis['errors'].append(f"Error calculating total size: {str(e)}")
            
            self._log_migration("INFO", f"Data detection complete: {analysis['user_count']} users, "
                              f"{analysis['conversation_count']} conversations, "
                              f"{analysis['document_count']} documents, "
                              f"{analysis['total_size_mb']} MB")
            
            return analysis
            
        except Exception as e:
            self._log_migration("ERROR", f"Error during data detection: {str(e)}")
            return {'errors': [str(e)]}
    
    async def validate_data_integrity(self, analysis: Dict) -> Dict:
        """
        Validate data integrity before migration.
        
        Args:
            analysis: Data analysis from detect_existing_data
            
        Returns:
            Dict: Validation results
        """
        try:
            self._log_migration("INFO", "Starting data integrity validation...")
            
            validation = {
                'valid': True,
                'warnings': [],
                'errors': [],
                'user_validation': {},
                'conversation_validation': {},
                'document_validation': {}
            }
            
            # Validate users file
            if analysis['users_file_exists']:
                users_file = os.path.join(self.user_data_dir, "users.json")
                try:
                    with open(users_file, 'r') as f:
                        users_data = json.load(f)
                    
                    for username, user_info in users_data.items():
                        user_validation = {
                            'has_user_id': 'user_id' in user_info,
                            'has_password_hash': 'password_hash' in user_info,
                            'has_salt': 'salt' in user_info,
                            'has_created_at': 'created_at' in user_info
                        }
                        
                        validation['user_validation'][username] = user_validation
                        
                        if not all(user_validation.values()):
                            validation['errors'].append(f"User {username} missing required fields")
                            validation['valid'] = False
                
                except Exception as e:
                    validation['errors'].append(f"Error validating users file: {str(e)}")
                    validation['valid'] = False
            
            # Validate conversations
            for user_id, conv_count in analysis['conversations_by_user'].items():
                conv_dir = os.path.join(self.user_data_dir, f"conversations_{user_id}")
                conv_file = os.path.join(conv_dir, "conversations.json")
                
                try:
                    with open(conv_file, 'r') as f:
                        conversations = json.load(f)
                    
                    conv_validation = {
                        'file_readable': True,
                        'valid_json': True,
                        'conversation_count': len(conversations),
                        'invalid_conversations': []
                    }
                    
                    for conv_id, conv_data in conversations.items():
                        if not isinstance(conv_data, dict):
                            conv_validation['invalid_conversations'].append(conv_id)
                            continue
                        
                        required_fields = ['title', 'messages', 'created_at']
                        if not all(field in conv_data for field in required_fields):
                            conv_validation['invalid_conversations'].append(conv_id)
                    
                    validation['conversation_validation'][user_id] = conv_validation
                    
                    if conv_validation['invalid_conversations']:
                        validation['warnings'].append(
                            f"User {user_id} has {len(conv_validation['invalid_conversations'])} invalid conversations"
                        )
                
                except Exception as e:
                    validation['errors'].append(f"Error validating conversations for user {user_id}: {str(e)}")
                    validation['valid'] = False
            
            # Validate documents
            for user_id, doc_count in analysis['documents_by_user'].items():
                rag_dir = os.path.join(self.user_data_dir, f"rag_{user_id}")
                
                doc_validation = {
                    'total_documents': doc_count,
                    'invalid_documents': [],
                    'missing_metadata': []
                }
                
                if os.path.exists(rag_dir):
                    for conv_dir in os.listdir(rag_dir):
                        conv_path = os.path.join(rag_dir, conv_dir)
                        if os.path.isdir(conv_path):
                            metadata_file = os.path.join(conv_path, "documents_metadata.json")
                            if os.path.exists(metadata_file):
                                try:
                                    with open(metadata_file, 'r') as f:
                                        metadata = json.load(f)
                                    
                                    for doc_hash, doc_info in metadata.items():
                                        required_fields = ['filename', 'file_type', 'chunk_count', 'added_at']
                                        if not all(field in doc_info for field in required_fields):
                                            doc_validation['invalid_documents'].append(doc_hash)
                                
                                except Exception as e:
                                    doc_validation['missing_metadata'].append(conv_dir)
                
                validation['document_validation'][user_id] = doc_validation
                
                if doc_validation['invalid_documents']:
                    validation['warnings'].append(
                        f"User {user_id} has {len(doc_validation['invalid_documents'])} invalid documents"
                    )
            
            self._log_migration("INFO", f"Data validation complete. Valid: {validation['valid']}, "
                              f"Warnings: {len(validation['warnings'])}, Errors: {len(validation['errors'])}")
            
            return validation
            
        except Exception as e:
            self._log_migration("ERROR", f"Error during data validation: {str(e)}")
            return {'valid': False, 'errors': [str(e)]}
    
    async def create_backup(self) -> str:
        """
        Create backup of existing file-based data.
        
        Returns:
            str: Backup directory path
        """
        try:
            self._log_migration("INFO", f"Creating backup at {self.backup_dir}...")
            
            if not os.path.exists(self.user_data_dir):
                self._log_migration("WARNING", "No user data directory to backup")
                return ""
            
            # Copy entire user data directory
            shutil.copytree(self.user_data_dir, self.backup_dir)
            
            # Create backup manifest
            manifest = {
                'backup_created': datetime.now().isoformat(),
                'original_path': self.user_data_dir,
                'backup_path': self.backup_dir,
                'migration_log': self.migration_log.copy()
            }
            
            manifest_file = os.path.join(self.backup_dir, "backup_manifest.json")
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            self._log_migration("INFO", f"Backup created successfully at {self.backup_dir}")
            return self.backup_dir
            
        except Exception as e:
            self._log_migration("ERROR", f"Error creating backup: {str(e)}")
            raise
    
    async def migrate_users(self) -> Tuple[int, List[str]]:
        """
        Migrate users from file-based storage to Supabase.
        
        Returns:
            Tuple[int, List[str]]: (success_count, error_messages)
        """
        try:
            self._log_migration("INFO", "Starting user migration...")
            
            users_file = os.path.join(self.user_data_dir, "users.json")
            if not os.path.exists(users_file):
                self._log_migration("WARNING", "No users file found")
                return 0, []
            
            with open(users_file, 'r') as f:
                users_data = json.load(f)
            
            success_count = 0
            errors = []
            user_mapping = {}  # old_user_id -> new_uuid mapping
            
            for username, user_info in users_data.items():
                try:
                    # Check if user already exists in Supabase
                    existing_user = await user_service.get_user_by_username(username)
                    if existing_user:
                        self._log_migration("INFO", f"User {username} already exists in Supabase")
                        user_mapping[user_info['user_id']] = existing_user['id']
                        success_count += 1
                        continue
                    
                    # Create user in Supabase with existing hash and salt
                    user_data = {
                        'username': username,
                        'password_hash': user_info['password_hash'],
                        'salt': user_info['salt'],
                        'user_id': user_info['user_id'],  # Keep legacy user_id
                        'email': user_info.get('email'),
                        'created_at': user_info.get('created_at', datetime.now().isoformat()),
                        'is_active': True
                    }
                    
                    result = connection_manager.execute_query(
                        table='users',
                        operation='insert',
                        data=user_data
                    )
                    
                    if result.data:
                        new_user = result.data[0]
                        user_mapping[user_info['user_id']] = new_user['id']
                        success_count += 1
                        self._log_migration("INFO", f"Migrated user: {username}")
                    else:
                        errors.append(f"Failed to create user {username}")
                
                except Exception as e:
                    error_msg = f"Error migrating user {username}: {str(e)}"
                    errors.append(error_msg)
                    self._log_migration("ERROR", error_msg)
            
            # Store user mapping for other migrations
            self.user_mapping = user_mapping
            
            self._log_migration("INFO", f"User migration complete: {success_count} users migrated")
            return success_count, errors
            
        except Exception as e:
            self._log_migration("ERROR", f"Error during user migration: {str(e)}")
            return 0, [str(e)]
    
    async def migrate_conversations(self, user_mapping: Dict) -> Tuple[int, List[str]]:
        """
        Migrate conversations from file-based storage to Supabase.
        
        Args:
            user_mapping: Mapping of old user_id to new UUID
            
        Returns:
            Tuple[int, List[str]]: (success_count, error_messages)
        """
        try:
            self._log_migration("INFO", "Starting conversation migration...")
            
            success_count = 0
            errors = []
            
            for old_user_id, new_user_uuid in user_mapping.items():
                conv_dir = os.path.join(self.user_data_dir, f"conversations_{old_user_id}")
                conv_file = os.path.join(conv_dir, "conversations.json")
                
                if not os.path.exists(conv_file):
                    self._log_migration("INFO", f"No conversations file for user {old_user_id}")
                    continue
                
                try:
                    with open(conv_file, 'r') as f:
                        conversations = json.load(f)
                    
                    for conv_id, conv_data in conversations.items():
                        try:
                            # Check if conversation already exists
                            existing_conv = await conversation_service.get_conversation(new_user_uuid, conv_id)
                            if existing_conv:
                                self._log_migration("INFO", f"Conversation {conv_id} already exists")
                                success_count += 1
                                continue
                            
                            # Prepare conversation data
                            conversation_data = {
                                'conversation_id': conv_id,
                                'user_id': new_user_uuid,
                                'title': conv_data.get('title', 'Untitled'),
                                'messages': json.dumps(conv_data.get('messages', [])),
                                'model': conv_data.get('model', 'meta-llama/llama-4-maverick-17b-128e-instruct'),
                                'created_at': conv_data.get('created_at', datetime.now().isoformat()),
                                'message_count': len(conv_data.get('messages', [])),
                                'is_archived': False
                            }
                            
                            result = connection_manager.execute_query(
                                table='conversations',
                                operation='insert',
                                data=conversation_data
                            )
                            
                            if result.data:
                                success_count += 1
                                self._log_migration("INFO", f"Migrated conversation: {conv_id}")
                            else:
                                errors.append(f"Failed to create conversation {conv_id}")
                        
                        except Exception as e:
                            error_msg = f"Error migrating conversation {conv_id}: {str(e)}"
                            errors.append(error_msg)
                            self._log_migration("ERROR", error_msg)
                
                except Exception as e:
                    error_msg = f"Error reading conversations for user {old_user_id}: {str(e)}"
                    errors.append(error_msg)
                    self._log_migration("ERROR", error_msg)
            
            self._log_migration("INFO", f"Conversation migration complete: {success_count} conversations migrated")
            return success_count, errors
            
        except Exception as e:
            self._log_migration("ERROR", f"Error during conversation migration: {str(e)}")
            return 0, [str(e)]
    
    async def migrate_documents(self, user_mapping: Dict) -> Tuple[int, List[str]]:
        """
        Migrate document metadata from file-based storage to Supabase.
        
        Args:
            user_mapping: Mapping of old user_id to new UUID
            
        Returns:
            Tuple[int, List[str]]: (success_count, error_messages)
        """
        try:
            self._log_migration("INFO", "Starting document migration...")
            
            success_count = 0
            errors = []
            
            for old_user_id, new_user_uuid in user_mapping.items():
                rag_dir = os.path.join(self.user_data_dir, f"rag_{old_user_id}")
                
                if not os.path.exists(rag_dir):
                    self._log_migration("INFO", f"No RAG directory for user {old_user_id}")
                    continue
                
                for conv_dir in os.listdir(rag_dir):
                    conv_path = os.path.join(rag_dir, conv_dir)
                    if not os.path.isdir(conv_path):
                        continue
                    
                    # Extract conversation ID from directory name
                    if conv_dir.startswith("conversation_"):
                        conversation_id = conv_dir.replace("conversation_", "")
                    else:
                        continue
                    
                    metadata_file = os.path.join(conv_path, "documents_metadata.json")
                    if not os.path.exists(metadata_file):
                        continue
                    
                    try:
                        with open(metadata_file, 'r') as f:
                            documents_metadata = json.load(f)
                        
                        for doc_hash, doc_info in documents_metadata.items():
                            try:
                                # Check if document already exists
                                existing_doc = await document_service.get_document_by_hash(new_user_uuid, doc_hash)
                                if existing_doc:
                                    self._log_migration("INFO", f"Document {doc_hash} already exists")
                                    success_count += 1
                                    continue
                                
                                # Prepare document data
                                doc_data = {
                                    'document_hash': doc_hash,
                                    'filename': doc_info.get('filename', 'Unknown'),
                                    'file_type': doc_info.get('file_type', 'unknown'),
                                    'file_size': doc_info.get('file_size', 0),
                                    'chunk_count': doc_info.get('chunk_count', 0),
                                    'metadata': doc_info,
                                    'is_processed': True
                                }
                                
                                if await document_service.save_document_metadata(new_user_uuid, conversation_id, doc_data):
                                    success_count += 1
                                    self._log_migration("INFO", f"Migrated document: {doc_info.get('filename', doc_hash)}")
                                else:
                                    errors.append(f"Failed to migrate document {doc_hash}")
                            
                            except Exception as e:
                                error_msg = f"Error migrating document {doc_hash}: {str(e)}"
                                errors.append(error_msg)
                                self._log_migration("ERROR", error_msg)
                    
                    except Exception as e:
                        error_msg = f"Error reading document metadata for {conv_dir}: {str(e)}"
                        errors.append(error_msg)
                        self._log_migration("ERROR", error_msg)
            
            self._log_migration("INFO", f"Document migration complete: {success_count} documents migrated")
            return success_count, errors
            
        except Exception as e:
            self._log_migration("ERROR", f"Error during document migration: {str(e)}")
            return 0, [str(e)]
    
    async def verify_migration(self) -> Dict:
        """
        Verify migration completeness and integrity.
        
        Returns:
            Dict: Verification results
        """
        try:
            self._log_migration("INFO", "Starting migration verification...")
            
            verification = {
                'success': True,
                'users_verified': 0,
                'conversations_verified': 0,
                'documents_verified': 0,
                'discrepancies': [],
                'errors': []
            }
            
            # Get original data analysis
            original_analysis = await self.detect_existing_data()
            
            # Verify users
            if original_analysis['users_file_exists']:
                users_file = os.path.join(self.user_data_dir, "users.json")
                with open(users_file, 'r') as f:
                    original_users = json.load(f)
                
                for username in original_users.keys():
                    migrated_user = await user_service.get_user_by_username(username)
                    if migrated_user:
                        verification['users_verified'] += 1
                    else:
                        verification['discrepancies'].append(f"User {username} not found in Supabase")
                        verification['success'] = False
            
            # Verify conversations
            for old_user_id, expected_count in original_analysis['conversations_by_user'].items():
                if old_user_id in self.user_mapping:
                    new_user_uuid = self.user_mapping[old_user_id]
                    migrated_conversations = await conversation_service.get_user_conversations(new_user_uuid)
                    actual_count = len(migrated_conversations)
                    
                    if actual_count == expected_count:
                        verification['conversations_verified'] += actual_count
                    else:
                        verification['discrepancies'].append(
                            f"User {old_user_id}: expected {expected_count} conversations, found {actual_count}"
                        )
                        verification['success'] = False
            
            # Verify documents
            for old_user_id, expected_count in original_analysis['documents_by_user'].items():
                if old_user_id in self.user_mapping:
                    new_user_uuid = self.user_mapping[old_user_id]
                    migrated_documents = await document_service.get_user_documents(new_user_uuid)
                    actual_count = len(migrated_documents)
                    
                    if actual_count == expected_count:
                        verification['documents_verified'] += actual_count
                    else:
                        verification['discrepancies'].append(
                            f"User {old_user_id}: expected {expected_count} documents, found {actual_count}"
                        )
                        verification['success'] = False
            
            self._log_migration("INFO", f"Migration verification complete. Success: {verification['success']}")
            return verification
            
        except Exception as e:
            self._log_migration("ERROR", f"Error during migration verification: {str(e)}")
            return {'success': False, 'errors': [str(e)]}
    
    async def rollback_migration(self, backup_path: str) -> bool:
        """
        Rollback migration by restoring from backup.
        
        Args:
            backup_path: Path to backup directory
            
        Returns:
            bool: Success status
        """
        try:
            self._log_migration("INFO", f"Starting migration rollback from {backup_path}...")
            
            if not os.path.exists(backup_path):
                self._log_migration("ERROR", f"Backup directory not found: {backup_path}")
                return False
            
            # Remove current user data directory
            if os.path.exists(self.user_data_dir):
                shutil.rmtree(self.user_data_dir)
            
            # Restore from backup
            shutil.copytree(backup_path, self.user_data_dir)
            
            self._log_migration("INFO", "Migration rollback completed successfully")
            return True
            
        except Exception as e:
            self._log_migration("ERROR", f"Error during rollback: {str(e)}")
            return False
    
    def get_migration_log(self) -> List[str]:
        """Get migration log entries."""
        return self.migration_log.copy()
    
    def save_migration_report(self, report_path: str = None) -> str:
        """Save migration report to file."""
        if not report_path:
            report_path = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'migration_timestamp': datetime.now().isoformat(),
            'backup_directory': self.backup_dir,
            'migration_log': self.migration_log,
            'user_mapping': getattr(self, 'user_mapping', {})
        }
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report_path

# Global migration service instance
migration_service = MigrationService()

# Convenience functions
async def detect_existing_data() -> Dict:
    """Detect existing file-based data."""
    return await migration_service.detect_existing_data()

async def migrate_all_data() -> Dict:
    """Migrate all data from files to Supabase."""
    try:
        # Detect and validate data
        analysis = await migration_service.detect_existing_data()
        validation = await migration_service.validate_data_integrity(analysis)
        
        if not validation['valid']:
            return {
                'success': False,
                'error': 'Data validation failed',
                'validation': validation
            }
        
        # Create backup
        backup_path = await migration_service.create_backup()
        
        # Migrate data
        user_count, user_errors = await migration_service.migrate_users()
        conv_count, conv_errors = await migration_service.migrate_conversations(migration_service.user_mapping)
        doc_count, doc_errors = await migration_service.migrate_documents(migration_service.user_mapping)
        
        # Verify migration
        verification = await migration_service.verify_migration()
        
        # Save report
        report_path = migration_service.save_migration_report()
        
        return {
            'success': verification['success'],
            'backup_path': backup_path,
            'users_migrated': user_count,
            'conversations_migrated': conv_count,
            'documents_migrated': doc_count,
            'errors': user_errors + conv_errors + doc_errors,
            'verification': verification,
            'report_path': report_path
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }