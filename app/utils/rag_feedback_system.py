"""
RAG-based Feedback System using LangChain
Provides personalized, context-aware feedback for English learning sessions
"""

import os
from typing import List, Dict, Optional
from datetime import datetime
import json

try:
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_community.vectorstores import FAISS
    from langchain_core.prompts import PromptTemplate
    from langchain_core.documents import Document
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    LANGCHAIN_AVAILABLE = False
    Document = None
    OpenAIEmbeddings = None
    ChatOpenAI = None
    FAISS = None
    PromptTemplate = None
    print(f"LangChain not installed: {e}")
    print("Install with: pip install langchain-openai langchain-community faiss-cpu")


class RAGFeedbackSystem:
    """RAG-based feedback system for personalized learning feedback"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the RAG feedback system"""
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.vector_store = None
        self.qa_chain = None
        self.initialized = False
        
        if not LANGCHAIN_AVAILABLE:
            print("Warning: LangChain not available. Using fallback feedback system.")
            return
        
        if not self.openai_api_key:
            print("Warning: OpenAI API key not found. RAG system will not be initialized.")
            return
        
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize embeddings, vector store, and LLM"""
        try:
            self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
            documents = self._load_example_feedback()
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
            self.llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0.7,
                openai_api_key=self.openai_api_key
            )
            self.initialized = True
            print("✓ RAG Feedback System initialized successfully")
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "429" in error_msg:
                print(f"⚠ OpenAI API quota exceeded. Using fallback feedback system.")
            else:
                print(f"Error initializing RAG system: {e}")
            self.initialized = False

    
    def _load_example_feedback(self) -> List[Document]:
        """Load example feedback patterns"""
        feedback_examples = [
            {
                "category": "interview",
                "score_range": "85-100",
                "user_level": "advanced",
                "example": """Excellent interview response! You demonstrated strong communication skills.

Strengths:
- Used specific examples with clear outcomes
- Followed STAR method effectively
- Professional and confident tone
- Provided measurable results

Your response shows you understand what interviewers are looking for. Keep practicing to maintain this excellent level!"""
            },
            {
                "category": "interview",
                "score_range": "70-84",
                "user_level": "intermediate",
                "example": """Good interview response with room for improvement.

Strengths:
- Relevant to the question
- Clear communication
- Professional tone

Areas to improve:
- Add more specific examples with numbers/metrics
- Use STAR method (Situation, Task, Action, Result)
- Include the outcome or lesson learned

Practice tip: Prepare 5-7 STAR stories covering different competencies."""
            },
            {
                "category": "interview",
                "score_range": "50-69",
                "user_level": "beginner",
                "example": """Your response addresses the question but needs more detail.

Areas to focus on:
- Provide specific examples from your experience
- Describe the situation and your actions clearly
- Mention the results or outcomes
- Practice the STAR method

Recommendation: Write out 3-5 example stories and practice telling them concisely."""
            }
        ]
        
        documents = []
        for example in feedback_examples:
            content = f"""
Category: {example['category']}
Score Range: {example['score_range']}
User Level: {example['user_level']}

Feedback Example:
{example['example']}
"""
            metadata = {
                "category": example['category'],
                "score_range": example['score_range'],
                "user_level": example['user_level']
            }
            documents.append(Document(page_content=content, metadata=metadata))
        
        return documents
    
    def _create_prompt_template(self) -> PromptTemplate:
        """Create prompt template for feedback generation"""
        template = """You are an expert interview coach providing personalized feedback.

Context from similar feedback examples:
{context}

User Information:
- Name: {user_name}
- Experience Level: {user_level}
- Total Interview Sessions: {interview_sessions}
- Average Score: {avg_score}

Current Session:
- Question: {question}
- Category: {category}
- Difficulty: {difficulty}
- Response: {transcript}
- Score: {score}/100
- Word Count: {word_count}
- Includes Examples: {has_examples}
- Mentions Outcomes: {has_outcomes}

Provide personalized feedback that:
1. Addresses {user_name} by name
2. Acknowledges their specific response to the question
3. Identifies 2-3 specific strengths from their answer
4. Suggests 2-3 concrete improvements
5. Gives actionable practice recommendations
6. Encourages continued progress

Make it personal, specific, and actionable. Reference their actual words when possible.

Feedback:"""
        
        return PromptTemplate(
            template=template,
            input_variables=[
                "context", "user_name", "user_level", "interview_sessions",
                "avg_score", "question", "category", "difficulty", "transcript",
                "score", "word_count", "has_examples", "has_outcomes"
            ]
        )
    
    def generate_feedback(self, user_data: Dict, session_data: Dict, performance_data: Dict) -> Dict:
        """Generate personalized feedback using RAG"""
        if not self.initialized:
            return self._generate_fallback_feedback(user_data, session_data, performance_data)
        
        try:
            # Retrieve relevant examples
            query = f"Score: {performance_data.get('score', 0)}, Level: {user_data.get('experience_level', 'intermediate')}"
            docs = self.vector_store.similarity_search(query, k=3)
            context = "\n\n".join([doc.page_content for doc in docs])
            
            # Create prompt
            prompt = f"""You are an expert interview coach providing personalized feedback.

