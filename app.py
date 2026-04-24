from flask import Flask, jsonify
from routes.github_routes import github_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(github_bp)


@app.route('/')
def home():
    """Home endpoint with API information."""
    return jsonify({
        'message': 'GitHub Repository Counter API',
        'version': '1.0.0',
        'endpoints': {
            'get_repository_count': '/api/github/repositories/count',
            'get_my_repository_count': '/api/github/user/repositories/count',
            'health_check': '/api/github/health'
        }
    })


@app.route('/health')
def health_check():
    """General health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'API is running successfully'
    }), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)