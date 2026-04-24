import requests
from typing import Optional, Dict, Any
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
        else:
            self.session.headers.update({
                'Accept': 'application/vnd.github.v3+json'
            })
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make GET request to GitHub API.
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If request fails
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            raise requests.RequestException(f"GitHub API request failed: {str(e)}")
    
    def get_authenticated_user(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user.
        
        Returns:
            User information dictionary
            
        Raises:
            requests.RequestException: If request fails or user not authenticated
        """
        if not self.token:
            raise requests.RequestException("Authentication token required")
        
        response = self.get('/user')
        return response.json()
    
    def get_user_repositories(self, username: str, page: int = 1, per_page: int = 100) -> Dict[str, Any]:
        """
        Get repositories for a specific user.
        
        Args:
            username: GitHub username
            page: Page number for pagination
            per_page: Number of repositories per page (max 100)
            
        Returns:
            API response with repositories data
            
        Raises:
            requests.RequestException: If request fails
        """
        params = {
            'page': page,
            'per_page': min(per_page, 100),
            'sort': 'updated',
            'direction': 'desc'
        }
        
        response = self.get(f'/users/{username}/repos', params=params)
        return response.json()