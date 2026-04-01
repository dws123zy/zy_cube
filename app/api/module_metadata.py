"""
模块元数据 API
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from ..core.dependencies import get_current_user_from_token

router = APIRouter()

@router.get("/modules/{module_id}/openapi")
async def get_module_openapi(module_id: str, request: Request, current_user=Depends(get_current_user_from_token)):
    loader = request.app.state.loader
    openapi_fragment = loader.get_module_openapi(module_id)
    if openapi_fragment is None:
        raise HTTPException(status_code=404, detail="Module not loaded")
    return openapi_fragment

@router.get("/modules/{module_id}/endpoints")
async def get_module_endpoints(module_id: str, request: Request, current_user=Depends(get_current_user_from_token)):
    loader = request.app.state.loader
    endpoints = loader.get_module_endpoints(module_id)
    if endpoints is None:
        raise HTTPException(status_code=404, detail="Module not loaded")
    return {"module_id": module_id, "endpoints": endpoints}