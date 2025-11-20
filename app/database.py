from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
import bcrypt
from mongoengine import connect

load_dotenv()

# Load environment variables
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGO_DB_NAME")

# Connect using MongoEngine
connect(
    db=DB_NAME,
    host=MONGO_URI
)

# Connect using PyMongo
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()  # test connection
    db = client[DB_NAME]
    print(f"✅ Connected to MongoDB: {DB_NAME}")
    MONGODB_AVAILABLE = True
except Exception as e:
    print(f"⚠️  MongoDB not available: {e}")
    print("📁 Falling back to JSON file storage")
    db = None
    MONGODB_AVAILABLE = False


# Collections
users_collection = db['users'] if db is not None else None
sessions_collection = db['sessions'] if db is not None else None

# Helper functions for password hashing
def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed):
    """Verify a password against a hash"""
    if isinstance(hashed, str):
        hashed = hashed.encode('utf-8')
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

# User operations
def create_user(user_data):
    """Create a new user in the database"""
    if MONGODB_AVAILABLE:
        # Hash password before storing
        if 'password' in user_data:
            user_data['password_hash'] = hash_password(user_data['password']).decode('utf-8')
            del user_data['password']
        
        user_data['created_at'] = datetime.utcnow()
        result = users_collection.insert_one(user_data)
        user_data['_id'] = str(result.inserted_id)
        return user_data
    else:
        # Fallback to JSON file
        import json
        users_file = 'users_data.json'
        users = {}
        
        if os.path.exists(users_file):
            with open(users_file, 'r') as f:
                users = json.load(f)
        
        if 'password' in user_data:
            user_data['password_hash'] = hash_password(user_data['password']).decode('utf-8')
            del user_data['password']
        
        user_data['created_at'] = datetime.utcnow().isoformat()
        users[user_data['id']] = user_data
        
        with open(users_file, 'w') as f:
            json.dump(users, f, indent=2)
        
        return user_data

def find_user_by_email(email):
    """Find a user by email"""
    if MONGODB_AVAILABLE:
        user = users_collection.find_one({'email': email})
        if user:
            user['id'] = user.get('id', str(user['_id']))
            # Ensure password_hash is present
            if 'password_hash' not in user:
                print(f"⚠️  Warning: User {email} missing password_hash in MongoDB")
                return None
        return user
    else:
        # Fallback to JSON file
        import json
        users_file = 'users_data.json'
        
        if not os.path.exists(users_file):
            return None
        
        with open(users_file, 'r') as f:
            users = json.load(f)
        
        for user in users.values():
            if user['email'] == email:
                # Convert password_hash to bytes if it's a string
                if 'password_hash' in user and isinstance(user['password_hash'], str):
                    user['password_hash'] = user['password_hash'].encode('utf-8')
                return user
        
        return None

def find_user_by_id(user_id):
    """Find a user by ID"""
    if MONGODB_AVAILABLE:
        user = users_collection.find_one({'id': user_id})
        if user:
            user['id'] = user.get('id', str(user['_id']))
        return user
    else:
        # Fallback to JSON file
        import json
        users_file = 'users_data.json'
        
        if not os.path.exists(users_file):
            return None
        
        with open(users_file, 'r') as f:
            users = json.load(f)
        
        user = users.get(user_id)
        if user and 'password_hash' in user and isinstance(user['password_hash'], str):
            user['password_hash'] = user['password_hash'].encode('utf-8')
        
        return user

def update_user(user_id, update_data):
    """Update user data"""
    if MONGODB_AVAILABLE:
        users_collection.update_one(
            {'id': user_id},
            {'$set': update_data}
        )
        return True
    else:
        # Fallback to JSON file
        import json
        users_file = 'users_data.json'
        
        if not os.path.exists(users_file):
            return False
        
        with open(users_file, 'r') as f:
            users = json.load(f)
        
        if user_id in users:
            users[user_id].update(update_data)
            
            with open(users_file, 'w') as f:
                # Convert bytes to string for JSON
                users_to_save = {}
                for uid, user in users.items():
                    user_copy = user.copy()
                    if 'password_hash' in user_copy and isinstance(user_copy['password_hash'], bytes):
                        user_copy['password_hash'] = user_copy['password_hash'].decode('utf-8')
                    users_to_save[uid] = user_copy
                json.dump(users_to_save, f, indent=2)
            
            return True
        
        return False

# Session operations
def create_session(session_data):
    """Create a new session"""
    if MONGODB_AVAILABLE:
        session_data['created_at'] = datetime.utcnow()
        result = sessions_collection.insert_one(session_data)
        session_data['_id'] = str(result.inserted_id)
        return session_data
    else:
        # Fallback to JSON file
        import json
        sessions_file = 'sessions_data.json'
        sessions = []
        
        if os.path.exists(sessions_file):
            with open(sessions_file, 'r') as f:
                sessions = json.load(f)
        
        session_data['created_at'] = datetime.utcnow().isoformat()
        sessions.append(session_data)
        
        with open(sessions_file, 'w') as f:
            json.dump(sessions, f, indent=2)
        
        return session_data

def get_user_sessions(user_id, session_type=None):
    """Get all sessions for a user"""
    if MONGODB_AVAILABLE:
        query = {'user_id': user_id}
        if session_type:
            query['session_type'] = session_type
        
        sessions = list(sessions_collection.find(query).sort('created_at', -1))
        for session in sessions:
            session['id'] = session.get('id', str(session['_id']))
        return sessions
    else:
        # Fallback to JSON file
        import json
        sessions_file = 'sessions_data.json'
        
        if not os.path.exists(sessions_file):
            return []
        
        with open(sessions_file, 'r') as f:
            sessions = json.load(f)
        
        user_sessions = [s for s in sessions if s.get('user_id') == user_id]
        
        if session_type:
            user_sessions = [s for s in user_sessions if s.get('session_type') == session_type]
        
        # Convert created_at strings to datetime for sorting
        for session in user_sessions:
            if 'created_at' in session and isinstance(session['created_at'], str):
                try:
                    session['created_at'] = datetime.fromisoformat(session['created_at'])
                except:
                    pass
        
        user_sessions.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
        
        return user_sessions

def get_all_sessions():
    """Get all sessions"""
    if MONGODB_AVAILABLE:
        sessions = list(sessions_collection.find().sort('created_at', -1))
        for session in sessions:
            session['id'] = session.get('id', str(session['_id']))
        return sessions
    else:
        # Fallback to JSON file
        import json
        sessions_file = 'sessions_data.json'
        
        if not os.path.exists(sessions_file):
            return []
        
        with open(sessions_file, 'r') as f:
            return json.load(f)

# Initialize database indexes
if MONGODB_AVAILABLE:
    try:
        # Create indexes for better performance
        users_collection.create_index('email', unique=True)
        users_collection.create_index('id', unique=True)
        sessions_collection.create_index('user_id')
        sessions_collection.create_index('session_type')
        sessions_collection.create_index('created_at')
        print("✅ Database indexes created")
    except Exception as e:
        print(f"⚠️  Index creation warning: {e}")
