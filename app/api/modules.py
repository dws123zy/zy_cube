"""
模块管理 API（需要 admin 角色）
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Dict
from ..core.dependencies import require_admin

router = APIRouter()

class LoadModuleRequest(BaseModel):
    module_path: str
    module_id: str = None
    api_prefix: str = None

class LoadFromManifestRequest(BaseModel):
    module_id: str

@router.post("/modules/load")
async def load_module(req: LoadModuleRequest, request: Request, admin=Depends(require_admin)):
    loader = request.app.state.loader
    try:
        info = loader.load_module(req.module_path, req.module_id, req.api_prefix)
        return {"status": "loaded", "id": info.id, "api_prefix": info.api_prefix}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/modules/load_from_manifest")
async def load_from_manifest(req: LoadFromManifestRequest, request: Request, admin=Depends(require_admin)):
    loader = request.app.state.loader
    mod_entry = next((m for m in loader.manifest if m.get("id") == req.module_id), None)
    if not mod_entry:
        raise HTTPException(status_code=404, detail="Module not found in manifest")
    if mod_entry.get("enabled"):
        raise HTTPException(status_code=400, detail="Module already loaded")
    try:
        info = loader.load_module(mod_entry["path"], mod_entry["id"], mod_entry.get("api_prefix"))
        return {"status": "loaded", "id": info.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/modules/unload")
async def unload_module(module_id: str, request: Request, admin=Depends(require_admin)):
    loader = request.app.state.loader
    if loader.unload_module(module_id):
        return {"status": "unloaded"}
    else:
        raise HTTPException(status_code=404, detail="Module not found")

@router.put("/modules/reload")
async def reload_module(module_id: str, request: Request, admin=Depends(require_admin)):
    loader = request.app.state.loader
    try:
        info = loader.reload_module(module_id)
        return {"status": "reloaded", "id": info.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/modules/list")
async def list_modules(request: Request, admin=Depends(require_admin)):
    loader = request.app.state.loader
    return loader.get_loaded_modules()

@router.get("/modules/manifest")
async def get_module_manifest(request: Request, admin=Depends(require_admin)):
    loader = request.app.state.loader
    loaded_ids = set(loader.loaded_modules.keys())
    result = []
    for mod in loader.manifest:
        mod_info = mod.copy()
        mod_info["loaded"] = mod_info.get("id") in loaded_ids
        result.append(mod_info)
    return result