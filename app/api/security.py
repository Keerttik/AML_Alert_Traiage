import os
import hmac
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import jwt
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from app.utils.config import BASE_DIR

SECRET_KEY = os.getenv("AML_JWT_SECRET", "AML_ENTERPRISE_PRODUCTION_SECRET_KEY_2026")
ALGORITHM = "HS256"
API_KEY_HEADER = APIKeyHeader(name="X-API-KEY", auto_error=False)
security_bearer = HTTPBearer(auto_error=False)

# Role definitions
VALID_ROLES = {"analyst", "compliance_manager", "auditor"}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token containing user identity and RBAC role."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=8))
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization token")

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    api_key: Optional[str] = Security(API_KEY_HEADER)
) -> Dict[str, Any]:
    """Validates user authentication via JWT bearer token or service API key."""
    # Service-to-service API Key auth
    if api_key and api_key == os.getenv("AML_SERVICE_API_KEY", "BANK_INTERNAL_API_KEY_9901"):
        return {"sub": "SYSTEM_INTEGRATION_SERVICE", "role": "compliance_manager", "service_account": True}

    # User JWT Auth
    if not credentials:
        # Default mock analyst for internal prototype/testing if no header provided
        return {"sub": "ANALYST-042", "role": "analyst", "name": "Sarah Chen"}

    token = credentials.credentials
    return decode_token(token)

def require_role(allowed_roles: List[str]):
    """RBAC dependency ensuring the caller has the required role permission."""
    def role_checker(user: Dict[str, Any] = Depends(get_current_user)):
        user_role = user.get("role", "analyst")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: User role '{user_role}' lacks permissions. Required: {allowed_roles}"
            )
        return user
    return role_checker
