document.addEventListener('DOMContentLoaded', function() {
    let mediaRecorder;
    let audioChunks = [];
    let recordingInterval;
    let recordingSeconds = 0;
    let isRecording = false;
    let isSending = false; // Flag to prevent multiple simultaneous uploads

    const audioRecordBtn = document.getElementById('audio-record-btn');
    const stopRecordingBtn = document.getElementById('stop-recording-btn');
    const audioControls = document.getElementById('audio-controls');
    const recordingTime = document.getElementById('recording-time');
    
    // Add custom audio styles to the document head
    const styleSheet = document.createElement('style');
    styleSheet.textContent = `
        /* Custom audio player styling */
        audio {
            height: 40px;
            border-radius: 20px;
            background-color: #f3f4f6;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }
        
        /* Webkit (Chrome, Safari) specific styles */
        audio::-webkit-media-controls-panel {
            background-color: #f3f4f6;
            border-radius: 20px;
        }
        
        audio::-webkit-media-controls-play-button {
            background-color: #6366f1;
            border-radius: 50%;
            margin-right: 5px;
        }
        
        audio::-webkit-media-controls-current-time-display,
        audio::-webkit-media-controls-time-remaining-display {
            color: #4b5563;
            font-size: 12px;
        }
        
        /* Loading indicator for audio upload */
        .audio-sending {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(99, 102, 241, 0.3);
            border-radius: 50%;
            border-top-color: #6366f1;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    `;
    document.head.appendChild(styleSheet);

    // Initialize recording
    audioRecordBtn.addEventListener('click', function() {
        if (isRecording || isSending) return; // Prevent starting new recording if already recording or sending

        // Request user permission for audio
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                isRecording = true;
                audioRecordBtn.disabled = true;
                audioRecordBtn.classList.add('text-gray-300');
                
                // Show recording controls
                audioControls.classList.remove('hidden');
                audioControls.classList.add('flex');

                // Create media recorder with better audio quality
                const options = {
                    mimeType: 'audio/webm;codecs=opus',
                    audioBitsPerSecond: 128000
                };
                
                try {
                    mediaRecorder = new MediaRecorder(stream, options);
                } catch (e) {
                    // Fallback if preferred options not supported
                    mediaRecorder = new MediaRecorder(stream);
                }

                // Start recording
                mediaRecorder.start();

                // Start recording timer
                recordingSeconds = 0;
                updateRecordingTime();
                recordingInterval = setInterval(updateRecordingTime, 1000);

                // Event listener for data available
                mediaRecorder.addEventListener('dataavailable', event => {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                });

                // Event listener for recording stop
                mediaRecorder.addEventListener('stop', () => {
                    // Stop all tracks in the stream
                    stream.getTracks().forEach(track => track.stop());

                    // Create audio blob from the chunks
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    
                    if (audioBlob.size > 0) {
                        // Show sending indicator
                        isSending = true;
                        const sendingIndicator = document.createElement('div');
                        sendingIndicator.className = 'flex items-center justify-center mt-2';
                        sendingIndicator.innerHTML = '<div class="audio-sending mr-2"></div><span class="text-sm text-gray-600">Sending audio...</span>';
                        audioControls.appendChild(sendingIndicator);
                        
                        // Upload audio file
                        uploadAudioFile(audioBlob).finally(() => {
                            // Reset sending state
                            isSending = false;
                            audioRecordBtn.disabled = false;
                            audioRecordBtn.classList.remove('text-gray-300');
                            
                            // Remove sending indicator
                            if (sendingIndicator.parentNode) {
                                sendingIndicator.parentNode.removeChild(sendingIndicator);
                            }
                            
                            // Hide recording controls
                            audioControls.classList.add('hidden');
                            audioControls.classList.remove('flex');
                        });
                    }

                    // Reset audio chunks and recording flag
                    audioChunks = [];
                    isRecording = false;
                });
            })
            .catch(error => {
                console.error('Error accessing microphone:', error);
                alert('Could not access microphone. Please check permissions.');
                isRecording = false;
                audioRecordBtn.disabled = false;
                audioRecordBtn.classList.remove('text-gray-300');
            });
    });

    // Stop recording
    stopRecordingBtn.addEventListener('click', function() {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop(); // Stop the media recorder
            clearInterval(recordingInterval); // Stop the timer
        }
    });

    // Update recording time display
    function updateRecordingTime() {
        recordingSeconds++;
        const minutes = Math.floor(recordingSeconds / 60);
        const seconds = recordingSeconds % 60;
        recordingTime.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        
        // Automatically stop recording after 5 minutes
        if (recordingSeconds >= 300) {
            stopRecordingBtn.click();
        }
    }

    // Upload audio file
    function uploadAudioFile(blob) {
        const formData = new FormData();
        formData.append('file', blob, `audio_${Date.now()}.webm`);
        
        return fetch(`/upload_file/${roomId}/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Server error: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            // Send message through WebSocket
            chatSocket.send(JSON.stringify({
                'message': 'Audio message',
                'type': 'audio',
                'file_url': data.file_url
            }));
            return data;
        })
        .catch(error => {
            console.error('Error uploading audio:', error);
            alert('Error uploading audio. Please try again.');
            throw error;
        });
    }
    
    // Get CSRF token from cookies
    function getCsrfToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue || '';
    }
    
    // Handle WebSocket reconnection if needed
    window.addEventListener('online', function() {
        if (chatSocket.readyState !== WebSocket.OPEN && !isRecording) {
            window.location.reload(); // Reload the page to reestablish WebSocket connection
        }
    });

    // Modify the existing addMessage function to enhance audio styling (this will run once after the original function exists)
    if (typeof window.addMessage === 'function') {
        const originalAddMessage = window.addMessage;
        window.addMessage = function(message, messageType, username, userId, timestamp, fileUrl = null) {
            originalAddMessage(message, messageType, username, userId, timestamp, fileUrl);
            
            // Add custom styling to the most recently added audio elements
            if (messageType === 'audio') {
                const audioElements = messageContainer.querySelectorAll('audio');
                if (audioElements.length > 0) {
                    const latestAudio = audioElements[audioElements.length - 1];
                    latestAudio.classList.add('custom-audio-player');
                }
            }
        };
    }
});