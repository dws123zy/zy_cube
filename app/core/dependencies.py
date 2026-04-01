"""
依赖项模块
提供认证依赖等公共依赖
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth import get_current_user

oauth2_scheme = HTTPBearer(auto_error=False)

async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)
):
    """
    依赖项：从 Bearer Token 解析用户
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    user = get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def require_admin(current_user: dict = Depends(get_current_user_from_token)):
    """
    依赖项：要求用户角色为 admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user