#!/usr/bin/env python3
"""
Main application file demonstrating the use of github_utils module.
"""

import logging
import sys
from typing import Optional
from github_utils import list_repositories, get_repository_info, GitHubAPIError
from config import Config

# Set up logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format=Config.LOG_FORMAT
)
logger = logging.getLogger(__name__)

def main():
    """Main application entry point."""
    
    # Validate configuration
    if not Config.validate_config():
        logger.error("Invalid configuration detected")
        sys.exit(1)
    
    # Example usage
    try:
        # List repositories for a user
        print("Fetching repositories for user 'octocat'...")
        repos = list_repositories(username='octocat', per_page=5)
        
        print(f"\nFound {len(repos)} repositories:")
        for repo in repos:
            print(f"- {repo['name']}: {repo['description'] or 'No description'}")
            print(f"  Language: {repo['language'] or 'Unknown'}")
            print(f"  Stars: {repo['stars']}, Forks: {repo['forks']}")
            print(f"  URL: {repo['url']}\n")
        
        # Get detailed info for the first repository
        if repos:
            first_repo = repos[0]
            print(f"Getting detailed info for {first_repo['full_name']}...")
            
            owner, repo_name = first_repo['full_name'].split('/')
            detailed_info = get_repository_info(owner, repo_name)
            
            print(f"\nDetailed information for {detailed_info['full_name']}:")
            print(f"Description: {detailed_info['description'] or 'No description'}")
            print(f"Language: {detailed_info['language'] or 'Unknown'}")
            print(f"Stars: {detailed_info['stars']}")
            print(f"Forks: {detailed_info['forks']}")
            print(f"Watchers: {detailed_info['watchers']}")
            print(f"Size: {detailed_info['size']} KB")
            print(f"Created: {detailed_info['created_at']}")
            print(f"Updated: {detailed_info['updated_at']}")
            print(f"Default branch: {detailed_info['default_branch']}")
            print(f"Topics: {', '.join(detailed_info['topics']) if detailed_info['topics'] else 'None'}")
            print(f"License: {detailed_info['license'] or 'No license'}")
            print(f"Archived: {'Yes' if detailed_info['archived'] else 'No'}")
            print(f"Disabled: {'Yes' if detailed_info['disabled'] else 'No'}")
        
        # Example: List repositories for an organization
        print("\n" + "="*50)
        print("Fetching repositories for organization 'github'...")
        
        org_repos = list_repositories(org='github', per_page=3)
        print(f"\nFound {len(org_repos)} repositories:")
        
        for repo in org_repos:
            print(f"- {repo['name']}: {repo['description'] or 'No description'}")
            print(f"  Language: {repo['language'] or 'Unknown'}")
            print(f"  Stars: {repo['stars']}, Forks: {repo['forks']}")
            print()
        
    except GitHubAPIError as e:
        logger.error(f"GitHub API error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

def interactive_mode():
    """Interactive mode for exploring repositories."""
    
    print("GitHub Repository Explorer")
    print("="*30)
    
    while True:
        print("\nOptions:")
        print("1. List user repositories")
        print("2. List organization repositories")
        print("3. Get repository details")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        try:
            if choice == '1':
                username = input("Enter GitHub username: ").strip()
                if username:
                    repos = list_repositories(username=username, per_page=10)
                    display_repositories(repos)
                
            elif choice == '2':
                org = input("Enter GitHub organization: ").strip()
                if org:
                    repos = list_repositories(org=org, per_page=10)
                    display_repositories(repos)
                
            elif choice == '3':
                owner = input("Enter repository owner: ").strip()
                repo_name = input("Enter repository name: ").strip()
                if owner and repo_name:
                    repo_info = get_repository_info(owner, repo_name)
                    display_repository_details(repo_info)
                
            elif choice == '4':
                print("Goodbye!")
                break
                
            else:
                print("Invalid choice. Please enter 1-4.")
                
        except GitHubAPIError as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")

def display_repositories(repos):
    """Display a list of repositories in a formatted way."""
    
    if not repos:
        print("No repositories found.")
        return
    
    print(f"\nFound {len(repos)} repositories:")
    print("-" * 60)
    
    for i, repo in enumerate(repos, 1):
        print(f"{i}. {repo['name']}")
        print(f"   Description: {repo['description'] or 'No description'}")
        print(f"   Language: {repo['language'] or 'Unknown'}")
        print(f"   Stars: {repo['stars']} | Forks: {repo['forks']} | Size: {repo['size']} KB")
        print(f"   Updated: {repo['updated_at']}")
        print(f"   URL: {repo['url']}")
        print()

def display_repository_details(repo_info):
    """Display detailed repository information."""
    
    print(f"\nRepository Details: {repo_info['full_name']}")
    print("=" * 50)
    print(f"Description: {repo_info['description'] or 'No description'}")
    print(f"Language: {repo_info['language'] or 'Unknown'}")
    print(f"Stars: {repo_info['stars']}")
    print(f"Forks: {repo_info['forks']}")
    print(f"Watchers: {repo_info['watchers']}")
    print(f"Size: {repo_info['size']} KB")
    print(f"Created: {repo_info['created_at']}")
    print(f"Updated: {repo_info['updated_at']}")
    print(f"Default branch: {repo_info['default_branch']}")
    print(f"Topics: {', '.join(repo_info['topics']) if repo_info['topics'] else 'None'}")
    print(f"License: {repo_info['license'] or 'No license'}")
    print(f"Private: {'Yes' if repo_info['private'] else 'No'}")
    print(f"Archived: {'Yes' if repo_info['archived'] else 'No'}")
    print(f"Disabled: {'Yes' if repo_info['disabled'] else 'No'}")
    print(f"Clone URL (HTTPS): {repo_info['clone_url']}")
    print(f"Clone URL (SSH): {repo_info['ssh_url']}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GitHub Repository Explorer")
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--user', '-u', type=str,
                       help='GitHub username to list repositories for')
    parser.add_argument('--org', '-o', type=str,
                       help='GitHub organization to list repositories for')
    parser.add_argument('--count', '-c', type=int, default=10,
                       help='Number of repositories to fetch (default: 10)')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    elif args.user:
        try:
            repos = list_repositories(username=args.user, per_page=args.count)
            display_repositories(repos)
        except GitHubAPIError as e:
            print(f"Error: {e}")
            sys.exit(1)
    elif args.org:
        try:
            repos = list_repositories(org=args.org, per_page=args.count)
            display_repositories(repos)
        except GitHubAPIError as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        main()