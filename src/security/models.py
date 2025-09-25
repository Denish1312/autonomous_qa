"""
Models for the security system components.
"""

from pydantic import BaseModel, Field, EmailStr, SecretStr
from typing import List, Dict, Optional, Set
from enum import Enum
from datetime import datetime
import uuid

class Role(str, Enum):
    """User roles in the system"""
    ADMIN = "admin"
    QA_LEAD = "qa_lead"
    QA_ENGINEER = "qa_engineer"
    DEVELOPER = "developer"
    VIEWER = "viewer"

class Permission(str, Enum):
    """Granular permissions"""
    READ_TESTS = "read:tests"
    WRITE_TESTS = "write:tests"
    EXECUTE_TESTS = "execute:tests"
    MANAGE_USERS = "manage:users"
    ACCESS_REPORTS = "access:reports"
    MANAGE_SETTINGS = "manage:settings"
    VIEW_SENSITIVE_DATA = "view:sensitive_data"

class EncryptionAlgorithm(str, Enum):
    """Supported encryption algorithms"""
    AES_256_GCM = "aes-256-gcm"
    CHACHA20_POLY1305 = "chacha20-poly1305"

class User(BaseModel):
    """User model with security attributes"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    hashed_password: SecretStr
    full_name: str
    roles: Set[Role]
    permissions: Set[Permission]
    api_keys: List[str] = []
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ApiKey(BaseModel):
    """API key for service authentication"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: SecretStr
    name: str
    user_id: str
    permissions: Set[Permission]
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    last_used: Optional[datetime] = None

class EncryptedData(BaseModel):
    """Model for encrypted data storage"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    algorithm: EncryptionAlgorithm
    ciphertext: bytes
    nonce: bytes
    tag: bytes
    key_id: str
    created_at: datetime = Field(default_factory=datetime.now)

class AccessLog(BaseModel):
    """Security audit log entry"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    action: str
    resource: str
    status: str
    ip_address: str
    user_agent: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, str] = {}

class SecurityConfig(BaseModel):
    """Security configuration settings"""
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    api_key_expiry_days: int = 90
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    encryption_algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM
    enable_2fa: bool = True
    allowed_origins: List[str] = ["*"]
    jwt_secret: SecretStr
    jwt_expiry_hours: int = 24

class RolePermissionMapping(BaseModel):
    """Default permissions for each role"""
    role: Role
    permissions: Set[Permission]

DEFAULT_ROLE_PERMISSIONS = [
    RolePermissionMapping(
        role=Role.ADMIN,
        permissions={
            Permission.READ_TESTS,
            Permission.WRITE_TESTS,
            Permission.EXECUTE_TESTS,
            Permission.MANAGE_USERS,
            Permission.ACCESS_REPORTS,
            Permission.MANAGE_SETTINGS,
            Permission.VIEW_SENSITIVE_DATA
        }
    ),
    RolePermissionMapping(
        role=Role.QA_LEAD,
        permissions={
            Permission.READ_TESTS,
            Permission.WRITE_TESTS,
            Permission.EXECUTE_TESTS,
            Permission.ACCESS_REPORTS,
            Permission.VIEW_SENSITIVE_DATA
        }
    ),
    RolePermissionMapping(
        role=Role.QA_ENGINEER,
        permissions={
            Permission.READ_TESTS,
            Permission.WRITE_TESTS,
            Permission.EXECUTE_TESTS,
            Permission.ACCESS_REPORTS
        }
    ),
    RolePermissionMapping(
        role=Role.DEVELOPER,
        permissions={
            Permission.READ_TESTS,
            Permission.EXECUTE_TESTS,
            Permission.ACCESS_REPORTS
        }
    ),
    RolePermissionMapping(
        role=Role.VIEWER,
        permissions={
            Permission.READ_TESTS,
            Permission.ACCESS_REPORTS
        }
    )
]
