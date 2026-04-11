from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from config.settings import settings
from db.session import get_db
from db.models import User
from sqlalchemy.orm import Session

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency — validates JWT and returns current user.
    Use this in any route that needs authentication.

    Usage:
        @router.post("/something")
        async def my_route(user: User = Depends(get_current_user)):
            ...
    """
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.app_secret_key,
            algorithms=["HS256"]
        )
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user_id"
            )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token. Please login again."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is disabled."
        )

    return user
