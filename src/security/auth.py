"""
Authentication and authorization service.
"""

from typing import Optional, Set, Dict, List
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from pydantic import ValidationError
import json
from pathlib import Path
import uuid
from .models import (
    User, ApiKey, Role, Permission,
    SecurityConfig, DEFAULT_ROLE_PERMISSIONS
)
from .encryption import PasswordHasher

class AuthService:
    """Handles authentication and authorization"""
    
    def __init__(
        self,
        storage_path: str = "./data/auth",
        config: Optional[SecurityConfig] = None
    ):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.config = config or SecurityConfig()
        self.password_hasher = PasswordHasher()
        
        # Load users and API keys
        self.users: Dict[str, User] = self._load_users()
        self.api_keys: Dict[str, ApiKey] = self._load_api_keys()
        
        # Initialize OAuth2 scheme
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
        self.api_key_header = APIKeyHeader(name="X-API-Key")
    
    def _load_users(self) -> Dict[str, User]:
        """Load users from storage"""
        users = {}
        if (self.storage_path / "users.json").exists():
            with open(self.storage_path / "users.json", "r") as f:
                data = json.load(f)
                for user_data in data:
                    user = User(**user_data)
                    users[user.id] = user
        return users
    
    def _save_users(self):
        """Save users to storage"""
        with open(self.storage_path / "users.json", "w") as f:
            json.dump(
                [user.dict() for user in self.users.values()],
                f,
                default=str
            )
    
    def _load_api_keys(self) -> Dict[str, ApiKey]:
        """Load API keys from storage"""
        api_keys = {}
        if (self.storage_path / "api_keys.json").exists():
            with open(self.storage_path / "api_keys.json", "r") as f:
                data = json.load(f)
                for key_data in data:
                    key = ApiKey(**key_data)
                    api_keys[key.key.get_secret_value()] = key
        return api_keys
    
    def _save_api_keys(self):
        """Save API keys to storage"""
        with open(self.storage_path / "api_keys.json", "w") as f:
            json.dump(
                [key.dict() for key in self.api_keys.values()],
                f,
                default=str
            )
    
    def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        roles: Set[Role]
    ) -> User:
        """Create a new user"""
        # Validate password
        if len(password) < self.config.password_min_length:
            raise ValueError("Password too short")
        
        # Hash password
        hash_b64, salt_b64 = self.password_hasher.hash_password(password)
        
        # Get permissions for roles
        permissions = set()
        for role_mapping in DEFAULT_ROLE_PERMISSIONS:
            if role_mapping.role in roles:
                permissions.update(role_mapping.permissions)
        
        # Create user
        user = User(
            email=email,
            hashed_password=f"{hash_b64}:{salt_b64}",
            full_name=full_name,
            roles=roles,
            permissions=permissions
        )
        
        self.users[user.id] = user
        self._save_users()
        return user
    
    def create_api_key(
        self,
        user_id: str,
        name: str,
        permissions: Optional[Set[Permission]] = None
    ) -> ApiKey:
        """Create a new API key for a user"""
        if user_id not in self.users:
            raise ValueError("User not found")
        
        # Generate API key
        key = f"ak_{uuid.uuid4().hex}"
        
        # Use user's permissions if none specified
        if permissions is None:
            permissions = self.users[user_id].permissions
        
        # Create API key
        api_key = ApiKey(
            key=key,
            name=name,
            user_id=user_id,
            permissions=permissions,
            expires_at=datetime.now() + timedelta(days=self.config.api_key_expiry_days)
        )
        
        self.api_keys[key] = api_key
        self._save_api_keys()
        return api_key
    
    def create_access_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token"""
        if expires_delta is None:
            expires_delta = timedelta(hours=self.config.jwt_expiry_hours)
        
        expires_at = datetime.utcnow() + expires_delta
        
        jwt_data = {
            "sub": user_id,
            "exp": expires_at
        }
        
        return jwt.encode(
            jwt_data,
            self.config.jwt_secret.get_secret_value(),
            algorithm="HS256"
        )
    
    async def get_current_user(
        self,
        token: str = Depends(oauth2_scheme)
    ) -> User:
        """Get current user from JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret.get_secret_value(),
                algorithms=["HS256"]
            )
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            user = self.users.get(user_id)
            if user is None:
                raise HTTPException(status_code=401, detail="User not found")
            
            return user
            
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def get_api_key_user(
        self,
        api_key: str = Security(api_key_header)
    ) -> User:
        """Get user from API key"""
        key_data = self.api_keys.get(api_key)
        if key_data is None:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        if key_data.expires_at and key_data.expires_at < datetime.now():
            raise HTTPException(status_code=401, detail="API key expired")
        
        user = self.users.get(key_data.user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Update last used timestamp
        key_data.last_used = datetime.now()
        self._save_api_keys()
        
        return user
    
    def verify_permissions(
        self,
        user: User,
        required_permissions: Set[Permission]
    ) -> bool:
        """Verify user has required permissions"""
        return required_permissions.issubset(user.permissions)
    
    def revoke_api_key(self, key: str):
        """Revoke an API key"""
        if key in self.api_keys:
            del self.api_keys[key]
            self._save_api_keys()
    
    def update_user_roles(
        self,
        user_id: str,
        roles: Set[Role]
    ) -> User:
        """Update user roles and recalculate permissions"""
        if user_id not in self.users:
            raise ValueError("User not found")
        
        user = self.users[user_id]
        user.roles = roles
        
        # Recalculate permissions
        permissions = set()
        for role_mapping in DEFAULT_ROLE_PERMISSIONS:
            if role_mapping.role in roles:
                permissions.update(role_mapping.permissions)
        
        user.permissions = permissions
        self._save_users()
        return user
