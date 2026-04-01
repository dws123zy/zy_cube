"""
认证模块：用户加载、JWT 生成与验证
"""
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
from jose import JWTError, jwt
from .config import config

# JWT 配置
SECRET_KEY = config.get("jwt_secret_key")
ALGORITHM = config.get("jwt_algorithm")
ACCESS_TOKEN_EXPIRE_MINUTES = config.get("token_expire_minutes")

# 用户存储
_users_db: Dict[str, Dict] = {}
_default_users = [
    {"username": "admin", "password": "admin", "role": "admin", "name": "Administrator"}
]

def load_users() -> None:
    """
    加载用户：优先使用外部 users.json，否则使用默认 admin/admin
    """
    global _users_db
    users_file = config.users_file
    if users_file.exists():
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "users" in data and isinstance(data["users"], list):
                _users_db = {}
                for u in data["users"]:
                    if "username" in u and "password" in u:
                        _users_db[u["username"]] = u
                # 如果文件为空或解析后无用户，回退默认
                if not _users_db:
                    _users_db = {u["username"]: u for u in _default_users}
                return
        except Exception as e:
            print(f"Failed to load users.json: {e}")
    # 文件不存在或无效，使用默认
    _users_db = {u["username"]: u for u in _default_users}

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """验证用户名密码，返回用户信息（不含密码）"""
    user = _users_db.get(username)
    if user and user.get("password") == password:
        # 返回用户信息副本，移除密码
        return {k: v for k, v in user.items() if k != "password"}
    return None

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
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
        if username is None:
            return None
        user = _users_db.get(username)
        if user:
            return {k: v for k, v in user.items() if k != "password"}
    except JWTError:
        pass
    return None

# 启动时加载用户
load_users()