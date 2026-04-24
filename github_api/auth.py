import os
from typing import Optional

class GitHubAuth:
    """Handle GitHub API authentication"""
    
    def __init__(self):
        self.token = self._get_token()
    
    def _get_token(self) -> Optional[str]:
        """Get GitHub token from environment variables"""
        return os.getenv('GITHUB_TOKEN')
    
    def get_headers(self) -> dict:
        """Get authentication headers for GitHub API requests"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Repository-Search-App'
        }
        
        if self.token:
            headers['Authorization'] = f'token {self.token}'
        
        return headers
    
    def is_authenticated(self) -> bool:
        """Check if we have a valid token"""
        return self.token is not None