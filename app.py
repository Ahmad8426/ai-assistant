from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
from flask_cors import CORS
import uuid
import logging
import dotenv
import time
from datetime import datetime
import json
import threading
from google import genai
from google.genai.types import HttpOptions
import base64

# Speech libraries
import tempfile
from vosk import Model, KaldiRecognizer
import io
import tempfile
import pygame
import numpy as np
from pydub import AudioSegment
import torch

# Alternative TTS libraries
import pyttsx3
import speech_recognition as sr
import PIL.Image

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if present
dotenv.load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24).hex())

# Initialize Google GenAI client
api_key = os.getenv('GOOGLE_API_KEY', "AIzaSyDBBf4uwKQpV7bbgDadhdmPmLIv99PI-1k")
client = genai.Client(api_key=api_key)

# Set the default model
DEFAULT_MODEL = "gemini-2.0-flash"  # Using the correct model name format

# Initialize Text-to-Speech engines
try:
    # Initialize pyttsx3 as primary TTS engine
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)  # Speed of speech
    voices = engine.getProperty('voices')
    if voices:
        engine.setProperty('voice', voices[0].id)
    
    # Initialize pygame for audio playback
    pygame.mixer.init()
    
    tts_available = True
except Exception as e:
    logger.error(f"Error initializing Text-to-Speech: {e}")
    tts_available = False

# Initialize Vosk for speech recognition
try:
    logger.info("Initializing Vosk model...")
    # Create a directory for Vosk models if it doesn't exist
    VOSK_MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vosk_models')
    os.makedirs(VOSK_MODEL_DIR, exist_ok=True)
    
    # Check if we have a model already downloaded
    model_path = os.path.join(VOSK_MODEL_DIR, 'vosk-model-small-en-us-0.15')
    if not os.path.exists(model_path):
        logger.info("Vosk model not found. Using default model path. You may need to download a model from https://alphacephei.com/vosk/models")
        # Use the current directory as fallback
        model_path = "vosk-model-small-en-us-0.15"
    
    # Initialize Vosk model
    vosk_model = Model(model_path)
    vosk_available = True
    logger.info("Vosk model initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Vosk: {e}")
    vosk_available = False

# Initialize TTS
try:
    logger.info("Initializing TTS model...")
    # Get device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")
    
    # Initialize TTS with a multilingual model
    tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    tts_available = True
except Exception as e:
    logger.error(f"Error initializing TTS: {e}")
    tts_available = False

# Local chat history storage
HISTORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_history')
os.makedirs(HISTORY_DIR, exist_ok=True)

# Store conversation history in memory for quick access
conversations = {}

def save_conversation(conversation_id, history):
    """Save conversation history to a local file"""
    try:
        file_path = os.path.join(HISTORY_DIR, f"{conversation_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")
        return False

def load_conversation(conversation_id):
    """Load conversation history from a local file"""
    try:
        file_path = os.path.join(HISTORY_DIR, f"{conversation_id}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading conversation: {e}")
        return []

def list_conversations():
    """List all saved conversations"""
    try:
        conversations = []
        for filename in os.listdir(HISTORY_DIR):
            if filename.endswith('.json'):
                conversation_id = filename[:-5]  # Remove .json extension
                file_path = os.path.join(HISTORY_DIR, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data and len(data) > 0:
                        # Get the first user message as title
                        title = next((item['content'] for item in data if item['role'] == 'user'), 'Untitled')
                        if len(title) > 30:
                            title = title[:30] + '...'
                        conversations.append({
                            'id': conversation_id,
                            'title': title,
                            'timestamp': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M")
                        })
        return sorted(conversations, key=lambda x: x['timestamp'], reverse=True)
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        return []

def generate_response(prompt, conversation_id, image_data=None):
    """Generate a response using the Gemini API."""
    try:
        # Get conversation history from memory or load from file
        history = conversations.get(conversation_id, load_conversation(conversation_id))
        
        # Format the prompt exactly like in our working test
        contents = prompt  # Start with just the prompt
        
        # Add image if present
        if image_data:
            try:
                import PIL.Image
                img_bytes = base64.b64decode(image_data.split(',')[1])
                image = PIL.Image.open(io.BytesIO(img_bytes))
                # Make a list of content parts
                contents = [prompt, image]
            except Exception as e:
                logger.error(f"Error processing image: {e}")
        
        # Make the API call with minimal parameters
        logger.info(f"Sending request to Gemini with model {DEFAULT_MODEL}")
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=contents
        )
        
        # Extract the response text
        response_content = response.text
        logger.info(f"Received response from Gemini: {response_content[:100]}...")
        
        # Update conversation history
        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": response_content})
        
        # Store updated conversation history
        conversations[conversation_id] = history[-40:]  # Keep more context
        
        # Save to file in background to avoid blocking
        threading.Thread(target=save_conversation, args=(conversation_id, conversations[conversation_id])).start()
        
        return response_content
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in generate_response: {error_msg}")
        return f"Sorry, I encountered an error: {error_msg}"

