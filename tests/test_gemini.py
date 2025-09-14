#!/usr/bin/env python3
"""
Gemini API Connectivity Test
Test script to verify Google Gemini AI API is accessible and working
"""

import os
import sys

def test_gemini_connection():
    """Test connection to Google Gemini API"""
    try:
        import google.generativeai as genai
        print("✅ Google GenerativeAI library imported successfully")
    except ImportError:
        print("❌ Failed to import google.generativeai")
        print("💡 Install with: pip install google-generativeai")
        return False

    # Get API key from environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY environment variable not set")
        print("💡 Set with: export GOOGLE_API_KEY=your-api-key")
        return False

    # Configure the API
    try:
        genai.configure(api_key=api_key)
        print("✅ Gemini API configured successfully")
    except Exception as e:
        print(f"❌ Failed to configure Gemini API: {e}")
        return False

    # Test the connection with a simple request
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Gemini 1.5 Flash model loaded successfully")

        response = model.generate_content("Test connection: respond with 'OK' if working")
        print(f"✅ Connection test successful!")
        print(f"📝 Response: {response.text}")
        return True

    except Exception as e:
        print(f"❌ Failed to generate content: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Gemini API Connectivity...")
    print("=" * 50)

    # Check API key setting
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")
    print(f"🔧 GOOGLE_GENAI_USE_VERTEXAI: {use_vertex}")

    # Run the test
    success = test_gemini_connection()

    print("=" * 50)
    if success:
        print("🎉 All tests passed! Gemini AI is ready to use.")
        return 0
    else:
        print("💥 Tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())