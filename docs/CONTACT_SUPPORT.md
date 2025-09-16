# Contact Support Feature

## Overview

The Contact Support feature provides users with multiple ways to get help and report issues with PharmGPT. It includes a comprehensive support ticket system, FAQ section, and contact information.

## Features

### 1. Support Ticket System
- **Ticket Submission Form**: Users can submit detailed support tickets with:
  - Issue type categorization
  - Priority levels (Low, Medium, High, Critical)
  - Detailed descriptions
  - Browser/device information
  - Error messages
  - Contact information

- **Automatic Ticket Management**: 
  - Unique ticket ID generation
  - Timestamp tracking
  - User authentication status
  - Local file storage in `user_data/support_tickets/`

### 2. FAQ Section
- Comprehensive frequently asked questions
- Expandable sections for easy navigation
- Covers common issues like:
  - Account management
  - Document uploads
  - AI model differences
  - Technical troubleshooting

### 3. Contact Information
- Multiple contact methods (email addresses for different issue types)
- Support hours information
- Response time expectations

### 4. System Information
- Automatic system diagnostics
- User session information
- App statistics
- Environment details
- OCR status checking
- Exportable system info for troubleshooting

## Access Points

The Contact Support feature is accessible from multiple locations:

1. **Navigation Sidebar**: Available for both authenticated and unauthenticated users
2. **Homepage Footer**: "Need Help? Contact Support" button
3. **Main App Footer**: Direct access from the main application

## File Structure

```
pages/
├── 4_📞_Contact_Support.py    # Main contact support page
└── admin_support.py           # Admin dashboard (development only)

utils/
└── support_manager.py         # Support ticket management utilities

docs/
└── CONTACT_SUPPORT.md         # This documentation

user_data/
└── support_tickets/           # Storage for submitted tickets
    ├── TICKET_username_timestamp.json
    └── ...
```

## Usage

### For Users

1. **Submitting a Ticket**:
   - Navigate to Contact Support page
   - Fill out the support ticket form
   - Include as much detail as possible
   - Submit and receive a ticket ID

2. **Getting Quick Help**:
   - Check the FAQ section first
   - Review contact information for direct communication
   - Use system information tab for technical details

### For Developers/Admins

1. **Viewing Tickets**:
   - Access `pages/nimi_admin.py` (secure admin only)
   - View dashboard with ticket statistics
   - Filter and manage tickets
   - Export ticket data

2. **Ticket Management**:
   - Use `utils/support_manager.py` functions
   - Update ticket status programmatically
   - Generate support statistics

## Configuration

### Email Addresses (Demo)
The current implementation uses demo email addresses:
- `support@pharmgpt.demo` - General support
- `bugs@pharmgpt.demo` - Bug reports
- `features@pharmgpt.demo` - Feature requests

### Storage Location
Support tickets are stored locally in:
```
user_data/support_tickets/TICKET_{username}_{timestamp}.json
```

## Integration with Existing Features

### Authentication
- Automatically detects user authentication status
- Pre-fills username for authenticated users
- Requires contact information for anonymous users

### Session Management
- Integrates with existing session state
- Preserves user context during support interactions
- Maintains navigation consistency

### Theme Support
- Uses existing theme system
- Consistent styling with the rest of the application
- Responsive design for different screen sizes

## Future Enhancements

### Potential Improvements
1. **Email Integration**: Connect to actual email service for notifications
2. **Real-time Chat**: Add live chat support widget
3. **Knowledge Base**: Expand FAQ into searchable knowledge base
4. **Ticket Tracking**: Allow users to track their ticket status
5. **File Attachments**: Support for uploading screenshots and files
6. **Auto-categorization**: AI-powered ticket categorization
7. **Response Templates**: Pre-defined responses for common issues

### Database Integration
When migrating to a database system:
- Store tickets in dedicated support tables
- Add user relationships and ticket history
- Implement proper indexing for search functionality
- Add audit trails for ticket modifications

## Security Considerations

### Data Privacy
- Support tickets contain user information
- Implement proper access controls in production
- Consider data retention policies
- Ensure GDPR compliance if applicable

### Admin Access
- Current admin dashboard is for development only
- Implement proper authentication for production admin access
- Add role-based permissions
- Audit admin actions

## Testing

### Manual Testing
1. Submit tickets as both authenticated and anonymous users
2. Test all form validations
3. Verify ticket storage and retrieval
4. Check system information accuracy
5. Test navigation from all access points

### Automated Testing
Consider adding tests for:
- Ticket submission validation
- File storage operations
- Support statistics generation
- System information collection

## Troubleshooting

### Common Issues
1. **Tickets not saving**: Check `user_data/support_tickets/` directory permissions
2. **System info errors**: Verify all imported modules are available
3. **Navigation issues**: Ensure all page references are correct
4. **OCR status errors**: Check OCR dependencies installation

### Debug Information
The system information tab provides comprehensive debugging data including:
- Session state details
- App statistics
- Environment information
- OCR capabilities
- Python and Streamlit versions