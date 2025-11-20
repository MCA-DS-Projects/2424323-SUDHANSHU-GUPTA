from datetime import datetime
from bson import ObjectId
import bcrypt
import jwt
from flask import current_app

class User:
    def __init__(self, db):
        self.collection = db.users
    
    def create_user(self, user_data):
        """Create a new user"""
        # Hash password
        password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt())
        
        user = {
            'name': user_data['name'],
            'email': user_data['email'],
            'password_hash': password_hash,
            'experience_level': user_data.get('experienceLevel', 'beginner'),
            'learning_goals': user_data.get('learningGoals', 'general'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'is_active': True
        }
        
        result = self.collection.insert_one(user)
        user['_id'] = result.inserted_id
        return user
    
    def find_by_email(self, email):
        """Find user by email"""
        return self.collection.find_one({'email': email})
    
    def find_by_id(self, user_id):
        """Find user by ID"""
        return self.collection.find_one({'_id': ObjectId(user_id)})
    
    def verify_password(self, user, password):
        """Verify user password"""
        return bcrypt.checkpw(password.encode('utf-8'), user['password_hash'])
    
    def generate_token(self, user):
        """Generate JWT token for user"""
        payload = {
            'user_id': str(user['_id']),
            'email': user['email'],
            'exp': datetime.utcnow().timestamp() + 86400  # 24 hours
        }
        return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    
    def verify_token(self, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

class Session:
    def __init__(self, db):
        self.collection = db.sessions
    
    def create_session(self, session_data):
        """Create a new session"""
        session = {
            'user_id': ObjectId(session_data['user_id']),
            'session_type': session_data['session_type'],
            'data': session_data['data'],
            'score': session_data.get('score'),
            'duration': session_data.get('duration'),
            'created_at': datetime.utcnow()
        }
        
        result = self.collection.insert_one(session)
        return result.inserted_id
    
    def get_user_sessions(self, user_id, session_type=None, limit=10):
        """Get user sessions"""
        query = {'user_id': ObjectId(user_id)}
        if session_type:
            query['session_type'] = session_type
        
        return list(self.collection.find(query).sort('created_at', -1).limit(limit))