def text_to_speech_gemini(text, lang='en'):
    """Convert text to speech using TTS library"""
    try:
        logger.info(f"Requesting text-to-speech for: {text[:50]}...")
        
        # Create a temporary file to save the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_filename = temp_file.name
        
        # Generate speech with TTS
        tts_model.tts_to_file(text=text, file_path=temp_filename, language=lang)
        
        # Play the audio
        pygame.mixer.music.load(temp_filename)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        # Clean up
        pygame.mixer.music.unload()
        os.unlink(temp_filename)
        return True
    except Exception as e:
        logger.error(f"Error in TTS: {e}")
        # Fallback to pyttsx3
        try:
            engine.say(text)
            engine.runAndWait()
            return True
        except Exception as e2:
            logger.error(f"Error in fallback TTS: {e2}")
            return False

def speech_to_text_gemini(audio_data):
    """Convert speech to text using Vosk"""
    try:
        logger.info("Processing speech-to-text with Vosk...")
        
        # Save audio data to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_file.write(audio_data)
            temp_filename = temp_file.name
        
        # Convert to the format Vosk expects (16kHz, 16-bit, mono)
        audio = AudioSegment.from_file(temp_filename)
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        
        # Save the converted audio
        converted_filename = temp_filename + "_converted.wav"
        audio.export(converted_filename, format="wav")
        
        # Read the converted audio file
        with open(converted_filename, "rb") as wf:
            # Create recognizer
            recognizer = KaldiRecognizer(vosk_model, 16000)
            
            # Process audio in chunks
            while True:
                data = wf.read(4000)
                if len(data) == 0:
                    break
                recognizer.AcceptWaveform(data)
            
            # Get the final result
            result = json.loads(recognizer.FinalResult())
            
        # Clean up
        os.unlink(temp_filename)
        os.unlink(converted_filename)
        
        # Extract the transcription from the response
        transcription = result.get("text", "")
        logger.info(f"Vosk transcription: {transcription}")
        
        return transcription
    except Exception as e:
        logger.error(f"Error in Vosk STT: {e}")
        # Fallback to SpeechRecognition
        try:
            recognizer = sr.Recognizer()
            with sr.AudioFile(io.BytesIO(audio_data)) as source:
                audio = recognizer.record(source)
                result = recognizer.recognize_google(audio)
                logger.info(f"Fallback transcription: {result}")
                return result
        except Exception as e2:
            logger.error(f"Error in fallback STT: {e2}")
            return ""

def translate_text(text, target_lang):
    """Translate text using Gemini's translation capabilities"""
    try:
        logger.info(f"Translating text to {target_lang}: {text[:50]}...")
        
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=[{
                "role": "user", 
                "parts": [{"text": f"Translate the following text to {target_lang}. Return only the translation with no additional text: {text}"}]
            }]
        )
        
        translation = response.text.strip()
        logger.info(f"Translation result: {translation[:50]}...")
        return translation
    except Exception as e:
        logger.error(f"Error in translation: {e}")
        return f"Translation error: {str(e)}"

