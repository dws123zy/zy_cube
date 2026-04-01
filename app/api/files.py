"""
文件服务 API
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from ..core.file_service import get_file_tree, get_file_meta, read_file_content
from ..core.config import config
from ..core.dependencies import get_current_user_from_token

router = APIRouter()

@router.get("/files/tree")
async def file_tree(root: str = Query("web", description="根目录标识（web）"), current_user=Depends(get_current_user_from_token)):
    if root == "web":
        base_dir = config.web_dir
    else:
        raise HTTPException(status_code=400, detail="Invalid root")
    if not base_dir.exists():
        raise HTTPException(status_code=404, detail="Root directory not found")
    tree = get_file_tree(base_dir)
    return tree

@router.get("/files/meta")
async def file_meta(path: str = Query(..., description="相对路径"), root: str = Query("web"), current_user=Depends(get_current_user_from_token)):
    if root == "web":
        base_dir = config.web_dir
    else:
        raise HTTPException(status_code=400, detail="Invalid root")
    meta = get_file_meta(base_dir, path)
    if not meta:
        raise HTTPException(status_code=404, detail="File not found")
    return meta

@router.get("/files/content")
async def file_content(path: str = Query(..., description="相对路径"), root: str = Query("web"), current_user=Depends(get_current_user_from_token)):
    if root == "web":
        base_dir = config.web_dir
    else:
        raise HTTPException(status_code=400, detail="Invalid root")
    content = read_file_content(base_dir, path)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found or not allowed")
    return {"content": content}