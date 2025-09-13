#!/usr/bin/env python3
"""
Deploy PharmGPT to GitHub for Streamlit Cloud deployment
This script helps safely push the project to GitHub without secrets
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed")
            print(f"   Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def check_git_status():
    """Check current git status"""
    print("🔍 Checking git status...")
    
    # Check if git is initialized
    if not os.path.exists('.git'):
        print("📁 Git repository not initialized")
        return False, "not_initialized"
    
    # Check for uncommitted changes
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print("📝 Uncommitted changes detected:")
        print(result.stdout)
        return True, "has_changes"
    else:
        print("✅ Working directory clean")
        return True, "clean"

def verify_secrets_excluded():
    """Verify that secrets are properly excluded"""
    print("🔐 Verifying secrets are excluded...")
    
    # Check if .env exists and is gitignored
    if os.path.exists('.env'):
        result = subprocess.run("git check-ignore .env", shell=True, capture_output=True)
        if result.returncode == 0:
            print("✅ .env file is properly ignored")
        else:
            print("⚠️  .env file exists but may not be ignored!")
            return False
    
    # Check if secrets.toml exists and is gitignored
    if os.path.exists('.streamlit/secrets.toml'):
        result = subprocess.run("git check-ignore .streamlit/secrets.toml", shell=True, capture_output=True)
        if result.returncode == 0:
            print("✅ secrets.toml is properly ignored")
        else:
            print("⚠️  secrets.toml exists but may not be ignored!")
            return False
    
    # Check for any files containing potential secrets (excluding documentation)
    sensitive_patterns = [
        "sk-",  # OpenAI API key pattern
        "gsk_",  # Groq API key pattern
    ]
    
    print("🔍 Scanning for actual API keys in tracked files...")
    for pattern in sensitive_patterns:
        result = subprocess.run(f"git ls-files | xargs grep -l '{pattern}' 2>/dev/null || true", 
                              shell=True, capture_output=True, text=True)
        if result.stdout.strip():
            files = result.stdout.strip().split('\n')
            # Filter out documentation and template files
            suspicious_files = [f for f in files if not any(f.endswith(ext) for ext in 
                              ('.md', 'config.py', 'prepare_deployment.py', 'deploy_to_github.py', 
                               '_template.toml', '.example'))]
            if suspicious_files:
                print(f"⚠️  Actual API key pattern '{pattern}' found in: {suspicious_files}")
                return False
    
    print("✅ No secrets detected in tracked files")
    return True

def create_github_workflow():
    """Create GitHub Actions workflow for automated deployment checks"""
    workflow_content = """name: Streamlit App Check

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  check:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Check app structure
      run: |
        python -c "
        import os
        required_files = ['app.py', 'requirements.txt', 'config.py']
        missing = [f for f in required_files if not os.path.exists(f)]
        if missing:
            print(f'Missing required files: {missing}')
            exit(1)
        print('All required files present')
        "
    
    - name: Verify no secrets in code
      run: |
        if grep -r "sk-" . --exclude-dir=.git --exclude="*.md" --exclude="deploy_to_github.py"; then
          echo "Potential API keys found in code!"
          exit 1
        fi
        echo "No API keys detected in code"
"""
    
    os.makedirs('.github/workflows', exist_ok=True)
    with open('.github/workflows/check.yml', 'w') as f:
        f.write(workflow_content)
    
    print("✅ Created GitHub Actions workflow")

def main():
    """Main deployment function"""
    print("🚀 Deploying PharmGPT to GitHub")
    print("=" * 50)
    
    # Check git status
    git_exists, status = check_git_status()
    
    # Initialize git if needed
    if not git_exists:
        if not run_command("git init", "Initializing git repository"):
            return False
    
    # Verify secrets are excluded
    if not verify_secrets_excluded():
        print("\n❌ Security check failed! Please fix secret exclusions before proceeding.")
        return False
    
    # Create GitHub workflow
    create_github_workflow()
    
    # Add all files
    if not run_command("git add .", "Adding files to git"):
        return False
    
    # Check what's being committed
    print("\n📋 Files to be committed:")
    subprocess.run("git diff --cached --name-only", shell=True)
    
    # Confirm before committing
    print(f"\n⚠️  IMPORTANT: Please verify that no secrets are being committed!")
    print(f"Review the file list above and ensure:")
    print(f"- No .env files")
    print(f"- No secrets.toml files") 
    print(f"- No API keys in any files")
    
    confirm = input(f"\nProceed with commit? (yes/no): ").lower().strip()
    if confirm != 'yes':
        print("❌ Deployment cancelled by user")
        return False
    
    # Commit changes
    commit_message = "Deploy PharmGPT to Streamlit Cloud - Production ready with RAG system"
    if not run_command(f'git commit -m "{commit_message}"', "Committing changes"):
        print("ℹ️  No changes to commit or commit failed")
    
    # Instructions for GitHub
    print(f"\n🎉 Local git repository prepared!")
    print(f"\n📋 Next Steps:")
    print(f"1. Create a new repository on GitHub")
    print(f"2. Add the remote origin:")
    print(f"   git remote add origin https://github.com/yourusername/pharmgpt.git")
    print(f"3. Push to GitHub:")
    print(f"   git branch -M main")
    print(f"   git push -u origin main")
    print(f"4. Go to Streamlit Cloud and deploy from your GitHub repo")
    print(f"5. Configure Streamlit secrets with your API keys")
    
    print(f"\n🔐 Streamlit Secrets Configuration:")
    print(f"In Streamlit Cloud, add these secrets:")
    print(f"- GROQ_API_KEY")
    print(f"- OPENROUTER_API_KEY") 
    print(f"- SUPABASE_URL")
    print(f"- SUPABASE_ANON_KEY")
    
    print(f"\n✅ Your app is ready for Streamlit Cloud deployment!")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)