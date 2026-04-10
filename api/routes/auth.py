from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import httpx
import secrets
from jose import jwt
from datetime import datetime, timedelta
import redis

from config.settings import settings
from config.encryption import encrypt_token
from db.session import get_db
from db.models import User

router = APIRouter(prefix='/auth', tags=['auth'])

GITHUB_AUTH_URL  = 'https://github.com/login/oauth/authorize'
GITHUB_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GITHUB_USER_API  = 'https://api.github.com/user'

# Redis for CSRF state storage
redis_client = redis.from_url(settings.redis_url)


def create_jwt_token(user_id: int, github_username: str) -> str:
    '''
    Creates a JWT token for the client to use
    in all future API requests.
    '''
    payload = {
        'user_id':         user_id,
        'github_username': github_username,
        'exp':             datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(
        payload,
        settings.app_secret_key,
        algorithm='HS256'
    )


@router.get('/github/login')
async def github_login():
    '''
    Step 1: Redirect user to GitHub OAuth page.
    Generates unique state token and stores in Redis.
    '''
    state = secrets.token_urlsafe(32)

    # Store state in Redis with 10 minute expiry
    redis_client.setex(f'oauth_state:{state}', 600, '1')

    params = {
        'client_id': settings.github_client_id,
        'scope':     'repo user:email',
        'state':     state
    }
    query = '&'.join(f'{k}={v}' for k, v in params.items())
    return RedirectResponse(f'{GITHUB_AUTH_URL}?{query}')


@router.get('/github/callback')
async def github_callback(
    code:  str = Query(...),
    state: str = Query(...),
    db:    Session = Depends(get_db)
):
    '''
    Step 2: GitHub redirects here after user approves.
    1. Verify state (CSRF check via Redis)
    2. Exchange code for token
    3. Encrypt and save to MySQL
    4. Return JWT to client
    '''

    # CSRF check via Redis
    state_key = f'oauth_state:{state}'
    if not redis_client.get(state_key):
        raise HTTPException(
            status_code=400,
            detail='Invalid or expired state. Please login again.'
        )
    redis_client.delete(state_key)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:

            # Exchange code for GitHub token
            token_response = await client.post(
                GITHUB_TOKEN_URL,
                headers={'Accept': 'application/json'},
                data={
                    'client_id':     settings.github_client_id,
                    'client_secret': settings.github_client_secret,
                    'code':          code,
                }
            )
            token_data = token_response.json()

            if 'error' in token_data:
                raise HTTPException(
                    status_code=400,
                    detail=f'GitHub error: {token_data.get("error_description")}'
                )

            access_token = token_data.get('access_token')
            if not access_token:
                raise HTTPException(
                    status_code=400,
                    detail='No access token returned from GitHub.'
                )

            # Get GitHub user info
            user_response = await client.get(
                GITHUB_USER_API,
                headers={'Authorization': f'Bearer {access_token}'}
            )

            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail='Failed to fetch GitHub user info.'
                )

            github_user = user_response.json()

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail='GitHub API timed out.')
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f'Network error: {str(e)}')

    # Encrypt token before saving
    encrypted = encrypt_token(access_token)

    # Save or update user in MySQL
    user = db.query(User).filter(
        User.github_id == github_user['id']
    ).first()

    if user:
        # Existing user — update token
        user.encrypted_github_token = encrypted
        user.github_username        = github_user['login']
        user.avatar_url             = github_user.get('avatar_url')
        user.email                  = github_user.get('email')
    else:
        # New user — create record
        user = User(
            github_id              = github_user['id'],
            github_username        = github_user['login'],
            email                  = github_user.get('email'),
            avatar_url             = github_user.get('avatar_url'),
            encrypted_github_token = encrypted
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    # Generate JWT for client
    jwt_token = create_jwt_token(user.id, user.github_username)

    return {
        'access_token':    jwt_token,
        'token_type':      'bearer',
        'github_username': user.github_username,
        'avatar_url':      user.avatar_url
    }
