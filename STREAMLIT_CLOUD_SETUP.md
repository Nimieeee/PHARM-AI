# Supabase Setup for Streamlit Cloud

Quick setup guide for getting PharmGPT working with Supabase on Streamlit Cloud.

## Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create a free account
2. Click "New Project"
3. Enter project name: `pharmgpt` (or any name you prefer)
4. Create a strong database password
5. Select a region close to your users
6. Click "Create new project" and wait for it to initialize

## Step 2: Set Up Database Schema

1. In your Supabase dashboard, go to **SQL Editor**
2. Click "New Query"
3. Copy the entire contents of `supabase_setup.sql` from your repository
4. Paste it into the SQL editor
5. Click "Run" to execute the script

This creates all the necessary tables, indexes, and policies for PharmGPT.

## Step 3: Get Your Credentials

1. In Supabase dashboard, go to **Settings** → **API**
2. Copy these two values:
   - **Project URL** (e.g., `https://abcdefgh.supabase.co`)
   - **Anon/Public Key** (starts with `eyJ...`)

## Step 4: Configure Streamlit Cloud Secrets

1. Go to your Streamlit Cloud app dashboard
2. Click on your app, then go to **Settings**
3. Click on **Secrets**
4. Add these secrets:

```toml
# Supabase Configuration
SUPABASE_URL = "https://your-project-id.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Your existing API keys (keep these)
GROQ_API_KEY = "your-groq-key"
OPENROUTER_API_KEY = "your-openrouter-key"
```

5. Click "Save"

## Step 5: Test Your Setup

1. Your Streamlit app will automatically restart after saving secrets
2. Go to your app URL and add `?page=streamlit_cloud_setup` to test the setup
   - Example: `https://your-app.streamlit.app/?page=streamlit_cloud_setup`
3. This will run connection tests and verify everything is working

## Step 6: Verify Everything Works

Your PharmGPT app should now:
- ✅ Allow user registration and login
- ✅ Save conversation history
- ✅ Persist user sessions
- ✅ Track uploaded documents

## Troubleshooting

### "Database connection not available"
- Check that your SUPABASE_URL and SUPABASE_ANON_KEY are correctly set in Streamlit secrets
- Make sure there are no extra spaces or quotes in the secrets

### "Missing tables" error
- Go back to Supabase SQL Editor and run the `supabase_setup.sql` script
- Check the Supabase logs for any SQL errors

### "Authentication failed"
- This usually means the database schema wasn't created properly
- Re-run the SQL setup script in Supabase

### RLS Policy Issues
- The setup uses simplified RLS policies that allow all operations
- This is fine for development; for production, you may want stricter policies

## Production Considerations

For production use:
1. **Backup**: Enable automatic backups in Supabase
2. **Monitoring**: Set up Supabase monitoring alerts
3. **Rate Limiting**: Consider implementing rate limiting
4. **Security**: Review and tighten RLS policies if needed

## Need Help?

1. Check the Supabase dashboard logs for detailed error messages
2. Use the test page (`streamlit_cloud_setup.py`) to diagnose issues
3. Verify your secrets are correctly formatted in Streamlit Cloud

Your PharmGPT app is now ready to use Supabase for all data operations! 🎉