from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import jwt
from datetime import datetime, timedelta
import uuid
import os

# Import database module
from app.database import (
    create_user, find_user_by_email, find_user_by_id, update_user,
    create_session, get_user_sessions, get_all_sessions,
    hash_password, verify_password, MONGODB_AVAILABLE
)

print(f"🗄️  Database mode: {'MongoDB' if MONGODB_AVAILABLE else 'JSON Files'}")

# Helper functions for backward compatibility
def get_sessions_db():
    """Get all sessions (for backward compatibility)"""
    return get_all_sessions()

def save_session_to_db(session_data):
    """Save a session (for backward compatibility)"""
    return create_session(session_data)

def get_users_db():
    """Get all users as dict (for backward compatibility) - NOT RECOMMENDED"""
    # This is a fallback for old code, should be refactored
    import json
    import os
    if os.path.exists('users_data.json'):
        with open('users_data.json', 'r') as f:
            return json.load(f)
    return {}

def save_users_db(users_dict):
    """Save users dict (for backward compatibility) - NOT RECOMMENDED"""
    import json
    with open('users_data.json', 'w') as f:
        json.dump(users_dict, f, indent=2)

# Create proxy objects for backward compatibility
class SessionsProxy:
    def append(self, session_data):
        create_session(session_data)
    
    def __iter__(self):
        return iter(get_all_sessions())
    
    def __len__(self):
        return len(get_all_sessions())

class UserDataProxy:
    """Proxy for user data that auto-saves changes"""
    def __init__(self, user_id, user_data):
        self._user_id = user_id
        self._data = user_data
    
    def __getitem__(self, key):
        return self._data.get(key)
    
    def __setitem__(self, key, value):
        self._data[key] = value
        # Auto-save to database
        update_user(self._user_id, {key: value})
    
    def get(self, key, default=None):
        return self._data.get(key, default)
    
    def __contains__(self, key):
        return key in self._data
    
    def keys(self):
        return self._data.keys()
    
    def values(self):
        return self._data.values()
    
    def items(self):
        return self._data.items()

class UsersProxy:
    def __getitem__(self, user_id):
        user = find_user_by_id(user_id)
        if user:
            return UserDataProxy(user_id, user)
        return None
    
    def __setitem__(self, user_id, user_data):
        # This shouldn't be used, but keep for compatibility
        if isinstance(user_data, dict):
            update_user(user_id, user_data)
    
    def get(self, user_id, default=None):
        user = find_user_by_id(user_id)
        if user:
            return UserDataProxy(user_id, user)
        return default
    
    def __contains__(self, user_id):
        return find_user_by_id(user_id) is not None
    
    def values(self):
        # This is inefficient but needed for backward compatibility
        return get_users_db().values()
    
    def keys(self):
        return get_users_db().keys()

# Create global proxy objects
sessions_db = SessionsProxy()
users_db = UsersProxy()

# Also need save functions
def save_sessions(sessions):
    pass  # Sessions are saved automatically in create_session

def save_users(users):
    pass  # Users are saved automatically in update_user

api_bp = Blueprint('api', __name__, url_prefix='/api')

