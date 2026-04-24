import requests
from typing import Optional, Dict, Any, List
import os


class GitHubClient:
    """GitHub API client for handling authentication and requests."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token. If None, will try to get from environment.
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.session = requests.Session()
        
        if self.token:
            self.session.headers.update({
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json'
            })
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make a GET request to GitHub API.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response
    
    def get_authenticated_user(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user.
        
        Returns:
            User information dictionary
            
        Raises:
            requests.RequestException: If request fails or not authenticated
        """
        if not self.token:
            raise ValueError("GitHub token is required for authenticated requests")
        
        response = self.get('user')
        return response.json()
    
    def get_user_repositories(self, username: Optional[str] = None, 
                            per_page: int = 100, page: int = 1) -> List[Dict[str, Any]]:
        """
        Get repositories for a user.
        
        Args:
            username: GitHub username. If None, gets repos for authenticated user.
            per_page: Number of repositories per page (max 100)
            page: Page number to fetch
            
        Returns:
            List of repository dictionaries
            
        Raises:
            requests.RequestException: If request fails
        """
        per_page = min(per_page, 100)  # GitHub API limit
        
        if username:
            endpoint = f'users/{username}/repos'
        else:
            if not self.token:
                raise ValueError("GitHub token is required to get authenticated user's repositories")
            endpoint = 'user/repos'
        
        params = {
            'per_page': per_page,
            'page': page,
            'sort': 'updated',
            'direction': 'desc'
        }
        
        response = self.get(endpoint, params=params)
        return response.json()
    
    def get_all_user_repositories(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all repositories for a user (handles pagination).
        
        Args:
            username: GitHub username. If None, gets repos for authenticated user.
            
        Returns:
            List of all repository dictionaries
            
        Raises:
            requests.RequestException: If request fails
        """
        all_repos = []
        page = 1
        per_page = 100
        
        while True:
            repos = self.get_user_repositories(username=username, per_page=per_page, page=page)
            
            if not repos:
                break
                
            all_repos.extend(repos)
            
            # If we got fewer repos than requested, we've reached the end
            if len(repos) < per_page:
                break
                
            page += 1
        
        return all_repos