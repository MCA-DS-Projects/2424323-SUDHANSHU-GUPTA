# Gemini AI Setup Guide for Fluency Coach

## Overview
This guide ensures your Fluency Coach uses Gemini AI for natural, context-aware conversations.

## Current Status
✅ Gemini API key is configured in `.env`
✅ `google-generativeai` package is in `requirements.txt`
✅ Endpoints updated to require Gemini (no fallback)

## Setup Steps

### 1. Install Required Package

```bash
pip install google-generativeai
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Verify API Key

Check your `.env` file:
```bash
GEMINI_API_KEY=AIzaSyC8l10T-wI78T_wcc72jciDSkHsiAQxOWM
```

✅ Your API key is already configured!

### 3. Restart Flask Application

```bash
python run.py
```

## How It Works Now

### Start Conversation
When you open Fluency Coach:

1. **Frontend calls**: `POST /api/conversation/start`
2. **Backend**:
   - Checks for Gemini API key
   - If missing: Returns fallback response
   - If present: Uses Gemini Pro (models/gemini-pro) to generate greeting
3. **Response**: Natural AI-generated greeting

**Console Output:**
```
🤖 Using Gemini API key: AIzaSyC8l10T-wI78T...
📝 Generating greeting with Gemini...
✅ Gemini response: Hi! I'm excited to practice English...
```

### Continue Conversation
When you send a message:

1. **Frontend calls**: `POST /api/conversation/continue`
2. **Backend**:
   - Checks for Gemini API key
   - If missing: Returns error (no fallback)
   - If present: Uses Gemini with conversation history
3. **Response**: Context-aware AI response

**Example:**
```
User: "I'm feeling tired today"
Gemini: "I understand. It sounds like you've had a lot going on. What's been keeping you so busy?"
```

**Console Output:**
```
🤖 Using Gemini for conversation response...
📝 Generating response for: I'm feeling tired today...
✅ Gemini response: I understand. It sounds like you've had...
```

## Error Handling

### If Gemini API Key Missing

**Error Response:**
```json
{
  "success": false,
  "error": "Gemini API key not configured. Please add GEMINI_API_KEY to your .env file."
}
```

**User sees**: Error message asking to configure API key

### If Package Not Installed

**Error Response:**
```json
{
  "success": false,
  "error": "Gemini AI package not installed. Please run: pip install google-generativeai"
}
```

**Console Output:**
```
❌ google-generativeai package not installed: No module named 'google.generativeai'
```

**Solution:**
```bash
pip install google-generativeai
```

### If API Error

**Error Response:**
```json
{
  "success": false,
  "error": "Gemini AI error: [error details]"
}
```

**Console Output:**
```
❌ Gemini error: [detailed error message]
[Full stack trace]
```

## Testing

### 1. Check Package Installation

```bash
python -c "import google.generativeai; print('✅ Package installed')"
```

**Expected Output:**
```
✅ Package installed
```

### 2. Test API Key

```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', os.getenv('GEMINI_API_KEY')[:20] + '...')"
```

**Expected Output:**
```
API Key: AIzaSyC8l10T-wI78T...
```

### 3. Start Application

```bash
python run.py
```

**Expected Console Output:**
```
✅ Connected to MongoDB: prospeak_ai
✅ Database indexes created
🗄️  Database mode: MongoDB
 * Running on http://127.0.0.1:5000
```

### 4. Test Fluency Coach

1. **Login** to application
2. **Go to Fluency Coach**
3. **Check browser console** (F12):
   ```
   Starting Gemini conversation...
   Making API request to: http://localhost:5000/api/conversation/start
   Response status: 200
   ```

4. **Check Flask console**:
   ```
   🤖 Using Gemini API key: AIzaSyC8l10T-wI78T...
   📝 Generating greeting with Gemini...
   ✅ Gemini response: Hi! I'm excited to practice English...
   ```

5. **Send a message**: "I'm feeling tired today"

6. **Check Flask console**:
   ```
   🤖 Using Gemini for conversation response...
   📝 Generating response for: I'm feeling tired today...
   ✅ Gemini response: I understand. It sounds like you've had...
   ```

7. **Verify response** is contextual and natural

## Conversation Examples

### Example 1: Tired/Stressed
**User**: "I'm feeling tired today"
**Gemini**: "I understand. It sounds like you've had a lot going on. What's been keeping you so busy?"

### Example 2: Work Discussion
**User**: "I have a big presentation tomorrow"
**Gemini**: "That sounds important! Presentations can be nerve-wracking. What topic are you presenting on, and how are you preparing for it?"

### Example 3: Learning Goals
**User**: "I want to improve my English for job interviews"
**Gemini**: "That's a great goal! Job interviews can be challenging. What kind of positions are you applying for, and what aspects of interview English do you find most difficult?"

### Example 4: Casual Conversation
**User**: "I went to the park today"
**Gemini**: "That sounds lovely! What did you enjoy most about your time at the park? Did you do anything special there?"

## Troubleshooting

### Issue: "Gemini API key not configured"

**Solution:**
1. Check `.env` file has: `GEMINI_API_KEY=your-key-here`
2. Restart Flask app
3. Try again

### Issue: "Package not installed"

**Solution:**
```bash
pip install google-generativeai
```

### Issue: API Rate Limit

**Error**: "Resource exhausted"

**Solution:**
- Gemini has rate limits
- Free tier: 60 requests/minute
- Wait a moment and try again
- Or upgrade to paid tier

### Issue: Invalid API Key

**Error**: "API key not valid"

**Solution:**
1. Get new API key from: https://makersuite.google.com/app/apikey
2. Update `.env` file
3. Restart Flask app

### Issue: Conversation Not Natural

**Check:**
1. Is `source: 'gemini'` in response?
2. Check Flask console for Gemini logs
3. If seeing fallback responses, check for errors

## API Key Management

### Get Gemini API Key

1. Go to: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key
4. Add to `.env`: `GEMINI_API_KEY=your-key-here`

### Free Tier Limits

- **Requests**: 60 per minute
- **Tokens**: Generous limits
- **Cost**: FREE for most use cases

### Paid Tier (if needed)

- **Cost**: Very affordable
- **Limits**: Much higher
- **Billing**: Pay-as-you-go

## Benefits of Gemini AI

✅ **Natural Conversations**: Truly understands context
✅ **Context Awareness**: Remembers conversation history
✅ **Adaptive Responses**: Changes based on user's mood/topic
✅ **Encouraging**: Supportive and motivating
✅ **Cost-Effective**: Free tier is generous
✅ **Fast**: Gemini 2.0 Flash is very quick
✅ **Reliable**: Google's infrastructure

## Summary

### What Changed

**Before:**
- Had fallback responses if Gemini failed
- Could work without Gemini (keyword-based)

**After:**
- **Requires Gemini** - no fallback
- Returns error if API key missing
- Better error messages
- More logging for debugging

### Current Setup

✅ **API Key**: Configured in `.env`
✅ **Package**: In `requirements.txt`
✅ **Endpoints**: Updated to require Gemini
✅ **Error Handling**: Clear error messages
✅ **Logging**: Detailed console output

### Next Steps

1. **Install package**: `pip install google-generativeai`
2. **Restart app**: `python run.py`
3. **Test**: Go to Fluency Coach
4. **Verify**: Check console logs for Gemini usage

**Your Fluency Coach will now use Gemini AI for all conversations!** 🎉
