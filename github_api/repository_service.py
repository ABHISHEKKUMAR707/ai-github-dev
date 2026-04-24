from typing import Dict, Any
import requests
from .client import GitHubClient


class RepositoryService:
    """Service for handling repository-related operations."""
    
    def __init__(self, client: GitHubClient):
        """
        Initialize repository service.
        
        Args:
            client: GitHubClient instance
        """
        self.client = client
    
    def get_user_repository_count(self, username: str) -> Dict[str, Any]:
        """
        Get the total count of repositories for a user.
        
        Args:
            username: GitHub username
            
        Returns:
            Dictionary containing repository count and user info
            
        Raises:
            requests.RequestException: If request fails
        """
        try:
            # First, get user info to verify user exists and get public repo count
            user_response = self.client.get(f'/users/{username}')
            user_data = user_response.json()
            
            # Get public repository count from user profile
            public_repos = user_data.get('public_repos', 0)
            
            # If we have authentication, we can also count private repos
            total_repos = public_repos
            private_repos = 0
            
            if self.client.token:
                try:
                    # Check if this is the authenticated user
                    auth_user = self.client.get_authenticated_user()
                    if auth_user.get('login') == username:
                        # For authenticated user, get total repo count including private
                        total_repos = user_data.get('total_private_repos', 0) + public_repos
                        private_repos = user_data.get('total_private_repos', 0)
                except requests.RequestException:
                    # If authentication fails, just use public count
                    pass
            
            return {
                'username': username,
                'public_repositories': public_repos,
                'private_repositories': private_repos,
                'total_repositories': total_repos,
                'profile_url': user_data.get('html_url'),
                'avatar_url': user_data.get('avatar_url'),
                'name': user_data.get('name'),
                'bio': user_data.get('bio')
            }
            
        except requests.RequestException as e:
            if 'Not Found' in str(e):
                raise requests.RequestException(f"User '{username}' not found")
            raise requests.RequestException(f"Failed to fetch repository count: {str(e)}")
    
    def get_authenticated_user_repository_count(self) -> Dict[str, Any]:
        """
        Get repository count for the authenticated user.
        
        Returns:
            Dictionary containing repository count and user info
            
        Raises:
            requests.RequestException: If not authenticated or request fails
        """
        if not self.client.token:
            raise requests.RequestException("Authentication required to get user repository count")
        
        try:
            user_data = self.client.get_authenticated_user()
            username = user_data.get('login')
            
            return self.get_user_repository_count(username)
            
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch authenticated user repository count: {str(e)}")