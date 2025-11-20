@echo off
echo ========================================
echo Installing Gemini AI for Fluency Coach
echo ========================================
echo.

echo Step 1: Installing google-generativeai package...
pip install google-generativeai
echo.

echo Step 2: Checking installation...
python -c "import google.generativeai; print('✅ Package installed successfully!')"
echo.

echo Step 3: Verifying API key...
python -c "import os; from dotenv import load_dotenv; load_dotenv(); key = os.getenv('GEMINI_API_KEY'); print('✅ API Key configured:', key[:20] + '...' if key else '❌ API Key not found')"
echo.

echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Make sure GEMINI_API_KEY is in your .env file
echo 2. Run: python run.py
echo 3. Go to Fluency Coach and start chatting!
echo.
pause
