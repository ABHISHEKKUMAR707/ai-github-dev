from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    app_env:               str = 'development'
    app_secret_key:        str

    # GitHub
    github_client_id:      str
    github_client_secret:  str
    redirect_uri:          str = 'http://localhost:8000/auth/github/callback'

    # Anthropic Claude
    anthropic_api_key:     str
    claude_model:          str = 'claude-sonnet-4-20250514'

    # MySQL — individual fields
    mysql_host:            str = 'localhost'
    mysql_port:            int = 3306
    mysql_user:            str = 'root'
    mysql_password:        str
    mysql_database:        str = 'ai_github_dev'

    # MySQL — full URL (built from above)
    database_url:          str

    # Redis
    redis_url:             str

    # Encryption
    token_encryption_key:  str

    # Agent
    max_retries:           int = 3
    agent_timeout_seconds: int = 120
    max_context_tokens:    int = 8000

    class Config:
        env_file = '.env'
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
