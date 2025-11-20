# RAG + LangChain Implementation Guide

## Overview
This guide explains how to implement RAG (Retrieval-Augmented Generation) with LangChain to provide personalized, dynamic AI feedback for ProSpeak AI users.

## What is RAG?

**RAG (Retrieval-Augmented Generation)** combines:
1. **Retrieval**: Finding relevant examples from a knowledge base
2. **Generation**: Using AI to create personalized responses based on those examples

## Architecture

```
User Session Data
       ↓
   RAG System
       ↓
   ┌─────────────────┐
   │ 1. Embed Query  │ → Convert user data to vectors
   └─────────────────┘
           ↓
   ┌─────────────────┐
   │ 2. Search DB    │ → Find similar feedback examples
   └─────────────────┘
           ↓
   ┌─────────────────┐
   │ 3. Generate     │ → Create personalized feedback
   └─────────────────┘
           ↓
   Personalized Feedback
```

## Installation

### Step 1: Install Required Packages

```bash
pip install langchain==0.1.0
pip install openai==1.6.1
pip install faiss-cpu==1.7.4
pip install tiktoken==0.5.2
```

### Step 2: Set Up OpenAI API Key

Add to your `.env` file:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Implementation

### 1. Create RAG Feedback System

The system is already created in `app/utils/rag_feedback_system.py`. Here's how it works:

#### Key Components:

**a) Example Feedback Database**
- Stores high-quality feedback examples
- Categorized by: type, score range, user level
- Used as templates for generating new feedback

**b) Vector Embeddings**
- Converts feedback examples to numerical vectors
- Enables semantic search (finding similar examples)

**c) LangChain QA Chain**
- Retrieves relevant examples
- Generates personalized feedback using GPT-3.5

### 2. Add Example Feedback

Create `app/data/feedback_examples.json`:

```json
{
  "pronunciation_examples": [
    {
      "category": "pronunciation",
      "score_range": "85-100",
      "user_level": "advanced",
      "example": "Excellent pronunciation! Your articulation is very clear..."
    },
    {
      "category": "pronunciation",
      "score_range": "70-84",
      "user_level": "intermediate",
      "example": "Good pronunciation overall! Focus on 'th' sounds..."
    }
  ],
  "fluency_examples": [
    {
      "category": "fluency",
      "score_range": "85-100",
      "user_level": "advanced",
      "example": "Outstanding fluency! Your speech flows naturally..."
    }
  ],
  "interview_examples": [
    {
      "category": "interview",
      "score_range": "85-100",
      "user_level": "advanced",
      "example": "Excellent interview response! You used STAR method..."
    }
  ]
}
```

### 3. Integrate with API

Update `app/routes/api.py`:

```python
from app.utils.rag_feedback_system import get_rag_system

@api_bp.route('/audio/analyze-ai', methods=['POST'])
@token_required
def analyze_audio_with_ai(current_user):
    try:
        data = request.get_json()
        
        # Get RAG system
        rag_system = get_rag_system()
        
        # Prepare user data
        user_data = {
            'name': current_user['name'],
            'experience_level': current_user['experience_level'],
            'learning_goals': current_user['learning_goals'],
            'total_sessions': current_user.get('total_sessions', 0),
            'average_score': calculate_average_score(current_user['id'])
        }
        
        # Prepare session data
        session_data = {
            'type': data.get('analysis_type', 'pronunciation'),
            'transcript': data.get('transcript', ''),
            'duration': data.get('duration', 0)
        }
        
        # Prepare performance data
        performance_data = {
            'score': calculate_score(data.get('transcript', '')),
            'accuracy': calculate_accuracy(data.get('transcript', ''))
        }
        
        # Generate personalized feedback using RAG
        feedback = rag_system.generate_feedback(
            user_data=user_data,
            session_data=session_data,
            performance_data=performance_data
        )
        
        return jsonify({
            'success': True,
            'feedback': feedback,
            'rag_enabled': feedback.get('rag_enabled', False)
        }), 200
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
```

### 4. Frontend Integration

The frontend already handles the feedback display. The RAG system works transparently in the background.

## How It Works

### Example Flow:

1. **User completes audio practice**
   - Transcript: "The project was complete ahead of schedule"
   - Score: 85/100
   - User level: Intermediate

2. **RAG System Processes**:
   ```python
   # Step 1: Create query embedding
   query = "pronunciation feedback for intermediate user, score 85"
   
   # Step 2: Search vector database
   similar_examples = vector_store.similarity_search(query, k=3)
   # Returns: 3 most similar feedback examples
   
   # Step 3: Generate personalized feedback
   feedback = llm.generate(
       context=similar_examples,
       user_data=user_info,
       performance=scores
   )
   ```

