// app/static/js/api.js

class APIClient {
    constructor() {
        // Smart environment detection for API base URL
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            this.baseURL = 'http://localhost:5000/api'; // Development
        } else {
            this.baseURL = '/api'; // Production - relative URL
        }
        
        this.token = localStorage.getItem('access_token');
    }

    /**
     * Set authentication token
     */
    setToken(token) {
        this.token = token;
        localStorage.setItem('access_token', token);
    }

    /**
     * Clear authentication token
     */
    clearToken() {
        this.token = null;
        localStorage.removeItem('access_token');
    }

    /**
     * Get authentication headers
     */
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    }

    /**
     * Make API request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            ...options,
            headers: this.getHeaders()
        };

        try {
            console.log('Making API request to:', url, 'with config:', config);
            const response = await fetch(url, config);
            console.log('Response status:', response.status);
            
            const data = await response.json();
            console.log('Response data:', data);

            if (!response.ok) {
                throw new Error(data.error || 'API request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            console.error('Error details:', error.message);
            throw error;
        }
    }

    // Authentication
    async register(userData) {
        const data = await this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        
        if (data.access_token) {
            this.setToken(data.access_token);
        }
        
        return data;
    }

    async login(email, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        
        if (data.access_token) {
            this.setToken(data.access_token);
        }
        
        return data;
    }

    async getCurrentUser() {
        return await this.request('/auth/me');
    }

    // Dashboard
    async getDashboardOverview() {
        return await this.request('/dashboard/overview');
    }

    async getDashboardStats() {
        return await this.request('/dashboard/stats');
    }

    // Interview Simulator
    async getInterviewQuestions(difficulty = 'all') {
        return await this.request(`/interview/questions?difficulty=${difficulty}`);
    }

    async startInterviewSession(numQuestions = 8) {
        return await this.request('/interview/start-session', {
            method: 'POST',
            body: JSON.stringify({ num_questions: numQuestions })
        });
    }

    async submitInterviewResponse(transcription) {
        return await this.request('/interview/submit-response', {
            method: 'POST',
            body: JSON.stringify({ transcription })
        });
    }

    async saveInterviewSession(sessionData) {
        return await this.request('/interview/save-session', {
            method: 'POST',
            body: JSON.stringify(sessionData)
        });
    }

    // Fluency Coach
    async getFluencyScenarios() {
        return await this.request('/fluency/scenarios');
    }

    async startConversation(scenario) {
        return await this.request('/fluency/start-conversation', {
            method: 'POST',
            body: JSON.stringify({ scenario })
        });
    }

    async getAIResponse(message, scenario, turn) {
        return await this.request('/fluency/get-response', {
            method: 'POST',
            body: JSON.stringify({ message, scenario, turn })
        });
    }

    async saveFluencySession(sessionData) {
        return await this.request('/fluency/save-session', {
            method: 'POST',
            body: JSON.stringify(sessionData)
        });
    }

    // Audio Practice
    async getAudioExercises(type = 'word-stress') {
        return await this.request(`/audio/exercises?type=${type}`);
    }

    async analyzePronunciation(transcription) {
        return await this.request('/audio/analyze-pronunciation', {
            method: 'POST',
            body: JSON.stringify({ transcription })
        });
    }

    async saveAudioSession(sessionData) {
        return await this.request('/audio/save-session', {
            method: 'POST',
            body: JSON.stringify(sessionData)
        });
    }

    async getAudioProgress() {
        return await this.request('/audio/progress');
    }

    // Presentation Practice
    async getPresentationTopics(category = 'all') {
        return await this.request(`/presentation/topics?category=${category}`);
    }

    async analyzePresentation(duration) {
        return await this.request('/presentation/analyze-presentation', {
            method: 'POST',
            body: JSON.stringify({ duration })
        });
    }

    async savePresentationSession(sessionData) {
        return await this.request('/presentation/save-session', {
            method: 'POST',
            body: JSON.stringify(sessionData)
        });
    }

    async getRecentPresentations() {
        return await this.request('/presentation/recent-presentations');
    }

    // Analytics
    async getAnalyticsOverview(range = '30d') {
        return await this.request(`/analytics/overview?range=${range}`);
    }

    async getTrends(days = 30) {
        return await this.request(`/analytics/trends?days=${days}`);
    }

    async getSessionHistory(page = 1, perPage = 10) {
        return await this.request(`/analytics/session-history?page=${page}&per_page=${perPage}`);
    }

    async getGoals() {
        return await this.request('/analytics/goals');
    }

    async getPeerComparison() {
        return await this.request('/analytics/comparison');
    }

    // Profile
    async getProfile() {
        return await this.request('/profile/');
    }

    async updateProfile(profileData) {
        return await this.request('/profile/update', {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });
    }

    async changePassword(currentPassword, newPassword) {
        return await this.request('/profile/change-password', {
            method: 'POST',
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
    }

    // Admin
    async getAdminDashboard() {
        return await this.request('/admin/dashboard');
    }

    async getUsers(page = 1, perPage = 10, search = '') {
        return await this.request(`/admin/users?page=${page}&per_page=${perPage}&search=${search}`);
    }

    async getUserDetails(userId) {
        return await this.request(`/admin/users/${userId}`);
    }

    async updateUser(userId, userData) {
        return await this.request(`/admin/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(userData)
        });
    }

    async deleteUser(userId) {
        return await this.request(`/admin/users/${userId}`, {
            method: 'DELETE'
        });
    }

    async getPlatformAnalytics(days = 30) {
        return await this.request(`/admin/analytics?days=${days}`);
    }

    // New AI Audio Analysis Methods
    async analyzeAudioWithAI(audioData, analysisType = 'pronunciation') {
        return await this.request('/audio/analyze-ai', {
            method: 'POST',
            body: JSON.stringify({
                audio_data: audioData,
                analysis_type: analysisType
            })
        });
    }

    async getAudioFeedback(sessionId) {
        return await this.request(`/audio/get-feedback/${sessionId}`);
    }

    async getAIPracticeExercises() {
        return await this.request('/audio/practice-exercises');
    }

    // Interview Analysis
    async analyzeInterviewResponse(question, transcript, category = 'General', difficulty = 'Medium') {
        return await this.request('/interview/analyze-response', {
            method: 'POST',
            body: JSON.stringify({
                question: question,
                transcript: transcript,
                category: category,
                difficulty: difficulty
            })
        });
    }

    async generateInterviewQuestion(category = 'Behavioral', difficulty = 'Medium', jobRole = 'Professional') {
        return await this.request('/interview/generate-question', {
            method: 'POST',
            body: JSON.stringify({
                category: category,
                difficulty: difficulty,
                job_role: jobRole
            })
        });
    }

    // Conversation AI
    async startAIConversation(conversationType = 'fluency_practice') {
        return await this.request('/conversation/start', {
            method: 'POST',
            body: JSON.stringify({
                conversation_type: conversationType
            })
        });
    }

    async continueAIConversation(userMessage, conversationHistory = []) {
        return await this.request('/conversation/continue', {
            method: 'POST',
            body: JSON.stringify({
                user_message: userMessage,
                conversation_history: conversationHistory
            })
        });
    }

    async generateQuickResponses(lastMessage = '', conversationHistory = []) {
        return await this.request('/conversation/quick-responses', {
            method: 'POST',
            body: JSON.stringify({
                last_message: lastMessage,
                conversation_history: conversationHistory
            })
        });
    }

    // Audio Practice with AI
    async generatePracticePhrase(exerciseType = 'word-stress', difficulty = 'medium') {
        return await this.request('/audio/generate-phrase', {
            method: 'POST',
            body: JSON.stringify({
                exercise_type: exerciseType,
                difficulty: difficulty
            })
        });
    }

    async getAudioPracticeStats() {
        return await this.request('/audio/stats');
    }

    // Session Tracking
    async trackSessionCompletion(sessionType = 'general', duration = 0) {
        return await this.request('/session/track', {
            method: 'POST',
            body: JSON.stringify({
                session_type: sessionType,
                duration: duration
            })
        });
    }

    async incrementSessionCount() {
        return await this.request('/dashboard/increment-session', {
            method: 'POST'
        });
    }
}

// Create global API client instance
const api = new APIClient();

// Make it available globally
window.api = api;

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIClient, api };
}