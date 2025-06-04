#!/usr/bin/env python3
"""
Healthcare AI Assistant Demo - Quick Start Script
This script helps set up and run the Healthcare AI Assistant demo.
"""

import sys
import subprocess
import os

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_requirements():
    """Install required packages"""
    print("\n📦 Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ All packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False

def run_streamlit_app():
    """Run the Streamlit application"""
    print("\n🚀 Starting Healthcare AI Assistant Demo...")
    print("📱 The application will open in your default web browser.")
    print("🌐 URL: http://localhost:8501")
    print("\n💡 Try these sample queries:")
    print("   • 'Show me the sales trend for Aspirin'")
    print("   • 'Compare drug sales performance'")
    print("   • 'How is Medication X performing in Europe?'")
    print("\n⏹️  Press Ctrl+C to stop the application")
    print("-" * 50)
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "demo_app.py"])
    except KeyboardInterrupt:
        print("\n👋 Demo stopped. Thank you for using Healthcare AI Assistant!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Streamlit: {e}")
        print("💡 Try running manually: streamlit run demo_app.py")

def main():
    """Main setup and run function"""
    print("🏥 Healthcare AI Assistant Demo - Quick Start")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found!")
        print("Please make sure you're in the correct directory.")
        return
    
    # Check if demo_app.py exists
    if not os.path.exists("demo_app.py"):
        print("❌ demo_app.py not found!")
        print("Please make sure you're in the correct directory.")
        return
    
    # Install requirements
    if not install_requirements():
        return
    
    # Run the application
    run_streamlit_app()

if __name__ == "__main__":
    main() 