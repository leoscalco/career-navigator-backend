"""
Authentication API endpoints for registration, login, and OAuth.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from career_navigator.api.schemas.auth import UserRegister, UserLogin, Token, OAuthProvider, OAuthCallback
from career_navigator.domain.services.auth_service import AuthService
from career_navigator.domain.repositories.user_repository import UserRepository
from career_navigator.infrastructure.repositories.user_repository import SQLAlchemyUserRepository
from career_navigator.infrastructure.database.session import get_db
from career_navigator.domain.models.user import User as DomainUser
from career_navigator.domain.models.user_group import UserGroup
from career_navigator.config import settings
import secrets

router = APIRouter(prefix="/auth", tags=["authentication"])
# HTTPBearer with auto_error=True (default) - will raise 403 if no token provided
# This is correct for protected endpoints
security = HTTPBearer(auto_error=True)


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    """Dependency to get user repository."""
    return SQLAlchemyUserRepository(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    repository: UserRepository = Depends(get_user_repository),
) -> DomainUser:
    """Dependency to get current authenticated user."""
    try:
        token = credentials.credentials
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token. Please include 'Authorization: Bearer <token>' header.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        payload = AuthService.verify_token(token)
        if payload is None:
            # Try to decode without verification to get more specific error
            import logging
            from jose import jwt as jose_jwt
            logger = logging.getLogger(__name__)
            try:
                # Decode without verification to see what's wrong
                unverified = jose_jwt.decode(token, options={"verify_signature": False})
                logger.warning(f"Token decode without verification succeeded. User ID: {unverified.get('sub')}, Exp: {unverified.get('exp')}")
                # Check if expired
                from datetime import datetime
                exp = unverified.get('exp')
                if exp and datetime.utcnow().timestamp() > exp:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication token has expired. Please login again.",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            except Exception as decode_error:
                logger.warning(f"Token decode error: {str(decode_error)}")
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token. Please login again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # JWT "sub" claim is stored as string, convert to int
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing user ID",
            )
        try:
            user_id: int = int(user_id_str)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: user ID must be a number",
            )
        
        user = repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"User {user_id} not found",
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user",
            )
        
        return user
    except HTTPException:
        raise
    except Exception as e:
        # Log unexpected errors for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Authentication error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserRegister,
    repository: UserRepository = Depends(get_user_repository),
):
    """Register a new user with email and password."""
    # Check if user already exists
    existing_user = repository.get_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Generate username if not provided
    username = user_data.username or user_data.email.split("@")[0]
    
    # Check username uniqueness
    # Note: This is a simplified check - you might want to add a get_by_username method
    all_users = repository.get_all()
    existing_usernames = {u.username for u in all_users if u.username}
    base_username = username
    counter = 1
    while username in existing_usernames:
        username = f"{base_username}_{counter}"
        counter += 1
    
    # Hash password
    password_hash = AuthService.get_password_hash(user_data.password)
    
    # Create user
    new_user = DomainUser(
        email=user_data.email,
        username=username,
        password_hash=password_hash,
        user_group=UserGroup.INEXPERIENCED_NO_GOAL,  # Default, will be updated after CV parsing
        is_active=True,
        is_verified=False,  # Email verification can be added later
    )
    
    created_user = repository.create(new_user)
    
    # Create access token - JWT requires "sub" to be a string
    access_token = AuthService.create_access_token(data={"sub": str(created_user.id), "email": created_user.email})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=created_user.id,
        email=created_user.email,
    )


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    repository: UserRepository = Depends(get_user_repository),
):
    """Login with email and password."""
    user = repository.get_by_email(credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account created with OAuth. Please use OAuth login.",
        )
    
    if not AuthService.verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    # Create access token - JWT requires "sub" to be a string
    access_token = AuthService.create_access_token(data={"sub": str(user.id), "email": user.email})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
    )


@router.get("/me")
def get_current_user_info(current_user: DomainUser = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "is_verified": current_user.is_verified,
        "oauth_provider": current_user.oauth_provider,
    }


@router.get("/test-token")
def test_token(current_user: DomainUser = Depends(get_current_user)):
    """Test endpoint to verify token is being read correctly."""
    return {
        "success": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "message": "Token is valid and user is authenticated"
    }


@router.get("/oauth/{provider}/authorize")
def oauth_authorize(provider: str):
    """Get OAuth authorization URL for the provider."""
    # Build redirect URI with provider
    redirect_uri = f"{settings.OAUTH_REDIRECT_URI}/{provider}"
    
    if provider == "google":
        if not settings.GOOGLE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth not configured",
            )
        state = secrets.token_urlsafe(32)
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={settings.GOOGLE_CLIENT_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope=openid email profile&"
            f"state={state}"
        )
        return {"auth_url": auth_url, "state": state}
    
    elif provider == "github":
        if not settings.GITHUB_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub OAuth not configured",
            )
        state = secrets.token_urlsafe(32)
        auth_url = (
            f"https://github.com/login/oauth/authorize?"
            f"client_id={settings.GITHUB_CLIENT_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"scope=user:email&"
            f"state={state}"
        )
        return {"auth_url": auth_url, "state": state}
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}",
        )


@router.post("/oauth/{provider}/callback", response_model=Token)
async def oauth_callback(
    provider: str,
    callback_data: OAuthCallback,
    repository: UserRepository = Depends(get_user_repository),
):
    """Handle OAuth callback and create/login user."""
    import httpx
    
    if provider == "google":
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth not configured",
            )
        
        # Exchange code for token
        redirect_uri = f"{settings.OAUTH_REDIRECT_URI}/{provider}"
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": callback_data.code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange OAuth code",
                )
            tokens = token_response.json()
            access_token = tokens.get("access_token")
            
            # Get user info
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info",
                )
            user_info = user_response.json()
            
            email = user_info.get("email")
            oauth_provider_id = user_info.get("id")
            name = user_info.get("name", "")
    
    elif provider == "github":
        if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GitHub OAuth not configured",
            )
        
        # Exchange code for token
        redirect_uri = f"{settings.OAUTH_REDIRECT_URI}/{provider}"
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "code": callback_data.code,
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                },
                headers={"Accept": "application/json"},
            )
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange OAuth code",
                )
            tokens = token_response.json()
            access_token = tokens.get("access_token")
            
            # Get user info
            user_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"token {access_token}"},
            )
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info",
                )
            user_info = user_response.json()
            
            # Get email (might need separate call)
            email_response = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"token {access_token}"},
            )
            emails = email_response.json() if email_response.status_code == 200 else []
            primary_email = next((e for e in emails if e.get("primary")), emails[0] if emails else {})
            email = primary_email.get("email") or user_info.get("email")
            
            oauth_provider_id = str(user_info.get("id"))
            name = user_info.get("name") or user_info.get("login", "")
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}",
        )
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not provided by OAuth provider",
        )
    
    # Check if user exists
    user = repository.get_by_email(email)
    
    if user:
        # Update OAuth info if needed
        if not user.oauth_provider or user.oauth_provider != provider:
            # This would require an update method - for now, just login
            pass
    else:
        # Create new user
        username = name.replace(" ", "_").lower()[:100] if name else email.split("@")[0]
        
        # Ensure username uniqueness
        all_users = repository.get_all()
        existing_usernames = {u.username for u in all_users if u.username}
        base_username = username
        counter = 1
        while username in existing_usernames:
            username = f"{base_username}_{counter}"
            counter += 1
        
        new_user = DomainUser(
            email=email,
            username=username,
            password_hash=None,  # OAuth users don't have passwords
            oauth_provider=provider,
            oauth_provider_id=oauth_provider_id,
            oauth_access_token=access_token,  # In production, encrypt this
            user_group=UserGroup.INEXPERIENCED_NO_GOAL,
            is_active=True,
            is_verified=True,  # OAuth emails are considered verified
        )
        user = repository.create(new_user)
    
    # Create access token - JWT requires "sub" to be a string
    access_token_jwt = AuthService.create_access_token(data={"sub": str(user.id), "email": user.email})
    
    return Token(
        access_token=access_token_jwt,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
    )

