from typing import Optional, Dict, Any, List, Tuple
from .client import GitHubClient


def get_user_repositories(username: Optional[str] = None, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get all repositories for a GitHub user.
    
    Args:
        username: GitHub username. If None, uses authenticated user.
        token: GitHub personal access token
        
    Returns:
        List of repository dictionaries
        
    Raises:
        Exception: If GitHub API request fails
    """
    try:
        client = GitHubClient(token=token)
        repositories = client.get_all_user_repositories(username=username)
        return repositories
    except Exception as e:
        raise Exception(f"Failed to fetch repositories: {str(e)}")


def count_repositories(username: Optional[str] = None, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Count repositories for a GitHub user with detailed breakdown.
    
    Args:
        username: GitHub username. If None, uses authenticated user.
        token: GitHub personal access token
        
    Returns:
        Dictionary containing repository counts and details
        
    Raises:
        Exception: If GitHub API request fails
    """
    try:
        repositories = get_user_repositories(username=username, token=token)
        
        # Count different types of repositories
        total_count = len(repositories)
        public_count = sum(1 for repo in repositories if not repo.get('private', False))
        private_count = sum(1 for repo in repositories if repo.get('private', False))
        fork_count = sum(1 for repo in repositories if repo.get('fork', False))
        original_count = sum(1 for repo in repositories if not repo.get('fork', False))
        archived_count = sum(1 for repo in repositories if repo.get('archived', False))
        
        # Get language breakdown
        languages = {}
        for repo in repositories:
            if repo.get('language'):
                lang = repo['language']
                languages[lang] = languages.get(lang, 0) + 1
        
        # Sort languages by count
        top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Calculate total stars and forks
        total_stars = sum(repo.get('stargazers_count', 0) for repo in repositories)
        total_forks = sum(repo.get('forks_count', 0) for repo in repositories)
        
        # Get user info if possible
        user_info = {}
        try:
            client = GitHubClient(token=token)
            if not username and token:
                user_info = client.get_authenticated_user()
                username = user_info.get('login', 'Unknown')
            elif username:
                response = client.get(f'users/{username}')
                user_info = response.json()
        except:
            # If we can't get user info, continue with what we have
            pass
        
        return {
            'username': username or 'Unknown',
            'total_repositories': total_count,
            'public_repositories': public_count,
            'private_repositories': private_count,
            'forked_repositories': fork_count,
            'original_repositories': original_count,
            'archived_repositories': archived_count,
            'total_stars': total_stars,
            'total_forks': total_forks,
            'top_languages': top_languages,
            'user_info': {
                'name': user_info.get('name', ''),
                'bio': user_info.get('bio', ''),
                'location': user_info.get('location', ''),
                'public_repos': user_info.get('public_repos', 0),
                'followers': user_info.get('followers', 0),
                'following': user_info.get('following', 0),
                'avatar_url': user_info.get('avatar_url', ''),
                'html_url': user_info.get('html_url', '')
            }
        }
        
    except Exception as e:
        raise Exception(f"Failed to count repositories: {str(e)}")


def get_repository_summary(username: Optional[str] = None, token: Optional[str] = None) -> str:
    """
    Get a text summary of repository statistics.
    
    Args:
        username: GitHub username. If None, uses authenticated user.
        token: GitHub personal access token
        
    Returns:
        Formatted string summary of repository statistics
        
    Raises:
        Exception: If GitHub API request fails
    """
    try:
        stats = count_repositories(username=username, token=token)
        
        summary = f"GitHub Repository Summary for {stats['username']}:\n"
        summary += f"Total Repositories: {stats['total_repositories']}\n"
        summary += f"Public: {stats['public_repositories']}, Private: {stats['private_repositories']}\n"
        summary += f"Original: {stats['original_repositories']}, Forks: {stats['forked_repositories']}\n"
        summary += f"Archived: {stats['archived_repositories']}\n"
        summary += f"Total Stars: {stats['total_stars']}, Total Forks: {stats['total_forks']}\n"
        
        if stats['top_languages']:
            summary += f"\nTop Languages:\n"
            for lang, count in stats['top_languages'][:5]:
                summary += f"  {lang}: {count} repositories\n"
        
        return summary
        
    except Exception as e:
        raise Exception(f"Failed to generate repository summary: {str(e)}")