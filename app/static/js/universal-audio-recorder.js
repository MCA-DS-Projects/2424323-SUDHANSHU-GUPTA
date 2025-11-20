/**
 * ProSpeak AI - Universal Audio Recorder
 * A reusable audio recording component for all pages
 */

class UniversalAudioRecorder {
    constructor(options = {}) {
        this.options = {
            recordButtonId: 'recordBtn',
            stopButtonId: 'stopBtn',
            playbackButtonId: 'playbackBtn',
            statusElementId: 'recordingStatus',
            timerElementId: 'recordingTimer',
            waveformCanvasId: 'waveformCanvas',
            transcriptionElementId: 'transcriptionText',
            sessionType: 'general',
            ...options
        };
        
        this.isRecording = false;
        this.isPaused = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.recordedAudioUrl = null;
        this.startTime = null;
        this.timer = null;
        this.audioEngine = null;
        this.currentSession = null;
        
        this.init();
    }
    
    async init() {
        try {
            console.log('Initializing Universal Audio Recorder...');
            
            // Check if AudioEngine is available
            if (window.AudioEngine) {
                this.audioEngine = new AudioEngine();
                this.setupAudioEngineHandlers();
            }
            
            // Setup UI event listeners
            this.setupEventListeners();
            
            // Initialize waveform if canvas exists
            this.initializeWaveform();
            
            console.log('Universal Audio Recorder initialized successfully');
        } catch (error) {
            console.error('Failed to initialize Universal Audio Recorder:', error);
        }
    }
    
    setupEventListeners() {
        const recordBtn = document.getElementById(this.options.recordButtonId);
        const stopBtn = document.getElementById(this.options.stopButtonId);
        const playbackBtn = document.getElementById(this.options.playbackButtonId);
        
        if (recordBtn) {
            recordBtn.addEventListener('click', () => this.toggleRecording());
        }
        
        if (stopBtn) {
            stopBtn.addEventListener('click', () => this.stopRecording());
        }
        
        if (playbackBtn) {
            playbackBtn.addEventListener('click', () => this.playRecording());
        }
    }
    
    setupAudioEngineHandlers() {
        if (!this.audioEngine) return;
        
        this.audioEngine.onRecognitionStart = () => {
            this.updateStatus('listening', 'Listening...');
            this.startTimer();
            this.animateWaveform();
            this.updateRecordButton(true);
        };
        
        this.audioEngine.onRecognitionEnd = () => {
            this.updateStatus('processing', 'Processing...');
            this.stopTimer();
            this.stopWaveformAnimation();
            this.updateRecordButton(false);
        };
        
        this.audioEngine.onTranscriptUpdate = (transcript, isFinal) => {
            this.updateTranscription(transcript, isFinal);
        };
        
        this.audioEngine.onRecognitionError = (error) => {
            console.error('Recognition error:', error);
            this.updateStatus('error', 'Error: ' + error);
            this.resetUI();
        };
        
        this.audioEngine.onAudioProcessed = (audioBlob, audioUrl) => {
            this.recordedAudioUrl = audioUrl;
            this.enablePlayback();
            this.onRecordingComplete(audioBlob, audioUrl);
        };
    }
    
    async toggleRecording() {
        if (!this.isRecording) {
            await this.startRecording();
        } else {
            this.stopRecording();
        }
    }
    
    async startRecording() {
        try {
            console.log('Starting recording...');
            
            // Check microphone permissions
            await this.checkMicrophonePermissions();
            
            if (this.audioEngine) {
                // Use AudioEngine for advanced recording
                this.currentSession = await this.audioEngine.startListening({
                    sessionType: this.options.sessionType,
                    userId: window.currentUser ? window.currentUser.id : 'anonymous'
                });
            } else {
                // Fallback to basic MediaRecorder
                await this.startBasicRecording();
            }
            
            this.isRecording = true;
            this.updateRecordingUI();
            
            console.log('Recording started successfully');
        } catch (error) {
            console.error('Failed to start recording:', error);
            this.showError('Failed to start recording: ' + error.message);
        }
    }
    
