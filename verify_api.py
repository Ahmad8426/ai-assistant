import os
import logging
from google import genai
import dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
dotenv.load_dotenv()

# Initialize client
api_key = os.getenv('GOOGLE_API_KEY', "AIzaSyDBBf4uwKQpV7bbgDadhdmPmLIv99PI-1k")
client = genai.Client(api_key=api_key)

# Test message
test_message = "Hello, how are you?"

try:
    # Make API call
    logger.info(f"Sending test message: {test_message}")
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=test_message
    )
    
    # Check response
    if response and hasattr(response, 'text'):
        logger.info(f"Success! Response: {response.text}")
    else:
        logger.error("No valid response from API")
        
except Exception as e:
    logger.error(f"Error: {str(e)}")
