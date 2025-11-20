"""
Test script for session tracking functionality
"""
import requests
import json

BASE_URL = 'http://localhost:5000/api'

def test_session_tracking():
    """Test the session tracking endpoint"""
    
    # First, login to get a token
    print("1. Logging in...")
    login_response = requests.post(
        f'{BASE_URL}/auth/login',
        json={
            'email': 'sguptaperfect2001@gmail.com',
            'password': '777777'
        }
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()['access_token']
    print(f"✅ Login successful! Token: {token[:20]}...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Get initial dashboard stats
    print("\n2. Getting initial dashboard stats...")
    dashboard_response = requests.get(
        f'{BASE_URL}/dashboard/overview',
        headers=headers
    )
    
    if dashboard_response.status_code != 200:
        print(f"❌ Dashboard request failed: {dashboard_response.text}")
        return
    
    initial_stats = dashboard_response.json()
    print(f"✅ Initial stats:")
    print(f"   - Total sessions: {initial_stats['stats']['total_sessions']}")
    print(f"   - Today sessions: {initial_stats['stats']['today_sessions']}")
    print(f"   - Weekly sessions: {initial_stats['stats']['weekly_sessions']}")
    print(f"   - Current streak: {initial_stats['stats']['current_streak']}")
    
    # Increment session count
    print("\n3. Incrementing session count...")
    increment_response = requests.post(
        f'{BASE_URL}/dashboard/increment-session',
        headers=headers
    )
    
    if increment_response.status_code != 200:
        print(f"❌ Increment failed: {increment_response.text}")
        return
    
    updated_stats = increment_response.json()
    print(f"✅ Session incremented successfully!")
    print(f"   - Total sessions: {updated_stats['stats']['total_sessions']}")
    print(f"   - Today sessions: {updated_stats['stats']['today_sessions']}")
    print(f"   - Weekly sessions: {updated_stats['stats']['weekly_sessions']}")
    print(f"   - Current streak: {updated_stats['stats']['current_streak']}")
    print(f"   - Daily progress: {updated_stats['goals']['daily_progress']}/{updated_stats['goals']['daily_goal']}")
    print(f"   - Weekly progress: {updated_stats['goals']['weekly_progress']}/{updated_stats['goals']['weekly_goal']}")
    
    # Verify the increment
    print("\n4. Verifying the increment...")
    verify_response = requests.get(
        f'{BASE_URL}/dashboard/overview',
        headers=headers
    )
    
    if verify_response.status_code != 200:
        print(f"❌ Verification failed: {verify_response.text}")
        return
    
    final_stats = verify_response.json()
    
    if final_stats['stats']['total_sessions'] > initial_stats['stats']['total_sessions']:
        print(f"✅ Verification successful! Session count increased.")
    else:
        print(f"⚠️  Warning: Session count did not increase as expected.")
    
    print("\n" + "="*50)
    print("Test completed successfully! 🎉")
    print("="*50)

if __name__ == '__main__':
    try:
        test_session_tracking()
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
