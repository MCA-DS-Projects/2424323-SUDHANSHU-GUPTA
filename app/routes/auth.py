from flask import Blueprint, render_template, request, redirect, url_for, session

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        # Minimal placeholder: set session and redirect
        session['user_id'] = 'demo_user'
        return redirect(url_for('pages.render_page', filename='user/user_dashboard.html'))
    return render_template('auth/login_register.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('auth.login'))
