"""
Support Ticket Management Utilities
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def get_support_tickets(username: Optional[str] = None) -> List[Dict]:
    """Get all support tickets, optionally filtered by username."""
    try:
        support_dir = "user_data/support_tickets"
        if not os.path.exists(support_dir):
            return []
        
        tickets = []
        for filename in os.listdir(support_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(support_dir, filename), 'r') as f:
                        ticket = json.load(f)
                        
                    # Filter by username if specified
                    if username and ticket.get('username') != username:
                        continue
                        
                    tickets.append(ticket)
                except Exception as e:
                    logger.error(f"Error reading ticket file {filename}: {e}")
                    continue
        
        # Sort by creation date (newest first)
        tickets.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return tickets
        
    except Exception as e:
        logger.error(f"Error getting support tickets: {e}")
        return []

def get_support_ticket(ticket_id: str) -> Optional[Dict]:
    """Get a specific support ticket by ID."""
    try:
        support_dir = "user_data/support_tickets"
        ticket_file = os.path.join(support_dir, f"{ticket_id}.json")
        
        if os.path.exists(ticket_file):
            with open(ticket_file, 'r') as f:
                return json.load(f)
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting support ticket {ticket_id}: {e}")
        return None

def update_support_ticket(ticket_id: str, updates: Dict) -> bool:
    """Update a support ticket with new information."""
    try:
        support_dir = "user_data/support_tickets"
        ticket_file = os.path.join(support_dir, f"{ticket_id}.json")
        
        if not os.path.exists(ticket_file):
            return False
        
        # Load existing ticket
        with open(ticket_file, 'r') as f:
            ticket = json.load(f)
        
        # Apply updates
        ticket.update(updates)
        ticket['updated_at'] = datetime.now().isoformat()
        
        # Save updated ticket
        with open(ticket_file, 'w') as f:
            json.dump(ticket, f, indent=2)
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating support ticket {ticket_id}: {e}")
        return False

def get_support_stats() -> Dict:
    """Get support ticket statistics."""
    try:
        tickets = get_support_tickets()
        
        stats = {
            'total_tickets': len(tickets),
            'open_tickets': len([t for t in tickets if t.get('status') == 'open']),
            'closed_tickets': len([t for t in tickets if t.get('status') == 'closed']),
            'by_type': {},
            'by_priority': {},
            'recent_tickets': tickets[:5]  # Last 5 tickets
        }
        
        # Count by issue type
        for ticket in tickets:
            issue_type = ticket.get('issue_type', 'Unknown')
            stats['by_type'][issue_type] = stats['by_type'].get(issue_type, 0) + 1
        
        # Count by priority
        for ticket in tickets:
            priority = ticket.get('priority', 'Medium')
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting support stats: {e}")
        return {
            'total_tickets': 0,
            'open_tickets': 0,
            'closed_tickets': 0,
            'by_type': {},
            'by_priority': {},
            'recent_tickets': []
        }

def export_support_tickets(format: str = 'json') -> Optional[str]:
    """Export all support tickets to a file."""
    try:
        tickets = get_support_tickets()
        
        if format.lower() == 'json':
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'total_tickets': len(tickets),
                'tickets': tickets
            }
            
            export_file = f"user_data/support_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return export_file
        
        return None
        
    except Exception as e:
        logger.error(f"Error exporting support tickets: {e}")
        return None