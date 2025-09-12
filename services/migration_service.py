"""
Migration Service for PharmGPT
Simple data migration utilities for Supabase
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st

from supabase_manager import get_supabase_client

logger = logging.getLogger(__name__)

class MigrationService:
    """Simple service for basic data migration tasks."""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def export_user_data(self, user_id: str) -> Dict:
        """Export a user's data from Supabase."""
        try:
            if not self.supabase:
                return {"error": "Database connection not available"}
            
            # Get user info
            user_result = self.supabase.table('users').select('*').eq('user_id', user_id).execute()
            if not user_result.data:
                return {"error": "User not found"}
            
            user = user_result.data[0]
            user_uuid = user['id']
            
            # Get conversations
            conversations_result = self.supabase.table('conversations').select('*').eq('user_uuid', user_uuid).execute()
            conversations = conversations_result.data or []
            
            # Get messages for each conversation
            for conversation in conversations:
                messages_result = self.supabase.table('messages').select('*').eq('conversation_uuid', conversation['id']).execute()
                conversation['messages'] = messages_result.data or []
            
            # Get documents
            documents_result = self.supabase.table('documents').select('*').eq('user_uuid', user_uuid).execute()
            documents = documents_result.data or []
            
            # Get sessions
            sessions_result = self.supabase.table('sessions').select('*').eq('user_uuid', user_uuid).execute()
            sessions = sessions_result.data or []
            
            return {
                "user": user,
                "conversations": conversations,
                "documents": documents,
                "sessions": sessions,
                "exported_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting user data: {e}")
            return {"error": str(e)}
    
    def import_user_data(self, data: Dict) -> bool:
        """Import user data into Supabase."""
        try:
            if not self.supabase:
                logger.error("Database connection not available")
                return False
            
            # This is a basic implementation - you would need to handle
            # conflicts, validation, etc. in a production system
            
            # Import user (if not exists)
            user_data = data.get('user', {})
            if user_data:
                existing = self.supabase.table('users').select('id').eq('username', user_data['username']).execute()
                if not existing.data:
                    self.supabase.table('users').insert(user_data).execute()
            
            # Import conversations, messages, documents, sessions...
            # (Implementation would depend on your specific needs)
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing user data: {e}")
            return False
    
    def cleanup_old_data(self, user_id: str, older_than_days: int = 30) -> bool:
        """Clean up old data for a user."""
        try:
            if not self.supabase:
                return False
            
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - older_than_days)
            
            # Get user UUID
            user_result = self.supabase.table('users').select('id').eq('user_id', user_id).execute()
            if not user_result.data:
                return False
            
            user_uuid = user_result.data[0]['id']
            
            # Clean up old sessions
            self.supabase.table('sessions').delete().eq('user_uuid', user_uuid).lt('created_at', cutoff_date.isoformat()).execute()
            
            # Clean up old conversations (if desired)
            # self.supabase.table('conversations').delete().eq('user_uuid', user_uuid).lt('created_at', cutoff_date.isoformat()).execute()
            
            logger.info(f"Cleaned up old data for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up data: {e}")
            return False

# Global migration service instance
migration_service = MigrationService()

# Convenience functions
def export_user_data(user_id: str) -> Dict:
    """Export user data."""
    return migration_service.export_user_data(user_id)

def cleanup_old_data(user_id: str, older_than_days: int = 30) -> bool:
    """Clean up old data."""
    return migration_service.cleanup_old_data(user_id, older_than_days)