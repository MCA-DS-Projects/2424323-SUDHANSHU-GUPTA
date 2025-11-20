# Implementation Plan

- [ ] 1. Add Gemini configuration to config module
  - Add `GEMINI_MODEL_NAME` constant set to `'gemini-1.5-flash'` in `app/config.py`
  - Add `GEMINI_API_KEY` configuration from environment variable
  - Add comments explaining model selection
  - _Requirements: 1.1, 1.3, 3.1_

- [ ] 2. Create Gemini helper utility module
  - [ ] 2.1 Create `app/utils/gemini_helper.py` file
    - Implement `get_gemini_model()` function that returns configured GenerativeModel instance
    - Implement `is_gemini_available()` function to check if Gemini is properly configured
    - Add proper error handling for missing API key and import errors
    - Add logging for debugging
    - _Requirements: 1.1, 1.4, 3.2_

  - [ ]* 2.2 Write unit tests for helper functions
    - Test `get_gemini_model()` with valid configuration
    - Test `get_gemini_model()` with missing API key
    - Test `get_gemini_model()` with missing package
    - Test `is_gemini_available()` in various scenarios
    - _Requirements: 1.4, 3.4_

- [ ] 3. Update audio phrase generation endpoint
  - Replace hardcoded `genai.GenerativeModel('gemini-pro')` with `get_gemini_model()` call in `/audio/generate-phrase` endpoint (around line 1936)
  - Import helper function at top of file
  - Update error handling to use helper's exceptions
  - Test endpoint functionality
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3_

- [ ] 4. Update interview question generation endpoint
  - Replace hardcoded model instantiation with `get_gemini_model()` call in `/interview/generate-question` endpoint (around line 1600)
  - Update error handling
  - Test endpoint functionality
  - _Requirements: 1.1, 1.2_

- [ ] 5. Update conversation endpoints
  - [ ] 5.1 Update `/conversation/start` endpoint
    - Replace `genai.GenerativeModel('gemini-2.0-flash-exp')` with `get_gemini_model()` call (around line 2227)
    - Update error handling
    - Test conversation start functionality
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4_

  - [ ] 5.2 Update `/conversation/continue` endpoint
    - Replace model instantiation with `get_gemini_model()` call (around line 2295)
    - Update error handling
    - Test conversation continuation
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4_

  - [ ] 5.3 Update `/conversation/quick-responses` endpoint
    - Replace model instantiation with `get_gemini_model()` call (around line 2397)
    - Update error handling
    - Test quick responses generation
    - _Requirements: 1.1, 1.2_

- [ ] 6. Update documentation
  - Update `GEMINI_SETUP_GUIDE.md` to reference `gemini-1.5-flash` instead of `gemini-pro`
  - Add troubleshooting section for 404 model errors
  - Document how to change model name in configuration
  - Add note about supported model names
  - _Requirements: 3.3_

- [ ]* 7. Integration testing
  - Test complete flow: start conversation → send message → receive response
  - Test audio phrase generation with new model
  - Test interview question generation with new model
  - Verify no 404 errors in console
  - Test error scenarios (missing API key, invalid model)
  - _Requirements: 1.2, 2.1, 2.2, 2.3_