def generate_token(user):
    payload = {
        'user_id': user['id'],
        'email': user['email'],
        'exp': datetime.utcnow().timestamp() + 86400  # 24 hours
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
            payload = verify_token(token)
            
            if not payload:
                return jsonify({'error': 'Token is invalid'}), 401
            
            current_user = find_user_by_id(payload['user_id'])
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
                
        except Exception as e:
            return jsonify({'error': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

# Authentication routes
@api_bp.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        print(f"📝 Registration attempt: {data.get('email')}")
        
        # Validate required fields
        required_fields = ['name', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                print(f"❌ Missing field: {field}")
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user already exists
        existing_user = find_user_by_email(data['email'])
        if existing_user:
            print(f"❌ User already exists: {data['email']}")
            return jsonify({'error': 'User already exists'}), 400
        
        # Create user
        user_id = str(uuid.uuid4())
        user_data = {
            'id': user_id,
            'name': data['name'],
            'email': data['email'],
            'password': data['password'],  # Will be hashed in create_user
            'experience_level': data.get('experienceLevel', 'beginner'),
            'learning_goals': data.get('learningGoals', 'general'),
            'profile_picture': 'https://images.pexels.com/photos/2379004/pexels-photo-2379004.jpeg?auto=compress&cs=tinysrgb&w=150',
            'daily_goal': get_default_daily_goal(data.get('experienceLevel', 'beginner')),
            'weekly_goal': 7,
            'streak_count': 0,
            'total_sessions': 0,
            'last_session_date': None,
            'is_active': True,
            'preferences': {
                'reminder_time': '18:00',
                'difficulty_preference': 'adaptive',
                'focus_areas': []
            }
        }
        
        # Save to database
        user = create_user(user_data)
        
        # Verify user was created with password_hash
        print(f"🔍 Created user keys: {list(user.keys())}")
        if 'password_hash' not in user:
            print(f"❌ ERROR: password_hash not in created user!")
            return jsonify({'error': 'Failed to create user properly'}), 500
        
        # Generate token
        token = generate_token(user)
        
        response_data = {
            'message': 'Registration successful! Welcome to ProSpeak AI!',
            'access_token': token,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'experience_level': user['experience_level'],
                'learning_goals': user['learning_goals']
            }
        }
        print(f"✅ Registration successful for: {user['email']}")
        return jsonify(response_data), 201
        
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        print(f"🔐 Login attempt: {data.get('email')}")
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Find user
        user = find_user_by_email(data['email'])
        
        if not user:
            print(f"❌ User not found: {data.get('email')}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        print(f"✅ User found: {user['email']}")
        print(f"🔍 User data keys: {list(user.keys())}")
        
        # Check if password_hash exists
        if 'password_hash' not in user:
            print(f"❌ ERROR: password_hash missing for user: {user['email']}")
            print(f"🔍 User data: {user}")
            return jsonify({'error': 'Account data corrupted. Please contact support.'}), 500
        
        # Verify password
        password_valid = verify_password(data['password'], user['password_hash'])
        print(f"🔑 Password valid: {password_valid}")
        
        if not password_valid:
            print(f"❌ Invalid password for: {user['email']}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate token
        token = generate_token(user)
        
        response_data = {
            'message': 'Login successful! Welcome back!',
            'access_token': token,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'experience_level': user['experience_level'],
                'learning_goals': user['learning_goals']
            }
        }
        print(f"✅ Login successful for: {user['email']}")
        return jsonify(response_data), 200
        
    except KeyError as e:
        print(f"❌ KeyError in login: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Missing required field: {str(e)}'}), 500
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/auth/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    return jsonify({
        'user': {
            'id': current_user['id'],
            'name': current_user['name'],
            'email': current_user['email'],
            'experience_level': current_user['experience_level'],
            'learning_goals': current_user['learning_goals'],
            'profile_picture': current_user.get('profile_picture', 'https://images.pexels.com/photos/2379004/pexels-photo-2379004.jpeg?auto=compress&cs=tinysrgb&w=150')
        }
    }), 200

@api_bp.route('/profile/update-picture', methods=['POST'])
@token_required
def update_profile_picture(current_user):
    try:
        data = request.get_json()
        
        if not data.get('profile_picture'):
            return jsonify({'error': 'Profile picture URL is required'}), 400
        
        # Update user's profile picture in database
        user_id = current_user['id']
        if user_id in users_db:
            users_db[user_id]['profile_picture'] = data['profile_picture']
            save_users(users_db)
            
            return jsonify({
                'message': 'Profile picture updated successfully',
                'profile_picture': data['profile_picture']
            }), 200
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        print(f"Profile picture update error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/profile/update-goals', methods=['POST'])
@token_required
def update_user_goals(current_user):
    try:
        data = request.get_json()
        
        user_id = current_user['id']
        if user_id in users_db:
            # Update goals
            if 'daily_goal' in data:
                users_db[user_id]['daily_goal'] = max(1, min(10, int(data['daily_goal'])))
            
            if 'weekly_goal' in data:
                users_db[user_id]['weekly_goal'] = max(1, min(50, int(data['weekly_goal'])))
            
            if 'preferences' in data:
                current_prefs = users_db[user_id].get('preferences', {})
                current_prefs.update(data['preferences'])
                users_db[user_id]['preferences'] = current_prefs
            
            save_users(users_db)
            
            return jsonify({
                'message': 'Goals updated successfully',
                'daily_goal': users_db[user_id]['daily_goal'],
                'weekly_goal': users_db[user_id]['weekly_goal'],
                'preferences': users_db[user_id]['preferences']
            }), 200
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        print(f"Update goals error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/profile/settings', methods=['GET'])
@token_required
def get_profile_settings(current_user):
    """Get user profile settings"""
    try:
        user_id = current_user['id']
        user = find_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get profile settings from user data
        profile_settings = user.get('profile_settings', {})
        
        # Return profile data with settings
        return jsonify({
            'success': True,
            'profile': {
                'displayName': user.get('name', ''),
                'email': user.get('email', ''),
                'firstName': profile_settings.get('firstName', ''),
                'lastName': profile_settings.get('lastName', ''),
                'phoneNumber': profile_settings.get('phoneNumber', ''),
                'dateOfBirth': profile_settings.get('dateOfBirth', ''),
                'timezone': profile_settings.get('timezone', ''),
                'country': profile_settings.get('country', ''),
                'city': profile_settings.get('city', ''),
                'profession': profile_settings.get('profession', ''),
                'company': profile_settings.get('company', ''),
                'bio': profile_settings.get('bio', ''),
                'learningGoals': profile_settings.get('learningGoals', []),
                'profile_picture': user.get('profile_picture', ''),
                'emailVerified': user.get('email_verified', False)
            }
        }), 200
        
    except Exception as e:
        print(f"Get profile settings error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/profile/update', methods=['POST'])
@token_required
def update_profile_settings(current_user):
    """Update user profile settings"""
    try:
        data = request.get_json()
        user_id = current_user['id']
        
        print(f"📝 Updating profile for user: {user_id}")
        print(f"📦 Data received: {data}")
        
        # Prepare profile settings data
        profile_settings = {
            'firstName': data.get('firstName', ''),
            'lastName': data.get('lastName', ''),
            'phoneNumber': data.get('phoneNumber', ''),
            'dateOfBirth': data.get('dateOfBirth', ''),
            'timezone': data.get('timezone', ''),
            'country': data.get('country', ''),
            'city': data.get('city', ''),
            'profession': data.get('profession', ''),
            'company': data.get('company', ''),
            'bio': data.get('bio', ''),
            'learningGoals': data.get('learningGoals', []),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Update user data
        update_data = {
            'profile_settings': profile_settings
        }
        
        # Update display name if provided
        if data.get('displayName'):
            update_data['name'] = data['displayName']
        
        # Update in database
        success = update_user(user_id, update_data)
        
        if success:
            print(f"✅ Profile updated successfully for user: {user_id}")
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'profile': profile_settings
            }), 200
        else:
            print(f"❌ Failed to update profile for user: {user_id}")
            return jsonify({'success': False, 'error': 'Failed to update profile'}), 500
            
    except Exception as e:
        print(f"❌ Update profile error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/profile/remove-picture', methods=['POST'])
@token_required
def remove_profile_picture(current_user):
    """Remove user profile picture"""
    try:
        user_id = current_user['id']
        
        # Set to default picture
        default_picture = 'https://images.unsplash.com/photo-1584824486509-112e4181ff6b?q=80&w=2940&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D'
        
        update_user(user_id, {'profile_picture': default_picture})
        
        return jsonify({
            'success': True,
            'message': 'Profile picture removed successfully',
            'profile_picture': default_picture
        }), 200
        
    except Exception as e:
        print(f"Remove profile picture error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/dashboard/stats', methods=['GET'])
@token_required
def get_dashboard_stats(current_user):
    try:
        # Get detailed statistics for charts and analytics
        user_sessions = [s for s in sessions_db if s.get('user_id') == current_user['id']]
        
        # Last 30 days activity
        from datetime import timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_sessions = [s for s in user_sessions 
                          if s.get('created_at', datetime.utcnow()) >= thirty_days_ago]
        
        # Daily activity for the last 7 days
        daily_activity = {}
        for i in range(7):
            date = (datetime.utcnow() - timedelta(days=i)).date()
            day_sessions = [s for s in recent_sessions 
                           if s.get('created_at', datetime.utcnow()).date() == date]
            daily_activity[date.isoformat()] = len(day_sessions)
        
        # Exercise type breakdown
        exercise_breakdown = {}
        for session in user_sessions:
            exercise_type = session.get('exercise_type', 'general')
            exercise_breakdown[exercise_type] = exercise_breakdown.get(exercise_type, 0) + 1
        
        # Score progression (last 10 sessions)
        score_progression = []
        scored_sessions = [s for s in user_sessions if s.get('scores', {}).get('overall')]
        for session in scored_sessions[-10:]:
            score_progression.append({
                'date': session.get('created_at', datetime.utcnow()).isoformat(),
                'score': session.get('scores', {}).get('overall', 0),
                'exercise_type': session.get('exercise_type', 'general')
            })
        
        return jsonify({
            'daily_activity': daily_activity,
            'exercise_breakdown': exercise_breakdown,
            'score_progression': score_progression,
            'total_practice_time': sum(s.get('duration', 0) for s in user_sessions),
            'average_session_duration': sum(s.get('duration', 0) for s in user_sessions) / len(user_sessions) if user_sessions else 0
        }), 200
        
    except Exception as e:
        print(f"Dashboard stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Dashboard routes
@api_bp.route('/dashboard/overview', methods=['GET'])
@token_required
def dashboard_overview(current_user):
    try:
        # Get user sessions
        user_sessions = [s for s in sessions_db if s.get('user_id') == current_user['id']]
        recent_sessions = user_sessions[-5:] if user_sessions else []
        
        # Calculate dynamic stats
        today_sessions = get_today_sessions(current_user['id'], sessions_db)
        weekly_sessions = calculate_weekly_progress(current_user['id'], sessions_db)
        current_streak = calculate_streak(current_user['id'], sessions_db)
        
        # Update user's streak and total sessions
        users_db[current_user['id']]['streak_count'] = current_streak
        users_db[current_user['id']]['total_sessions'] = len(user_sessions)
        save_users(users_db)
        
        # Calculate scores and performance
        if user_sessions:
            scores = [s.get('scores', {}).get('overall', 0) for s in user_sessions if s.get('scores')]
            avg_score = sum(scores) / len(scores) if scores else 0
            best_score = max(scores) if scores else 0
            recent_avg = sum(scores[-5:]) / len(scores[-5:]) if len(scores) >= 5 else avg_score
        else:
            avg_score = 0
            best_score = 0
            recent_avg = 0
        
        # Daily goal progress
        daily_goal = current_user.get('daily_goal', 3)
        daily_progress = len(today_sessions)
        daily_progress_percentage = min(100, (daily_progress / daily_goal) * 100)
        
        # Weekly goal progress
        weekly_goal = current_user.get('weekly_goal', 7)
        weekly_progress_percentage = min(100, (weekly_sessions / weekly_goal) * 100)
        
        # Performance trend
        if len(user_sessions) >= 10:
            recent_scores = scores[-5:] if len(scores) >= 5 else scores
            older_scores = scores[-10:-5] if len(scores) >= 10 else scores[:-5] if len(scores) > 5 else []
            
            if older_scores:
                recent_avg_trend = sum(recent_scores) / len(recent_scores)
                older_avg_trend = sum(older_scores) / len(older_scores)
                trend = 'improving' if recent_avg_trend > older_avg_trend + 3 else 'declining' if recent_avg_trend < older_avg_trend - 3 else 'stable'
            else:
                trend = 'stable'
        else:
            trend = 'new' if len(user_sessions) < 3 else 'stable'
        
        return jsonify({
            'user': {
                'name': current_user['name'],
                'experience_level': current_user['experience_level'],
                'learning_goals': current_user['learning_goals'],
                'profile_picture': current_user.get('profile_picture')
            },
            'stats': {
                'total_sessions': len(user_sessions),
                'today_sessions': daily_progress,
                'weekly_sessions': weekly_sessions,
                'current_streak': current_streak,
                'average_score': round(avg_score, 1),
                'best_score': round(best_score, 1),
                'recent_average': round(recent_avg, 1)
            },
            'goals': {
                'daily_goal': daily_goal,
                'daily_progress': daily_progress,
                'daily_percentage': round(daily_progress_percentage, 1),
                'weekly_goal': weekly_goal,
                'weekly_progress': weekly_sessions,
                'weekly_percentage': round(weekly_progress_percentage, 1)
            },
            'performance': {
                'trend': trend,
                'improvement_rate': round(recent_avg - avg_score, 1) if avg_score > 0 else 0
            },
            'recent_sessions': [
                {
                    'id': session.get('id', str(uuid.uuid4())),
                    'type': session['session_type'],
                    'exercise_type': session.get('exercise_type', 'general'),
                    'score': session.get('scores', {}).get('overall', 0),
                    'duration': session.get('duration', 0),
                    'created_at': session['created_at'].isoformat() if isinstance(session.get('created_at'), datetime) else datetime.utcnow().isoformat()
                } for session in recent_sessions
            ]
        }), 200
        
    except Exception as e:
        print(f"Dashboard overview error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Audio Practice Routes
@api_bp.route('/audio/analyze-pronunciation', methods=['POST'])
@token_required
def analyze_pronunciation(current_user):
    try:
        data = request.get_json()
        
        if not data.get('transcript'):
            return jsonify({'error': 'Transcript is required'}), 400
        
        transcript = data['transcript']
        target_text = data.get('target_text', '')
        exercise_type = data.get('exercise_type', 'general')
        
        # Simple pronunciation analysis
        words = transcript.lower().split()
        target_words = target_text.lower().split() if target_text else words
        
        analysis = {
            'overall_score': min(95, max(60, 75 + len(words) * 2)),
            'confidence': min(100, max(50, 80 + len(words))),
            'fluency_score': min(100, max(60, 70 + len(words) * 3)),
            'word_count': len(words),
            'accuracy': calculate_accuracy(words, target_words),
            'feedback': generate_pronunciation_feedback(transcript, exercise_type),
            'suggestions': get_pronunciation_suggestions(exercise_type)
        }
        
        return jsonify(analysis), 200
        
    except Exception as e:
        print(f"Pronunciation analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Removed duplicate - using the new implementation below with Gemini integration

@api_bp.route('/audio/exercises', methods=['GET'])
@token_required
def get_audio_exercises(current_user):
    exercises = [
        {
            'id': 'word-stress',
            'name': 'Word Stress Practice',
            'description': 'Practice emphasizing the correct syllables',
            'difficulty': 'medium',
            'sample_text': 'The PROJECT was COMPLETE ahead of schedule.'
        },
        {
            'id': 'th-sounds',
            'name': 'TH Sounds',
            'description': 'Master the challenging TH pronunciation',
            'difficulty': 'hard',
            'sample_text': 'Think about the thick thread through the thin cloth.'
        },
        {
            'id': 'r-sounds',
            'name': 'R Sounds',
            'description': 'Perfect your R pronunciation',
            'difficulty': 'medium',
            'sample_text': 'The red rabbit ran rapidly around the rough rock.'
        },
        {
            'id': 'vowel-sounds',
            'name': 'Vowel Clarity',
            'description': 'Improve vowel pronunciation',
            'difficulty': 'easy',
            'sample_text': 'The cat sat on the mat with a fat rat.'
        }
    ]
    
    return jsonify({'exercises': exercises}), 200

@api_bp.route('/audio/user-history', methods=['GET'])
@token_required
def get_user_audio_history(current_user):
    try:
        # Get user's audio practice sessions
        user_sessions = [s for s in sessions_db if s.get('user_id') == current_user['id'] and s.get('session_type') == 'audio_practice']
        
        # Sort by date (most recent first)
        user_sessions.sort(key=lambda x: x.get('created_at', datetime.min), reverse=True)
        
        # Calculate statistics
        if user_sessions:
            scores = [s.get('scores', {}).get('overall', 0) for s in user_sessions]
            avg_score = sum(scores) / len(scores)
            best_score = max(scores)
            recent_trend = calculate_trend(scores[-10:] if len(scores) >= 10 else scores)
        else:
            avg_score = 0
            best_score = 0
            recent_trend = 'stable'
        
        return jsonify({
            'sessions': [
                {
                    'score': s.get('scores', {}).get('overall', 0),
                    'date': s.get('created_at', datetime.utcnow()).isoformat(),
                    'exerciseType': s.get('exercise_type', 'general'),
                    'duration': s.get('duration', 0)
                } for s in user_sessions[-20:]  # Last 20 sessions
            ],
            'statistics': {
                'total_sessions': len(user_sessions),
                'average_score': round(avg_score, 1),
                'best_score': best_score,
                'recent_trend': recent_trend
            }
        }), 200
        
    except Exception as e:
        print(f"Get user history error: {str(e)}")
        return jsonify({'sessions': [], 'statistics': {'total_sessions': 0, 'average_score': 0, 'best_score': 0, 'recent_trend': 'stable'}}), 200

def calculate_trend(scores):
    if len(scores) < 3:
        return 'stable'
    
    # Simple trend calculation
    recent_avg = sum(scores[-3:]) / 3
    older_avg = sum(scores[:-3]) / len(scores[:-3]) if len(scores) > 3 else recent_avg
    
    if recent_avg > older_avg + 5:
        return 'improving'
    elif recent_avg < older_avg - 5:
        return 'declining'
    else:
        return 'stable'

def calculate_accuracy(spoken_words, target_words):
    if not target_words:
        return 85  # Default score if no target
    
    matches = sum(1 for i, word in enumerate(spoken_words) 
                  if i < len(target_words) and word == target_words[i])
    
    return min(100, max(60, int((matches / len(target_words)) * 100)))

def generate_pronunciation_feedback(transcript, exercise_type):
    feedback = []
    
    if exercise_type == 'th-sounds':
        if 'th' in transcript.lower():
            feedback.append("Good job including TH sounds!")
        else:
            feedback.append("Try to include more TH sounds in your practice.")
    
    if exercise_type == 'r-sounds':
        r_count = transcript.lower().count('r')
        if r_count > 2:
            feedback.append("Excellent R sound practice!")
        else:
            feedback.append("Focus on pronouncing R sounds clearly.")
    
    if len(transcript.split()) > 5:
        feedback.append("Good sentence length for practice.")
    
    return feedback

def get_pronunciation_suggestions(exercise_type):
    suggestions = {
        'word-stress': [
            "Emphasize stressed syllables by making them louder and longer",
            "Practice with a metronome to maintain rhythm"
        ],
        'th-sounds': [
            "Place your tongue between your teeth for TH sounds",
            "Practice 'think' vs 'sink' to hear the difference"
        ],
        'r-sounds': [
            "Curl your tongue slightly without touching the roof of your mouth",
            "Practice 'red' vs 'led' to master the R sound"
        ],
        'vowel-sounds': [
            "Open your mouth wider for clear vowel sounds",
            "Practice minimal pairs like 'cat' vs 'cut'"
        ]
    }
    
    return suggestions.get(exercise_type, ["Keep practicing regularly for improvement"])

def get_default_daily_goal(experience_level):
    """Get default daily goal based on experience level"""
    goals = {
        'beginner': 2,      # 2 sessions per day
        'intermediate': 3,   # 3 sessions per day
        'advanced': 4,      # 4 sessions per day
        'native': 2         # 2 sessions per day for maintenance
    }
    return goals.get(experience_level, 2)

def generate_intelligent_response(user_message, conversation_history):
    """
    Generate intelligent contextual responses without AI API
    Analyzes message content and conversation flow to create natural responses
    """
    import random
    
    # Analyze the message
    message_lower = user_message.lower()
    words = message_lower.split()
    
    # Check conversation length for variety
    conv_length = len(conversation_history)
    
    # Topic detection
    topics = {
        'project': ['project', 'app', 'application', 'software', 'system', 'platform', 'tool'],
        'learning': ['learn', 'study', 'practice', 'improve', 'skill', 'training', 'education'],
        'english': ['english', 'speaking', 'language', 'fluency', 'pronunciation', 'vocabulary'],
        'interview': ['interview', 'job', 'career', 'professional', 'work', 'company'],
        'feeling': ['feel', 'feeling', 'think', 'believe', 'hope', 'want', 'like'],
        'help': ['help', 'assist', 'support', 'guide', 'teach', 'show'],
        'student': ['student', 'learner', 'user', 'people', 'person'],
        'ai': ['ai', 'artificial', 'intelligence', 'machine', 'learning', 'technology']
    }
    
    detected_topics = []
    for topic, keywords in topics.items():
        if any(keyword in message_lower for keyword in keywords):
            detected_topics.append(topic)
    
    # Question detection
    is_question = '?' in user_message
    
    # Generate response based on context
    responses = []
    
    # Topic-specific responses
    if 'project' in detected_topics:
        responses.extend([
            "That sounds like an interesting project! What inspired you to work on it?",
            "I'd love to hear more about your project. What are its main features?",
            "Projects like that can be really impactful. What's been the most challenging part?",
            "That's exciting! How long have you been working on this project?"
        ])
    
    if 'learning' in detected_topics or 'english' in detected_topics:
        responses.extend([
            "Learning English is such a valuable skill. What motivated you to improve?",
            "That's great that you're focused on learning! What methods work best for you?",
            "Improving language skills takes dedication. How often do you practice?",
            "English fluency opens so many doors. What are your goals?"
        ])
    
    if 'interview' in detected_topics:
        responses.extend([
            "Interview preparation is so important. What type of interviews are you preparing for?",
            "That's smart to practice interviews. What aspects do you find most challenging?",
            "Job interviews can be nerve-wracking. How do you usually prepare?",
            "Professional communication is key. What industry are you interested in?"
        ])
    
    if 'help' in detected_topics or 'student' in detected_topics:
        responses.extend([
            "It's wonderful that you want to help others! What inspired this passion?",
            "Helping students learn is so rewarding. What's your approach?",
            "That's a noble goal. How do you plan to make a difference?",
            "Supporting learners is valuable work. What feedback have you received?"
        ])
    
    if 'ai' in detected_topics:
        responses.extend([
            "AI technology is fascinating! How are you incorporating it?",
            "Artificial intelligence has so much potential. What excites you most about it?",
            "AI can really enhance learning experiences. What's your vision?",
            "Technology and education are a powerful combination. Tell me more!"
        ])
    
    # If question, acknowledge and ask back
    if is_question:
        responses.extend([
            "That's a great question! What are your thoughts on it?",
            "I'd love to explore that with you. What do you think?",
            "Interesting question! How would you answer it yourself?",
            "Good point to consider. What's your perspective?"
        ])
    
    # Conversation flow responses
    if conv_length < 3:
        responses.extend([
            "Tell me more about that. I'm interested to hear your thoughts!",
            "That's interesting! Can you elaborate on that?",
            "I'd love to know more. What else can you share?",
            "That sounds important to you. What details can you add?"
        ])
    elif conv_length < 6:
        responses.extend([
            "You're doing great with this conversation! What else would you like to discuss?",
            "I'm enjoying our chat. What other aspects should we explore?",
            "This is a good discussion. What's your next thought on this?",
            "You're expressing yourself well. What else is on your mind?"
        ])
    else:
        responses.extend([
            "We've covered a lot! What's the most important point for you?",
            "This has been a great conversation. What would you like to focus on now?",
            "You've shared some interesting ideas. Which one excites you most?",
            "We're having a good dialogue. What conclusion are you reaching?"
        ])
    
    # If no specific topics detected, use general responses
    if not responses:
        responses = [
            "That's interesting! Tell me more about your thoughts on that.",
            "I'd love to hear more details. Can you elaborate?",
            "That sounds important. What aspects matter most to you?",
            "Thanks for sharing. What else would you like to discuss?",
            "I'm curious to know more. What's your perspective?",
            "That's a good point. How did you come to that conclusion?",
            "Interesting! What made you think about this?",
            "I see. What are your goals related to this?"
        ]
    
    # Select a response
    return random.choice(responses)

def calculate_streak(user_id, sessions):
    """
    Calculate current streak for a user.
    A streak counts consecutive days with at least one session.
    - Day 1: Sessions from 12:00 AM to 11:59 PM count as day 1
    - Day 2: Next day's sessions (12:00 AM onwards) increment the streak
    - If a day is missed, the streak resets to 0
    """
    if not sessions:
        return 0
    
    # Get all user sessions
    user_sessions = [s for s in sessions if s.get('user_id') == user_id]
    
    if not user_sessions:
        return 0
    
    # Get unique dates with sessions (sorted most recent first)
    session_dates = set()
    for session in user_sessions:
        session_date = session.get('created_at', datetime.utcnow()).date()
        session_dates.add(session_date)
    
    # Sort dates in descending order (most recent first)
    sorted_dates = sorted(session_dates, reverse=True)
    
    if not sorted_dates:
        return 0
    
    # Current date
    today = datetime.utcnow().date()
    
    # Check if the most recent session is today or yesterday
    # (Allow yesterday to maintain streak if user hasn't practiced today yet)
    most_recent_date = sorted_dates[0]
    
    # If last session was more than 1 day ago, streak is broken
    days_since_last_session = (today - most_recent_date).days
    if days_since_last_session > 1:
        return 0
    
    # Count consecutive days backwards from the most recent session
    streak = 0
    expected_date = most_recent_date
    
    for session_date in sorted_dates:
        if session_date == expected_date:
            streak += 1
            expected_date = expected_date - timedelta(days=1)
        else:
            # Gap found, stop counting
            break
    
    return streak

def get_today_sessions(user_id, sessions):
    """Get today's sessions for a user"""
    today = datetime.utcnow().date()
    return [s for s in sessions 
            if s.get('user_id') == user_id and 
            s.get('created_at', datetime.utcnow()).date() == today]

def calculate_weekly_progress(user_id, sessions):
    """Calculate this week's progress"""
    from datetime import timedelta
    
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())
    
    week_sessions = [s for s in sessions 
                    if s.get('user_id') == user_id and 
                    s.get('created_at', datetime.utcnow()).date() >= week_start]
    
    return len(week_sessions)

# Placeholder routes for other features
@api_bp.route('/interview/questions', methods=['GET'])
@token_required
def get_interview_questions(current_user):
    # Mock data for now
    questions = [
        {"id": 1, "question": "Tell me about yourself", "difficulty": "easy"},
        {"id": 2, "question": "What are your strengths?", "difficulty": "medium"},
        {"id": 3, "question": "Where do you see yourself in 5 years?", "difficulty": "medium"},
    ]
    return jsonify({'questions': questions}), 200

@api_bp.route('/fluency/scenarios', methods=['GET'])
@token_required
def get_fluency_scenarios(current_user):
    scenarios = [
        {"id": 1, "name": "Business Meeting", "description": "Practice professional communication"},
        {"id": 2, "name": "Job Interview", "description": "Prepare for interview conversations"},
        {"id": 3, "name": "Casual Conversation", "description": "Improve everyday English"},
    ]
    return jsonify({'scenarios': scenarios}), 200

# AI Audio Analysis Routes
@api_bp.route('/audio/analyze-ai', methods=['POST'])
@token_required
def analyze_audio_with_ai(current_user):
    """Analyze audio using AI (OpenAI or Demo mode)"""
    try:
        data = request.get_json()
        
        if not data.get('audio_data'):
            return jsonify({'error': 'Audio data is required'}), 400
        
        # Get analysis type from request
        analysis_type = data.get('analysis_type', 'pronunciation')
        demo_mode = False
        result = None
        
        # Check if OpenAI API key is configured
        openai_key = os.getenv('OPENAI_API_KEY')
        use_openai = openai_key and openai_key != '' and openai_key != 'your-api-key-here'
        
        # Try OpenAI first if configured
        if use_openai:
            try:
                print("🤖 Attempting OpenAI analysis...")
                from app.utils.audio_analyzer import AudioAnalyzer
                analyzer = AudioAnalyzer()
                result = analyzer.analyze_audio(data['audio_data'], analysis_type)
                
                if result['success']:
                    print("✅ OpenAI analysis successful")
                    demo_mode = False
                else:
                    raise Exception(result.get('error', 'OpenAI analysis failed'))
                    
            except Exception as openai_error:
                print(f"⚠️ OpenAI analysis failed: {openai_error}")
                print("📝 Falling back to demo mode...")
                result = None
        else:
            print("📝 OpenAI API key not configured, using demo mode")
        
        # Fall back to demo mode if OpenAI failed or not configured
        if not result or not result.get('success'):
            try:
                from app.utils.demo_analyzer import DemoAnalyzer
                analyzer = DemoAnalyzer()
                result = analyzer.analyze_audio(data['audio_data'], analysis_type)
                demo_mode = True
                print("✅ Demo mode analysis successful")
            except Exception as demo_error:
                print(f"❌ Demo mode also failed: {demo_error}")
                return jsonify({
                    'error': 'Analysis failed. Please try again.',
                    'details': str(demo_error)
                }), 500
        
        if not result or not result.get('success'):
            return jsonify({'error': result.get('error', 'Analysis failed')}), 500
        
        # Save session data
        session_data = {
            'id': str(uuid.uuid4()),
            'user_id': current_user['id'],
            'session_type': 'ai_audio_analysis',
            'analysis_type': analysis_type,
            'transcript': result['transcript'],
            'feedback': result['analysis']['feedback_text'],
            'score': result['analysis']['score'],
            'suggestions': result['analysis']['suggestions'],
            'audio_feedback': result.get('audio_feedback', {}),
            'duration': data.get('duration', 0),
            'demo_mode': demo_mode,
            'created_at': datetime.utcnow()
        }
        
        sessions_db.append(session_data)
        save_sessions(sessions_db)
        
        message = 'Audio analyzed successfully!'
        if demo_mode:
            message += ' (Demo mode - add OpenAI credits for full AI analysis)'
        
        return jsonify({
            'success': True,
            'session_id': session_data['id'],
            'transcript': result['transcript'],
            'analysis': result['analysis'],
            'audio_feedback': result['audio_feedback'],
            'demo_mode': demo_mode,
            'message': message
        }), 200
        
    except Exception as e:
        print(f"Audio analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@api_bp.route('/audio/get-feedback/<session_id>', methods=['GET'])
@token_required
def get_audio_feedback(current_user, session_id):
    """Get detailed feedback for a specific audio session"""
    try:
        # Find the session
        session = None
        for s in sessions_db:
            if s.get('id') == session_id and s.get('user_id') == current_user['id']:
                session = s
                break
        
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        return jsonify({
            'session_id': session['id'],
            'transcript': session.get('transcript', ''),
            'feedback': session.get('feedback', ''),
            'score': session.get('score', 0),
            'suggestions': session.get('suggestions', []),
            'audio_feedback': session.get('audio_feedback', {}),
            'analysis_type': session.get('analysis_type', 'pronunciation'),
            'created_at': session.get('created_at', datetime.utcnow()).isoformat()
        }), 200
        
    except Exception as e:
        print(f"Get feedback error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/audio/practice-exercises', methods=['GET'])
@token_required
def get_ai_practice_exercises(current_user):
    """Get AI-powered practice exercises based on user's level and history"""
    try:
        # Get user's recent sessions to personalize exercises
        user_sessions = [s for s in sessions_db if s.get('user_id') == current_user['id']]
        
        # Base exercises
        exercises = [
            {
                'id': 'pronunciation_basics',
                'title': 'Pronunciation Fundamentals',
                'description': 'Master basic English sounds and phonetics',
                'difficulty': 'beginner',
                'type': 'pronunciation',
                'sample_text': 'The quick brown fox jumps over the lazy dog.',
                'focus_areas': ['consonants', 'vowels', 'word_stress']
            },
            {
                'id': 'fluency_conversation',
                'title': 'Conversational Fluency',
                'description': 'Improve natural speaking flow and rhythm',
                'difficulty': 'intermediate',
                'type': 'fluency',
                'sample_text': 'I believe that effective communication is essential in today\'s workplace. It helps build strong relationships and ensures that projects are completed successfully.',
                'focus_areas': ['rhythm', 'intonation', 'natural_pauses']
            },
            {
                'id': 'interview_practice',
                'title': 'Interview Communication',
                'description': 'Practice professional interview responses',
                'difficulty': 'advanced',
                'type': 'interview',
                'sample_text': 'I am passionate about this role because it aligns perfectly with my career goals and allows me to utilize my skills in a meaningful way.',
                'focus_areas': ['confidence', 'clarity', 'professional_tone']
            },
            {
                'id': 'accent_reduction',
                'title': 'Accent Refinement',
                'description': 'Work on neutral English pronunciation',
                'difficulty': 'advanced',
                'type': 'pronunciation',
                'sample_text': 'I would like to schedule a meeting to discuss the quarterly results and plan our strategy for the upcoming fiscal year.',
                'focus_areas': ['r_sounds', 'th_sounds', 'vowel_clarity']
            }
        ]
        
        # Personalize based on user level
        user_level = current_user.get('experience_level', 'beginner')
        if user_level == 'beginner':
            recommended_exercises = [e for e in exercises if e['difficulty'] in ['beginner', 'intermediate']]
        elif user_level == 'intermediate':
            recommended_exercises = [e for e in exercises if e['difficulty'] in ['intermediate', 'advanced']]
        else:
            recommended_exercises = exercises
        
        return jsonify({
            'exercises': recommended_exercises,
            'user_level': user_level,
            'total_sessions': len(user_sessions)
        }), 200
        
    except Exception as e:
        print(f"Get exercises error: {str(e)}")
        return jsonify({'exercises': [], 'user_level': 'beginner', 'total_sessions': 0}), 200

# Interview Analysis Routes
@api_bp.route('/interview/analyze-response', methods=['POST'])
@token_required
def analyze_interview_response(current_user):
    """Analyze interview response using RAG + LangChain for personalized feedback"""
    try:
        data = request.get_json()
        
        if not data.get('transcript'):
            return jsonify({'error': 'Transcript is required'}), 400
        
        question = data.get('question', '')
        transcript = data.get('transcript', '')
        question_category = data.get('category', 'General')
        question_difficulty = data.get('difficulty', 'Medium')
        
        # Calculate basic score
        word_count = len(transcript.split())
        has_examples = any(word in transcript.lower() for word in ['example', 'time', 'when', 'situation', 'project'])
        has_outcomes = any(word in transcript.lower() for word in ['result', 'outcome', 'achieved', 'success', 'learned'])
        
        base_score = 70
        if word_count > 50:
            base_score += 10
        if has_examples:
            base_score += 10
        if has_outcomes:
            base_score += 10
        
        import random
        overall_score = min(95, base_score + random.randint(-5, 5))
        
        # Get user's session history for context
        user_sessions = [s for s in sessions_db if s.get('user_id') == current_user['id']]
        interview_sessions = [s for s in user_sessions if s.get('session_type') == 'interview_analysis']
        
        # Calculate average score
        if interview_sessions:
            scores = [s.get('score', 0) for s in interview_sessions]
            avg_score = sum(scores) / len(scores) if scores else 0
        else:
            avg_score = 0
        
        # Use AI-powered interview analyzer for dynamic feedback
        try:
            from app.utils.interview_analyzer import get_interview_analyzer
            
            analyzer = get_interview_analyzer()
            
            # Prepare user context
            user_context = {
                'name': current_user.get('name', 'there'),
                'experience_level': current_user.get('experience_level', 'intermediate'),
                'total_sessions': len(user_sessions),
                'interview_sessions': len(interview_sessions),
                'average_score': avg_score
            }
            
            # Analyze the answer
            print("Analyzing interview response with AI...")
            analysis_result = analyzer.analyze_answer(
                question=question,
                answer=transcript,
                category=question_category,
                difficulty=question_difficulty,
                user_context=user_context
            )
            
            overall_score = analysis_result['score']
            detailed_feedback = analysis_result['feedback_text']
            
            # Build feedback components
            feedback_components = {
                'overall_score': overall_score,
                'feedback_items': [],
                'detailed_feedback': detailed_feedback
            }
            
            # Add strengths
            for strength in analysis_result.get('strengths', [])[:3]:
                feedback_components['feedback_items'].append({
                    'type': 'positive',
                    'title': 'Strength',
                    'content': strength,
                    'icon': 'fas fa-thumbs-up',
                    'color': 'secondary'
                })
            
            # Add improvements
            for improvement in analysis_result.get('improvements', [])[:3]:
                feedback_components['feedback_items'].append({
                    'type': 'improvement',
                    'title': 'Area to Improve',
                    'content': improvement,
                    'icon': 'fas fa-exclamation-triangle',
                    'color': 'warning'
                })
            
            # Add suggestions
            for suggestion in analysis_result.get('suggestions', [])[:2]:
                feedback_components['feedback_items'].append({
                    'type': 'tip',
                    'title': 'Recommendation',
                    'content': suggestion,
                    'icon': 'fas fa-lightbulb',
                    'color': 'accent'
                })
            
            ai_powered = analysis_result.get('ai_powered', False)
            demo_mode = not ai_powered
            rag_enabled = ai_powered
            
            if ai_powered:
                print("✓ AI-powered feedback generated successfully")
            else:
                print("⚠ Using basic feedback (AI not available)")
                
        except Exception as analysis_error:
            print(f"Analysis failed: {analysis_error}, falling back to demo mode")
            # Fall back to demo mode
            feedback_components = generate_demo_interview_feedback(question, transcript, question_category, question_difficulty)
            detailed_feedback = feedback_components['detailed_feedback']
            overall_score = feedback_components['overall_score']
            demo_mode = True
            rag_enabled = False
        
        # Save interview session
        session_data = {
            'id': str(uuid.uuid4()),
            'user_id': current_user['id'],
            'session_type': 'interview_analysis',
            'question': question,
            'question_category': question_category,
            'question_difficulty': question_difficulty,
            'transcript': transcript,
            'feedback': detailed_feedback,
            'score': feedback_components.get('overall_score', overall_score),
            'feedback_components': feedback_components,
            'demo_mode': demo_mode,
            'rag_enabled': rag_enabled,
            'created_at': datetime.utcnow()
        }
        
        sessions_db.append(session_data)
        save_sessions(sessions_db)
        
        message = 'Interview response analyzed successfully!'
        if demo_mode:
            message += ' (Demo mode - add OpenAI credits for full AI analysis)'
        
        return jsonify({
            'success': True,
            'session_id': session_data['id'],
            'transcript': transcript,
            'overall_score': session_data['score'],
            'detailed_feedback': detailed_feedback,
            'feedback_components': feedback_components,
            'demo_mode': demo_mode,
            'rag_enabled': rag_enabled,
            'message': message
        }), 200
        
    except Exception as e:
        print(f"Interview analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

def parse_interview_feedback(feedback_text):
    """Parse AI feedback into structured components"""
    import re
    
    # Extract score
    score_match = re.search(r'score[:\s]+(\d+)', feedback_text.lower())
    overall_score = int(score_match.group(1)) if score_match else 75
    
    # Extract feedback categories
    feedback_items = []
    
    # Look for positive feedback
    positive_patterns = [
        r'(excellent|great|good|strong|well|clear|effective)([^.!?]*[.!?])',
        r'(you did well|good job|nice work)([^.!?]*[.!?])'
    ]
    
    for pattern in positive_patterns:
        matches = re.finditer(pattern, feedback_text, re.IGNORECASE)
        for match in matches:
            feedback_items.append({
                'type': 'positive',
                'title': 'Strength Identified',
                'content': match.group(0).strip(),
                'icon': 'fas fa-thumbs-up',
                'color': 'secondary'
            })
    
    # Look for improvement areas
    improvement_patterns = [
        r'(improve|better|consider|try|focus on|work on)([^.!?]*[.!?])',
        r'(could|should|might want to)([^.!?]*[.!?])'
    ]
    
    for pattern in improvement_patterns:
        matches = re.finditer(pattern, feedback_text, re.IGNORECASE)
        for match in matches:
            feedback_items.append({
                'type': 'improvement',
                'title': 'Area for Improvement',
                'content': match.group(0).strip(),
                'icon': 'fas fa-exclamation-triangle',
                'color': 'warning'
            })
    
    # Look for specific tips
    tip_patterns = [
        r'(tip|suggestion|recommend|advice)([^.!?]*[.!?])',
        r'(next time|in future)([^.!?]*[.!?])'
    ]
    
    for pattern in tip_patterns:
        matches = re.finditer(pattern, feedback_text, re.IGNORECASE)
        for match in matches:
            feedback_items.append({
                'type': 'tip',
                'title': 'Pro Tip',
                'content': match.group(0).strip(),
                'icon': 'fas fa-lightbulb',
                'color': 'accent'
            })
    
    # If no specific feedback found, create general items
    if not feedback_items:
        feedback_items = [
            {
                'type': 'positive',
                'title': 'Good Response',
                'content': 'You provided a relevant answer to the question.',
                'icon': 'fas fa-thumbs-up',
                'color': 'secondary'
            },
            {
                'type': 'improvement',
                'title': 'Add More Detail',
                'content': 'Consider providing more specific examples and outcomes.',
                'icon': 'fas fa-exclamation-triangle',
                'color': 'warning'
            }
        ]
    
    return {
        'overall_score': overall_score,
        'feedback_items': feedback_items[:6],  # Limit to 6 items
        'detailed_feedback': feedback_text
    }

def generate_demo_interview_feedback(question, transcript, category, difficulty):
    """Generate dynamic demo interview feedback based on actual answer content"""
    import random
    
    # Analyze response characteristics
    word_count = len(transcript.split())
    sentences = [s.strip() for s in transcript.split('.') if s.strip()]
    sentence_count = len(sentences)
    
    # Content analysis
    has_examples = any(word in transcript.lower() for word in 
                      ['example', 'time', 'when', 'situation', 'project', 'experience', 'once'])
    has_outcomes = any(word in transcript.lower() for word in 
                      ['result', 'outcome', 'achieved', 'success', 'learned', 'improved', 'increased'])
    has_numbers = any(char.isdigit() for char in transcript)
    has_action_words = any(word in transcript.lower() for word in 
                          ['led', 'managed', 'created', 'developed', 'implemented', 'solved'])
    
    # Calculate dynamic score
    base_score = 60
    if word_count > 100:
        base_score += 15
    elif word_count > 50:
        base_score += 10
    elif word_count > 30:
        base_score += 5
    
    if has_examples:
        base_score += 10
    if has_outcomes:
        base_score += 10
    if has_numbers:
        base_score += 5
    if has_action_words:
        base_score += 5
    
    overall_score = min(95, base_score + random.randint(-3, 3))
    
    # Generate dynamic feedback items
    feedback_items = []
    strengths = []
    improvements = []
    
    # Dynamic positive feedback based on actual content
    if word_count > 80:
        feedback_items.append({
            'type': 'positive',
            'title': 'Comprehensive Response',
            'content': f'Your {word_count}-word answer shows thorough thinking and good detail.',
            'icon': 'fas fa-thumbs-up',
            'color': 'secondary'
        })
        strengths.append(f'Comprehensive {word_count}-word response with good depth')
    elif word_count > 40:
        feedback_items.append({
            'type': 'positive',
            'title': 'Good Detail',
            'content': f'You provided a solid {word_count}-word response with relevant information.',
            'icon': 'fas fa-thumbs-up',
            'color': 'secondary'
        })
        strengths.append(f'Solid {word_count}-word response with relevant details')
    
    if has_examples:
        feedback_items.append({
            'type': 'positive',
            'title': 'Specific Examples',
            'content': 'Excellent! You included specific examples which makes your answer credible and memorable.',
            'icon': 'fas fa-thumbs-up',
            'color': 'secondary'
        })
        strengths.append('Included specific examples from experience')
    
    if has_outcomes:
        feedback_items.append({
            'type': 'positive',
            'title': 'Results-Oriented',
            'content': 'Great job mentioning outcomes and results - this demonstrates impact.',
            'icon': 'fas fa-thumbs-up',
            'color': 'secondary'
        })
        strengths.append('Mentioned measurable outcomes and results')
    
    if has_action_words:
        strengths.append('Used strong action verbs to describe contributions')
    
    # Dynamic improvement feedback
    if not has_examples:
        feedback_items.append({
            'type': 'improvement',
            'title': 'Add Specific Examples',
            'content': 'Your answer would be stronger with a concrete example from your experience. Try: "For instance, when I..."',
            'icon': 'fas fa-exclamation-triangle',
            'color': 'warning'
        })
        improvements.append('Add a specific example from your experience')
    
    if not has_outcomes:
        feedback_items.append({
            'type': 'improvement',
            'title': 'Include Results',
            'content': 'Strengthen your answer by mentioning the outcome. What was the result of your actions?',
            'icon': 'fas fa-exclamation-triangle',
            'color': 'warning'
        })
        improvements.append('Include the results or outcomes of your actions')
    
    if word_count < 40:
        feedback_items.append({
            'type': 'improvement',
            'title': 'Expand Your Answer',
            'content': f'Your {word_count}-word answer is brief. Aim for 60-100 words with more specific details.',
            'icon': 'fas fa-exclamation-triangle',
            'color': 'warning'
        })
        improvements.append('Expand your answer with more specific details')
    
    if not has_numbers and has_outcomes:
        improvements.append('Add quantifiable metrics to make results more concrete')
    
    # Category-specific suggestions
    if category == 'Behavioral':
        feedback_items.append({
            'type': 'tip',
            'title': 'STAR Method',
            'content': 'Structure your answer: Situation → Task → Action → Result for maximum impact.',
            'icon': 'fas fa-lightbulb',
            'color': 'accent'
        })
    elif category == 'Technical':
        feedback_items.append({
            'type': 'tip',
            'title': 'Technical Depth',
            'content': 'Explain your technical reasoning and trade-offs you considered.',
            'icon': 'fas fa-lightbulb',
            'color': 'accent'
        })
    
    # Ensure we have at least 3 feedback items
    if len(feedback_items) < 3:
        feedback_items.append({
            'type': 'tip',
            'title': 'Practice Regularly',
            'content': 'Record yourself answering questions to identify areas for improvement.',
            'icon': 'fas fa-lightbulb',
            'color': 'accent'
        })
    
    # Build dynamic detailed feedback
    strengths_text = '\n'.join(f'• {s}' for s in strengths) if strengths else '• Addressed the question directly'
    improvements_text = '\n'.join(f'• {i}' for i in improvements) if improvements else '• Continue practicing to refine delivery'
    
    score_assessment = "excellent" if overall_score >= 85 else "good" if overall_score >= 70 else "solid"
    
    detailed_feedback = f"""Your answer scored {overall_score}/100 - {score_assessment} performance!

STRENGTHS:
{strengths_text}

AREAS TO IMPROVE:
{improvements_text}

NEXT STEPS:
• Prepare 3-5 detailed stories you can adapt to different questions
• Practice using the STAR method for behavioral questions
• Record yourself to improve delivery and confidence

{f"Note: Your answer is quite brief ({word_count} words). Aim for 60-100 words for more complete responses." if word_count < 40 else ""}

Keep practicing - you're making progress! 🚀"""
    
    return {
        'overall_score': overall_score,
        'feedback_items': feedback_items[:6],  # Limit to 6 items
        'detailed_feedback': detailed_feedback.strip()
    }

# Generate Single Interview Question with Gemini
@api_bp.route('/interview/generate-question', methods=['POST'])
@token_required
def generate_single_question(current_user):
    """Generate a single interview question using Gemini AI"""
    try:
        data = request.get_json()
        
        category = data.get('category', 'Behavioral')
        difficulty = data.get('difficulty', 'Medium')
        job_role = data.get('job_role', 'Professional')
        previous_questions = data.get('previous_questions', [])
        
        # Try Gemini AI
        try:
            import google.generativeai as genai
            import os
            
            gemini_key = os.getenv('GEMINI_API_KEY')
            if not gemini_key:
                raise Exception("Gemini API key not found")
            
            genai.configure(api_key=gemini_key)
            # Use stable Gemini 2.5 Flash model
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            
            # Create prompt
            prompt = f"""Generate ONE unique interview question for a {job_role} position.

Requirements:
- Category: {category}
- Difficulty: {difficulty}
- Must be different from these previous questions: {', '.join(previous_questions[:3]) if previous_questions else 'None'}
- Should be realistic and commonly asked in interviews
- Should be clear and specific

Return ONLY the question text without quotes or extra formatting.
Example: Tell me about a time when you had to overcome a significant challenge at work."""
            
            response = model.generate_content(prompt)
            question_text = response.text.strip().strip('"').strip("'")
            
            return jsonify({
                'success': True,
                'question': question_text,
                'category': category,
                'difficulty': difficulty,
                'ai_generated': True
            }), 200
            
        except Exception as ai_error:
            print(f"Gemini generation failed: {ai_error}")
            # Fallback to predefined questions
            fallback_questions = {
                'Behavioral': [
                    "Tell me about a time when you had to work with a difficult team member.",
                    "Describe a situation where you had to meet a tight deadline.",
                    "Give me an example of a time you showed leadership.",
                ],
                'Technical': [
                    "Explain your approach to solving complex technical problems.",
                    "What technologies are you most comfortable working with?",
                    "How do you stay updated with industry trends?",
                ],
                'General': [
                    "Tell me about yourself and your background.",
                    "Why are you interested in this position?",
                    "Where do you see yourself in five years?",
                ]
            }
            
            import random
            questions_list = fallback_questions.get(category, fallback_questions['General'])
            question_text = random.choice(questions_list)
            
            return jsonify({
                'success': True,
                'question': question_text,
                'category': category,
                'difficulty': difficulty,
                'ai_generated': False
            }), 200
        
    except Exception as e:
        print(f"Question generation error: {str(e)}")
        return jsonify({'error': f'Failed to generate question: {str(e)}'}), 500

# Real-time Speech Analysis
@api_bp.route('/interview/analyze-realtime', methods=['POST'])
@token_required
def analyze_realtime_speech(current_user):
    """Analyze speech in real-time for pronunciation, pace, confidence, etc."""
    try:
        data = request.get_json()
        
        transcript = data.get('transcript', '')
        is_final = data.get('is_final', False)
        
        # Get analyzer
        from app.utils.realtime_speech_analyzer import get_realtime_analyzer
        analyzer = get_realtime_analyzer()
        
        # Reset on first call or if explicitly requested
        if data.get('reset', False):
            analyzer.reset()
        
        # Analyze transcript
        metrics = analyzer.analyze_transcript(transcript, is_final)
        
        return jsonify({
            'success': True,
            'metrics': metrics
        }), 200
        
    except Exception as e:
        print(f"Real-time analysis error: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

# Dynamic Interview Question Generation
@api_bp.route('/interview/generate-questions', methods=['POST'])
@token_required
def generate_interview_questions(current_user):
    """Generate dynamic interview questions based on user preferences"""
    try:
        data = request.get_json()
        
        job_role = data.get('job_role', 'Software Engineer')
        industry = data.get('industry', 'Technology')
        difficulty = data.get('difficulty', 'Medium')
        question_count = min(int(data.get('question_count', 8)), 15)  # Max 15 questions
        
        # Try OpenAI first, fall back to demo mode
        try:
            from app.utils.audio_analyzer import AudioAnalyzer
            analyzer = AudioAnalyzer()
            
            # Create prompt for question generation
            question_prompt = f"""
            Generate {question_count} realistic job interview questions for a {job_role} position in the {industry} industry.
            
            Requirements:
            - Difficulty level: {difficulty}
            - Mix of question types: behavioral, technical, situational, and general
            - Questions should be relevant to {job_role} role
            - Include a variety of difficulty levels
            - Format each question as: "Question text" | Category | Difficulty
            
            Example format:
            "Tell me about a time when you had to debug a complex issue." | Behavioral | Medium
            "What is your experience with cloud technologies?" | Technical | Easy
            
            Generate {question_count} questions now:
            """
            
            response = analyzer.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert HR interviewer creating realistic job interview questions."},
                    {"role": "user", "content": question_prompt}
                ],
                max_tokens=1000,
                temperature=0.8
            )
            
            questions_text = response.choices[0].message.content
            questions = parse_generated_questions(questions_text)
            demo_mode = False
            
        except Exception as openai_error:
            print(f"OpenAI question generation failed: {openai_error}")
            # Fall back to demo mode
            questions = generate_demo_questions(job_role, industry, difficulty, question_count)
            demo_mode = True
        
        message = f'Generated {len(questions)} interview questions!'
        if demo_mode:
            message += ' (Demo mode - add OpenAI credits for AI-generated questions)'
        
        return jsonify({
            'success': True,
            'questions': questions,
            'demo_mode': demo_mode,
            'message': message
        }), 200
        
    except Exception as e:
        print(f"Question generation error: {str(e)}")
        return jsonify({'error': f'Failed to generate questions: {str(e)}'}), 500

def parse_generated_questions(questions_text):
    """Parse AI-generated questions into structured format"""
    questions = []
    lines = questions_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Try to parse format: "Question" | Category | Difficulty
        if '|' in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:
                question_text = parts[0].strip('"').strip()
                category = parts[1].strip()
                difficulty = parts[2].strip()
                
                if question_text:
                    questions.append({
                        'text': question_text,
                        'category': category,
                        'difficulty': difficulty
                    })
        else:
            # Simple format - just the question
            question_text = line.strip('0123456789.-) ').strip('"').strip()
            if len(question_text) > 20:  # Reasonable question length
                questions.append({
                    'text': question_text,
                    'category': 'General',
                    'difficulty': 'Medium'
                })
    
    return questions

def generate_demo_questions(job_role, industry, difficulty, count):
    """Generate demo questions when AI is not available"""
    import random
    
    # Base question templates
    templates = {
        'Behavioral': [
            f"Tell me about a time when you faced a challenge in your {job_role} role.",
            f"Describe a situation where you had to work with a difficult team member.",
            f"Give me an example of a project you're proud of in {industry}.",
            f"Tell me about a time when you had to learn something new quickly.",
            f"Describe a situation where you had to meet a tight deadline."
        ],
        'Technical': [
            f"What technical skills are most important for a {job_role}?",
            f"How do you stay updated with trends in {industry}?",
            f"Explain your approach to problem-solving in {job_role}.",
            f"What tools and technologies are you most comfortable with?",
            f"How would you handle a technical disagreement with a colleague?"
        ],
        'Situational': [
            f"How would you prioritize multiple projects as a {job_role}?",
            f"What would you do if you disagreed with your manager's decision?",
            f"How would you handle receiving critical feedback?",
            f"What would you do if you made a mistake that affected the team?",
            f"How would you approach mentoring a junior team member?"
        ],
        'General': [
            f"Why are you interested in this {job_role} position?",
            f"What attracts you to the {industry} industry?",
            f"Where do you see yourself in five years?",
            f"What are your greatest strengths as a {job_role}?",
            f"Why should we hire you for this position?"
        ]
    }
    
    # Generate questions
    questions = []
    categories = list(templates.keys())
    
    for i in range(count):
        category = categories[i % len(categories)]
        question_list = templates[category]
        question_text = random.choice(question_list)
        
        # Vary difficulty
        if i < count // 3:
            diff = 'Easy'
        elif i < 2 * count // 3:
            diff = 'Medium'
        else:
            diff = 'Hard'
        
        questions.append({
            'text': question_text,
            'category': category,
            'difficulty': diff
        })
    
    # Shuffle for variety
    random.shuffle(questions)
    
    return questions

def update_user_stats_after_session(user_id):
    """Update user statistics after completing a session"""
    if user_id not in users_db:
        return
    
    # Get all user sessions
    user_sessions = [s for s in sessions_db if s.get('user_id') == user_id]
    
    # Update total sessions
    users_db[user_id]['total_sessions'] = len(user_sessions)
    
    # Update streak
    current_streak = calculate_streak(user_id, sessions_db)
    users_db[user_id]['streak_count'] = current_streak
    
    # Update last session date
    users_db[user_id]['last_session_date'] = datetime.utcnow().date()
    
    # Save changes
    save_users(users_db)

@api_bp.route('/dashboard/increment-session', methods=['POST'])
@token_required
def increment_session_count(current_user):
    """Increment session count and return updated stats"""
    try:
        # Update user stats
        update_user_stats_after_session(current_user['id'])
        
        # Get updated stats
        today_sessions = get_today_sessions(current_user['id'], sessions_db)
        weekly_sessions = calculate_weekly_progress(current_user['id'], sessions_db)
        current_streak = calculate_streak(current_user['id'], sessions_db)
        total_sessions = len([s for s in sessions_db if s.get('user_id') == current_user['id']])
        
        # Calculate scores
        user_sessions = [s for s in sessions_db if s.get('user_id') == current_user['id']]
        if user_sessions:
            scores = [s.get('scores', {}).get('overall', 0) for s in user_sessions if s.get('scores')]
            avg_score = sum(scores) / len(scores) if scores else 0
        else:
            avg_score = 0
        
        # Daily and weekly goals
        daily_goal = current_user.get('daily_goal', 3)
        weekly_goal = current_user.get('weekly_goal', 7)
        
        return jsonify({
            'success': True,
            'stats': {
                'total_sessions': total_sessions,
                'today_sessions': len(today_sessions),
                'weekly_sessions': weekly_sessions,
                'current_streak': current_streak,
                'average_score': round(avg_score, 1)
            },
            'goals': {
                'daily_goal': daily_goal,
                'daily_progress': len(today_sessions),
                'daily_percentage': min(100, (len(today_sessions) / daily_goal) * 100),
                'weekly_goal': weekly_goal,
                'weekly_progress': weekly_sessions,
                'weekly_percentage': min(100, (weekly_sessions / weekly_goal) * 100)
            }
        }), 200
        
    except Exception as e:
        print(f"Increment session error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Gemini Integration for Dynamic Practice Phrases
import google.generativeai as genai
import os

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Use stable Gemini 2.5 Flash model
    gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    gemini_model = None

@api_bp.route('/audio/generate-phrase', methods=['POST'])
@token_required
def generate_practice_phrase(current_user):
    """Generate a unique practice phrase using Gemini AI"""
    try:
        data = request.get_json()
        exercise_type = data.get('exercise_type', 'word-stress')
        difficulty = data.get('difficulty', 'medium')
        
        # Define prompts for different exercise types
        prompts = {
            'word-stress': f"Generate a single English sentence (10-15 words) for pronunciation practice focusing on word stress patterns. Difficulty: {difficulty}. Mark stressed syllables with CAPITAL letters (e.g., 'The PRO-ject was COM-plete'). Return only the sentence.",
            'phonetic': f"Generate a single English sentence (10-15 words) for phonetic pronunciation practice with challenging sounds like 'th', 'r', 'l'. Difficulty: {difficulty}. Return only the sentence.",
            'sentence-rhythm': f"Generate a single English sentence (10-15 words) for practicing sentence rhythm and intonation. Difficulty: {difficulty}. Mark stressed words with CAPITAL letters. Return only the sentence.",
            'conversation': f"Generate a single conversational English sentence (10-15 words) for fluency practice. Difficulty: {difficulty}. Make it natural and practical. Return only the sentence."
        }
        
        prompt = prompts.get(exercise_type, prompts['word-stress'])
        
        # Try Gemini first
        if gemini_model:
            try:
                response = gemini_model.generate_content(prompt)
                phrase = response.text.strip()
                
                # Clean up the response
                phrase = phrase.replace('"', '').replace("'", "").strip()
                
                return jsonify({
                    'success': True,
                    'phrase': phrase,
                    'exercise_type': exercise_type,
                    'difficulty': difficulty,
                    'source': 'gemini'
                }), 200
                
            except Exception as e:
                print(f"Gemini error: {str(e)}")
                # Fall through to fallback phrases
        
        # Fallback phrases if Gemini fails or is not configured
        fallback_phrases = {
            'word-stress': [
                "The PROJECT manager PRESENTED the QUARTERLY results YESTERDAY.",
                "We need to ADDRESS the ISSUE before the DEADLINE approaches.",
                "The CONFERENCE will FEATURE several PROMINENT speakers this YEAR.",
                "EFFECTIVE communication REQUIRES both CLARITY and CONFIDENCE.",
                "The COMPANY announced a MAJOR BREAKTHROUGH in TECHNOLOGY development."
            ],
            'phonetic': [
                "Think about the thick thread through the thin cloth carefully.",
                "The three brothers threw their things through the threshold.",
                "She sells seashells by the seashore on sunny summer days.",
                "Red lorry, yellow lorry, rolling down the rural road rapidly.",
                "Proper pronunciation practice produces perfect performance over time."
            ],
            'sentence-rhythm': [
                "I THINK we should GO to the STORE before it CLOSES tonight.",
                "The MEETING starts at THREE, so we NEED to LEAVE now.",
                "She LOVES to READ books in the PARK every WEEKEND morning.",
                "PLEASE remember to BRING your LAPTOP to the OFFICE tomorrow.",
                "We're PLANNING a TRIP to the MOUNTAINS next SUMMER vacation."
            ],
            'conversation': [
                "How are you doing today? I hope everything is going well.",
                "Would you like to grab some coffee after work this evening?",
                "I really enjoyed our conversation yesterday about the new project.",
                "Have you had a chance to review the documents I sent?",
                "Let me know if you need any help with that assignment."
            ]
        }
        
        import random
        phrases = fallback_phrases.get(exercise_type, fallback_phrases['word-stress'])
        phrase = random.choice(phrases)
        
        return jsonify({
            'success': True,
            'phrase': phrase,
            'exercise_type': exercise_type,
            'difficulty': difficulty,
            'source': 'fallback'
        }), 200
        
    except Exception as e:
        print(f"Generate phrase error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/audio/save-session', methods=['POST'])
@token_required
def save_audio_practice_session(current_user):
    """Save an audio practice session"""
    try:
        data = request.get_json()
        
        session = {
            'id': str(uuid.uuid4()),
            'user_id': current_user['id'],
            'session_type': 'audio_practice',
            'exercise_type': data.get('exercise_type', 'word-stress'),
            'phrase': data.get('phrase', ''),
            'transcript': data.get('transcript', ''),
            'duration': data.get('duration', 0),
            'scores': data.get('scores', {}),
            'created_at': datetime.utcnow()
        }
        
        sessions_db.append(session)
        save_sessions(sessions_db)
        
        # Update user stats
        user_id = current_user['id']
        if user_id in users_db:
            users_db[user_id]['total_sessions'] = len([s for s in sessions_db if s.get('user_id') == user_id])
            users_db[user_id]['last_session_date'] = datetime.utcnow().date()
            save_users(users_db)
        
        return jsonify({
            'success': True,
            'message': 'Session saved successfully',
            'session_id': session['id']
        }), 201
        
    except Exception as e:
        print(f"Save session error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/audio/stats', methods=['GET'])
@token_required
def get_audio_practice_stats(current_user):
    """Get audio practice statistics"""
    try:
        user_id = current_user['id']
        
        # Get all audio practice sessions for this user
        audio_sessions = [s for s in sessions_db 
                         if s.get('user_id') == user_id and 
                         s.get('session_type') == 'audio_practice']
        
        # Today's sessions
        today = datetime.utcnow().date()
        today_sessions = [s for s in audio_sessions 
                         if s.get('created_at', datetime.utcnow()).date() == today]
        
        # Calculate stats by exercise type
        exercise_stats = {}
        for exercise_type in ['phonetic', 'word-stress', 'sentence-rhythm', 'conversation']:
            type_sessions = [s for s in audio_sessions if s.get('exercise_type') == exercise_type]
            today_type = [s for s in today_sessions if s.get('exercise_type') == exercise_type]
            
            exercise_stats[exercise_type] = {
                'total': len(type_sessions),
                'today': len(today_type),
                'goal': 5,  # Daily goal per exercise type
                'percentage': min(100, (len(today_type) / 5) * 100)
            }
        
        # Calculate overall stats
        all_scores = [s.get('scores', {}).get('overall', 0) for s in audio_sessions if s.get('scores')]
        avg_accuracy = sum(all_scores) / len(all_scores) if all_scores else 0
        
        # Total practice time in minutes
        total_time = sum(s.get('duration', 0) for s in audio_sessions) / 60000  # Convert ms to minutes
        
        # Improvement rate (compare last 5 vs previous 5)
        if len(all_scores) >= 10:
            recent_avg = sum(all_scores[-5:]) / 5
            previous_avg = sum(all_scores[-10:-5]) / 5
            improvement = ((recent_avg - previous_avg) / previous_avg) * 100 if previous_avg > 0 else 0
        else:
            improvement = 0
        
        # Current streak
        streak = calculate_streak(user_id, sessions_db)
        
        # Daily goal progress
        daily_goal = 10  # 10 exercises per day
        daily_progress = len(today_sessions)
        daily_percentage = min(100, (daily_progress / daily_goal) * 100)
        
        return jsonify({
            'success': True,
            'stats': {
                'total_sessions': len(audio_sessions),
                'today_sessions': len(today_sessions),
                'avg_accuracy': round(avg_accuracy, 1),
                'total_practice_time': round(total_time, 1),
                'improvement_rate': round(improvement, 1),
                'current_streak': streak
            },
            'exercise_stats': exercise_stats,
            'daily_goal': {
                'goal': daily_goal,
                'progress': daily_progress,
                'percentage': round(daily_percentage, 1)
            }
        }), 200
        
    except Exception as e:
        print(f"Audio stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/session/track', methods=['POST'])
@token_required
def track_session_completion(current_user):
    """Track session completion and update user stats"""
    try:
        data = request.get_json()
        session_type = data.get('session_type', 'general')
        duration = data.get('duration', 0)
        
        # Create a session completion record if duration is provided
        if duration > 0:
            completion_session = {
                'id': str(uuid.uuid4()),
                'user_id': current_user['id'],
                'session_type': session_type + '_completion',
                'duration': duration,
                'created_at': datetime.utcnow()
            }
            sessions_db.append(completion_session)
            save_sessions(sessions_db)
        
        # Update user's session count
        user_id = current_user['id']
        if user_id in users_db:
            # Get all sessions for this user
            user_sessions = [s for s in sessions_db if s.get('user_id') == user_id]
            
            # Update totals
            users_db[user_id]['total_sessions'] = len(user_sessions)
            users_db[user_id]['last_session_date'] = datetime.utcnow().date()
            
            # Calculate streak
            streak = calculate_streak(user_id, sessions_db)
            users_db[user_id]['streak_count'] = streak
            
            save_users(users_db)
            
            # Get today's progress
            today_sessions = get_today_sessions(user_id, sessions_db)
            weekly_sessions = calculate_weekly_progress(user_id, sessions_db)
            
            # Calculate performance stats for audio practice
            audio_sessions = [s for s in user_sessions if s.get('session_type') == 'audio_practice']
            avg_score = 0
            total_practice_time = 0
            
            if audio_sessions:
                scores = [s.get('scores', {}).get('overall', 0) for s in audio_sessions if s.get('scores')]
                avg_score = sum(scores) / len(scores) if scores else 0
                total_practice_time = sum(s.get('duration', 0) for s in audio_sessions) / 60000  # Convert to minutes
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_sessions': len(user_sessions),
                    'today_sessions': len(today_sessions),
                    'weekly_sessions': weekly_sessions,
                    'current_streak': streak,
                    'avg_score': round(avg_score, 1),
                    'total_practice_time': round(total_practice_time, 1)
                },
                'goals': {
                    'daily_goal': users_db[user_id].get('daily_goal', 3),
                    'weekly_goal': users_db[user_id].get('weekly_goal', 7),
                    'daily_progress': len(today_sessions),
                    'weekly_progress': weekly_sessions,
                    'daily_percentage': min(100, (len(today_sessions) / users_db[user_id].get('daily_goal', 3)) * 100),
                    'weekly_percentage': min(100, (weekly_sessions / users_db[user_id].get('weekly_goal', 7)) * 100)
                }
            }), 200
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        print(f"Track session error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Fluency Coach Conversation Routes
@api_bp.route('/conversation/start', methods=['POST'])
@token_required
def start_conversation(current_user):
    """Start a new conversation with OpenAI"""
    try:
        data = request.get_json()
        conversation_type = data.get('conversation_type', 'fluency_practice')
        
        # Try Bytez AI first, fall back to Intelligent System
        api_key = os.getenv('OPENAI_API_KEY')
        
        if api_key and api_key != '':
            try:
                from bytez import Bytez
                
                print("🤖 Using Bytez AI for greeting...")
                
                sdk = Bytez(api_key)
                model = sdk.model("openai/gpt-4o-mini")
                
                messages = [
                    {
                        "role": "system",
                        "content": "You are a friendly English fluency coach. Start a natural conversation with a student."
                    },
                    {
                        "role": "user",
                        "content": "Give me a friendly greeting and ask an open-ended question to start practicing English (2-3 sentences max)."
                    }
                ]
                
                response = model.run(messages)
                
                if response.error:
                    raise Exception(f"Bytez error: {response.error}")
                
                # Extract content from response
                if isinstance(response.output, dict) and 'content' in response.output:
                    greeting = response.output['content'].strip()
                else:
                    greeting = str(response.output).strip()
                print(f"✅ Bytez greeting: {greeting[:50]}...")
                
                return jsonify({
                    'success': True,
                    'message': greeting,
                    'source': 'bytez_ai',
                    'using_ai': True
                }), 200
                
            except Exception as bytez_error:
                print(f"⚠️ Bytez failed: {bytez_error}")
                print(f"📝 Using Intelligent System...")
        
        # Use Intelligent Greeting System (fallback)
        print("🤖 Using Intelligent Greeting System...")
        
        greetings = [
            "Hello! I'm your English fluency coach. Let's have a great conversation today. What would you like to talk about?",
            "Hi there! I'm here to help you practice your English. How are you doing today?",
            "Hey! Ready to practice some English? Tell me, what's on your mind today?",
            "Good to see you! Let's work on your English fluency together. What topic interests you?",
            "Welcome! I'm excited to help you improve your English. What would you like to discuss?"
        ]
        import random
        greeting = random.choice(greetings)
        
        print(f"✅ Greeting: {greeting[:50]}...")
        
        return jsonify({
            'success': True,
            'message': greeting,
            'source': 'intelligent_system',
            'using_ai': False
        }), 200
            
    except Exception as e:
        print(f"Start conversation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': "Hi! Let's practice English together. How are you today?"
        }), 200

@api_bp.route('/conversation/continue', methods=['POST'])
@token_required
def continue_conversation(current_user):
    """Continue conversation with Gemini AI based on user's response"""
    try:
        print("\n" + "="*50)
        print("🔵 CONVERSATION CONTINUE REQUEST")
        print("="*50)
        
        data = request.get_json()
        conversation_history = data.get('conversation_history', [])
        user_message = data.get('user_message', '')
        
        print(f"👤 User: {current_user.get('name', 'Unknown')}")
        print(f"💬 Message: {user_message}")
        print(f"📚 History length: {len(conversation_history)}")
        
        if not user_message:
            print("❌ No user message provided")
            return jsonify({'error': 'User message is required'}), 400
        
        # Try Bytez AI first, fall back to Intelligent System if it fails
        api_key = os.getenv('OPENAI_API_KEY')
        
        if api_key and api_key != '':
            # Try using Bytez
            try:
                from bytez import Bytez
                
                print(f"🤖 Using Bytez AI (GPT-4o)...")
                print(f"📝 Message: {user_message[:50]}...")
                
                # Initialize Bytez
                sdk = Bytez(api_key)
                model = sdk.model("openai/gpt-4o-mini")
                
                # Build messages
                messages = [
                    {
                        "role": "system",
                        "content": "You are a friendly English fluency coach. Be encouraging, ask follow-up questions, and keep responses conversational (2-4 sentences)."
                    }
                ]
                
                # Add history
                for msg in conversation_history[-10:]:
                    role = "assistant" if msg.get('role') == 'assistant' else "user"
                    messages.append({"role": role, "content": msg.get('content', '')})
                
                messages.append({"role": "user", "content": user_message})
                
                # Call Bytez
                import time
                start_time = time.time()
                
                response = model.run(messages)
                
                if response.error:
                    raise Exception(f"Bytez error: {response.error}")
                
                elapsed = time.time() - start_time
                
                # Extract content from response
                if isinstance(response.output, dict) and 'content' in response.output:
                    ai_message = response.output['content'].strip()
                else:
                    ai_message = str(response.output).strip()
                
                print(f"✅ Bytez AI responded in {elapsed:.2f}s")
                print(f"📝 Response: {ai_message[:100]}...")
                
                return jsonify({
                    'success': True,
                    'message': ai_message,
                    'tips': [],
                    'source': 'bytez_ai',
                    'using_ai': True
                }), 200
                
            except Exception as bytez_error:
                print(f"⚠️ Bytez AI failed: {bytez_error}")
                print(f"📝 Falling back to Intelligent System...")
        else:
            print(f"⚠️ No API key found")
            print(f"📝 Using Intelligent System...")
        
        # Use Intelligent Conversation System (fallback)
        try:
            import time
            start_time = time.time()
            
            ai_message = generate_intelligent_response(user_message, conversation_history)
            
            elapsed = time.time() - start_time
            print(f"✅ Intelligent response in {elapsed:.3f}s")
            print(f"📝 Response: {ai_message[:100]}...")
            
            return jsonify({
                'success': True,
                'message': ai_message,
                'tips': [],
                'source': 'intelligent_system',
                'using_ai': False
            }), 200
            
        except Exception as error:
            print(f"❌ Error: {error}")
            
            return jsonify({
                'success': True,
                'message': "That's interesting! Tell me more about that.",
                'tips': [],
                'source': 'fallback',
                'using_ai': False
            }), 200
            
    except Exception as e:
        print(f"❌ Continue conversation error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Always return success with fallback message
        fallback_responses = [
            "That's interesting! Tell me more about that.",
            "I'd love to hear more about your thoughts on this.",
            "That's a great point. Can you expand on that?",
            "Thanks for sharing. What else would you like to discuss?"
        ]
        import random
        return jsonify({
            'success': True,
            'message': random.choice(fallback_responses),
            'tips': [],
            'source': 'fallback',
            'using_ai': False
        }), 200


@api_bp.route('/conversation/quick-responses', methods=['POST'])
@token_required
def generate_quick_responses(current_user):
    """Generate contextual quick responses using Gemini"""
    try:
        data = request.get_json()
        last_message = data.get('last_message', '')
        conversation_history = data.get('conversation_history', [])
        
        if not last_message:
            # Default quick responses
            return jsonify({
                'success': True,
                'quick_responses': [
                    "Could you clarify that?",
                    "I need more time to think",
                    "Let me get back to you"
                ]
            }), 200
        
        # Try to use Gemini for contextual quick responses
        try:
            import google.generativeai as genai
            import os
            
            # Configure Gemini
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise Exception("Gemini API key not configured")
            
            genai.configure(api_key=api_key)
            # Use stable Gemini 2.5 Flash model
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            
            # Generate contextual quick responses
            prompt = f"""Based on this conversation message from the coach:
"{last_message}"

Generate 3 short, natural quick response options that a student could use to reply. These should be:
- Relevant to what the coach just said
- Natural and conversational
- Short (3-8 words each)
- Varied in tone (one agreeing, one asking for clarification, one continuing the topic)

Format: Return ONLY 3 responses, one per line, without quotes or numbering.

Example format:
That sounds interesting!
Could you explain more about that?
I'd like to share my thoughts"""
            
            response = model.generate_content(prompt)
            responses_text = response.text.strip()
            
            # Parse responses (one per line)
            quick_responses = [r.strip() for r in responses_text.split('\n') if r.strip()]
            
            # Ensure we have exactly 3 responses
            if len(quick_responses) < 3:
                quick_responses.extend([
                    "That's interesting!",
                    "Tell me more",
                    "I understand"
                ])
            quick_responses = quick_responses[:3]
            
            return jsonify({
                'success': True,
                'quick_responses': quick_responses,
                'source': 'gemini'
            }), 200
            
        except Exception as gemini_error:
            print(f"Gemini quick responses error: {gemini_error}")
            # Fallback to context-aware defaults
            if '?' in last_message:
                quick_responses = [
                    "Yes, I think so",
                    "Let me think about that",
                    "Could you rephrase that?"
                ]
            else:
                quick_responses = [
                    "That's interesting!",
                    "Tell me more",
                    "I see what you mean"
                ]
            
            return jsonify({
                'success': True,
                'quick_responses': quick_responses,
                'source': 'fallback'
            }), 200
            
    except Exception as e:
        print(f"Quick responses error: {str(e)}")
        return jsonify({
            'success': True,
            'quick_responses': [
                "I understand",
                "Could you clarify?",
                "That makes sense"
            ]
        }), 200



