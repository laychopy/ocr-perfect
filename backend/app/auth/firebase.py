"""Firebase Authentication middleware and utilities."""

from typing import Optional

import firebase_admin
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth, credentials

from app.config import get_settings
from app.models.schemas import UserInfo

# Initialize Firebase Admin SDK
# Uses Application Default Credentials (ADC) in Cloud Run
# or GOOGLE_APPLICATION_CREDENTIALS locally
if not firebase_admin._apps:
    settings = get_settings()
    try:
        # Try default credentials (works in Cloud Run)
        firebase_admin.initialize_app(
            options={"projectId": settings.gcp_project}
        )
    except Exception:
        # Fallback for local development
        firebase_admin.initialize_app()

# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> UserInfo:
    """
    Verify Firebase ID token and return user info.

    Args:
        credentials: Bearer token from Authorization header

    Returns:
        UserInfo with uid, email, name, and picture

    Raises:
        HTTPException: If token is missing or invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Verify the ID token
        decoded_token = auth.verify_id_token(token)

        return UserInfo(
            uid=decoded_token["uid"],
            email=decoded_token.get("email"),
            name=decoded_token.get("name"),
            picture=decoded_token.get("picture"),
        )

    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[UserInfo]:
    """
    Optionally verify Firebase ID token.

    Returns None if no token provided, UserInfo if valid token.
    Raises HTTPException only if token is provided but invalid.
    """
    if credentials is None:
        return None

    return await get_current_user(credentials)
