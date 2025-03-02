from google import genai

# Initialize the client with just the API key
client = genai.Client(api_key="AIzaSyDBBf4uwKQpV7bbgDadhdmPmLIv99PI-1k")

try:
    # Make the simplest possible API call
    print("Making a simple API call...")
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents="Hello, how are you?"
    )
    print(f"Success! Response: {response.text}")
    
except Exception as e:
    print(f"Error: {str(e)}")
