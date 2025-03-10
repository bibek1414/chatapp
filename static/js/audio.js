document.addEventListener('DOMContentLoaded', function() {
    let mediaRecorder;
    let audioChunks = [];
    let recordingInterval;
    let recordingSeconds = 0;
    
    const audioRecordBtn = document.getElementById('audio-record-btn');
    const stopRecordingBtn = document.getElementById('stop-recording-btn');
    const audioControls = document.getElementById('audio-controls');
    const recordingTime = document.getElementById('recording-time');
    
    // Initialize recording
    audioRecordBtn.addEventListener('click', function() {
        // Request user permission for audio
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                // Show recording controls
                audioControls.classList.remove('d-none');
                
                // Create media recorder
                mediaRecorder = new MediaRecorder(stream);
                
                // Start recording
                mediaRecorder.start();
                
                // Start recording timer
                recordingSeconds = 0;
                updateRecordingTime();
                recordingInterval = setInterval(updateRecordingTime, 1000);
                
                // Event listener for data available
                mediaRecorder.addEventListener('dataavailable', event => {
                    audioChunks.push(event.data);
                });
                
                // Event listener for recording stop
                mediaRecorder.addEventListener('stop', () => {
                    // Stop all tracks in the stream
                    stream.getTracks().forEach(track => track.stop());
                    
                    // Create audio blob
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    
                    // Upload audio file
                    uploadAudioFile(audioBlob);
                    
                    // Reset audio chunks
                    audioChunks = [];
                });
            })
            .catch(error => {
                console.error('Error accessing microphone:', error);
                alert('Could not access microphone. Please check permissions.');
            });
    });
    
    // Stop recording
    stopRecordingBtn.addEventListener('click', function() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            clearInterval(recordingInterval);
            audioControls.classList.add('d-none');
        }
    });
    
    // Update recording time display
    function updateRecordingTime() {
        recordingSeconds++;
        const minutes = Math.floor(recordingSeconds / 60);
        const seconds = recordingSeconds % 60;
        recordingTime.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    
    // Upload audio file
    function uploadAudioFile(blob) {
        const formData = new FormData();
        formData.append('file', blob, 'audio.webm');
        
        fetch(`/upload_file/${roomId}/`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Send message through WebSocket
            chatSocket.send(JSON.stringify({
                'message': 'Audio message',
                'type': 'audio',
                'file_url': data.file_url
            }));
        })
        .catch(error => {
            console.error('Error uploading audio:', error);
            alert('Error uploading audio. Please try again.');
        });
    }
});