@app.route('/')
def home():
    # Generate a new conversation ID if not in session
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
    
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        logger.info(f"Received chat request with data: {data}")
        
        if not data or 'message' not in data:
            logger.error("No message provided in request")
            return jsonify({'error': 'No message provided'})
        
        message = data['message']
        logger.info(f"Processing message: {message}")
        
        # Make the API call with minimal parameters
        logger.info("Making Gemini API call...")
        
        # Ensure message is a string
        if not isinstance(message, str):
            message = str(message)
        
        # Make the API call as simple as possible - exactly like our working test
        response = client.models.generate_content(
            model=DEFAULT_MODEL,
            contents=message
        )
        
        # Get the response text
        if response and hasattr(response, 'text'):
            response_text = response.text
            logger.info(f"Got response from API: {response_text[:100]}...")
            
            return jsonify({
                'response': response_text,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        else:
            logger.error("No valid response from Gemini API")
            return jsonify({'error': 'No valid response from AI model'})
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in chat endpoint: {error_msg}")
        return jsonify({'error': error_msg})

@app.route('/speak', methods=['POST'])
def speak():
    """Convert text to speech and play it"""
    data = request.get_json()
    text = data.get('text', '')
    lang = data.get('lang', 'en')
    
    if not text:
        return jsonify({'success': False, 'error': 'No text provided'})
    
    try:
        # Create a temporary file to save the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            temp_filename = temp_file.name
        
        # Generate speech with TTS
        if tts_available:
            tts_model.tts_to_file(text=text, file_path=temp_filename, language=lang)
            
            # Play the audio
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            # Clean up
            pygame.mixer.music.unload()
            os.unlink(temp_filename)
            success = True
        else:
            # Fallback to pyttsx3
            engine.say(text)
            engine.runAndWait()
            success = True
    except Exception as e:
        logger.error(f"Error in TTS: {e}")
        success = False
    
    return jsonify({'success': success})

@app.route('/voice', methods=['POST'])
def voice():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'})
    
    audio_file = request.files['audio']
    conversation_id = request.form.get('conversation_id', session.get('conversation_id', str(uuid.uuid4())))
    
    try:
        # Save the audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_filename = temp_file.name
        
        # Read the audio file
        with open(temp_filename, 'rb') as f:
            audio_data = f.read()
        
        # Transcribe audio using Vosk
        if vosk_available:
            transcription = speech_to_text_gemini(audio_data)
        else:
            # Fallback to SpeechRecognition
            recognizer = sr.Recognizer()
            with sr.AudioFile(temp_filename) as source:
                audio = recognizer.record(source)
                transcription = recognizer.recognize_google(audio)
        
        # Clean up
        os.unlink(temp_filename)
        
        if not transcription:
            return jsonify({'error': 'Could not transcribe audio'})
        
        # Generate response
        response = generate_response(transcription, conversation_id)
        
        # Speak the response
        if tts_available:
            # Create a temporary file to save the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                output_filename = temp_file.name
            
            # Generate speech with TTS
            tts_model.tts_to_file(text=response, file_path=output_filename)
        
        return jsonify({
            'transcription': transcription,
            'response': response,
            'conversation_id': conversation_id
        })
    except Exception as e:
        logger.error(f"Error processing voice: {e}")
        return jsonify({'error': str(e)})

@app.route('/translate', methods=['POST'])
def translate():
    """Translate text to a specified language"""
    try:
        data = request.json
        text = data.get('text', '')
        target_lang = data.get('lang', 'en')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Use Gemini for translation
        translation = translate_text(text, target_lang)
        
        return jsonify({
            'original': text,
            'translation': translation,
            'language': target_lang
        })
    except Exception as e:
        logger.error(f"Error in translate route: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/clear_conversation', methods=['POST'])
def clear_conversation():
    data = request.get_json()
    conversation_id = data.get('conversation_id', session.get('conversation_id'))
    
    if not conversation_id:
        return jsonify({'success': False, 'error': 'No conversation ID provided'})
    
    # Clear conversation from memory
    if conversation_id in conversations:
        del conversations[conversation_id]
    
    # Remove conversation file
    file_path = os.path.join(HISTORY_DIR, f"{conversation_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Generate a new conversation ID
    new_conversation_id = str(uuid.uuid4())
    session['conversation_id'] = new_conversation_id
    
    return jsonify({'success': True, 'conversation_id': new_conversation_id})

@app.route('/available_languages')
def available_languages():
    # List of supported languages for translation and TTS
    languages = {
        'en': 'English',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ja': 'Japanese',
        'zh-cn': 'Chinese (Simplified)',
        'ar': 'Arabic',
        'hi': 'Hindi'
    }
    return jsonify(languages)

@app.route('/get_conversations')
def get_conversations():
    conversations = list_conversations()
    return jsonify(conversations)

@app.route('/load_chat', methods=['POST'])
def load_chat():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    
    if not conversation_id:
        return jsonify({'success': False, 'error': 'No conversation ID provided'})
    
    # Load conversation history
    history = load_conversation(conversation_id)
    
    # Store in memory cache
    conversations[conversation_id] = history
    
    # Store in session
    session['conversation_id'] = conversation_id
    
    # Format for display
    formatted_history = []
    for message in history:
        formatted_history.append({
            'role': message['role'],
            'content': message['content'],
            'timestamp': message.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M"))
        })
    
    return jsonify({
        'success': True,
        'conversation_id': conversation_id,
        'history': formatted_history
    })

@app.route('/delete_conversation', methods=['POST'])
def delete_conversation():
    data = request.get_json()
    conversation_id = data.get('conversation_id')
    
    if not conversation_id:
        return jsonify({'success': False, 'error': 'No conversation ID provided'})
    
    # Remove from memory
    if conversation_id in conversations:
        del conversations[conversation_id]
    
    # Remove file
    file_path = os.path.join(HISTORY_DIR, f"{conversation_id}.json")
    if os.path.exists(file_path):
        os.remove(file_path)
        
    # Create a new conversation if the deleted one was active
    if session.get('conversation_id') == conversation_id:
        session['conversation_id'] = str(uuid.uuid4())
    
    return jsonify({
        'success': True,
        'conversations': list_conversations(),
        'active_conversation_id': session.get('conversation_id')
    })

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        data = request.get_json()
        # Save settings (you can expand this to save to a file/database)
        settings = {
            'tts_enabled': data.get('tts_enabled', True),
            'voice_speed': data.get('voice_speed', 150),
            'theme': data.get('theme', 'light')
        }
        # Example of updating settings
        if 'voice_speed' in settings:
            try:
                engine.setProperty('rate', int(settings['voice_speed']))
            except Exception as e:
                logger.error(f"Error updating voice speed: {e}")
        
        return jsonify({'success': True, 'settings': settings})
    else:
        # Return current settings
        return jsonify({
            'tts_enabled': True,
            'voice_speed': 150,
            'theme': 'light'
        })

@app.route('/voice_chat', methods=['POST'])
def voice_chat():
    """Process voice input and return voice response"""
    try:
        data = request.json
        audio_data = data.get('audio')
        conversation_id = data.get('conversation_id', str(uuid.uuid4()))
        
        if not audio_data:
            return jsonify({'error': 'No audio data provided'}), 400
        
        # Decode base64 audio data
        audio_bytes = base64.b64decode(audio_data.split(',')[1])
        
        # Convert speech to text
        transcription = speech_to_text_gemini(audio_bytes)
        
        if not transcription:
            return jsonify({'error': 'Could not transcribe audio'}), 400
        
        # Generate response from Gemini
        response_text = generate_response(transcription, conversation_id)
        
        # Convert response to speech
        # We'll just return the text and let the client handle TTS
        # to avoid timing out the request
        
        return jsonify({
            'transcription': transcription,
            'response': response_text,
            'conversation_id': conversation_id
        })
    except Exception as e:
        logger.error(f"Error in voice_chat route: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/start_voice_session', methods=['POST'])
def start_voice_session():
    """Start a new voice chat session with Gemini Live API"""
    try:
        data = request.json
        session_id = str(uuid.uuid4())
        
        # We'll just return a session ID for now
        # The actual streaming would be handled via WebSockets in a production app
        
        return jsonify({
            'session_id': session_id,
            'message': 'Voice session started. Use the session_id for subsequent requests.'
        })
    except Exception as e:
        logger.error(f"Error starting voice session: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting AI Assistant application...")
    app.run(debug=True, host='0.0.0.0', port=5000)