3. **Output**:
   ```
   Great job, John! Your pronunciation shows solid progress.
   
   Strengths:
   - Clear enunciation of most sounds
   - Good word stress on "project" and "complete"
   
   Areas to improve:
   - Practice the 'th' sound in "the"
   - Work on linking words smoothly
   
   Recommendation: Try recording yourself daily and compare
   with native speakers. Focus on the 'th' sound exercises.
   ```

## Benefits of RAG

### 1. **Personalized Feedback**
- Uses user's name
- Considers their level and history
- Adapts to their learning goals

### 2. **Consistent Quality**
- Based on high-quality examples
- Maintains professional tone
- Follows proven feedback patterns

### 3. **Scalable**
- Add new examples easily
- System learns from patterns
- No manual feedback writing needed

### 4. **Context-Aware**
- Considers user's progress
- Adapts to session type
- References previous performance

## Adding New Feedback Examples

### Method 1: Via Code

```python
from app.utils.rag_feedback_system import get_rag_system

rag_system = get_rag_system()

rag_system.add_feedback_example(
    category="pronunciation",
    score_range="60-69",
    example="""
    You're making progress! Focus on these areas:
    - Practice vowel sounds daily
    - Use a mirror to watch mouth position
    - Record and listen to yourself
    """,
    user_level="beginner"
)
```

### Method 2: Via JSON File

Add to `feedback_examples.json` and reload the system.

## Testing

### Test the RAG System:

```python
# test_rag.py
from app.utils.rag_feedback_system import RAGFeedbackSystem

# Initialize
rag = RAGFeedbackSystem(openai_api_key="your_key")

# Test data
user_data = {
    'name': 'John',
    'experience_level': 'intermediate',
    'learning_goals': 'interview preparation',
    'total_sessions': 15,
    'average_score': 78
}

session_data = {
    'type': 'pronunciation',
    'transcript': 'The project was complete ahead of schedule',
    'duration': 30
}

performance_data = {
    'score': 85,
    'accuracy': 90
}

# Generate feedback
feedback = rag.generate_feedback(user_data, session_data, performance_data)

print(feedback['feedback_text'])
print(f"Suggestions: {feedback['suggestions']}")
print(f"RAG Enabled: {feedback['rag_enabled']}")
```

## Monitoring

### Check if RAG is Working:

```python
# In your API response
{
    "feedback": {
        "feedback_text": "...",
        "rag_enabled": true,  # ← Should be true
        "personalized": true   # ← Should be true
    }
}
```

### Fallback Behavior:

If RAG fails (no API key, error, etc.), the system automatically falls back to basic feedback generation.

## Cost Considerations

### OpenAI API Costs:

- **Embeddings**: ~$0.0001 per 1K tokens
- **GPT-3.5-Turbo**: ~$0.002 per 1K tokens
- **Average cost per feedback**: ~$0.01

### Optimization Tips:

1. **Cache embeddings**: Don't re-embed same examples
2. **Limit context**: Use k=3 (3 examples) instead of k=10
3. **Use GPT-3.5**: Cheaper than GPT-4, still good quality
4. **Batch requests**: Process multiple feedbacks together

## Troubleshooting

### Issue: "LangChain not installed"

**Solution**:
```bash
pip install langchain openai faiss-cpu
```

### Issue: "OpenAI API key not found"

**Solution**:
Add to `.env`:
```
OPENAI_API_KEY=sk-...
```

### Issue: "RAG system not initialized"

**Check**:
1. API key is valid
2. LangChain is installed
3. Check console for error messages

### Issue: "Feedback is generic, not personalized"

**Check**:
1. `rag_enabled` should be `true` in response
2. Add more example feedback
3. Verify user data is being passed correctly

## Advanced Features

### 1. User-Specific Learning

Track what feedback works best for each user:

```python
# Store feedback effectiveness
feedback_effectiveness = {
    'user_id': user_id,
    'feedback_id': feedback_id,
    'user_rating': 5,  # User rates feedback
    'improvement': 10  # Score improvement after feedback
}
```

### 2. Dynamic Example Selection

Choose examples based on user's learning style:

```python
# Visual learners get more descriptive feedback
# Auditory learners get pronunciation-focused feedback
# Kinesthetic learners get practice-oriented feedback
```

### 3. Multi-Language Support

Add feedback examples in multiple languages:

```python
feedback_examples_es = [
    {
        "category": "pronunciation",
        "language": "es",
        "example": "¡Excelente pronunciación!..."
    }
]
```

## Next Steps

1. ✅ Install dependencies
2. ✅ Set up OpenAI API key
3. ✅ Test RAG system
4. ✅ Add more feedback examples
5. ✅ Monitor feedback quality
6. ✅ Collect user feedback
7. ✅ Iterate and improve

---

**Status**: Ready for implementation
**Estimated Setup Time**: 30 minutes
**Estimated Cost**: ~$0.01 per feedback generation
