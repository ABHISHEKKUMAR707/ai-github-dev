from flask import Blueprint, jsonify, request
import requests
import os
from github_api import GitHubClient, RepositoryService

github_bp = Blueprint('github', __name__, url_prefix='/api/github')


@github_bp.route('/repositories/count', methods=['GET'])
def get_repository_count():
    """
    Get repository count for a GitHub user.
    
    Query Parameters:
        username (optional): GitHub username. If not provided, uses authenticated user.
        token (optional): GitHub personal access token for authentication.
    
    Returns:
        JSON response with repository count information
    """
    try:
        # Get parameters
        username = request.args.get('username')
        token = request.args.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '') or os.getenv('GITHUB_TOKEN')
        
        # Initialize GitHub client
        client = GitHubClient(token=token)
        service = RepositoryService(client)
        
        # Get repository count
        if username:
            # Get count for specific user
            result = service.get_user_repository_count(username)
        else:
            # Get count for authenticated user
            result = service.get_authenticated_user_repository_count()
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except requests.RequestException as e:
        error_message = str(e)
        status_code = 404 if 'not found' in error_message.lower() else 400
        
        return jsonify({
            'success': False,
            'error': error_message
        }), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }), 500


@github_bp.route('/user/repositories/count', methods=['GET'])
def get_my_repository_count():
    """
    Get repository count for the authenticated user.
    Simplified endpoint that requires authentication.
    
    Headers:
        Authorization: Bearer <github_token>
    
    Returns:
        JSON response with repository count information
    """
    try:
        # Get token from headers or environment
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else os.getenv('GITHUB_TOKEN')
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'GitHub token required. Provide it in Authorization header or GITHUB_TOKEN environment variable.'
            }), 401
        
        # Initialize GitHub client and service
        client = GitHubClient(token=token)
        service = RepositoryService(client)
        
        # Get repository count for authenticated user
        result = service.get_authenticated_user_repository_count()
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except requests.RequestException as e:
        error_message = str(e)
        status_code = 401 if 'Authentication' in error_message else 400
        
        return jsonify({
            'success': False,
            'error': error_message
        }), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }), 500


@github_bp.route('/health', methods=['GET'])
def github_health_check():
    """Health check endpoint for GitHub API integration."""
    try:
        # Test GitHub API connectivity
        client = GitHubClient()
        response = client.get('/rate_limit')
        
        return jsonify({
            'success': True,
            'message': 'GitHub API integration is healthy',
            'rate_limit': response.json()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'GitHub API integration health check failed',
            'error': str(e)
        }), 503