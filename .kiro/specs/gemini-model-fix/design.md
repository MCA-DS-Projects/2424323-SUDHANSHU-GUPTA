# Design Document

## Overview

This design addresses the Gemini API 404 error by updating all model references to use currently supported model names. The solution centralizes model configuration and updates all endpoints that use Gemini to reference the correct model.

Based on Google's Gemini API documentation (as of November 2024), the correct model names are:
- `gemini-1.5-flash` - Fast, efficient model for most tasks
- `gemini-1.5-pro` - More capable model for complex tasks
- `gemini-2.0-flash-exp` - Experimental 2.0 flash model (may not be stable)

The error indicates that `gemini-pro` (without version) is deprecated and `gemini-2.0-flash-exp` may not be available in the v1beta API.

## Architecture

### Current State

The application currently has:
1. Multiple hardcoded model names scattered across `app/routes/api.py`
2. Model instantiation at the endpoint level
3. No centralized configuration for Gemini models
4. Inconsistent model names: `gemini-pro` and `gemini-2.0-flash-exp`

### Proposed State

1. Centralized model configuration in `app/config.py`
2. Helper function to get configured Gemini model
3. All endpoints use the helper function
4. Consistent model name across all features
5. Easy to update in one place

## Components and Interfaces

### 1. Configuration Module (`app/config.py`)

Add Gemini model configuration:

```python
# Gemini AI Configuration
GEMINI_MODEL_NAME = 'gemini-1.5-flash'  # Fast, reliable model
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
```

### 2. Gemini Helper Module (`app/utils/gemini_helper.py`)

Create a new utility module for Gemini operations:

```python
def get_gemini_model():
    """
    Get configured Gemini model instance
    Returns: GenerativeModel instance or None if not configured
    Raises: Exception if API key missing or model invalid
    """
    pass

def is_gemini_available():
    """
    Check if Gemini is properly configured
    Returns: bool
    """
    pass
```

### 3. API Routes Updates (`app/routes/api.py`)

Update all endpoints that use Gemini:
- `/audio/generate-phrase` (line ~1936)
- `/interview/generate-question` (line ~1600)
- `/conversation/start` (line ~2227)
- `/conversation/continue` (line ~2295)
- `/conversation/quick-responses` (line ~2397)

Each endpoint should:
1. Import the helper function
2. Use `get_gemini_model()` instead of direct instantiation
3. Handle exceptions gracefully

## Data Models

No new data models required. Existing conversation and session models remain unchanged.

## Error Handling

### Model Not Found Error (404)

**Current Behavior:**
- Application crashes with 404 error
- User sees generic error message
- No fallback behavior

**New Behavior:**
1. Helper function validates model name before use
2. If model invalid, log clear error with model name
3. Return user-friendly error message
4. Suggest checking API documentation for valid models

### API Key Missing

**Current Behavior:**
- Inconsistent error handling across endpoints

**New Behavior:**
1. Centralized check in helper function
2. Clear error message: "Gemini API key not configured"
3. Instructions to add key to .env file

### Import Error

**Current Behavior:**
- Try/except blocks in each endpoint

**New Behavior:**
1. Check in helper function
2. Clear error: "google-generativeai package not installed"
3. Instructions: "pip install google-generativeai"

## Testing Strategy

### Manual Testing

1. **Test with valid model name:**
   - Start conversation in Fluency Coach
   - Verify greeting is generated
   - Send message and verify response
   - Check console for success logs

2. **Test error scenarios:**
   - Remove API key from .env
   - Verify clear error message
   - Restore API key
   - Verify functionality restored

3. **Test all affected endpoints:**
   - Audio phrase generation
   - Interview question generation
   - Conversation start
   - Conversation continue
   - Quick responses

### Validation Checklist

- [ ] No 404 model not found errors
- [ ] All Gemini endpoints work correctly
- [ ] Error messages are clear and actionable
- [ ] Console logs show correct model name
- [ ] Configuration is centralized
- [ ] Documentation is updated

## Implementation Notes

### Model Selection Rationale

**Recommended: `gemini-1.5-flash`**
- Stable and well-supported
- Fast response times
- Good for conversational AI
- Lower cost than Pro model
- Suitable for all current use cases

**Alternative: `gemini-1.5-pro`**
- More capable for complex tasks
- Higher cost
- Slower response times
- Overkill for current use cases

**Not Recommended: `gemini-2.0-flash-exp`**
- Experimental model
- May not be available in all API versions
- Could be deprecated without notice
- Causing current 404 errors

### Migration Path

1. Add configuration to `app/config.py`
2. Create `app/utils/gemini_helper.py`
3. Update endpoints one by one
4. Test each endpoint after update
5. Remove old model instantiation code
6. Update documentation

### Backward Compatibility

No breaking changes for users. This is an internal implementation fix that maintains the same API interface.

## Security Considerations

- API key remains in environment variables (secure)
- No changes to authentication or authorization
- Model name is not user-configurable (prevents injection)

## Performance Considerations

- `gemini-1.5-flash` is optimized for speed
- Centralized model instance creation may allow for connection pooling in future
- No performance degradation expected

## Documentation Updates

Update `GEMINI_SETUP_GUIDE.md`:
- Change references from `gemini-pro` to `gemini-1.5-flash`
- Update model name in examples
- Add troubleshooting section for 404 errors
- Document how to change model name in config
