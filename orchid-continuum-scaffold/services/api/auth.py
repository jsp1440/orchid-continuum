"""
Authentication and authorization system for The Orchid Continuum.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import User, DatabaseManager

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None
    role: Optional[str] = None

class AuthManager:
    """Handles authentication and authorization."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.security = HTTPBearer()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            role: str = payload.get("role")
            
            if email is None or user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return TokenData(email=email, user_id=user_id, role=role)
            
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

# Global auth manager instance
auth_manager = None

def get_auth_manager():
    """Get the global auth manager instance."""
    global auth_manager
    if auth_manager is None:
        secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
        auth_manager = AuthManager(secret_key)
    return auth_manager

def get_db():
    """Get database session - this should be imported from database.py in production."""
    from database import DatabaseManager
    db_manager = DatabaseManager(os.getenv("DATABASE_URL", "postgresql://localhost/orchid_db"))
    return next(db_manager.get_session())

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    auth = get_auth_manager()
    token_data = auth.verify_token(credentials.credentials)
    
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def require_role(required_role: str):
    """Decorator to require specific role."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                # Try to get from dependencies
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Role hierarchy
            role_levels = {
                "viewer": 1,
                "member": 2,
                "contributor": 3,
                "curator": 4,
                "admin": 5
            }
            
            user_level = role_levels.get(current_user.role, 0)
            required_level = role_levels.get(required_role, 0)
            
            if user_level < required_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{required_role}' or higher required"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Role-based dependency factories
def require_curator():
    """Dependency that requires curator role or higher."""
    async def _require_curator(current_user: User = Depends(get_current_user)) -> User:
        role_levels = {"viewer": 1, "member": 2, "contributor": 3, "curator": 4, "admin": 5}
        if role_levels.get(current_user.role, 0) < 4:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Curator role or higher required"
            )
        return current_user
    return _require_curator

def require_admin():
    """Dependency that requires admin role."""
    async def _require_admin(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required"
            )
        return current_user
    return _require_admin

# Optional auth for public endpoints
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None