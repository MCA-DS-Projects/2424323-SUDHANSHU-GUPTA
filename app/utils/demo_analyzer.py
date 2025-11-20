"""
Demo Audio Analyzer - Works without API calls for testing UI
"""
import time
import random
from typing import Dict, Any

class DemoAnalyzer:
    def __init__(self):
        """Initialize demo analyzer"""
        self.demo_mode = True
    
    def analyze_audio(self, audio_data: str, analysis_type: str = "pronunciation") -> Dict[str, Any]:
        """
        Simulate AI analysis for demo purposes
        """
        # Simulate processing time
        time.sleep(2)
        
        # Generate realistic demo results
        transcript = self._generate_demo_transcript(analysis_type)
        analysis = self._generate_demo_analysis(transcript, analysis_type)
        audio_feedback = self._generate_demo_audio_feedback(analysis['feedback_text'])
        
        return {
            'success': True,
            'transcript': transcript,
            'analysis': analysis,
            'audio_feedback': audio_feedback
        }
    
    def _generate_demo_transcript(self, analysis_type: str) -> str:
        """Generate demo transcript based on analysis type"""
        transcripts = {
            'pronunciation': "The quick brown fox jumps over the lazy dog.",
            'fluency': "I believe that effective communication is essential in today's workplace.",
            'interview': "I am passionate about this role because it aligns with my career goals."
        }
        return transcripts.get(analysis_type, transcripts['pronunciation'])
    
    def _generate_demo_analysis(self, transcript: str, analysis_type: str) -> Dict[str, Any]:
        """Generate demo analysis results"""
        
        # Generate realistic score
        base_score = random.randint(70, 95)
        
        feedback_templates = {
            'pronunciation': f"""
            Excellent work on your pronunciation! Your speech is clear and well-articulated.

            Strengths:
            • Clear consonant sounds
            • Good vowel pronunciation
            • Natural word stress patterns

            Areas for improvement:
            • Focus on the 'th' sound in "the"
            • Practice linking words smoothly

            Overall Score: {base_score}/100

            Keep practicing regularly to maintain this excellent level!
            """,
            
            'fluency': f"""
            Great fluency and natural speech flow! Your communication is effective and engaging.

            Strengths:
            • Natural rhythm and pace
            • Good sentence structure
            • Confident delivery

            Areas for improvement:
            • Add more pauses for emphasis
            • Vary your intonation slightly more

            Overall Score: {base_score}/100

            Your conversational skills are developing well!
            """,
            
            'interview': f"""
            Professional and confident interview response! You communicate your points clearly.

            Strengths:
            • Clear and professional tone
            • Well-structured response
            • Confident delivery

            Areas for improvement:
            • Add specific examples
            • Use more varied vocabulary

            Overall Score: {base_score}/100

            You're well-prepared for professional interviews!
            """
        }
        
        feedback_text = feedback_templates.get(analysis_type, feedback_templates['pronunciation'])
        
        suggestions = [
            "Practice daily for 10-15 minutes",
            "Record yourself and listen back",
            "Focus on problem sounds",
            "Use a mirror to watch mouth movements",
            "Practice with tongue twisters"
        ]
        
        return {
            'type': analysis_type,
            'feedback_text': feedback_text.strip(),
            'score': base_score,
            'suggestions': random.sample(suggestions, 3)
        }
    
    def _generate_demo_audio_feedback(self, feedback_text: str) -> Dict[str, Any]:
        """Generate demo audio feedback"""
        
        summary_texts = [
            "Great job! Your pronunciation is clear and natural. Keep practicing!",
            "Excellent work! Focus on linking words smoothly for even better fluency.",
            "Well done! Your confidence is showing. Practice daily to maintain progress.",
            "Nice improvement! Work on those 'th' sounds and you'll be perfect.",
            "Outstanding effort! Your speech is becoming more natural every day."
        ]
        
        return {
            'text': random.choice(summary_texts),
            'audio_base64': None,  # No actual audio in demo mode
            'audio_url': None,
            'demo_mode': True
        }