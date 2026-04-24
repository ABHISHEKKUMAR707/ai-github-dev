from flask import Blueprint, render_template, request, jsonify, flash
from github_api.client import GitHubAPIClient
import logging

github_bp = Blueprint('github', __name__)
logger = logging.getLogger(__name__)

@github_bp.route('/')
def index():
    """Main page with search form"""
    return render_template('repository_search.html')

@github_bp.route('/search', methods=['GET', 'POST'])
def search_repositories():
    """Search repositories for a specific username"""
    if request.method == 'GET':
        return render_template('repository_search.html')
    
    username = request.form.get('username', '').strip()
    repo_filter = request.form.get('filter', 'all')
    
    if not username:
        flash('Please enter a username', 'error')
        return render_template('repository_search.html')
    
    try:
        client = GitHubAPIClient()
        
        # Get user info
        user_info = client.get_user_info(username)
        
        # Get repositories
        repositories = client.get_user_repositories(username)
        
        # Apply filters
        filtered_repos = client.filter_repositories(repositories, repo_filter)
        
        # Get statistics
        stats = client.get_repository_stats(repositories)
        filtered_stats = client.get_repository_stats(filtered_repos)
        
        return render_template('repository_search.html',
                             user_info=user_info,
                             repositories=filtered_repos,
                             stats=stats,
                             filtered_stats=filtered_stats,
                             current_filter=repo_filter,
                             search_performed=True)
                             
    except ValueError as e:
        flash(str(e), 'error')
        logger.error(f"Error searching repositories for {username}: {e}")
        return render_template('repository_search.html')
    except Exception as e:
        flash('An unexpected error occurred. Please try again.', 'error')
        logger.error(f"Unexpected error searching repositories for {username}: {e}")
        return render_template('repository_search.html')

@github_bp.route('/api/search/<username>')
def api_search_repositories(username):
    """API endpoint for searching repositories"""
    try:
        client = GitHubAPIClient()
        repo_filter = request.args.get('filter', 'all')
        
        # Get user info and repositories
        user_info = client.get_user_info(username)
        repositories = client.get_user_repositories(username)
        filtered_repos = client.filter_repositories(repositories, repo_filter)
        stats = client.get_repository_stats(repositories)
        
        return jsonify({
            'success': True,
            'user_info': user_info,
            'repositories': filtered_repos,
            'stats': stats,
            'total_repositories': len(repositories),
            'filtered_count': len(filtered_repos)
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error(f"API error searching repositories for {username}: {e}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500