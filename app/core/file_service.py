"""
文件服务模块：提供安全的文件树和元数据访问
"""
import os
import stat
from pathlib import Path
import traceback
from datetime import datetime
from typing import Dict, List, Union, Optional
from .config import config

import logging
logger = logging.getLogger(__name__)

# 允许的扩展名
ALLOWED_EXTENSIONS = config.get("allowed_extensions", [".html", ".htm"])

def is_safe_path(base_dir: Path, target_path: str) -> bool:
    """
    检查目标路径是否在 base_dir 内，防止路径遍历
    """
    try:
        resolved_base = base_dir.resolve()
        resolved_target = (base_dir / target_path).resolve()
        # 确保 resolved_target 在 resolved_base 下
        return resolved_target.is_relative_to(resolved_base)
    except Exception:
        logger.error(f"Error resolving path: {target_path}")
        logger.error(traceback.format_exc())
        return False

def get_file_tree(root_path: Path, rel_path: str = "") -> Dict:
    """
    递归获取文件树结构
    :param root_path: 根目录的绝对路径
    :param rel_path: 相对于根目录的路径（用于递归）
    :return: 树节点字典
    """
    full_path = root_path / rel_path
    if not full_path.exists():
        return {"error": "Path does not exist"}

    stat_info = full_path.stat()
    node = {
        "name": full_path.name if rel_path else root_path.name,
        "path": rel_path,
        "type": "directory" if full_path.is_dir() else "file",
        "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat()
    }
    if full_path.is_file():
        node["size"] = stat_info.st_size
        # 检查扩展名是否允许
        if full_path.suffix not in ALLOWED_EXTENSIONS:
            node["allowed"] = False
        else:
            node["allowed"] = True
    else:
        # 目录
        children = []
        try:
            for item in sorted(full_path.iterdir()):
                if item.name.startswith('.'):
                    continue  # 忽略隐藏文件
                child_rel = str(Path(rel_path) / item.name) if rel_path else item.name
                child_node = get_file_tree(root_path, child_rel)
                children.append(child_node)
        except PermissionError:
            pass
        node["children"] = children
    return node

def get_file_meta(root_path: Path, rel_path: str) -> Optional[Dict]:
    """获取单个文件或目录的元数据"""
    full_path = root_path / rel_path
    if not full_path.exists():
        return None
    if not is_safe_path(root_path, rel_path):
        return None

    stat_info = full_path.stat()
    node = {
        "name": full_path.name,
        "path": rel_path,
        "type": "directory" if full_path.is_dir() else "file",
        "modified": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
        "size": stat_info.st_size if full_path.is_file() else None,
        "allowed": full_path.suffix in ALLOWED_EXTENSIONS if full_path.is_file() else None
    }
    return node

def read_file_content(root_path: Path, rel_path: str) -> Optional[str]:
    """读取文件内容（仅限文本文件）"""
    full_path = root_path / rel_path
    if not full_path.exists():
        return None
    if not is_safe_path(root_path, rel_path):
        return None
    # 检查扩展名
    if full_path.suffix not in ALLOWED_EXTENSIONS:
        return None
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        logger.error(f"Error reading file: {full_path}")
        logger.error(traceback.format_exc())
        return None