    async startBasicRecording() {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            }
        });
        
        this.mediaRecorder = new MediaRecorder(stream);
        this.audioChunks = [];
        
        this.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                this.audioChunks.push(event.data);
            }
        };
        
        this.mediaRecorder.onstop = () => {
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
            this.recordedAudioUrl = URL.createObjectURL(audioBlob);
            this.enablePlayback();
            this.onRecordingComplete(audioBlob, this.recordedAudioUrl);
        };
        
        this.mediaRecorder.start();
        this.startTimer();
        this.animateWaveform();
    }
    
    stopRecording() {
        console.log('Stopping recording...');
        
        if (this.audioEngine && this.audioEngine.isRecording) {
            this.currentSession = this.audioEngine.stopListening();
        } else if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        
        this.isRecording = false;
        this.stopTimer();
        this.stopWaveformAnimation();
        this.resetUI();
        
        console.log('Recording stopped');
    }
    
    playRecording() {
        if (this.recordedAudioUrl) {
            const audio = new Audio(this.recordedAudioUrl);
            audio.play();
        }
    }
    
    async checkMicrophonePermissions() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop());
            return true;
        } catch (error) {
            throw new Error('Microphone access required. Please enable microphone permissions.');
        }
    }
    
    updateRecordingUI() {
        const recordBtn = document.getElementById(this.options.recordButtonId);
        const stopBtn = document.getElementById(this.options.stopButtonId);
        const playbackBtn = document.getElementById(this.options.playbackButtonId);
        
        if (recordBtn) {
            recordBtn.disabled = true;
            recordBtn.classList.add('recording-active');
        }
        
        if (stopBtn) {
            stopBtn.disabled = false;
        }
        
        if (playbackBtn) {
            playbackBtn.disabled = true;
        }
        
        this.updateStatus('recording', 'Recording...');
    }
    
    resetUI() {
        const recordBtn = document.getElementById(this.options.recordButtonId);
        const stopBtn = document.getElementById(this.options.stopButtonId);
        
        if (recordBtn) {
            recordBtn.disabled = false;
            recordBtn.classList.remove('recording-active');
        }
        
        if (stopBtn) {
            stopBtn.disabled = true;
        }
        
        this.updateStatus('ready', 'Ready to record');
    }
    
    updateRecordButton(isRecording) {
        const recordBtn = document.getElementById(this.options.recordButtonId);
        if (recordBtn) {
            if (isRecording) {
                recordBtn.classList.add('recording-active');
            } else {
                recordBtn.classList.remove('recording-active');
            }
        }
    }
    
    enablePlayback() {
        const playbackBtn = document.getElementById(this.options.playbackButtonId);
        if (playbackBtn) {
            playbackBtn.disabled = false;
        }
    }
    
    updateStatus(status, message) {
        const statusElement = document.getElementById(this.options.statusElementId);
        if (statusElement) {
            const textElement = statusElement.querySelector('span') || statusElement;
            const iconElement = statusElement.querySelector('i');
            
            if (textElement) {
                textElement.textContent = message;
            }
            
            if (iconElement) {
                switch (status) {
                    case 'recording':
                    case 'listening':
                        iconElement.className = 'fas fa-microphone mr-2 text-accent';
                        break;
                    case 'processing':
                        iconElement.className = 'fas fa-cog fa-spin mr-2 text-primary';
                        break;
                    case 'error':
                        iconElement.className = 'fas fa-exclamation-triangle mr-2 text-red-500';
                        break;
                    default:
                        iconElement.className = 'fas fa-microphone-slash mr-2';
                }
            }
        }
    }
    
    updateTranscription(transcript, isFinal) {
        const transcriptionElement = document.getElementById(this.options.transcriptionElementId);
        if (transcriptionElement) {
            if (isFinal) {
                transcriptionElement.textContent = transcript;
            } else {
                transcriptionElement.innerHTML = `${transcript} <span class="text-gray-400 italic">...</span>`;
            }
        }
    }
    
    startTimer() {
        this.startTime = Date.now();
        const timerElement = document.getElementById(this.options.timerElementId);
        
        if (timerElement) {
            timerElement.classList.remove('hidden');
            
            this.timer = setInterval(() => {
                const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }, 1000);
        }
    }
    
    stopTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        
        const timerElement = document.getElementById(this.options.timerElementId);
        if (timerElement) {
            timerElement.classList.add('hidden');
        }
    }
    
    initializeWaveform() {
        const canvas = document.getElementById(this.options.waveformCanvasId);
        if (canvas) {
            this.waveformCanvas = canvas;
            this.waveformCtx = canvas.getContext('2d');
            this.drawWaveform([]);
        }
    }
    
    animateWaveform() {
        if (!this.waveformCtx) return;
        
        const animate = () => {
            const data = Array.from({length: 20}, () => Math.random() * 0.8 + 0.2);
            this.drawWaveform(data);
            
            if (this.isRecording) {
                this.animationId = requestAnimationFrame(animate);
            }
        };
        
        animate();
    }
    
    stopWaveformAnimation() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        this.drawWaveform([]);
    }
    
    drawWaveform(data) {
        if (!this.waveformCtx) return;
        
        const canvas = this.waveformCanvas;
        const ctx = this.waveformCtx;
        
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        if (data.length === 0) {
            ctx.strokeStyle = '#e5e7eb';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(0, canvas.height / 2);
            ctx.lineTo(canvas.width, canvas.height / 2);
            ctx.stroke();
            return;
        }
        
        const barWidth = canvas.width / data.length;
        
        data.forEach((value, index) => {
            const barHeight = value * canvas.height * 0.8;
            const x = index * barWidth;
            const y = (canvas.height - barHeight) / 2;
            
            const intensity = Math.floor(255 * (1 - value));
            ctx.fillStyle = `rgb(${intensity}, 100, 255)`;
            
            ctx.fillRect(x, y, barWidth - 2, barHeight);
        });
    }
    
    showError(message) {
        this.updateStatus('error', message);
        
        if (window.notifications) {
            window.notifications.error(message);
        }
        
        console.error('Audio Recorder Error:', message);
    }
    
    // Override this method in specific implementations
    onRecordingComplete(audioBlob, audioUrl) {
        console.log('Recording completed:', { audioBlob, audioUrl });
        
        // Save session if API is available
        this.saveSession(audioBlob);
    }
    
    async saveSession(audioBlob) {
        try {
            if (window.api && window.api.token) {
                const sessionData = {
                    session_type: this.options.sessionType,
                    duration: this.startTime ? Date.now() - this.startTime : 0,
                    transcript: this.currentSession?.transcript || '',
                    scores: this.currentSession?.scores || {}
                };
                
                await window.api.request('/audio/save-session', {
                    method: 'POST',
                    body: JSON.stringify(sessionData)
                });
                
                // Increment session count
                if (window.incrementSessionCount) {
                    window.incrementSessionCount();
                }
                
                // Trigger stats refresh
                if (window.loadAudioPracticeStats) {
                    setTimeout(() => window.loadAudioPracticeStats(), 500);
                }
                
                // Trigger dashboard refresh
                if (window.loadDashboardData) {
                    setTimeout(() => window.loadDashboardData(), 500);
                }
                
                console.log('Session saved and counts updated');
            }
        } catch (error) {
            console.error('Failed to save session:', error);
        }
    }
}

// Export for global use
window.UniversalAudioRecorder = UniversalAudioRecorder;