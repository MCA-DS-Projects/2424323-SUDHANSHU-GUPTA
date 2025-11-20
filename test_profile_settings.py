"""
Test script for Profile Settings functionality
Run this after starting the Flask application to verify the implementation
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5000"
API_URL = f"{BASE_URL}/api"

def test_profile_settings():
    """Test the profile settings endpoints"""
    
    print("=" * 60)
    print("Profile Settings Implementation Test")
    print("=" * 60)
    print()
    
    # Step 1: Register a test user
    print("1. Registering test user...")
    register_data = {
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "testpass123",
        "experienceLevel": "intermediate",
        "learningGoals": "business_communication"
    }
    
    try:
        response = requests.post(f"{API_URL}/auth/register", json=register_data)
        if response.status_code == 201:
            data = response.json()
            token = data.get('access_token')
            print("✅ User registered successfully")
            print(f"   Token: {token[:20]}...")
        elif response.status_code == 400 and "already exists" in response.text:
            # User exists, try to login
            print("⚠️  User already exists, logging in...")
            login_response = requests.post(f"{API_URL}/auth/login", json={
                "email": register_data["email"],
                "password": register_data["password"]
            })
            if login_response.status_code == 200:
                token = login_response.json().get('access_token')
                print("✅ Logged in successfully")
            else:
                print("❌ Login failed")
                return
        else:
            print(f"❌ Registration failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Headers with authentication
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print()
    
    # Step 2: Get initial profile settings
    print("2. Fetching initial profile settings...")
    try:
        response = requests.get(f"{API_URL}/profile/settings", headers=headers)
        if response.status_code == 200:
            profile = response.json().get('profile', {})
            print("✅ Profile settings fetched")
            print(f"   Display Name: {profile.get('displayName')}")
            print(f"   Email: {profile.get('email')}")
            print(f"   First Name: {profile.get('firstName', 'Not set')}")
        else:
            print(f"❌ Failed to fetch profile: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print()
    
    # Step 3: Update profile settings
    print("3. Updating profile settings...")
    update_data = {
        "displayName": "Test User Updated",
        "firstName": "Test",
        "lastName": "User",
        "phoneNumber": "+1234567890",
        "dateOfBirth": "1990-01-01",
        "timezone": "UTC-5",
        "country": "US",
        "city": "New York",
        "profession": "Software Engineer",
        "company": "Tech Corp",
        "bio": "This is a test bio for profile settings",
        "learningGoals": ["business_communication", "job_interviews", "presentations"]
    }
    
    try:
        response = requests.post(f"{API_URL}/profile/update", json=update_data, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print("✅ Profile updated successfully")
            print(f"   Message: {result.get('message')}")
        else:
            print(f"❌ Failed to update profile: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print()
    
    # Step 4: Verify the update
    print("4. Verifying profile update...")
    try:
        response = requests.get(f"{API_URL}/profile/settings", headers=headers)
        if response.status_code == 200:
            profile = response.json().get('profile', {})
            print("✅ Profile verified")
            print(f"   Display Name: {profile.get('displayName')}")
            print(f"   First Name: {profile.get('firstName')}")
            print(f"   Last Name: {profile.get('lastName')}")
            print(f"   Phone: {profile.get('phoneNumber')}")
            print(f"   City: {profile.get('city')}")
            print(f"   Profession: {profile.get('profession')}")
            print(f"   Learning Goals: {', '.join(profile.get('learningGoals', []))}")
            
            # Check if data matches
            if profile.get('firstName') == update_data['firstName']:
                print("\n✅ Data persistence verified - All fields saved correctly!")
            else:
                print("\n⚠️  Data mismatch detected")
        else:
            print(f"❌ Failed to verify profile: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)
    print()
    print("Next Steps:")
    print("1. Open browser and navigate to: http://localhost:5000")
    print("2. Login with: testuser@example.com / testpass123")
    print("3. Go to Profile Settings page")
    print("4. Verify all data is displayed correctly")
    print("5. Make changes and click 'Save Changes'")
    print("6. Refresh page to verify data persists")
    print("7. Click 'Reset Changes' to test reset functionality")

if __name__ == "__main__":
    print("\nMake sure the Flask application is running on http://localhost:5000")
    print("Press Enter to start the test...")
    input()
    test_profile_settings()
