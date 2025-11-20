from flask import Blueprint, render_template, send_from_directory, current_app
from flask import request
pages_bp = Blueprint('pages', __name__)

# Redirect root to login page
@pages_bp.route('/')
def index():
    return render_template('auth/login_register.html')

@pages_bp.route('/pages/<path:filename>')
def render_page(filename):
    # filename like 'user/dashboard.html' or 'auth/login_register.html'
    return render_template(filename)
