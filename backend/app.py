import os
import sys
from flask import Flask, render_template
from flask_cors import CORS

# Add the current directory to the path so Python can find the modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Now import the config
from config import config

def create_app(config_name='default'):
    """Create and configure the Flask application"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    # Fix the import path for the blueprint
    from api.routes import api_blueprint
    app.register_blueprint(api_blueprint)
    
    # Root route to serve the HTML template
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    app_config = os.environ.get('FLASK_ENV', 'development')
    app = create_app(app_config)
    app.run(host='0.0.0.0', port=5000)