import os
import tempfile
import base64
from openai import OpenAI
from pydub import AudioSegment
import io

class AudioAnalyzer:
    def __init__(self, api_key=None):
        """Initialize the AudioAnalyzer with OpenAI API key"""
        self.client = OpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY')
        )
    
    def analyze_audio(self, audio_data, analysis_type="pronunciation"):
        """
        Analyze audio data and return feedback
        
        Args:
            audio_data: Base64 encoded audio data or file path
            analysis_type: Type of analysis (pronunciation, fluency, interview)
        
        Returns:
            dict: Analysis results with text feedback and audio feedback
        """
        try:
            # Convert audio to text using Whisper
            transcript = self._transcribe_audio(audio_data)
            
            if not transcript:
                return {
                    'success': False,
                    'error': 'Could not transcribe audio'
                }
            
            # Analyze the transcript based on type
            analysis = self._analyze_transcript(transcript, analysis_type)
            
            # Generate audio feedback
            audio_feedback = self._generate_audio_feedback(analysis['feedback_text'])
            
            return {
                'success': True,
                'transcript': transcript,
                'analysis': analysis,
                'audio_feedback': audio_feedback
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _transcribe_audio(self, audio_data):
        """Transcribe audio using OpenAI Whisper"""
        temp_file_path = None
        wav_path = None
        
        try:
            # Check if API key is available
            if not self.client.api_key or self.client.api_key == 'your-api-key-here':
                raise Exception("OpenAI API key not configured")
            
            # Handle base64 encoded audio
            if isinstance(audio_data, str) and audio_data.startswith('data:audio'):
                # Extract base64 data
                header, encoded = audio_data.split(',', 1)
                audio_bytes = base64.b64decode(encoded)
                
                # Validate audio data
                if len(audio_bytes) < 100:
                    raise Exception("Audio data too short - no speech detected")
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_file:
                    temp_file.write(audio_bytes)
                    temp_file_path = temp_file.name
                
                # Convert to WAV if needed
                try:
                    audio = AudioSegment.from_file(temp_file_path)
                    
                    # Check audio duration
                    duration_seconds = len(audio) / 1000.0
                    if duration_seconds < 0.5:
                        raise Exception("Audio too short - please speak for at least 1 second")
                    
                    wav_path = temp_file_path.replace('.webm', '.wav')
                    audio.export(wav_path, format="wav")
                    
                    # Transcribe using Whisper
                    with open(wav_path, 'rb') as audio_file:
                        response = self.client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                            response_format="text"
                        )
                    
                    # Handle response
                    if isinstance(response, str):
                        transcript = response.strip()
                    else:
                        transcript = response.text.strip() if hasattr(response, 'text') else str(response).strip()
                    
                    # Validate transcript
                    if not transcript or len(transcript) < 2:
                        raise Exception("No speech detected in audio")
                    
                    return transcript
                    
                except Exception as e:
                    print(f"Audio processing error: {e}")
                    raise e
                finally:
                    # Clean up temporary files
                    if temp_file_path and os.path.exists(temp_file_path):
                        try:
                            os.unlink(temp_file_path)
                        except:
                            pass
                    if wav_path and os.path.exists(wav_path):
                        try:
                            os.unlink(wav_path)
                        except:
                            pass
            else:
                raise Exception("Invalid audio data format")
            
        except Exception as e:
            print(f"Transcription error: {e}")
            # Clean up on error
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            if wav_path and os.path.exists(wav_path):
                try:
                    os.unlink(wav_path)
                except:
                    pass
            raise e
    
    def _analyze_transcript(self, transcript, analysis_type):
        """Analyze transcript using GPT"""
        
        # Define prompts for different analysis types
        prompts = {
            'pronunciation': f"""
            Analyze the following speech transcript for pronunciation and clarity:
            
            Transcript: "{transcript}"
            
            Provide feedback on:
            1. Overall clarity and pronunciation
            2. Specific words that may need improvement
            3. Suggestions for better pronunciation
            4. A score from 1-100
            
            Format your response as constructive feedback for an English learner.
            """,
            
            'fluency': f"""
            Analyze the following speech transcript for fluency and natural flow:
            
            Transcript: "{transcript}"
            
            Provide feedback on:
            1. Speaking pace and rhythm
            2. Natural flow and pauses
            3. Grammar and sentence structure
            4. Vocabulary usage
            5. A score from 1-100
            
            Format your response as helpful guidance for improving conversational fluency.
            """,
            
            'interview': f"""
            Analyze the following interview response:
            
            Transcript: "{transcript}"
            
            Provide feedback on:
            1. Content quality and relevance
            2. Professional communication style
            3. Confidence and clarity
            4. Areas for improvement
            5. A score from 1-100
            
            Format your response as professional interview coaching feedback.
            """
        }
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert English language coach providing constructive feedback to help learners improve their speaking skills."},
                    {"role": "user", "content": prompts.get(analysis_type, prompts['pronunciation'])}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            feedback_text = response.choices[0].message.content
            
            # Extract score if mentioned
            score = self._extract_score(feedback_text)
            
            return {
                'type': analysis_type,
                'feedback_text': feedback_text,
                'score': score,
                'suggestions': self._extract_suggestions(feedback_text)
            }
            
        except Exception as e:
            return {
                'type': analysis_type,
                'feedback_text': f"Analysis error: {str(e)}",
                'score': 0,
                'suggestions': []
            }
    
    def _generate_audio_feedback(self, feedback_text):
        """Generate audio feedback using OpenAI TTS"""
        try:
            # Summarize feedback for audio (keep it concise)
            summary_prompt = f"""
            Summarize the following feedback into a brief, encouraging audio message (max 50 words):
            
            {feedback_text}
            
            Make it sound natural and supportive for an English learner.
            """
            
            summary_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=100
            )
            
            summary_text = summary_response.choices[0].message.content
            
            # Generate audio using TTS
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="nova",  # Female voice, good for teaching
                input=summary_text
            )
            
            # Convert to base64 for frontend
            audio_base64 = base64.b64encode(response.content).decode('utf-8')
            
            return {
                'text': summary_text,
                'audio_base64': audio_base64,
                'audio_url': f"data:audio/mp3;base64,{audio_base64}"
            }
            
        except Exception as e:
            return {
                'text': "Great job practicing! Keep up the good work!",
                'audio_base64': None,
                'audio_url': None,
                'error': str(e)
            }
    
    def _extract_score(self, feedback_text):
        """Extract numerical score from feedback text"""
        import re
        
        # Look for patterns like "score: 85", "85/100", "Score of 85"
        patterns = [
            r'score[:\s]+(\d+)',
            r'(\d+)/100',
            r'(\d+)\s*out\s*of\s*100',
            r'rate[d]?\s+(\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, feedback_text.lower())
            if match:
                score = int(match.group(1))
                return min(max(score, 0), 100)  # Ensure score is between 0-100
        
        return None
    
    def _extract_suggestions(self, feedback_text):
        """Extract actionable suggestions from feedback"""
        # Simple extraction - look for numbered points or bullet points
        suggestions = []
        lines = feedback_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if (line.startswith(('1.', '2.', '3.', '4.', '5.')) or 
                line.startswith(('•', '-', '*')) or
                'suggest' in line.lower() or
                'try' in line.lower() or
                'practice' in line.lower()):
                suggestions.append(line)
        
        return suggestions[:5]  # Limit to 5 suggestions