from google import genai
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_gemini_api():
    """Test basic text generation with Gemini API"""
    # Initialize Google GenAI client
    client = genai.Client(
        api_key="AIzaSyDBBf4uwKQpV7bbgDadhdmPmLIv99PI-1k"
    )
    
    try:
        # Create a simple completion using the new SDK
        logger.info("Testing text generation with Gemini 2.0 Flash")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Hello, how are you?"
        )
        
        # Print the response
        print("\nAPI Test Successful!\n")
        print("Response from Gemini API:")
        print("--------------------------")
        print(response.text)
        return True
    except Exception as e:
        print("\nAPI Test Failed!\n")
        print(f"Error: {str(e)}")
        return False

def test_translation():
    """Test translation capability with Gemini API"""
    # Initialize Google GenAI client
    client = genai.Client(
        api_key="AIzaSyDBBf4uwKQpV7bbgDadhdmPmLIv99PI-1k"
    )
    
    try:
        # Test translation
        logger.info("Testing translation with Gemini 2.0 Flash")
        text_to_translate = "Hello, how are you today? I hope you're doing well."
        target_language = "French"
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{
                "role": "user", 
                "parts": [{"text": f"Translate the following text to {target_language}. Return only the translation with no additional text: {text_to_translate}"}]
            }]
        )
        
        # Print the response
        print("\nTranslation Test Successful!\n")
        print(f"Original ({target_language}):")
        print(text_to_translate)
        print("\nTranslation:")
        print("--------------------------")
        print(response.text)
        return True
    except Exception as e:
        print("\nTranslation Test Failed!\n")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\nTesting connection to Google Gemini API...\n")
    success = test_gemini_api()
    
    if success:
        print("\nThe integration with Google Gemini API is working correctly!")
        
        # Test translation if basic test passed
        print("\nTesting translation capability...\n")
        translation_success = test_translation()
        
        if translation_success:
            print("\nTranslation capability is working correctly!")
        else:
            print("\nTranslation test failed, but basic API connection is working.")
    else:
        print("\nFailed to connect to the Gemini API. Please check your configuration and API key.")
        sys.exit(1)
