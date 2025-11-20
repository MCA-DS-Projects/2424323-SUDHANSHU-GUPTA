"""
Dynamic Interview Answer Analyzer
Provides specific, personalized feedback based on actual answer content
Supports both OpenAI and Google Gemini APIs
"""

import os
from typing import Dict, List

class InterviewAnalyzer:
    """Analyzes interview responses and provides dynamic, specific feedback"""
    
    def __init__(self, openai_key: str = None, gemini_key: str = None):
        """Initialize the analyzer with API keys"""
        self.openai_key = openai_key or os.getenv('OPENAI_API_KEY')
        self.gemini_key = gemini_key or os.getenv('GEMINI_API_KEY')
        self.client = None
        self.ai_provider = None
        self.initialized = False
        
        # Try Gemini first (free tier available)
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                # Use Gemini 2.5 Flash - stable and fast
                self.client = genai.GenerativeModel('gemini-2.5-flash')
                self.ai_provider = 'gemini'
                self.initialized = True
                print("✓ Initialized with Google Gemini 2.5 Flash")
            except Exception as e:
                print(f"Failed to initialize Gemini: {e}")
        
        # Fall back to OpenAI if Gemini fails
        if not self.initialized and self.openai_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.openai_key)
                self.ai_provider = 'openai'
                self.initialized = True
                print("✓ Initialized with OpenAI")
            except Exception as e:
                print(f"Failed to initialize OpenAI: {e}")
        
        if not self.initialized:
            print("⚠ No AI provider available, using smart fallback mode")
    
    def analyze_answer(self, question: str, answer: str, category: str = "General", 
                      difficulty: str = "Medium", user_context: Dict = None) -> Dict:
        """
        Analyze an interview answer and provide specific, dynamic feedback
        
        Args:
            question: The interview question asked
            answer: The user's answer/transcript
            category: Question category (Behavioral, Technical, etc.)
            difficulty: Question difficulty level
            user_context: Additional context about the user (optional)
        
        Returns:
            Dictionary with score, feedback, strengths, improvements, and suggestions
        """
        if not self.initialized:
            return self._generate_basic_feedback(question, answer, category)
        
        try:
            # Create a detailed prompt for analysis
            prompt = self._create_analysis_prompt(question, answer, category, difficulty, user_context)
            
            # Call appropriate AI API
            if self.ai_provider == 'gemini':
                feedback_text = self._call_gemini(prompt)
            elif self.ai_provider == 'openai':
                feedback_text = self._call_openai(prompt)
            else:
                raise Exception("No AI provider configured")
            
            # Parse the feedback into structured components
            parsed = self._parse_feedback(feedback_text, answer)
            
            return {
                'success': True,
                'score': parsed['score'],
                'feedback_text': feedback_text,
                'strengths': parsed['strengths'],
                'improvements': parsed['improvements'],
                'suggestions': parsed['suggestions'],
                'ai_powered': True,
                'ai_provider': self.ai_provider
            }
            
        except Exception as e:
            print(f"AI analysis failed: {e}")
            return self._generate_basic_feedback(question, answer, category)
    
    def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API"""
        response = self.client.generate_content(prompt)
        return response.text
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert interview coach who provides specific, actionable feedback on interview responses. Always reference specific parts of the candidate's answer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        return response.choices[0].message.content
    
    def _create_analysis_prompt(self, question: str, answer: str, category: str, 
                               difficulty: str, user_context: Dict = None) -> str:
        """Create a detailed prompt for answer analysis"""
        
        user_info = ""
        if user_context:
            user_info = f"""
User Context:
- Name: {user_context.get('name', 'the candidate')}
- Experience Level: {user_context.get('experience_level', 'intermediate')}
- Previous Sessions: {user_context.get('total_sessions', 0)}
"""
        
        prompt = f"""Analyze this interview response and provide specific, personalized feedback.

{user_info}
Interview Question ({category} - {difficulty}):
"{question}"

Candidate's Answer:
"{answer}"

Provide a detailed analysis with:

1. SCORE (0-100): Rate the answer quality considering:
   - Relevance to the question
   - Completeness and depth
   - Use of specific examples
   - Structure and clarity
   - Professional communication

2. SPECIFIC STRENGTHS (2-3 points):
   - Quote or reference specific parts of their answer
   - Explain WHY these parts are effective
   - Be genuine - only mention real strengths you observe

3. SPECIFIC IMPROVEMENTS (2-3 points):
   - Point out what's missing or could be better
   - Reference specific parts of their answer
   - Explain HOW they can improve
   - Be constructive and actionable

4. ACTIONABLE SUGGESTIONS (2-3 points):
   - Give concrete next steps
   - Provide specific techniques or frameworks
   - Tailor advice to their answer quality

Format your response as:

SCORE: [number]

STRENGTHS:
- [Specific strength with reference to their answer]
- [Another specific strength]

IMPROVEMENTS:
- [Specific area to improve with reference to their answer]
- [Another specific improvement]

SUGGESTIONS:
- [Actionable suggestion]
- [Another actionable suggestion]

OVERALL FEEDBACK:
[2-3 sentences of personalized, encouraging feedback that references their specific answer]

