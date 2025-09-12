# Supabase Setup Guide for PharmGPT

This guide will help you set up Supabase integration for PharmGPT from scratch.

## Prerequisites

1. **Supabase Account**: Create a free account at [supabase.com](https://supabase.com)
2. **Python Dependencies**: Make sure you have the required packages installed:
   ```bash
   pip install supabase streamlit
   ```

## Step 1: Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Choose your organization
4. Enter a project name (e.g., "pharmgpt")
5. Create a strong database password
6. Select a region close to your users
7. Click "Create new project"

## Step 2: Get Your Supabase Credentials

1. In your Supabase dashboard, go to **Settings** → **API**
2. Copy the following values:
   - **Project URL** (looks like: `https://your-project.supabase.co`)
   - **Anon/Public Key** (starts with `eyJ...`)

## Step 3: Configure Streamlit Secrets

Create or update your `.streamlit/secrets.toml` file:

```toml
# Supabase Configuration
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Your existing API keys
GROQ_API_KEY = "your-groq-key"
OPENROUTER_API_KEY = "your-openrouter-key"
```

## Step 4: Set Up the Database Schema

Run the setup script to create all required tables and policies:

```bash
streamlit run setup_supabase.py
```

This will:
- Create all necessary tables (users, sessions, conversations, messages, documents)
- Set up proper indexes for performance
- Configure Row Level Security (RLS) policies
- Create helper functions and views

## Step 5: Test Your Setup

Run the test script to verify everything is working:

```bash
python test_supabase_setup.py
```

This will test:
- Database connection
- Table accessibility
- User creation and authentication
- Basic CRUD operations

## Step 6: Update Your Application

The application should now automatically use Supabase for all data operations. The key changes:

- **User Management**: All user accounts are stored in Supabase
- **Sessions**: User sessions are persisted in the database
- **Conversations**: Chat history is saved and retrievable
- **Documents**: Uploaded files are tracked in the database

## Database Schema Overview

### Tables Created

1. **users**: User accounts with authentication
2. **sessions**: User session management
3. **conversations**: Chat conversation metadata
4. **messages**: Individual chat messages
5. **documents**: Uploaded document tracking

### Security Features

- **Row Level Security (RLS)**: Users can only access their own data
- **Password Hashing**: Secure password storage with salt
- **Session Management**: Automatic session cleanup
- **Data Isolation**: Complete user data separation

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check your SUPABASE_URL and SUPABASE_ANON_KEY in secrets.toml
   - Ensure your Supabase project is active

2. **Table Not Found**
   - Run `streamlit run setup_supabase.py` to create the schema
   - Check the Supabase dashboard for any error messages

3. **Authentication Issues**
   - Verify RLS policies are properly configured
   - Check the Supabase logs in your dashboard

4. **Permission Denied**
   - Ensure you're using the correct anon key (not the service role key)
   - Check that RLS policies allow the operation

### Getting Help

1. Check the Supabase dashboard logs
2. Run the test script for detailed error messages
3. Review the database schema in your Supabase dashboard

## Production Considerations

For production deployment:

1. **Environment Variables**: Use proper environment variables instead of secrets.toml
2. **Connection Pooling**: The connection manager handles this automatically
3. **Monitoring**: Set up Supabase monitoring and alerts
4. **Backups**: Configure automatic database backups
5. **Rate Limiting**: Consider implementing rate limiting for API calls

## Migration from File-Based Storage

If you're migrating from the previous file-based system:

1. Export your existing data (if any)
2. Run the setup script
3. Import your data using the migration tools (if needed)
4. Test thoroughly before switching to production

Your PharmGPT application is now ready to use Supabase for all data operations!