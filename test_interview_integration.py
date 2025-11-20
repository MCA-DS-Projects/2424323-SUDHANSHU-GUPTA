#!/usr/bin/env python3
"""
Test the interview AI analysis integration
"""

from dotenv import load_dotenv
load_dotenv()

def test_interview_analysis():
    print("🎯 Testing Interview AI Analysis Integration")
    print("=" * 50)
    
    # Test demo analyzer for interview
    try:
        from app.utils.demo_analyzer import DemoAnalyzer
        demo = DemoAnalyzer()
        
        # Test interview analysis
        result = demo.analyze_audio("test", "interview")
        
        if result['success']:
            print("✅ Demo interview analysis working")
            print(f"   Score: {result['analysis']['score']}")
            print(f"   Feedback: {result['analysis']['feedback_text'][:100]}...")
        else:
            print("❌ Demo interview analysis failed")
            
    except Exception as e:
        print(f"❌ Demo mode error: {e}")
    
    # Test interview feedback parsing
    try:
        from app.routes.api import generate_demo_interview_feedback
        
        question = "Tell me about a time when you had to work with a difficult team member."
        transcript = "I had a situation where a team member was not contributing to our project. I approached them privately to understand their concerns and worked with them to find a solution. As a result, we completed the project successfully."
        
        feedback = generate_demo_interview_feedback(question, transcript, "Behavioral", "Medium")
        
        print("✅ Interview feedback generation working")
        print(f"   Score: {feedback['overall_score']}")
        print(f"   Feedback items: {len(feedback['feedback_items'])}")
        
    except Exception as e:
        print(f"❌ Feedback generation error: {e}")
    
    print("\n🎉 Interview Integration Test Complete!")
    print("\nHow to use:")
    print("1. Start Flask: python run.py")
    print("2. Go to: http://localhost:5000/pages/user/interview_simulator.html")
    print("3. Click 'AI Mode' button to enable AI analysis")
    print("4. Record your interview response")
    print("5. Get dynamic AI feedback based on your answer!")

if __name__ == "__main__":
    test_interview_analysis()