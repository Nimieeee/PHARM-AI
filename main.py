from openai_client import chat_completion
from website import Website
from prompts import system_prompt, user_prompt, pharmacology_system_prompt
from streamer import stream_brochure
import subprocess
import sys

def test_basic_functionality():
    """Test basic functionality of the chatbot components."""
    print("🧪 Testing PharmBot Components...")
    
    # Test OpenAI connection
    try:
        response = chat_completion(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello! Test message for pharmacology bot."}],
        )
        print("✅ OpenAI Connection: Working")
        print(f"Sample Response: {response[:100]}...")
    except Exception as e:
        print(f"❌ OpenAI Connection: Failed - {e}")
    
    # Test pharmacology prompt
    try:
        response = chat_completion(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": pharmacology_system_prompt},
                {"role": "user", "content": "What is the mechanism of action of aspirin?"},
            ],
        )
        print("✅ Pharmacology System Prompt: Working")
        print(f"Pharmacology Response: {response[:150]}...")
    except Exception as e:
        print(f"❌ Pharmacology System Prompt: Failed - {e}")

def run_streamlit_app():
    """Launch the Streamlit app."""
    print("🚀 Launching PharmBot Streamlit App...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "streamlit_app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to launch Streamlit app: {e}")
    except KeyboardInterrupt:
        print("\n👋 Streamlit app stopped by user")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PharmBot - Pharmacology Chatbot")
    parser.add_argument("--test", action="store_true", help="Run component tests")
    parser.add_argument("--app", action="store_true", help="Launch Streamlit app")
    
    args = parser.parse_args()
    
    if args.test:
        test_basic_functionality()
    elif args.app:
        run_streamlit_app()
    else:
        print("PharmBot - Pharmacology Chatbot")
        print("Usage:")
        print("  python main.py --test    # Test components")
        print("  python main.py --app     # Launch Streamlit app")
        print("  streamlit run streamlit_app.py  # Direct Streamlit launch")
