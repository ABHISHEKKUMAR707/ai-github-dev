import os
from typing import Optional

class Config:
    """Configuration class for application settings."""
    
    # GitHub API Configuration
    GITHUB_TOKEN: Optional[str] = os.getenv('GITHUB_TOKEN')
    GITHUB_API_URL: str = os.getenv('GITHUB_API_URL', 'https://api.github.com')
    
    # Request Configuration
    REQUEST_TIMEOUT: int = int(os.getenv('REQUEST_TIMEOUT', '30'))
    DEFAULT_PER_PAGE: int = int(os.getenv('DEFAULT_PER_PAGE', '30'))
    MAX_PER_PAGE: int = int(os.getenv('MAX_PER_PAGE', '100'))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT: str = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    @classmethod
    def validate_config(cls) -> bool:
        """
        Validate configuration settings.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        if cls.REQUEST_TIMEOUT <= 0:
            return False
            
        if cls.DEFAULT_PER_PAGE <= 0 or cls.DEFAULT_PER_PAGE > cls.MAX_PER_PAGE:
            return False
            
        return True
    
    @classmethod
    def get_github_token(cls) -> Optional[str]:
        """
        Get GitHub token with fallback methods.
        
        Returns:
            str: GitHub token if found, None otherwise
        """
        # Try environment variable first
        token = cls.GITHUB_TOKEN
        if token:
            return token
        
        # Try reading from file (common in containerized environments)
        token_file = os.getenv('GITHUB_TOKEN_FILE')
        if token_file and os.path.exists(token_file):
            try:
                with open(token_file, 'r') as f:
                    return f.read().strip()
            except IOError:
                pass
        
        return None