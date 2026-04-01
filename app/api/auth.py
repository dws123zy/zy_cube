"""
认证相关 API
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from ..core.auth import authenticate_user, create_access_token
from ..core.dependencies import get_current_user_from_token

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

@router.post("/auth/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user_from_token)):
    return current_user