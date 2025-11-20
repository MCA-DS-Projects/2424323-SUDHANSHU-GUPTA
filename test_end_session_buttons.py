"""
Test script to verify End Session buttons in Audio Practice and Fluency Coach pages
"""
import re
from pathlib import Path

def test_end_session_buttons():
    """Test that End Session buttons are properly configured"""
    
    print("🧪 Testing End Session Buttons\n")
    print("=" * 60)
    
    # Test Audio Practice Mode
    print("\n📝 Testing Audio Practice Mode...")
    audio_practice_file = Path("app/templates/user/audio_practice_mode.html")
    
    if not audio_practice_file.exists():
        print("❌ Audio practice file not found!")
        return False
    
    audio_content = audio_practice_file.read_text(encoding='utf-8')
    
    # Check for End Session button in HTML
    audio_button_pattern = r'<button[^>]*id=["\']endSessionBtn["\'][^>]*>.*?End Session.*?</button>'
    audio_buttons = re.findall(audio_button_pattern, audio_content, re.DOTALL | re.IGNORECASE)
    
    if audio_buttons:
        print(f"✅ Found {len(audio_buttons)} End Session button(s) in HTML")
        for i, btn in enumerate(audio_buttons, 1):
            print(f"   Button {i}: {btn[:100]}...")
    else:
        print("❌ No End Session button found in HTML")
        return False
    
    # Check for endPracticeSession function
    if 'function endPracticeSession' in audio_content or 'endPracticeSession = function' in audio_content:
        print("✅ endPracticeSession() function exists")
    else:
        print("❌ endPracticeSession() function not found")
        return False
    
    # Check for event listener setup
    if "addEventListener('click', endSessionHandler)" in audio_content:
        print("✅ Event listener properly attached with endSessionHandler")
    elif "endPracticeSession()" in audio_content:
        print("✅ endPracticeSession() is called in the code")
    else:
        print("⚠️  Event listener attachment unclear")
    
    # Check for preventDefault
    if "e.preventDefault()" in audio_content and "endSessionHandler" in audio_content:
        print("✅ preventDefault() is used to prevent default button behavior")
    else:
        print("⚠️  preventDefault() not found in endSessionHandler")
    
    # Check for redirect logic
    if "window.location.href = '/pages/user/user_dashboard.html'" in audio_content:
        print("✅ Redirect to dashboard is implemented")
    else:
        print("⚠️  Dashboard redirect not found")
    
    # Test Fluency Coach
    print("\n📝 Testing Fluency Coach...")
    fluency_file = Path("app/templates/user/fluency_coach.html")
    
    if not fluency_file.exists():
        print("❌ Fluency coach file not found!")
        return False
    
    fluency_content = fluency_file.read_text(encoding='utf-8')
    
    # Check for End Session button in HTML
    fluency_button_pattern = r'<button[^>]*id=["\']endSessionBtn["\'][^>]*>.*?End Session.*?</button>'
    fluency_buttons = re.findall(fluency_button_pattern, fluency_content, re.DOTALL | re.IGNORECASE)
    
    if fluency_buttons:
        print(f"✅ Found {len(fluency_buttons)} End Session button(s) in HTML")
        for i, btn in enumerate(fluency_buttons, 1):
            print(f"   Button {i}: {btn[:100]}...