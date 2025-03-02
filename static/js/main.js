$(document).ready(function() {
    // Constants and variables
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    let isRecording = false;
    let languages = {};
    let currentTheme = localStorage.getItem('theme') || 'light';
    let isVoiceChatActive = false;
    let mediaRecorder = null;
    let audioChunks = [];
    
    // Initialize
    loadLanguages();
    loadConversations();
    initializeTheme();
    
    // Event listeners
    $('#sendBtn').on('click', sendMessage);
    $('#userInput').on('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    $('#voiceInputBtn').on('click', toggleVoiceRecording);
    $('#speakBtn').on('click', speakLastResponse);
    $('#translateBtn').on('click', translateLastResponse);
    $('#clearBtn').on('click', clearChat);
    $('#newChatBtn').on('click', newChat);
    $('#themeToggle').on('click', toggleTheme);
    $('#mobileMenuToggle').on('click', toggleMobileMenu);
    
    // Add voice chat button to the UI
    $('.button-row').append(
        $('<button>').attr('id', 'voiceChatBtn')
            .addClass('btn btn-sm btn-outline-info')
            .html('<i class="fas fa-comment-dots"></i> Voice Chat')
            .on('click', toggleVoiceChat)
    );
    
    // Functions
    function sendMessage() {
        const userInput = $('#userInput').val().trim();
        if (userInput === '') return;
        
        // Add user message to chat
        displayMessage(userInput, 'user');
        $('#userInput').val('');
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send request to backend
        $.ajax({
            url: '/chat',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ message: userInput }),
            success: function(data) {
                // Hide typing indicator
                hideTypingIndicator();
                
                // Display assistant response
                if (data.response) {
                    displayMessage(data.response, 'assistant', data.timestamp);
                    scrollToBottom();
                    
                    // Refresh conversation list
                    loadConversations();
                }
            },
            error: function(xhr, status, error) {
                hideTypingIndicator();
                const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : 'An error occurred while processing your request.';
                displayError(errorMsg);
            }
        });
    }
    
    function displayMessage(text, sender, timestamp = null) {
        const time = timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const messageDiv = $('<div>').addClass('message').addClass(sender + '-message');
        
        // Process markdown if it's an assistant message
        if (sender === 'assistant') {
            const formattedText = marked.parse(text);
            messageDiv.html(formattedText);
        } else {
            messageDiv.text(text);
        }
        
        // Add timestamp
        const timeSpan = $('<span>').addClass('message-timestamp').text(time);
        messageDiv.append(timeSpan);
        
        // Add action buttons for assistant messages
        if (sender === 'assistant') {
            const actionsDiv = $('<div>').addClass('message-actions');
            
            const speakBtn = $('<button>').addClass('action-btn').attr('title', 'Speak')
                                        .html('<i class="fas fa-volume-up"></i>')
                                        .on('click', function() {
                                            speakText(text);
                                        });
                                        
            const translateBtn = $('<button>').addClass('action-btn').attr('title', 'Translate')
                                            .html('<i class="fas fa-language"></i>')
                                            .on('click', function() {
                                                translateText(text);
                                            });
                                            
            const copyBtn = $('<button>').addClass('action-btn').attr('title', 'Copy to clipboard')
                                        .html('<i class="fas fa-copy"></i>')
                                        .on('click', function() {
                                            navigator.clipboard.writeText(text).then(function() {
                                                showToast('Copied to clipboard!');
                                            });
                                        });
                                        
            actionsDiv.append(speakBtn, translateBtn, copyBtn);
            messageDiv.append(actionsDiv);
        }
        
        $('#chatMessages').append(messageDiv);
        scrollToBottom();
    }
    
    function displayError(message) {
        const errorDiv = $('<div>').addClass('error-message').text(message);
        $('#chatMessages').append(errorDiv);
        scrollToBottom();
    }
    
    function scrollToBottom() {
        const chatContainer = document.getElementById('chatMessages');
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    
    function toggleVoiceRecording() {
        if (isRecording) {
            // Stop recording
            $('#voiceInputBtn').removeClass('recording');
            $('#voiceInputBtn').html('<i class="fas fa-microphone"></i>');
            isRecording = false;
            hideLoading();
            
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
            }
        } else {
            // Start recording
            $('#voiceInputBtn').addClass('recording');
            $('#voiceInputBtn').html('<i class="fas fa-stop"></i>');
            isRecording = true;
            showLoading('Listening...');
            
            // Check if we should use the new audio recording method
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                startAudioRecording();
            } else {
                // Fall back to the old method
                legacyVoiceRecording();
            }
        }
    }
    
    function startAudioRecording() {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                audioChunks = [];
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.addEventListener('dataavailable', event => {
                    audioChunks.push(event.data);
                });
                
                mediaRecorder.addEventListener('stop', () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    sendAudioToServer(audioBlob);
                    
                    // Stop all tracks to release the microphone
                    stream.getTracks().forEach(track => track.stop());
                });
                
                mediaRecorder.start();
            })
            .catch(error => {
                console.error('Error accessing microphone:', error);
                showToast('Error accessing microphone. Please check permissions.', 3000);
                resetRecordingState();
                legacyVoiceRecording(); // Try the legacy method as fallback
            });
    }
    
    function sendAudioToServer(audioBlob) {
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
            const base64Audio = reader.result;
            
            $.ajax({
                url: '/voice_chat',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    audio: base64Audio,
                    conversation_id: getCurrentConversationId()
                }),
                success: function(data) {
                    resetRecordingState();
                    
                    if (data.transcription) {
                        // Display what was recognized
                        displayMessage(data.transcription, 'user');
                        
                        // Display the response
                        if (data.response) {
                            displayMessage(data.response, 'assistant');
                            
                            // If voice chat is active, automatically speak the response
                            if (isVoiceChatActive) {
                                speakText(data.response);
                            }
                        }
                    } else if (data.error) {
                        displayError(data.error);
                    }
                },
                error: function(xhr, status, error) {
                    resetRecordingState();
                    const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : 'An error occurred with voice recognition.';
                    displayError(errorMsg);
                }
            });
        };
    }
    
    function legacyVoiceRecording() {
        // Make API call to backend using the old method
        $.ajax({
            url: '/voice',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({}),
            success: function(data) {
                resetRecordingState();
                
                if (data.message) {
                    $('#userInput').val(data.message);
                    // Show what was recognized
                    showToast(`Recognized: "${data.message}" (using ${data.engine})`, 3000);
                    // Send the message
                    sendMessage();
                } else if (data.error) {
                    displayError(data.error);
                }
            },
            error: function(xhr, status, error) {
                resetRecordingState();
                const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : 'An error occurred with voice recognition.';
                displayError(errorMsg);
            }
        });
    }
    
    function resetRecordingState() {
        // Reset recording state
        $('#voiceInputBtn').removeClass('recording');
        $('#voiceInputBtn').html('<i class="fas fa-microphone"></i>');
        isRecording = false;
        hideLoading();
    }
    
    function speakLastResponse() {
        const lastResponse = $('#chatMessages .assistant-message').last().text();
        if (lastResponse) {
            speakText(lastResponse);
        }
    }
    
    function speakText(text) {
        showLoading('Speaking...');
        const voiceType = $('#voiceSelect').val();
        const lang = $('#languageSelect').val();
        
        $.ajax({
            url: '/speak',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ 
                text: text, 
                voice: voiceType,
                lang: lang 
            }),
            success: function(data) {
                hideLoading();
                if (data.status === "spoken") {
                    showToast(`Speaking using ${data.engine} engine`);
                } else if (data.error) {
                    displayError(data.error);
                }
            },
            error: function(xhr, status, error) {
                hideLoading();
                const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : 'An error occurred while speaking.';
                displayError(errorMsg);
            }
        });
    }
    
    function translateLastResponse() {
        const lastResponse = $('#chatMessages .assistant-message').last().text();
        if (lastResponse) {
            translateText(lastResponse);
        }
    }
    
    function translateText(text) {
        showLoading('Translating...');
        const lang = $('#languageSelect').val();
        
        $.ajax({
            url: '/translate',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ 
                text: text, 
                lang: lang 
            }),
            success: function(data) {
                hideLoading();
                
                if (data.translation) {
                    // Create a modal to show the translation
                    const modalId = 'translationModal';
                    let modal = $(`#${modalId}`);
                    
                    // Remove existing modal if any
                    if (modal.length) {
                        modal.remove();
                    }
                    
                    // Create new modal
                    modal = $('<div>').attr({
                        'id': modalId,
                        'class': 'modal fade',
                        'tabindex': '-1',
                        'role': 'dialog'
                    });
                    
                    const modalContent = `
                        <div class="modal-dialog" role="document">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">Translation (${data.language})</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="original-text mb-3">
                                        <h6>Original:</h6>
                                        <p>${data.original}</p>
                                    </div>
                                    <div class="translation-text">
                                        <h6>Translation:</h6>
                                        <p>${data.translation}</p>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                    <button type="button" class="btn btn-primary copy-translation">Copy Translation</button>
                                    <button type="button" class="btn btn-info speak-translation">Speak Translation</button>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    modal.html(modalContent);
                    $('body').append(modal);
                    
                    // Initialize the modal
                    const modalInstance = new bootstrap.Modal(document.getElementById(modalId));
                    modalInstance.show();
                    
                    // Add event listeners
                    $('.copy-translation').on('click', function() {
                        navigator.clipboard.writeText(data.translation).then(function() {
                            showToast('Translation copied to clipboard!');
                        });
                    });
                    
                    $('.speak-translation').on('click', function() {
                        speakText(data.translation, data.language);
                    });
                } else {
                    showToast('Translation failed. Please try again.');
                }
            },
            error: function(xhr, status, error) {
                hideLoading();
                const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : 'An error occurred during translation.';
                showToast('Error: ' + errorMsg, 3000);
            }
        });
    }
    
    function clearChat() {
        if (confirm('Are you sure you want to clear this chat?')) {
            $('#chatMessages').empty();
            
            $.ajax({
                url: '/clear',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({}),
                success: function(data) {
                    // Welcome message
                    const welcomeMsg = "I'm your AI Assistant. How can I help you today?";
                    displayMessage(welcomeMsg, 'assistant');
                    
                    // Refresh conversation list
                    loadConversations();
                },
                error: function(xhr, status, error) {
                    const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : 'An error occurred while clearing the chat.';
                    displayError(errorMsg);
                }
            });
        }
    }
    
    function newChat() {
        clearChat();
    }
    
    function loadLanguages() {
        $.ajax({
            url: '/available_languages',
            type: 'GET',
            success: function(data) {
                languages = data;
                const languageSelect = $('#languageSelect');
                languageSelect.empty();
                
                $.each(data, function(code, name) {
                    languageSelect.append($('<option>').val(code).text(name));
                });
            },
            error: function(xhr, status, error) {
                console.error('Error loading languages:', error);
            }
        });
    }
    
    function loadConversations() {
        $.ajax({
            url: '/conversations',
            type: 'GET',
            success: function(data) {
                const conversationList = $('#conversationList');
                conversationList.empty();
                
                if (data.length === 0) {
                    conversationList.append($('<div>').addClass('text-center text-muted').text('No saved conversations'));
                    return;
                }
                
                $.each(data, function(index, conversation) {
                    const item = $('<div>').addClass('conversation-item');
                    
                    const titleSpan = $('<div>').addClass('title').text(conversation.title);
                    const timestampSpan = $('<div>').addClass('timestamp').text(conversation.timestamp);
                    const deleteBtn = $('<button>').addClass('delete-btn').html('<i class="fas fa-trash"></i>');
                    
                    item.append(titleSpan, timestampSpan, deleteBtn);
                    
                    // Load conversation on click
                    item.on('click', function(e) {
                        if (!$(e.target).closest('.delete-btn').length) {
                            loadConversation(conversation.id);
                        }
                    });
                    
                    // Delete conversation
                    deleteBtn.on('click', function(e) {
                        e.stopPropagation();
                        deleteConversation(conversation.id);
                    });
                    
                    conversationList.append(item);
                });
            },
            error: function(xhr, status, error) {
                console.error('Error loading conversations:', error);
            }
        });
    }
    
    function loadConversation(id) {
        showLoading('Loading conversation...');
        
        $.ajax({
            url: '/load_conversation',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ id: id }),
            success: function(data) {
                hideLoading();
                
                // Clear current chat
                $('#chatMessages').empty();
                
                // Display messages
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(function(msg) {
                        if (msg.role !== 'system') {
                            displayMessage(msg.content, msg.role);
                        }
                    });
                    
                    scrollToBottom();
                    
                    // Close mobile sidebar if open
                    if ($('.sidebar').hasClass('open')) {
                        toggleMobileMenu();
                    }
                }
            },
            error: function(xhr, status, error) {
                hideLoading();
                const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : 'An error occurred while loading the conversation.';
                displayError(errorMsg);
            }
        });
    }
    
    function deleteConversation(id) {
        if (confirm('Are you sure you want to delete this conversation?')) {
            $.ajax({
                url: '/delete_conversation',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ id: id }),
                success: function(data) {
                    loadConversations();
                    showToast('Conversation deleted');
                },
                error: function(xhr, status, error) {
                    const errorMsg = xhr.responseJSON ? xhr.responseJSON.error : 'An error occurred while deleting the conversation.';
                    displayError(errorMsg);
                }
            });
        }
    }
    
    function initializeTheme() {
        // Set theme from localStorage
        setTheme(currentTheme);
        
        // Update toggle position
        $('#themeToggle').attr('data-theme', currentTheme);
    }
    
    function toggleTheme() {
        currentTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(currentTheme);
        
        // Update toggle position
        $('#themeToggle').attr('data-theme', currentTheme);
        
        // Save to localStorage
        localStorage.setItem('theme', currentTheme);
        
        // Save to server
        $.ajax({
            url: '/settings',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ theme: currentTheme }),
            error: function(xhr, status, error) {
                console.error('Error saving theme setting:', error);
            }
        });
    }
    
    function setTheme(theme) {
        $('html').attr('data-theme', theme);
    }
    
    function toggleMobileMenu() {
        $('.sidebar').toggleClass('open');
    }
    
    function showTypingIndicator() {
        const typingDiv = $('<div>').addClass('typing-indicator');
        for (let i = 0; i < 3; i++) {
            typingDiv.append($('<span>'));
        }
        $('#chatMessages').append(typingDiv);
        scrollToBottom();
    }
    
    function hideTypingIndicator() {
        $('.typing-indicator').remove();
    }
    
    function showLoading(message = 'Processing...') {
        $('#loadingText').text(message);
        loadingModal.show();
    }
    
    function hideLoading() {
        loadingModal.hide();
    }
    
    function showToast(message, duration = 2000) {
        // Create toast element if it doesn't exist
        if ($('#toast-container').length === 0) {
            $('body').append(`
                <div id="toast-container" style="position: fixed; bottom: 20px; right: 20px; z-index: 1050;"></div>
            `);
        }
        
        // Create and show the toast
        const toast = $(`
            <div class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-bs-delay="${duration}">
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `);
        
        $('#toast-container').append(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove after it's hidden
        toast.on('hidden.bs.toast', function() {
            toast.remove();
        });
    }
    
    function getCurrentConversationId() {
        // Get the current conversation ID from the URL or use a default
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('id') || 'default';
    }
    
    // Voice chat functionality
    function toggleVoiceChat() {
        isVoiceChatActive = !isVoiceChatActive;
        
        if (isVoiceChatActive) {
            $('#voiceChatBtn').addClass('active').html('<i class="fas fa-comment-dots"></i> Voice Chat (ON)');
            showToast('Voice chat mode activated. Click the microphone to start a voice conversation.', 3000);
        } else {
            $('#voiceChatBtn').removeClass('active').html('<i class="fas fa-comment-dots"></i> Voice Chat');
            showToast('Voice chat mode deactivated.', 2000);
        }
    }
    
    // Display initial welcome message
    const welcomeMsg = "I'm your AI Assistant. How can I help you today?";
    displayMessage(welcomeMsg, 'assistant');
});
