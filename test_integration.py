#!/usr/bin/env python3
"""
Test the integrated AI audio analysis functionality
"""

from dotenv import load_dotenv
load_dotenv()

def test_integration():
    print("🎯 Testing Integrated AI Audio Analysis")
    print("=" * 50)
    
    # Test demo analyzer
    try:
        from app.utils.demo_analyzer import DemoAnalyzer
        demo = DemoAnalyzer()
        result = demo.analyze_audio("test", "pronunciation")
        
        if result['success']:
            print("✅ Demo mode working")
            print(f"   Score: {result['analysis']['score']}")
        else:
            print("❌ Demo mode failed")
            
    except Exception as e:
        print(f"❌ Demo mode error: {e}")
    
    # Test OpenAI analyzer (if available)
    try:
        from app.utils.audio_analyzer import AudioAnalyzer
        analyzer = AudioAnalyzer()
        print("✅ OpenAI analyzer available")
        
        # Test text analysis only (no audio)
        result = analyzer._analyze_transcript("Hello world", "pronunciation")
        if result and result.get('feedback_text'):
            print("✅ OpenAI text analysis working")
        else:
            print("⚠️  OpenAI may need credits")
            
    except Exception as e:
        print(f"⚠️  OpenAI analyzer: {e}")
    
    print("\n🎉 Integration Test Complete!")
    print("\nHow to use:")
    print("1. Start Flask: python run.py")
    print("2. Go to: http://localhost:5000/pages/user/audio_practice_mode.html")
    print("3. Click 'AI Analysis' button to enable AI mode")
    print("4. Record audio and get AI feedback!")

if __name__ == "__main__":
    test_integration()