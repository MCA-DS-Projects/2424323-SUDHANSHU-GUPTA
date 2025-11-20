"""
Real-time Speech Analysis
Analyzes speech metrics in real-time during recording
"""

import re
from collections import Counter
from datetime import datetime

class RealtimeSpeechAnalyzer:
    """Analyzes speech in real-time for pronunciation, pace, confidence, etc."""
    
    # Common filler words to detect
    FILLER_WORDS = [
        'um', 'uh', 'like', 'you know', 'actually', 'basically', 
        'literally', 'sort of', 'kind of', 'i mean', 'well',
        'so', 'right', 'okay', 'yeah', 'hmm', 'er', 'ah'
    ]
    
    # Words that indicate confidence
    CONFIDENCE_WORDS = [
        'definitely', 'certainly', 'absolutely', 'clearly', 'obviously',
        'successfully', 'achieved', 'accomplished', 'led', 'managed',
        'created', 'developed', 'improved', 'increased', 'reduced'
    ]
    
    # Words that indicate hesitation
    HESITATION_WORDS = [
        'maybe', 'perhaps', 'possibly', 'might', 'could', 'probably',
        'i think', 'i guess', 'i suppose', 'not sure', 'uncertain'
    ]
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all metrics"""
        self.start_time = None
        self.word_count = 0
        self.filler_count = 0
        self.filler_details = Counter()
        self.confidence_indicators = 0
        self.hesitation_indicators = 0
        self.total_syllables = 0
        self.pause_count = 0
        self.last_word_time = None
    
    def start_analysis(self):
        """Start timing for analysis"""
        self.start_time = datetime.now()
        self.last_word_time = self.start_time
    
    def analyze_transcript(self, transcript: str, is_final: bool = False) -> dict:
        """
        Analyze transcript and return real-time metrics
        
        Args:
            transcript: The speech transcript to analyze
            is_final: Whether this is the final transcript
        
        Returns:
            Dictionary with analysis metrics
        """
        if not transcript or not transcript.strip():
            return self._get_default_metrics()
        
        # Start timing if not started
        if not self.start_time:
            self.start_analysis()
        
        # Calculate elapsed time
        elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        if elapsed_seconds < 1:
            elapsed_seconds = 1
        
        # Analyze text
        words = transcript.lower().split()
        self.word_count = len(words)
        
        # Calculate speaking pace (WPM) - cap at reasonable values
        # Assume average speaking time is word_count / 2.5 words per second (150 WPM baseline)
        estimated_speaking_time = max(elapsed_seconds, self.word_count / 2.5)
        wpm = int((self.word_count / estimated_speaking_time) * 60)
        wpm = min(wpm, 250)  # Cap at 250 WPM (very fast)
        
        # Detect filler words
        self._detect_filler_words(transcript.lower())
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(words)
        
        # Estimate pronunciation accuracy (based on hesitations and fillers)
        pronunciation_score = self._estimate_pronunciation(words)
        
        # Analyze speaking pace quality
        pace_quality = self._analyze_pace(wpm)
        
        # Detect pauses (multiple spaces or punctuation)
        pause_count = len(re.findall(r'[.!?]+|\s{2,}', transcript))
        
        return {
            'pronunciation': {
                'score': pronunciation_score,
                'percentage': pronunciation_score
            },
            'speaking_pace': {
                'wpm': wpm,
                'quality': pace_quality,
                'optimal_range': '140-160',
                'percentage': min(100, int((wpm / 150) * 100))
            },
            'confidence': {
                'score': confidence_score,
                'percentage': confidence_score,
                'indicators': self.confidence_indicators,
                'hesitations': self.hesitation_indicators
            },
            'filler_words': {
                'count': self.filler_count,
                'details': dict(self.filler_details.most_common(5)),
                'rate': round(self.filler_count / max(1, self.word_count) * 100, 1)
            },
            'volume': {
                'level': 4,  # This would come from audio analysis
                'status': 'good'
            },
            'word_count': self.word_count,
            'duration': elapsed_seconds,
            'pause_count': pause_count
        }
    
    def _detect_filler_words(self, text: str):
        """Detect and count filler words"""
        self.filler_count = 0
        self.filler_details = Counter()
        
        for filler in self.FILLER_WORDS:
            # Count occurrences
            if ' ' in filler:
                # Multi-word fillers
                count = text.count(filler)
            else:
                # Single word fillers (with word boundaries)
                pattern = r'\b' + re.escape(filler) + r'\b'
                count = len(re.findall(pattern, text))
            
            if count > 0:
                self.filler_count += count
                self.filler_details[filler] = count
    
    def _calculate_confidence(self, words: list) -> int:
        """Calculate confidence score based on word choice"""
        self.confidence_indicators = 0
        self.hesitation_indicators = 0
        
        text = ' '.join(words)
        
        # Count confidence indicators
        for word in self.CONFIDENCE_WORDS:
            if word in text:
                self.confidence_indicators += 1
        
        # Count hesitation indicators
        for word in self.HESITATION_WORDS:
            if word in text:
                self.hesitation_indicators += 1
        
        # Calculate base confidence
        base_confidence = 70
        
        # Adjust for confidence words
        base_confidence += min(20, self.confidence_indicators * 3)
        
        # Penalize for hesitations
        base_confidence -= min(15, self.hesitation_indicators * 5)
        
        # Penalize for excessive fillers
        filler_penalty = min(20, self.filler_count * 2)
        base_confidence -= filler_penalty
        
        # Ensure score is between 0-100
        return max(0, min(100, base_confidence))
    
    def _estimate_pronunciation(self, words: list) -> int:
        """Estimate pronunciation accuracy"""
        # Base score
        base_score = 85
        
        # Penalize for fillers (indicates unclear speech)
        filler_penalty = min(20, self.filler_count * 2)
        base_score -= filler_penalty
        
        # Penalize for hesitations
        hesitation_penalty = min(10, self.hesitation_indicators * 3)
        base_score -= hesitation_penalty
        
        # Bonus for longer words (indicates clear pronunciation)
        long_words = sum(1 for word in words if len(word) > 7)
        long_word_bonus = min(10, long_words)
        base_score += long_word_bonus
        
        return max(0, min(100, base_score))
    
    def _analyze_pace(self, wpm: int) -> str:
        """Analyze speaking pace quality"""
        if wpm < 100:
            return 'Too Slow'
        elif wpm < 130:
            return 'Slow'
        elif wpm <= 170:
            return 'Good'
        elif wpm <= 190:
            return 'Fast'
        else:
            return 'Too Fast'
    
    def _get_default_metrics(self) -> dict:
        """Return default metrics when no transcript available"""
        return {
            'pronunciation': {'score': 0, 'percentage': 0},
            'speaking_pace': {'wpm': 0, 'quality': 'N/A', 'optimal_range': '140-160', 'percentage': 0},
            'confidence': {'score': 0, 'percentage': 0, 'indicators': 0, 'hesitations': 0},
            'filler_words': {'count': 0, 'details': {}, 'rate': 0},
            'volume': {'level': 0, 'status': 'unknown'},
            'word_count': 0,
            'duration': 0,
            'pause_count': 0
        }


# Global instance
_analyzer = None

def get_realtime_analyzer():
    """Get or create global analyzer instance"""
    global _analyzer
    if _analyzer is None:
        _analyzer = RealtimeSpeechAnalyzer()
    return _analyzer
