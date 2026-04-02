"""
认证模块：使用 DuckDB 存储用户，密码 bcrypt 加密
"""
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import config

import logging
logger = logging.getLogger(__name__)


# JWT 配置
SECRET_KEY = config.get("jwt_secret_key")
ALGORITHM = config.get("jwt_algorithm")
ACCESS_TOKEN_EXPIRE_MINUTES = config.get("token_expire_minutes")

# 用户数据库路径
USER_DB_PATH = config.conf_dir / "users.duckdb"

def _get_engine():
    """获取 DuckDB 引擎"""
    return create_engine(f"duckdb:///{USER_DB_PATH.as_posix()}")

def _hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def _verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def _init_user_db():
    """初始化用户数据库，仅在无任何用户时创建默认管理员账户"""
    engine = _get_engine()
    with engine.connect() as conn:
        # 创建用户表
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL,
                name VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()

        # 检查是否已有任何用户
        result = conn.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        if count == 0:
            hashed = _hash_password("admin")
            # 手动计算下一个 id（表为空时从 1 开始）
            next_id = 1
            conn.execute(
                text("INSERT INTO users (id, username, password_hash, role, name) VALUES (:id, :username, :password, :role, :name)"),
                {"id": next_id, "username": "admin", "password": hashed, "role": "admin", "name": "Administrator"}
            )
            conn.commit()
            logger.warning("✅ 已创建默认管理员账户: admin / admin")


# 初始化数据库
_init_user_db()

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """验证用户名密码，返回用户信息（不含密码哈希）"""
    engine = _get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, username, password_hash, role, name FROM users WHERE username = :username"),
            {"username": username}
        )
        row = result.fetchone()
        if row and _verify_password(password, row[2]):
            return {
                "id": row[0],
                "username": row[1],
                "role": row[3],
                "name": row[4]
            }
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """生成 JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str) -> Optional[Dict]:
    """从 token 中解析用户信息"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return None
        engine = _get_engine()
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, username, role, name FROM users WHERE username = :username"),
                {"username": username}
            )
            row = result.fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "role": row[2],
                    "name": row[3]
                }
    except JWTError:
        pass
    return None