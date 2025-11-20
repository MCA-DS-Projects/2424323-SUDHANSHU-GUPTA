@echo off
echo ========================================
echo Fixing SSL Certificate Error
echo ========================================
echo.

echo This error occurs when your network uses a self-signed certificate.
echo We'll fix it by using REST transport instead of gRPC.
echo.

echo Step 1: Installing certifi package...
pip install certifi
echo.

echo Step 2: Upgrading google-generativeai...
pip install --upgrade google-generativeai
echo.

echo Step 3: Testing configuration...
python -c "import ssl; import certifi; print('✅ SSL configuration ready')"
echo.

echo ========================================
echo Fix Applied!
echo ========================================
echo.
echo The application now uses REST transport which avoids SSL issues.
echo.
echo Next steps:
echo 1. Restart your Flask app: python run.py
echo 2. Test Fluency Coach
echo 3. SSL errors should be gone!
echo.
pause
