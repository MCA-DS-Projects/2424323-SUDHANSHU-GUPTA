/**
 * ProSpeak AI - Audio Engine
 * Handles speech recognition, synthesis, and audio processing
 */

class AudioEngine {
    constructor() {
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.currentSession = null;
        
        this.initializeSpeechRecognition();
        this.initializeAudioRecording();
    }

    // Initialize Web Speech API
    initializeSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            
            this.recognition.continuous = true;
            this.recognition.interimResults = true;
            this.recognition.lang = 'en-US';
            
            this.recognition.onstart = () => {
                console.log('Speech recognition started');
                this.onRecognitionStart();
            };
            
            this.recognition.onresult = (event) => {
                this.handleSpeechResult(event);
            };
            
            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.onRecognitionError(event.error);
            };
            
            this.recognition.onend = () => {
                console.log('Speech recognition ended');
                this.onRecognitionEnd();
            };
        } else {
            console.warn('Speech recognition not supported');
        }
    }

    // Initialize audio recording
    async initializeAudioRecording() {
        try {
            // Request microphone permission
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: 44100
                } 
            });
            
            this.audioStream = stream;
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecordedAudio();
            };
            
            this.mediaRecorder.onerror = (event) => {
                console.error('MediaRecorder error:', event.error);
                this.onRecordingError(event.error);
            };
            
            console.log('Audio recording initialized successfully');
            return true;
        } catch (error) {
            console.error('Failed to initialize audio recording:', error);
            this.onPermissionError(error);
            return false;
        }
    }

    // Start speech recognition and recording
    async startListening(options = {}) {
        if (!this.recognition) {
            throw new Error('Speech recognition not available');
        }

        // Ensure audio recording is initialized
        if (!this.mediaRecorder) {
            const initialized = await this.initializeAudioRecording();
            if (!initialized) {
                throw new Error('Microphone access denied or not available');
            }
        }

        this.currentSession = {
            startTime: Date.now(),
            transcript: '',
            confidence: 0,
            words: [],
            userId: options.userId || 'anonymous',
            ...options
        };

        this.audioChunks = [];
        
        try {
            // Start speech recognition
            this.recognition.start();
            
            // Start audio recording if available
            if (this.mediaRecorder && this.mediaRecorder.state === 'inactive') {
                this.mediaRecorder.start(100); // Collect data every 100ms
            }
            
            this.isRecording = true;
            console.log('Recording started successfully');
            return this.currentSession;
        } catch (error) {
            console.error('Failed to start listening:', error);
            throw error;
        }
    }

    // Stop listening
    stopListening() {
        if (this.recognition) {
            this.recognition.stop();
        }
        
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
        }
        
        this.isRecording = false;
        return this.currentSession;
    }

    // Handle speech recognition results
    handleSpeechResult(event) {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            const transcript = result[0].transcript;
            
            if (result.isFinal) {
                finalTranscript += transcript;
                this.currentSession.confidence = result[0].confidence;
            } else {
                interimTranscript += transcript;
            }
        }
        
        if (finalTranscript) {
            this.currentSession.transcript += finalTranscript;
            this.currentSession.words = this.analyzeWords(finalTranscript);
            this.onTranscriptUpdate(finalTranscript, true);
        }
        
        if (interimTranscript) {
            this.onTranscriptUpdate(interimTranscript, false);
        }
    }

    // Analyze words for pronunciation feedback
    analyzeWords(transcript) {
        const words = transcript.toLowerCase().split(' ').filter(word => word.length > 0);
        return words.map(word => ({
            word: word,
            pronunciation: this.analyzePronunciation(word),
            difficulty: this.getWordDifficulty(word),
            suggestions: this.getPronunciationSuggestions(word)
        }));
    }

    // Analyze pronunciation (basic implementation)
    analyzePronunciation(word) {
        // This is a simplified analysis - in production, you'd use more sophisticated algorithms
        const commonMistakes = {
            'th': ['d', 't', 'f', 'v'],
            'r': ['l', 'w'],
            'l': ['r', 'w'],
            'v': ['b', 'f', 'w'],
            'w': ['v', 'r']
        };
        
        let score = 85; // Base score
        let issues = [];
        
        // Check for common pronunciation challenges
        for (const [sound, mistakes] of Object.entries(commonMistakes)) {
            if (word.includes(sound)) {
                // Simulate pronunciation analysis
                if (Math.random() < 0.3) { // 30% chance of detecting an issue
                    score -= 10;
                    issues.push(`${sound} sound needs improvement`);
                }
            }
        }
        
        return {
            score: Math.max(score, 60),
            issues: issues,
            clarity: score > 80 ? 'excellent' : score > 70 ? 'good' : 'needs improvement'
        };
    }

    // Get word difficulty level
    getWordDifficulty(word) {
        if (word.length <= 4) return 'easy';
        if (word.length <= 7) return 'medium';
        return 'hard';
    }

    // Get pronunciation suggestions
    getPronunciationSuggestions(word) {
        const suggestions = [];
        
        if (word.includes('th')) {
            suggestions.push('Place tongue between teeth for "th" sound');
        }
        if (word.includes('r')) {
            suggestions.push('Curl tongue slightly for "r" sound');
        }
        if (word.includes('l')) {
            suggestions.push('Touch tongue to roof of mouth for "l" sound');
        }
        
        return suggestions;
    }

    // Process recorded audio
    processRecordedAudio() {
        if (this.audioChunks.length === 0) return;
        
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);
        
        if (this.currentSession) {
            this.currentSession.audioBlob = audioBlob;
            this.currentSession.audioUrl = audioUrl;
            this.currentSession.duration = Date.now() - this.currentSession.startTime;
        }
        
        this.onAudioProcessed(audioBlob, audioUrl);
    }

    // Text-to-speech feedback
    speak(text, options = {}) {
        if (!this.synthesis) {
            console.warn('Speech synthesis not available');
            return;
        }
        
        // Stop any ongoing speech
        this.synthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = options.rate || 0.9;
        utterance.pitch = options.pitch || 1;
        utterance.volume = options.volume || 0.8;
        utterance.lang = options.lang || 'en-US';
        
        utterance.onstart = () => this.onSpeechStart();
        utterance.onend = () => this.onSpeechEnd();
        utterance.onerror = (event) => this.onSpeechError(event);
        
        this.synthesis.speak(utterance);
        return utterance;
    }

    // Get available voices
    getVoices() {
        return this.synthesis.getVoices().filter(voice => voice.lang.startsWith('en'));
    }

    // Generate feedback based on session
    generateFeedback(session) {
        if (!session || !session.transcript) {
            return {
                overall: 'No speech detected. Please try speaking clearly.',
                score: 0,
                suggestions: ['Ensure microphone is working', 'Speak louder and clearer']
            };
        }
        
        const words = session.words || [];
        const avgScore = words.length > 0 
            ? words.reduce((sum, word) => sum + word.pronunciation.score, 0) / words.length 
            : 0;
        
        let feedback = {
            overall: '',
            score: Math.round(avgScore),
            pronunciation: {},
            suggestions: [],
            strengths: [],
            improvements: []
        };
        
        // Overall feedback
        if (avgScore >= 85) {
            feedback.overall = 'Excellent pronunciation! Your speech is clear and well-articulated.';
            feedback.strengths.push('Clear articulation', 'Good pace', 'Natural flow');
        } else if (avgScore >= 75) {
            feedback.overall = 'Good pronunciation with room for improvement in specific areas.';
            feedback.strengths.push('Generally clear speech');
        } else {
            feedback.overall = 'Your pronunciation needs practice. Focus on the highlighted areas.';
        }
        
        // Specific pronunciation feedback
        const issues = words.flatMap(word => word.pronunciation.issues);
        const uniqueIssues = [...new Set(issues)];
        
        feedback.pronunciation = {
            issues: uniqueIssues,
            problematicWords: words.filter(word => word.pronunciation.score < 75)
        };
        
        // Suggestions
        if (uniqueIssues.length > 0) {
            feedback.suggestions.push('Practice the highlighted sounds slowly');
            feedback.suggestions.push('Record yourself and compare with native speakers');
        }
        
        if (session.confidence < 0.7) {
            feedback.suggestions.push('Speak more clearly and at a steady pace');
            feedback.improvements.push('Speech clarity');
        }
        
        return feedback;
    }

    // Dynamic scoring based on user performance
    calculateDynamicScore(session, userHistory = []) {
        const baseScore = this.calculateBaseScore(session);
        
        // Adjust based on user's historical performance
        if (userHistory.length > 0) {
            const avgHistoricalScore = userHistory.reduce((sum, s) => sum + s.score, 0) / userHistory.length;
            const improvement = baseScore - avgHistoricalScore;
            
            // Bonus for improvement
            if (improvement > 0) {
                baseScore += Math.min(improvement * 0.1, 5);
            }
        }
        
        // Adjust based on exercise difficulty
        const difficultyMultiplier = {
            'easy': 1.0,
            'medium': 0.95,
            'hard': 0.9
        };
        
        const difficulty = session.exerciseType === 'th-sounds' ? 'hard' : 
                          session.exerciseType === 'r-sounds' ? 'medium' : 'easy';
        
        return Math.round(baseScore * (difficultyMultiplier[difficulty] || 1.0));
    }
    
    calculateBaseScore(session) {
        if (!session.transcript) return 0;
        
        const words = session.words || [];
        if (words.length === 0) return 60;
        
        // Calculate pronunciation score
        const pronunciationScore = words.reduce((sum, word) => sum + word.pronunciation.score, 0) / words.length;
        
        // Calculate fluency based on speech rate and pauses
        const duration = (Date.now() - session.startTime) / 1000;
        const wordsPerMinute = (words.length / duration) * 60;
        const optimalWPM = 150;
        const fluencyScore = Math.max(60, 100 - Math.abs(wordsPerMinute - optimalWPM) * 2);
        
        // Calculate confidence penalty
        const confidenceBonus = session.confidence > 0.8 ? 5 : session.confidence > 0.6 ? 0 : -5;
        
        // Weighted average
        const finalScore = (pronunciationScore * 0.6) + (fluencyScore * 0.3) + (session.confidence * 100 * 0.1) + confidenceBonus;
        
        return Math.max(60, Math.min(100, Math.round(finalScore)));
    }

    // Event handlers (to be overridden)
    onRecognitionStart() {}
    onRecognitionEnd() {}
    onRecognitionError(error) {}
    onTranscriptUpdate(transcript, isFinal) {}
    onAudioProcessed(audioBlob, audioUrl) {}
    onSpeechStart() {}
    onSpeechEnd() {}
    onSpeechError(event) {}
    onPermissionError(error) {}
    onRecordingError(error) {}
}

// Export for use in other scripts
window.AudioEngine = AudioEngine;