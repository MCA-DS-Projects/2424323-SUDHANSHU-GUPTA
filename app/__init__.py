from flask import Flask
from flask_cors import CORS
from .config import Config
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Enable CORS
    CORS(app)

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.pages import pages_bp
    from .routes.admin import admin_bp
    from .routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    return app
