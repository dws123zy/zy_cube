"""
用户管理 API（仅限 admin）
提供用户的增删改查，密码加密存储。
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import traceback

from app.core.dependencies import require_admin, get_current_user_from_token
from app.core.config import config
from app.core.auth import _get_engine

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["user_management"])

import bcrypt
def _hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

# 请求/响应模型
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=4)
    role: str = Field(..., pattern="^(admin|user)$")
    name: Optional[str] = None

class UserUpdate(BaseModel):
    password: Optional[str] = Field(None, min_length=4)
    role: Optional[str] = Field(None, pattern="^(admin|user)$")
    name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    name: Optional[str]

@router.get("/", description="获取所有用户列表")
async def list_users(admin=Depends(require_admin)) -> List[UserResponse]:
    engine = _get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, username, role, name FROM users ORDER BY id"))
        users = [{"id": row[0], "username": row[1], "role": row[2], "name": row[3]} for row in result.fetchall()]
    return users


@router.post("/", description="创建新用户")
async def create_user(user: UserCreate, admin=Depends(require_admin)) -> UserResponse:
    engine = _get_engine()
    with engine.connect() as conn:
        existing = conn.execute(text("SELECT id FROM users WHERE username = :username"), {"username": user.username}).fetchone()
        if existing:
            logger.warning(f"用户名已存在: {user.username}")
            raise HTTPException(status_code=400, detail="用户名已存在")
        hashed = _hash_password(user.password)
        # 计算下一个 id
        max_id_result = conn.execute(text("SELECT COALESCE(MAX(id), 0) FROM users"))
        next_id = max_id_result.scalar() + 1
        try:
            # 插入时不使用 RETURNING
            conn.execute(
                text("INSERT INTO users (id, username, password_hash, role, name) VALUES (:id, :username, :password, :role, :name)"),
                {"id": next_id, "username": user.username, "password": hashed, "role": user.role, "name": user.name}
            )
            conn.commit()
            # 重新查询新用户
            result = conn.execute(text("SELECT id, username, role, name FROM users WHERE username = :username"), {"username": user.username})
            new_user = result.fetchone()
            if new_user:
                return UserResponse(id=new_user[0], username=new_user[1], role=new_user[2], name=new_user[3])
            else:
                logger.error(f"创建用户后查询失败: {user.username}")
                raise HTTPException(status_code=500, detail="创建用户后查询失败")
        except SQLAlchemyError as e:
            logger.error(f"数据库错误: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")


@router.put("/{user_id}", description="更新用户信息（密码可选）")
async def update_user(user_id: int, update: UserUpdate, admin=Depends(require_admin)) -> dict:
    engine = _get_engine()
    with engine.connect() as conn:
        # 检查用户是否存在
        user = conn.execute(text("SELECT id FROM users WHERE id = :id"), {"id": user_id}).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        # 构建动态更新 SQL
        updates = []
        params = {"id": user_id}
        if update.password is not None:
            updates.append("password_hash = :password")
            params["password"] = _hash_password(update.password)
        if update.role is not None:
            updates.append("role = :role")
            params["role"] = update.role
        if update.name is not None:
            updates.append("name = :name")
            params["name"] = update.name
        if not updates:
            return {"message": "无需更新"}
        sql = f"UPDATE users SET {', '.join(updates)} WHERE id = :id"
        conn.execute(text(sql), params)
        conn.commit()
    logger.warning(f"用户 {user_id} 更新成功")
    return {"message": "更新成功"}

@router.delete("/{user_id}", description="删除用户（禁止删除自己）")
async def delete_user(user_id: int, current_user=Depends(get_current_user_from_token), admin=Depends(require_admin)):
    if current_user["id"] == user_id:
        raise HTTPException(status_code=403, detail="不能删除自己的账户")
    engine = _get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        conn.commit()
        if result.rowcount == 0:
            logger.warning(f"用户 {user_id} 不存在")
            raise HTTPException(status_code=404, detail="用户不存在")
    logger.warning(f"用户 {user_id} 删除成功")
    return {"message": "删除成功"}