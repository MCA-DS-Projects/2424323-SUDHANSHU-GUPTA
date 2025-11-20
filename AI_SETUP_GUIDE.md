# AI Audio Analysis Setup Guide

This guide will help you set up AI-powered audio analysis using OpenAI's APIs for speech-to-text transcription and intelligent feedback generation.

## Prerequisites

1. **OpenAI API Account**: Sign up at [OpenAI Platform](https://platform.openai.com/)
2. **API Key**: Generate an API key from your OpenAI dashboard
3. **Python Dependencies**: Install required packages

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The following packages will be installed:
- `openai>=1.0.0` - OpenAI API client
- `pydub>=0.25.1` - Audio processing library

### 2. Set Up Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

### 3. Configure Audio Dependencies

For audio processing, you may need to install additional system dependencies:

**Windows:**
- Download and install [FFmpeg](https://ffmpeg.org/download.html)
- Add FFmpeg to your system PATH

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

## Features

### 1. Speech-to-Text Transcription
- Uses OpenAI's Whisper model for accurate speech recognition
- Supports multiple audio formats (WebM, WAV, MP3)
- Real-time transcription during recording

### 2. AI-Powered Feedback
- **Pronunciation Analysis**: GPT-4 analyzes pronunciation accuracy
- **Fluency Assessment**: Evaluates speaking pace, rhythm, and flow
- **Interview Practice**: Professional communication feedback
- **Personalized Suggestions**: Actionable improvement recommendations

### 3. Audio Feedback Generation
- Text-to-Speech feedback using OpenAI's TTS models
- Natural-sounding voice feedback
- Encouraging and constructive tone

## Usage

### 1. Access AI Audio Practice

Navigate to the AI Audio Practice page:
```
http://localhost:5000/pages/user/audio_practice_mode_ai.html
```

### 2. Select Analysis Type

Choose from three analysis modes:
- **Pronunciation Focus**: Detailed pronunciation analysis
- **Fluency Training**: Natural speech flow assessment  
- **Interview Practice**: Professional communication evaluation

### 3. Record and Analyze

1. Click the microphone button to start recording
2. Speak the provided text clearly
3. Click stop when finished
4. Wait for AI analysis (usually 5-10 seconds)
5. Review detailed feedback and suggestions

### 4. Audio Feedback

- Click the audio feedback button to hear spoken feedback
- Get personalized tips for improvement
- Save sessions for progress tracking

## API Endpoints

The following API endpoints handle AI audio analysis:

### POST `/api/audio/analyze-ai`
Analyzes audio using OpenAI's Whisper and GPT models.

**Request:**
```json
{
  "audio_data": "data:audio/webm;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEA...",
  "analysis_type": "pronunciation",
  "duration": 5.2
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid-here",
  "transcript": "The quick brown fox jumps over the lazy dog",
  "analysis": {
    "type": "pronunciation",
    "feedback_text": "Great job! Your pronunciation is clear...",
    "score": 85,
    "suggestions": ["Focus on 'th' sounds", "Practice word stress"]
  },
  "audio_feedback": {
    "text": "Excellent work! Keep practicing...",
    "audio_url": "data:audio/mp3;base64,..."
  }
}
```

### GET `/api/audio/get-feedback/<session_id>`
Retrieves detailed feedback for a specific session.

### GET `/api/audio/practice-exercises`
Gets personalized practice exercises based on user level.

## Troubleshooting

### Common Issues

1. **"Audio analysis service not available"**
   - Check that OpenAI API key is set correctly
   - Verify internet connection
   - Ensure `openai` package is installed

2. **"Microphone access denied"**
   - Allow microphone permissions in browser
   - Check browser security settings
   - Use HTTPS in production

3. **"Analysis failed"**
   - Check API key validity and credits
   - Verify audio format compatibility
   - Check network connectivity

4. **Poor transcription quality**
   - Ensure quiet recording environment
   - Speak clearly and at moderate pace
   - Check microphone quality

### Audio Format Issues

If you encounter audio format errors:

1. **Install FFmpeg** (see installation steps above)
2. **Check browser compatibility**:
   - Chrome/Edge: Full WebM support
   - Firefox: Limited WebM support
   - Safari: May need MP3 fallback

3. **Audio processing errors**:
   ```bash
   # Test FFmpeg installation
   ffmpeg -version
   
   # Test audio conversion
   ffmpeg -i test.webm test.wav
   ```

## Cost Considerations

### OpenAI API Pricing (as of 2024)

- **Whisper (Speech-to-Text)**: $0.006 per minute
- **GPT-4 (Analysis)**: ~$0.03-0.06 per request
- **TTS (Audio Feedback)**: $0.015 per 1K characters

**Example costs for 100 practice sessions:**
- Transcription (5 min avg): $3.00
- Analysis feedback: $4.50
- Audio feedback: $1.50
- **Total: ~$9.00 for 100 sessions**

### Cost Optimization Tips

1. **Limit audio length**: Keep recordings under 2 minutes
2. **Cache responses**: Store analysis results to avoid re-processing
3. **Batch processing**: Process multiple recordings together
4. **Use GPT-3.5**: For basic feedback (cheaper than GPT-4)

## Alternative: Google Gemini Integration

If you prefer Google's Gemini API:

1. Get API key from [Google AI Studio](https://makersuite.google.com/)
2. Install Google AI SDK:
   ```bash
   pip install google-generativeai
   ```
3. Set environment variable:
   ```env
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

Note: Gemini doesn't include speech-to-text, so you'll need a separate service for transcription.

## Security Best Practices

1. **Environment Variables**: Never commit API keys to version control
2. **Rate Limiting**: Implement request limits to prevent abuse
3. **Audio Privacy**: Don't store sensitive audio data
4. **HTTPS**: Use secure connections in production
5. **Input Validation**: Validate audio file sizes and formats

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review OpenAI API documentation
3. Check browser console for JavaScript errors
4. Verify network connectivity and API quotas

## Next Steps

1. **Test the basic setup** with a simple recording
2. **Customize feedback prompts** in `app/utils/audio_analyzer.py`
3. **Add more exercise types** based on your needs
4. **Implement progress tracking** with detailed analytics
5. **Add user preferences** for feedback style and difficulty

The AI audio analysis system is now ready to provide intelligent, personalized feedback for English language learning!