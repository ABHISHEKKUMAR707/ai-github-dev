from flask import Flask
from routes.github import github_bp
import logging
import os

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Register blueprints
    app.register_blueprint(github_bp)
    
    return app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Check for GitHub token
    if not os.getenv('GITHUB_TOKEN'):
        print("Warning: GITHUB_TOKEN environment variable not set.")
        print("You may encounter rate limiting issues without authentication.")
        print("To set a token, create a GitHub personal access token and set:")
        print("export GITHUB_TOKEN=your_token_here")
    
    # Run the application
    app.run(debug=True, host='0.0.0.0', port=5000)