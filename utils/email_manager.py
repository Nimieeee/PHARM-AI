"""
Email Manager for Support Ticket Notifications
"""

import logging
import json
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def send_ticket_confirmation(ticket_data: Dict) -> bool:
    """
    Send confirmation email for support ticket.
    In production, this would integrate with an email service.
    For now, it creates a local confirmation record.
    """
    try:
        # Create confirmation record
        confirmation = {
            'ticket_id': ticket_data.get('ticket_id'),
            'email': ticket_data.get('contact_email'),
            'subject': ticket_data.get('subject'),
            'sent_at': datetime.now().isoformat(),
            'status': 'sent',
            'type': 'ticket_confirmation'
        }
        
        # Save confirmation record (in production, send actual email)
        save_email_confirmation(confirmation)
        
        logger.info(f"Confirmation sent for ticket {ticket_data.get('ticket_id')}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send confirmation: {e}")
        return False

def save_email_confirmation(confirmation: Dict) -> bool:
    """Save email confirmation record."""
    try:
        import os
        
        # Create email confirmations directory
        email_dir = "user_data/email_confirmations"
        os.makedirs(email_dir, exist_ok=True)
        
        # Save confirmation
        filename = f"{confirmation['ticket_id']}_confirmation.json"
        filepath = os.path.join(email_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(confirmation, f, indent=2)
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to save email confirmation: {e}")
        return False

def get_confirmation_template(ticket_data: Dict) -> str:
    """Generate email confirmation template."""
    template = f"""
Subject: Support Ticket Confirmation - {ticket_data.get('ticket_id')}

Dear {ticket_data.get('contact_name', 'User')},

Thank you for contacting PharmGPT Support. We have received your support ticket and will respond as soon as possible.

Ticket Details:
- Ticket ID: {ticket_data.get('ticket_id')}
- Subject: {ticket_data.get('subject')}
- Priority: {ticket_data.get('priority')}
- Issue Type: {ticket_data.get('issue_type')}
- Submitted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Your message:
{ticket_data.get('description', 'No description provided')}

What happens next?
- Our support team will review your ticket
- We typically respond within 24-48 hours
- You'll receive updates via email at {ticket_data.get('contact_email')}

For urgent issues, please include "URGENT" in your subject line.

Best regards,
PharmGPT Support Team

---
This is an automated confirmation. Please do not reply to this email.
For additional support, visit: https://your-app.streamlit.app/4_📞_Contact_Support
"""
    return template