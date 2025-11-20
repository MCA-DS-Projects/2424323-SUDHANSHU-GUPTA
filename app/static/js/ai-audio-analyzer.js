/**
 * AI Audio Analyzer - Handles audio recording, analysis, and feedback
 */
class AIAudioAnalyzer {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isRecording = false;
        this.recordingStartTime = null;
        this.currentAnalysisType = 'pronunciation';
        
        // Initialize audio context
        this.audioContext = null;
        this.analyser = null;
        this.microphone = null;
        
        // Bind methods
        this.startRecording = this.startRecording.bind(this);
        this.stopRecording = this.stopRecording.bind(this);
        this.analyzeAudio = this.analyzeAudio.bind(this);
    }
    
    /**
     * Initialize the audio analyzer
     */
    async initialize() {
        try {
            // Request microphone permission
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 44100
                } 
            });
            
            // Initialize audio context for visualization
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.analyser = this.audioContext.createAnalyser();
            this.microphone = this.audioContext.createMediaStreamSource(stream);
            this.microphone.connect(this.analyser);
            
            // Configure analyzer
            this.analyser.fftSize = 256;
            
            // Initialize media recorder
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };
            
            console.log('AI Audio Analyzer initialized successfully');
            return true;
            
        } catch (error) {
            console.error('Failed to initialize audio analyzer:', error);
            throw new Error('Microphone access denied or not available');
        }
    }
    
    /**
     * Start recording audio
     */
    async startRecording(analysisType = 'pronunciation') {
        try {
            if (!this.mediaRecorder) {
                await this.initialize();
            }
            
            if (this.isRecording) {
                console.warn('Already recording');
                return false;
            }
            
            this.currentAnalysisType = analysisType;
            this.audioChunks = [];
            this.recordingStartTime = Date.now();
            
            this.mediaRecorder.start(100); // Collect data every 100ms
            this.isRecording = true;
            
            // Start visualization if available
            this.startVisualization();
            
            console.log(`Started recording for ${analysisType} analysis`);
            return true;
            
        } catch (error) {
            console.error('Failed to start recording:', error);
            throw error;
        }
    }
    
    /**
     * Stop recording audio
     */
    stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) {
            console.warn('Not currently recording');
            return false;
        }
        
        this.mediaRecorder.stop();
        this.isRecording = false;
        
        // Stop visualization
        this.stopVisualization();
        
        console.log('Stopped recording');
        return true;
    }
    
    /**
     * Process the recorded audio
     */
    async processRecording() {
        try {
            if (this.audioChunks.length === 0) {
                throw new Error('No audio data recorded');
            }
            
            // Create blob from chunks
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            const duration = (Date.now() - this.recordingStartTime) / 1000;
            
            // Convert to base64 for API
            const audioBase64 = await this.blobToBase64(audioBlob);
            
            // Analyze with AI
            const analysis = await this.analyzeAudio(audioBase64, duration);
            
            return analysis;
            
        } catch (error) {
            console.error('Failed to process recording:', error);
            throw error;
        }
    }
    
    /**
     * Analyze audio using AI API
     */
    async analyzeAudio(audioData, duration) {
        try {
            const response = await api.request('/audio/analyze-ai', {
                method: 'POST',
                body: JSON.stringify({
                    audio_data: audioData,
                    analysis_type: this.currentAnalysisType,
                    duration: duration
                })
            });
            
            if (!response.success) {
                throw new Error(response.error || 'Analysis failed');
            }
            
            return {
                success: true,
                sessionId: response.session_id,
                transcript: response.transcript,
                analysis: response.analysis,
                audioFeedback: response.audio_feedback,
                duration: duration
            };
            
        } catch (error) {
            console.error('AI analysis failed:', error);
            return {
                success: false,
                error: error.message || 'Analysis failed'
            };
        }
    }
    
    /**
     * Get detailed feedback for a session
     */
    async getFeedback(sessionId) {
        try {
            const response = await api.request(`/audio/get-feedback/${sessionId}`);
            return response;
        } catch (error) {
            console.error('Failed to get feedback:', error);
            throw error;
        }
    }
    
    /**
     * Get AI-powered practice exercises
     */
    async getPracticeExercises() {
        try {
            const response = await api.request('/audio/practice-exercises');
            return response;
        } catch (error) {
            console.error('Failed to get exercises:', error);
            return { exercises: [], user_level: 'beginner', total_sessions: 0 };
        }
    }
    
    /**
     * Convert blob to base64
     */
    blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }
    
    /**
     * Start audio visualization
     */
    startVisualization() {
        if (!this.analyser) return;
        
        const canvas = document.getElementById('audioVisualization');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        const draw = () => {
            if (!this.isRecording) return;
            
            requestAnimationFrame(draw);
            
            this.analyser.getByteFrequencyData(dataArray);
            
            ctx.fillStyle = 'rgb(240, 240, 240)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            const barWidth = (canvas.width / bufferLength) * 2.5;
            let barHeight;
            let x = 0;
            
            for (let i = 0; i < bufferLength; i++) {
                barHeight = (dataArray[i] / 255) * canvas.height;
                
                const r = barHeight + 25 * (i / bufferLength);
                const g = 250 * (i / bufferLength);
                const b = 50;
                
                ctx.fillStyle = `rgb(${r},${g},${b})`;
                ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
                
                x += barWidth + 1;
            }
        };
        
        draw();
    }
    
    /**
     * Stop audio visualization
     */
    stopVisualization() {
        const canvas = document.getElementById('audioVisualization');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'rgb(240, 240, 240)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }
    
    /**
     * Play audio feedback
     */
    playAudioFeedback(audioFeedback) {
        if (!audioFeedback || !audioFeedback.audio_url) {
            console.warn('No audio feedback available');
            return;
        }
        
        const audio = new Audio(audioFeedback.audio_url);
        audio.play().catch(error => {
            console.error('Failed to play audio feedback:', error);
        });
    }
    
    /**
     * Get recording status
     */
    getStatus() {
        return {
            isRecording: this.isRecording,
            isInitialized: !!this.mediaRecorder,
            analysisType: this.currentAnalysisType
        };
    }
    
    /**
     * Set analysis type
     */
    setAnalysisType(type) {
        const validTypes = ['pronunciation', 'fluency', 'interview'];
        if (validTypes.includes(type)) {
            this.currentAnalysisType = type;
            return true;
        }
        return false;
    }
    
    /**
     * Clean up resources
     */
    cleanup() {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
        }
        
        if (this.audioContext) {
            this.audioContext.close();
        }
        
        this.isRecording = false;
        this.audioChunks = [];
    }
}

// Create global instance
window.aiAudioAnalyzer = new AIAudioAnalyzer();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AIAudioAnalyzer;
}