Remember: Be specific, reference their actual words, and make it personal to THIS answer."""
        
        return prompt
    
    def _parse_feedback(self, feedback_text: str, answer: str) -> Dict:
        """Parse AI feedback into structured components"""
        import re
        
        # Extract score
        score_match = re.search(r'SCORE:\s*(\d+)', feedback_text, re.IGNORECASE)
        score = int(score_match.group(1)) if score_match else self._calculate_basic_score(answer)
        
        # Extract strengths
        strengths = []
        strengths_section = re.search(r'STRENGTHS?:(.*?)(?=IMPROVEMENTS?:|SUGGESTIONS?:|OVERALL|$)', 
                                     feedback_text, re.DOTALL | re.IGNORECASE)
        if strengths_section:
            strength_items = re.findall(r'[-•]\s*(.+?)(?=\n[-•]|\n\n|$)', strengths_section.group(1), re.DOTALL)
            strengths = [s.strip() for s in strength_items if s.strip()]
        
        # Extract improvements
        improvements = []
        improvements_section = re.search(r'IMPROVEMENTS?:(.*?)(?=SUGGESTIONS?:|OVERALL|$)', 
                                        feedback_text, re.DOTALL | re.IGNORECASE)
        if improvements_section:
            improvement_items = re.findall(r'[-•]\s*(.+?)(?=\n[-•]|\n\n|$)', improvements_section.group(1), re.DOTALL)
            improvements = [i.strip() for i in improvement_items if i.strip()]
        
        # Extract suggestions
        suggestions = []
        suggestions_section = re.search(r'SUGGESTIONS?:(.*?)(?=OVERALL|$)', 
                                       feedback_text, re.DOTALL | re.IGNORECASE)
        if suggestions_section:
            suggestion_items = re.findall(r'[-•]\s*(.+?)(?=\n[-•]|\n\n|$)', suggestions_section.group(1), re.DOTALL)
            suggestions = [s.strip() for s in suggestion_items if s.strip()]
        
        return {
            'score': score,
            'strengths': strengths[:3],
            'improvements': improvements[:3],
            'suggestions': suggestions[:3]
        }
    
    def _calculate_basic_score(self, answer: str) -> int:
        """Calculate a basic score based on answer characteristics"""
        word_count = len(answer.split())
        has_examples = any(word in answer.lower() for word in 
                          ['example', 'time', 'when', 'situation', 'project', 'experience'])
        has_outcomes = any(word in answer.lower() for word in 
                          ['result', 'outcome', 'achieved', 'success', 'learned', 'improved'])
        has_numbers = any(char.isdigit() for char in answer)
        
        score = 60  # Base score
        
        if word_count > 100:
            score += 15
        elif word_count > 50:
            score += 10
        elif word_count > 30:
            score += 5
        
        if has_examples:
            score += 10
        if has_outcomes:
            score += 10
        if has_numbers:
            score += 5
        
        return min(95, score)
    
    def _generate_basic_feedback(self, question: str, answer: str, category: str) -> Dict:
        """Generate basic feedback when AI is not available"""
        word_count = len(answer.split())
        has_examples = any(word in answer.lower() for word in 
                          ['example', 'time', 'when', 'situation', 'project'])
        has_outcomes = any(word in answer.lower() for word in 
                          ['result', 'outcome', 'achieved', 'success', 'learned'])
        
        score = self._calculate_basic_score(answer)
        
        # Generate specific feedback based on actual content
        strengths = []
        improvements = []
        suggestions = []
        
        # Analyze strengths
        if word_count > 80:
            strengths.append(f"Your answer is comprehensive with {word_count} words, showing thorough thinking")
        elif word_count > 40:
            strengths.append(f"You provided a solid {word_count}-word response with good detail")
        
        if has_examples:
            strengths.append("You included specific examples, which makes your answer more credible")
        
        if has_outcomes:
            strengths.append("You mentioned results and outcomes, demonstrating impact")
        
        # Analyze improvements
        if not has_examples:
            improvements.append("Add a specific example from your experience to illustrate your point")
        
        if not has_outcomes:
            improvements.append("Include the results or outcomes of your actions to show impact")
        
        if word_count < 40:
            improvements.append("Expand your answer with more details and specific examples")
        
        # Generate suggestions
        if category == "Behavioral":
            suggestions.append("Use the STAR method: Situation, Task, Action, Result")
        
        suggestions.append("Practice your answer out loud to improve fluency and confidence")
        
        if score < 75:
            suggestions.append("Prepare 3-5 detailed stories you can adapt to different questions")
        
        feedback_text = f"""Your answer scored {score}/100.

STRENGTHS:
{chr(10).join('- ' + s for s in strengths) if strengths else '- You addressed the question'}

IMPROVEMENTS:
{chr(10).join('- ' + i for i in improvements) if improvements else '- Keep practicing to refine your delivery'}

SUGGESTIONS:
{chr(10).join('- ' + s for s in suggestions)}

Keep practicing to improve your interview performance!"""
        
        return {
            'success': True,
            'score': score,
            'feedback_text': feedback_text,
            'strengths': strengths or ["You addressed the question"],
            'improvements': improvements or ["Keep practicing to refine your delivery"],
            'suggestions': suggestions,
            'ai_powered': False
        }


# Global instance
_analyzer = None

def get_interview_analyzer() -> InterviewAnalyzer:
    """Get or create global analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = InterviewAnalyzer()
    return _analyzer
