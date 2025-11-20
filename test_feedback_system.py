#!/usr/bin/env python3
"""
Test the interview feedback system end-to-end
"""

import requests
import json
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:5000"

def test_feedback_system():
    print("🧪 Testing Interview Feedback System")
    print("=" * 60)
    
    # Step 1: Login to get token
    print("\n1️⃣ Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": "sguptaperfect2001@gmail.com",
            "password": "777777"
        }
    )
    
    if login_response.status_code == 200:
        token = login_response.json()['access_token']
        print("✅ Login successful")
    else:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Test interview response analysis
    print("\n2️⃣ Testing interview response analysis...")
    
    test_data = {
        "transcript": "I had a situation where a team member was not contributing to our project. I approached them privately to understand their concerns and worked with them to find a solution. As a result, we completed the project successfully and the team member became more engaged.",
        "question": "Tell me about a time when you had to work with a difficult team member.",
        "category": "Behavioral",
        "difficulty": "Medium"
    }
    
    analysis_response = requests.post(
        f"{BASE_URL}/api/interview/analyze-response",
        headers=headers,
        json=test_data
    )
    
    if analysis_response.status_code == 200:
        result = analysis_response.json()
        print("✅ Analysis successful!")
        print(f"   Session ID: {result.get('session_id')}")
        print(f"   Overall Score: {result.get('overall_score')}")
        print(f"   Demo Mode: {result.get('demo_mode')}")
        print(f"   Feedback Items: {len(result.get('feedback_components', {}).get('feedback_items', []))}")
        
        # Display feedback items
        if result.get('feedback_components'):
            print("\n   📋 Feedback Items:")
            for item in result['feedback_components'].get('feedback_items', [])[:3]:
                print(f"      • {item['title']}: {item['content'][:50]}...")
        
        print(f"\n   📝 Detailed Feedback Preview:")
        print(f"      {result.get('detailed_feedback', '')[:150]}...")
        
    else:
        print(f"❌ Analysis failed: {analysis_response.status_code}")
        print(f"   Error: {analysis_response.text}")
        return False
    
    # Step 3: Test question generation
    print("\n3️⃣ Testing dynamic question generation...")
    
    question_data = {
        "job_role": "Software Engineer",
        "industry": "Technology",
        "difficulty": "Medium",
        "question_count": 5
    }
    
    questions_response = requests.post(
        f"{BASE_URL}/api/interview/generate-questions",
        headers=headers,
        json=question_data
    )
    
    if questions_response.status_code == 200:
        result = questions_response.json()
        print("✅ Question generation successful!")
        print(f"   Generated: {len(result.get('questions', []))} questions")
        print(f"   Demo Mode: {result.get('demo_mode')}")
        
        # Display first 2 questions
        print("\n   📝 Sample Questions:")
        for i, q in enumerate(result.get('questions', [])[:2], 1):
            print(f"      {i}. [{q['category']}] {q['text'][:60]}...")
    else:
        print(f"❌ Question generation failed: {questions_response.status_code}")
        print(f"   Error: {questions_response.text}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All feedback system tests passed!")
    print("\n✨ The feedback system is working correctly!")
    print("\n📌 Next steps:")
    print("   1. Open: http://127.0.0.1:5000/pages/user/interview_simulator.html")
    print("   2. Click 'AI Mode' button")
    print("   3. Record your answer")
    print("   4. See dynamic AI feedback!")
    
    return True

if __name__ == "__main__":
    try:
        test_feedback_system()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Flask server is not running!")
        print("   Please start the server with: python run.py")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()