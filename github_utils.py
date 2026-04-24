import requests
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""
    pass

def get_github_token() -> Optional[str]:
    """
    Get GitHub token from environment variable.
    
    Returns:
        str: GitHub token if found, None otherwise
    """
    return os.getenv('GITHUB_TOKEN')

def list_repositories(username: Optional[str] = None, 
                     org: Optional[str] = None,
                     per_page: int = 30,
                     page: int = 1) -> List[Dict]:
    """
    List repositories for a user or organization using GitHub API.
    
    Args:
        username (str, optional): GitHub username to list repositories for
        org (str, optional): GitHub organization to list repositories for
        per_page (int): Number of repositories per page (max 100)
        page (int): Page number to retrieve
        
    Returns:
        List[Dict]: List of repository dictionaries containing repo information
        
    Raises:
        GitHubAPIError: If API request fails or returns error
        ValueError: If neither username nor org is provided
    """
    if not username and not org:
        raise ValueError("Either username or org must be provided")
    
    if username and org:
        raise ValueError("Cannot specify both username and org")
    
    # Validate pagination parameters
    if per_page < 1 or per_page > 100:
        raise ValueError("per_page must be between 1 and 100")
    
    if page < 1:
        raise ValueError("page must be >= 1")
    
    # Construct API URL
    if username:
        url = f"https://api.github.com/users/{username}/repos"
    else:
        url = f"https://api.github.com/orgs/{org}/repos"
    
    # Set up headers
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'github-utils/1.0'
    }
    
    # Add authentication if token is available
    token = get_github_token()
    if token:
        headers['Authorization'] = f'token {token}'
    
    # Set up parameters
    params = {
        'per_page': per_page,
        'page': page,
        'sort': 'updated',
        'direction': 'desc'
    }
    
    try:
        logger.info(f"Fetching repositories for {'user' if username else 'org'}: {username or org}")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        # Handle rate limiting
        if response.status_code == 403 and 'rate limit' in response.text.lower():
            raise GitHubAPIError(f"GitHub API rate limit exceeded. Reset at: {response.headers.get('X-RateLimit-Reset')}")
        
        # Handle authentication errors
        if response.status_code == 401:
            raise GitHubAPIError("Invalid GitHub token or authentication required")
        
        # Handle not found errors
        if response.status_code == 404:
            raise GitHubAPIError(f"User or organization '{username or org}' not found")
        
        # Raise for other HTTP errors
        response.raise_for_status()
        
        repositories = response.json()
        
        # Extract relevant information from each repository
        repo_list = []
        for repo in repositories:
            repo_info = {
                'name': repo['name'],
                'full_name': repo['full_name'],
                'description': repo.get('description'),
                'url': repo['html_url'],
                'clone_url': repo['clone_url'],
                'ssh_url': repo['ssh_url'],
                'private': repo['private'],
                'language': repo.get('language'),
                'stars': repo['stargazers_count'],
                'forks': repo['forks_count'],
                'size': repo['size'],
                'created_at': repo['created_at'],
                'updated_at': repo['updated_at'],
                'default_branch': repo['default_branch']
            }
            repo_list.append(repo_info)
        
        logger.info(f"Successfully retrieved {len(repo_list)} repositories")
        return repo_list
        
    except requests.exceptions.Timeout:
        raise GitHubAPIError("Request timed out while connecting to GitHub API")
    except requests.exceptions.ConnectionError:
        raise GitHubAPIError("Failed to connect to GitHub API")
    except requests.exceptions.HTTPError as e:
        raise GitHubAPIError(f"HTTP error occurred: {e}")
    except requests.exceptions.RequestException as e:
        raise GitHubAPIError(f"Request error occurred: {e}")
    except ValueError as e:
        raise GitHubAPIError(f"Invalid JSON response from GitHub API: {e}")

def get_repository_info(owner: str, repo_name: str) -> Dict:
    """
    Get detailed information about a specific repository.
    
    Args:
        owner (str): Repository owner (username or organization)
        repo_name (str): Repository name
        
    Returns:
        Dict: Repository information dictionary
        
    Raises:
        GitHubAPIError: If API request fails or returns error
    """
    url = f"https://api.github.com/repos/{owner}/{repo_name}"
    
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'github-utils/1.0'
    }
    
    token = get_github_token()
    if token:
        headers['Authorization'] = f'token {token}'
    
    try:
        logger.info(f"Fetching repository info for {owner}/{repo_name}")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 404:
            raise GitHubAPIError(f"Repository '{owner}/{repo_name}' not found")
        
        response.raise_for_status()
        repo = response.json()
        
        repo_info = {
            'name': repo['name'],
            'full_name': repo['full_name'],
            'description': repo.get('description'),
            'url': repo['html_url'],
            'clone_url': repo['clone_url'],
            'ssh_url': repo['ssh_url'],
            'private': repo['private'],
            'language': repo.get('language'),
            'stars': repo['stargazers_count'],
            'forks': repo['forks_count'],
            'watchers': repo['watchers_count'],
            'size': repo['size'],
            'created_at': repo['created_at'],
            'updated_at': repo['updated_at'],
            'default_branch': repo['default_branch'],
            'topics': repo.get('topics', []),
            'license': repo.get('license', {}).get('name') if repo.get('license') else None,
            'archived': repo['archived'],
            'disabled': repo['disabled']
        }
        
        logger.info(f"Successfully retrieved repository info for {owner}/{repo_name}")
        return repo_info
        
    except requests.exceptions.RequestException as e:
        raise GitHubAPIError(f"Error fetching repository info: {e}")