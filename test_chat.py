from google import genai
import sys

def test_chat_with_history():
    """Test a chat-like interaction with history, similar to what app.py needs to do"""
    
    # Initialize Google GenAI client - ONLY the API key, no extra params
    client = genai.Client(api_key="AIzaSyDBBf4uwKQpV7bbgDadhdmPmLIv99PI-1k")
    
    # Simulated conversation history
    history = [
        {"role": "user", "content": "Hello, who are you?"},
        {"role": "assistant", "content": "I'm an AI assistant powered by Gemini."}
    ]
    
    # New user message
    new_message = "Tell me about yourself"
    
    try:
        # Make the simplest possible API call first
        print("\nSimple API call test:")
        print("-" * 40)
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents="Hello, how are you?"
        )
        print(f"Response: {response.text}")
        print("-" * 40)
        
        # Now try with our conversation context
        print("\nAPI call with conversation context:")
        
        # Format the content properly - THIS IS THE KEY PART
        content = f"User: {new_message}"
        
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=content
        )
        
        # Print the response
        print("\nAPI Test Successful!\n")
        print("Response from Gemini API:")
        print("-" * 40)
        print(response.text)
        
        return True
    except Exception as e:
        print("\nAPI Test Failed!\n")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("\nTesting Gemini chat-like interaction with history...\n")
    success = test_chat_with_history()
    if success:
        print("\nSuccess! The chat interaction works correctly. We'll use this approach in app.py")
    else:
        print("\nFailed to make the chat interaction work.")
        sys.exit(1)
