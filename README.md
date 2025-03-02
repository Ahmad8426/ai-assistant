# AI Assistant

A comprehensive AI assistant with chat, voice, speech, and translation capabilities powered by Google's Gemini 2.0 Flash model.

## Features

- **Chat with Gemini**: Interact with Google's Gemini 2.0 Flash for intelligent conversations
- **Voice Chat**: Have natural voice conversations with the AI
- **Voice Input**: Speak to your assistant using offline speech recognition with Vosk
- **Text-to-Speech**: Listen to AI responses through text-to-speech
- **Translation**: Translate conversations to multiple languages
- **Conversation History**: Maintain context across your conversation
- **Markdown Support**: Format AI responses with rich markdown
- **Multimodal Support**: Upload and analyze images along with text

## Setup Instructions

1. **Clone the repository**

2. **Set up a virtual environment (optional but recommended)**
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

4. **Environment Variables**
   Create a `.env` file in the project root with the following:
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   SECRET_KEY=your_secret_key
   ```

5. **Run the application**
   ```
   python app.py
   ```

6. **Access the application**
   Open your browser and go to: `http://localhost:5000`

## Usage

- Type in the text area and press Enter or the Send button to chat with the AI
- Click the microphone button to use voice input
- Toggle Voice Chat mode to have continuous voice conversations
- Use the Speak button to hear the AI's response
- Select a language and click Translate to translate the AI's response
- Click Clear Chat to start a new conversation

## New Gemini 2.0 Flash Features

- **Improved Translation**: More accurate and natural-sounding translations
- **Enhanced Voice Chat**: Continuous voice conversations with the AI
- **Offline Speech Recognition**: Using Vosk for completely free, offline multilingual speech recognition
- **Multimodal Support**: Upload and analyze images along with text
- **Better Response Quality**: More coherent and contextually relevant responses

## Requirements

- Python 3.9+
- A Google Gemini API key
- Internet connection for API calls and translation services

## Troubleshooting

- **Text-to-Speech issues**: Make sure you have the proper audio drivers installed
- **Voice recognition problems**: Check your microphone settings and permissions
- **Vosk model not found**: Download the appropriate language model from https://alphacephei.com/vosk/models and place it in the vosk_models directory
- **API errors**: Verify your API keys are correct and have sufficient quota

## License

This project is licensed under the MIT License - see the LICENSE file for details.
