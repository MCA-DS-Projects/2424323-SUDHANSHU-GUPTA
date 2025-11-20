"""
Reset Database Script
Cleans all users and sessions from MongoDB
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = 'prospeak_ai'

try:
    print("🔄 Connecting to MongoDB...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()  # Test connection
    db = client[DB_NAME]
    
    print(f"✅ Connected to MongoDB: {DB_NAME}")
    
    # Delete all users
    users_result = db.users.delete_many({})
    print(f"🗑️  Deleted {users_result.deleted_count} users")
    
    # Delete all sessions
    sessions_result = db.sessions.delete_many({})
    print(f"🗑️  Deleted {sessions_result.deleted_count} sessions")
    
    print("\n✅ Database cleaned successfully!")
    print("📝 You can now register a new account.")
    print("\n🚀 Start the app with: python run.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n💡 Make sure MongoDB is running:")
    print("   - Windows: Check Services for 'MongoDB Server'")
    print("   - Mac/Linux: Run 'sudo systemctl status mongod'")
