import requests
from typing import List, Dict, Any, Optional
from .auth import GitHubAuth

class GitHubAPIClient:
    """GitHub API client for fetching user repositories"""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.auth = GitHubAuth()
        self.session = requests.Session()
        self.session.headers.update(self.auth.get_headers())
    
    def get_user_repositories(self, username: str, per_page: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch all repositories for a given username
        
        Args:
            username: GitHub username
            per_page: Number of repositories per page (max 100)
            
        Returns:
            List of repository dictionaries
        """
        repositories = []
        page = 1
        
        while True:
            try:
                url = f"{self.base_url}/users/{username}/repos"
                params = {
                    'per_page': per_page,
                    'page': page,
                    'type': 'all',
                    'sort': 'updated',
                    'direction': 'desc'
                }
                
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                page_repos = response.json()
                
                if not page_repos:
                    break
                
                repositories.extend(page_repos)
                page += 1
                
            except requests.exceptions.RequestException as e:
                if hasattr(e.response, 'status_code') and e.response.status_code == 404:
                    raise ValueError(f"User '{username}' not found")
                elif hasattr(e.response, 'status_code') and e.response.status_code == 403:
                    raise ValueError("GitHub API rate limit exceeded or access denied")
                else:
                    raise ValueError(f"Error fetching repositories: {str(e)}")
        
        return repositories
    
    def get_user_info(self, username: str) -> Dict[str, Any]:
        """
        Get basic user information
        
        Args:
            username: GitHub username
            
        Returns:
            User information dictionary
        """
        try:
            url = f"{self.base_url}/users/{username}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            if hasattr(e.response, 'status_code') and e.response.status_code == 404:
                raise ValueError(f"User '{username}' not found")
            else:
                raise ValueError(f"Error fetching user info: {str(e)}")
    
    def filter_repositories(self, repositories: List[Dict[str, Any]], repo_type: str = "all") -> List[Dict[str, Any]]:
        """
        Filter repositories by type
        
        Args:
            repositories: List of repository dictionaries
            repo_type: Filter type ('all', 'public', 'private', 'forks', 'sources')
            
        Returns:
            Filtered list of repositories
        """
        if repo_type == "all":
            return repositories
        elif repo_type == "public":
            return [repo for repo in repositories if not repo.get('private', False)]
        elif repo_type == "private":
            return [repo for repo in repositories if repo.get('private', False)]
        elif repo_type == "forks":
            return [repo for repo in repositories if repo.get('fork', False)]
        elif repo_type == "sources":
            return [repo for repo in repositories if not repo.get('fork', False)]
        else:
            return repositories
    
    def get_repository_stats(self, repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate statistics for a list of repositories
        
        Args:
            repositories: List of repository dictionaries
            
        Returns:
            Dictionary containing repository statistics
        """
        if not repositories:
            return {
                'total_count': 0,
                'public_count': 0,
                'private_count': 0,
                'fork_count': 0,
                'source_count': 0,
                'languages': {},
                'total_stars': 0,
                'total_forks': 0
            }
        
        public_repos = [repo for repo in repositories if not repo.get('private', False)]
        private_repos = [repo for repo in repositories if repo.get('private', False)]
        forks = [repo for repo in repositories if repo.get('fork', False)]
        sources = [repo for repo in repositories if not repo.get('fork', False)]
        
        languages = {}
        for repo in repositories:
            lang = repo.get('language')
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
        
        total_stars = sum(repo.get('stargazers_count', 0) for repo in repositories)
        total_forks = sum(repo.get('forks_count', 0) for repo in repositories)
        
        return {
            'total_count': len(repositories),
            'public_count': len(public_repos),
            'private_count': len(private_repos),
            'fork_count': len(forks),
            'source_count': len(sources),
            'languages': languages,
            'total_stars': total_stars,
            'total_forks': total_forks
        }