Context from similar feedback examples:
{context}

User Information:
- Name: {user_data.get('name', 'there')}
- Experience Level: {user_data.get('experience_level', 'intermediate')}
- Total Interview Sessions: {user_data.get('interview_sessions', 0)}
- Average Score: {user_data.get('average_score', 0)}

Current Session:
- Question: {session_data.get('question', '')}
- Category: {session_data.get('category', 'General')}
- Difficulty: {session_data.get('difficulty', 'Medium')}
- Response: {session_data.get('transcript', '')}
- Score: {performance_data.get('score', 0)}/100
- Word Count: {session_data.get('word_count', 0)}
- Includes Examples: {session_data.get('has_examples', False)}
- Mentions Outcomes: {session_data.get('has_outcomes', False)}

Provide personalized feedback that:
1. Addresses {user_data.get('name', 'there')} by name
2. Acknowledges their specific response to the question
3. Identifies 2-3 specific strengths from their answer
4. Suggests 2-3 concrete improvements
5. Gives actionable practice recommendations
6. Encourages continued progress

Make it personal, specific, and actionable. Reference their actual words when possible.

Feedback:"""
            
            # Generate feedback
            result = self.llm.predict(prompt)
            
            return {
                "feedback_text": result,
                "score": performance_data.get('score', 0),
                "category": session_data.get('type', 'interview'),
                "suggestions": self._extract_suggestions(result),
                "strengths": self._extract_strengths(result),
                "improvements": self._extract_improvements(result),
                "generated_at": datetime.utcnow().isoformat(),
                "personalized": True,
                "rag_enabled": True
            }
        except Exception as e:
            print(f"RAG generation error: {e}")
            return self._generate_fallback_feedback(user_data, session_data, performance_data)
    
    def _extract_suggestions(self, text: str) -> List[str]:
        """Extract suggestions from feedback"""
        suggestions = []
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if any(kw in line.lower() for kw in ['practice', 'try', 'recommend', 'tip', 'suggestion']):
                if 20 < len(line) < 200:
                    suggestions.append(line.lstrip('- •*'))
        return suggestions[:5]
    
    def _extract_strengths(self, text: str) -> List[str]:
        """Extract strengths from feedback"""
        strengths = []
        lines = text.split('\n')
        in_strengths = False
        for line in lines:
            line = line.strip()
            if 'strength' in line.lower():
                in_strengths = True
                continue
            if in_strengths and line.startswith(('-', '•', '*', '✓')):
                strengths.append(line.lstrip('- •*✓'))
            elif in_strengths and ('improve' in line.lower() or 'area' in line.lower()):
                break
        return strengths[:5]
    
    def _extract_improvements(self, text: str) -> List[str]:
        """Extract improvements from feedback"""
        improvements = []
        lines = text.split('\n')
        in_improvements = False
        for line in lines:
            line = line.strip()
            if any(kw in line.lower() for kw in ['improve', 'area', 'focus', 'work on']):
                in_improvements = True
                continue
            if in_improvements and line.startswith(('-', '•', '*', '→')):
                improvements.append(line.lstrip('- •*→'))
        return improvements[:5]
    
    def _generate_fallback_feedback(self, user_data: Dict, session_data: Dict, performance_data: Dict) -> Dict:
        """Generate basic feedback when RAG unavailable"""
        score = performance_data.get('score', 0)
        name = user_data.get('name', 'there')
        
        if score >= 85:
            message = f"Excellent work, {name}! Your interview response demonstrates strong communication skills and clear thinking."
        elif score >= 70:
            message = f"Good job, {name}! Your response is solid. Focus on adding more specific examples and outcomes to reach the next level."
        else:
            message = f"Nice effort, {name}! Keep practicing. Try using the STAR method to structure your responses better."
        
        return {
            "feedback_text": message,
            "score": score,
            "category": "interview",
            "suggestions": ["Practice STAR method", "Add specific examples", "Mention measurable outcomes"],
            "strengths": ["Completed the response", "Addressed the question"],
            "improvements": ["Add more detail", "Use specific examples"],
            "generated_at": datetime.utcnow().isoformat(),
            "personalized": False,
            "rag_enabled": False
        }


# Global instance
_rag_system = None

def get_rag_system() -> RAGFeedbackSystem:
    """Get or create global RAG system instance"""
    global _rag_system
    if _rag_system is None:
        _rag_system = RAGFeedbackSystem()
    return _rag_system
