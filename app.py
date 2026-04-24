from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
import os
from github import count_repositories, get_repository_summary

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')

@app.route('/github/repo-count', methods=['GET', 'POST'])
def github_repo_count():
    """GitHub repository count page."""
    if request.method == 'GET':
        return render_template('repo_count.html')
    
    # Handle POST request
    username = request.form.get('username', '').strip()
    token = request.form.get('token', '').strip()
    
    # Use environment variable if no token provided
    if not token:
        token = os.getenv('GITHUB_TOKEN')
    
    if not username and not token:
        flash('Please provide either a GitHub username or personal access token.', 'error')
        return render_template('repo_count.html')
    
    try:
        # Count repositories
        stats = count_repositories(username=username if username else None, token=token)
        
        return render_template('repo_count.html', 
                             stats=stats, 
                             success=True)
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return render_template('repo_count.html')

@app.route('/api/github/repo-count', methods=['POST'])
def api_github_repo_count():
    """API endpoint for GitHub repository count."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        username = data.get('username', '').strip()
        token = data.get('token', '').strip()
        
        # Use environment variable if no token provided
        if not token:
            token = os.getenv('GITHUB_TOKEN')
        
        if not username and not token:
            return jsonify({
                'error': 'Please provide either a GitHub username or personal access token.'
            }), 400
        
        # Count repositories
        stats = count_repositories(username=username if username else None, token=token)
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404 error handler."""
    return render_template('error.html', 
                         error_code=404, 
                         error_message='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler."""
    return render_template('error.html', 
                         error_code=500, 
                         error_message='Internal server error'), 500

if __name__ == '__main__':
    app.run(debug=True)