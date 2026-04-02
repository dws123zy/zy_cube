"""
动态模块加载器：加载/卸载子模块，管理模块元数据
"""
import sys
import importlib
import importlib.util
from pathlib import Path
import traceback
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, APIRouter
from fastapi.routing import APIRoute
import json
from .config import config

import logging
logger = logging.getLogger(__name__)


class ModuleInfo:
    def __init__(self, id: str, path: str, api_prefix: str, router: APIRouter, routes_list: List):
        self.id = id
        self.path = path
        self.api_prefix = api_prefix
        self.router = router
        self.routes = routes_list  # 保存路由列表，用于卸载

class ModuleLoader:
    def __init__(self, app: FastAPI):
        self.app = app
        self.allowed_paths = [Path(p).resolve() for p in config.get("module_allowed_paths", [])]
        self.loaded_modules: Dict[str, ModuleInfo] = {}
        self.manifest = []  # 公开属性
        self._manifest_path = config.modules_manifest_file
        self._load_manifest()

    def _load_manifest(self):
        """加载 manifest 文件，获取需要自动加载的模块"""
        if self._manifest_path.exists():
            try:
                with open(self._manifest_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.manifest = data.get("modules", [])
            except Exception:
                self.manifest = []
        else:
            self.manifest = []
            self._save_manifest()

    def _save_manifest(self):
        """保存 manifest 到文件"""
        data = {"modules": self.manifest}
        self._manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._manifest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _is_safe_path(self, module_path: Path) -> bool:
        """检查模块路径是否在白名单内"""
        try:
            resolved = module_path.resolve()
            for allowed in self.allowed_paths:
                if resolved.is_relative_to(allowed):
                    return True
            return False
        except Exception:
            logger.error(f"Error resolving path: {module_path}")
            return False

    def load_module(self, module_path: str, module_id: str = None, api_prefix: str = None) -> ModuleInfo:
        """
        加载模块
        :param module_path: 模块目录的路径（绝对或相对）
        :param module_id: 模块唯一标识，若不提供则使用目录名
        :param api_prefix: API 前缀，默认 /api/{module_id}
        """
        # 解析路径
        path_obj = Path(module_path).resolve()
        if not path_obj.exists():
            raise ValueError(f"Module path does not exist: {module_path}")
        if not self._is_safe_path(path_obj):
            raise ValueError(f"Module path not allowed: {module_path}")

        # 在 load_module 开头添加
        for loaded in self.loaded_modules.values():
            other_prefix = loaded.api_prefix
            if (api_prefix.startswith(other_prefix + '/') or other_prefix.startswith(api_prefix + '/')):
                raise ValueError(f"API prefix conflict: '{api_prefix}' conflicts with '{other_prefix}'")

        # 确定 module_id
        if module_id is None:
            module_id = path_obj.name

        # 确定 api_prefix
        if api_prefix is None:
            api_prefix = f"/api/{module_id}"

        # 查找模块入口文件：优先 api.py，其次 __init__.py
        entry_file = path_obj / "api.py"
        if not entry_file.exists():
            entry_file = path_obj / "__init__.py"
        if not entry_file.exists():
            raise ValueError(f"No api.py or __init__.py found in {module_path}")

        # 动态导入模块
        spec = importlib.util.spec_from_file_location(module_id, entry_file)
        if spec is None:
            raise ImportError(f"Could not load spec for {module_id}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_id] = module
        spec.loader.exec_module(module)

        # 获取 router
        if not hasattr(module, "router"):
            raise ValueError(f"Module {module_id} does not expose a 'router' (APIRouter)")
        router = getattr(module, "router")
        if not isinstance(router, APIRouter):
            raise ValueError(f"router in {module_id} is not an APIRouter")

        # 自动添加 tags（如果没有）
        if not router.tags:
            router.tags = [module_id]

        # 注册到 FastAPI
        self.app.include_router(router, prefix=api_prefix)

        # 记录路由信息，用于卸载
        # 注意：此时 router.routes 是已定义的，但我们无法直接获取 FastAPI 中的路由对象，
        # 可以保存当前 app 的路由列表快照，卸载时对比删除。更简单的方法：卸载时重建路由。
        # 此处我们保存路由路径模式以便后续删除
        routes_list = [route.path for route in router.routes]
        info = ModuleInfo(module_id, str(path_obj), api_prefix, router, routes_list)
        self.loaded_modules[module_id] = info

        # 更新 manifest
        # 查找是否已有，若无则添加
        existing = next((m for m in self.manifest if m.get("id") == module_id), None)
        if existing:
            existing["enabled"] = True
            existing["path"] = str(path_obj)
            existing["api_prefix"] = api_prefix
        else:
            self.manifest.append({
                "id": module_id,
                "path": str(path_obj),
                "enabled": True,
                "auto_load": True,
                "description": "",
                "api_prefix": api_prefix
            })
        self._save_manifest()

        return info

    def unload_module(self, module_id: str) -> bool:
        if module_id not in self.loaded_modules:
            return False
        info = self.loaded_modules[module_id]
        prefix = info.api_prefix

        # 过滤路由：保留所有不以 prefix 开头的路由（严格匹配）
        new_routes = []
        for route in self.app.router.routes:
            # 仅处理具有 path 属性的路由（APIRoute, Mount 等）
            path = getattr(route, 'path', None)
            if path is not None:
                # 精确匹配 prefix 或以 prefix/ 开头
                if path == prefix or path.startswith(prefix + '/'):
                    continue
            new_routes.append(route)

        self.app.router.routes = new_routes

        # 从 sys.modules 中删除模块
        if module_id in sys.modules:
            del sys.modules[module_id]

        # 从 loaded_modules 中删除
        del self.loaded_modules[module_id]

        # 更新 manifest
        for m in self.manifest:
            if m.get("id") == module_id:
                m["enabled"] = False
                break
        self._save_manifest()
        return True

    def reload_module(self, module_id: str) -> ModuleInfo:
        """重新加载模块"""
        if module_id not in self.loaded_modules:
            raise ValueError(f"Module {module_id} not loaded")
        info = self.loaded_modules[module_id]
        # 保存路径和前缀
        path_str = info.path
        api_prefix = info.api_prefix
        # 卸载
        self.unload_module(module_id)
        # 重新加载
        return self.load_module(path_str, module_id, api_prefix)

    def get_loaded_modules(self) -> List[Dict]:
        """获取已加载模块列表（用于 API 返回）"""
        result = []
        for mod_id, info in self.loaded_modules.items():
            result.append({
                "id": mod_id,
                "path": info.path,
                "api_prefix": info.api_prefix,
                "enabled": True,
                "routes": info.routes
            })
        return result

    def get_module_openapi(self, module_id: str) -> Optional[Dict]:
        """获取模块的 OpenAPI 片段（基于完整 OpenAPI 过滤）"""
        if module_id not in self.loaded_modules:
            return None
        info = self.loaded_modules[module_id]
        # 获取完整 OpenAPI
        openapi = self.app.openapi()
        # 过滤 paths，只保留该模块的路径（根据 tags 或路径前缀）
        # 使用 tags 过滤（因为 router 有 tags）
        tag = info.router.tags[0] if info.router.tags else module_id
        filtered_paths = {}
        # 收集该模块使用的 schemas 引用
        used_schemas = set()
        for path, methods in openapi.get("paths", {}).items():
            # 检查路径是否以 api_prefix 开头（更可靠）
            if path.startswith(info.api_prefix):
                filtered_paths[path] = methods
                # 收集 schemas
                for method, details in methods.items():
                    # 解析 requestBody 和 responses 中的 schema ref
                    # 简化处理：从 OpenAPI 中递归提取 $ref
                    self._collect_schema_refs(details, used_schemas)

        # 过滤 components/schemas
        filtered_schemas = {}
        all_schemas = openapi.get("components", {}).get("schemas", {})
        for schema_name in used_schemas:
            if schema_name in all_schemas:
                filtered_schemas[schema_name] = all_schemas[schema_name]

        result = {
            "openapi": openapi.get("openapi", "3.0.0"),
            "info": openapi.get("info", {}),
            "paths": filtered_paths,
            "components": {"schemas": filtered_schemas}
        }
        return result

    def _collect_schema_refs(self, obj, used_schemas):
        """递归收集 $ref 中的 schema 名称"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "$ref" and isinstance(value, str):
                    # 格式: "#/components/schemas/SchemaName"
                    if value.startswith("#/components/schemas/"):
                        schema_name = value.split("/")[-1]
                        used_schemas.add(schema_name)
                else:
                    self._collect_schema_refs(value, used_schemas)
        elif isinstance(obj, list):
            for item in obj:
                self._collect_schema_refs(item, used_schemas)

    def get_module_endpoints(self, module_id: str) -> List[Dict]:
        """获取模块的简化端点信息"""
        if module_id not in self.loaded_modules:
            return None
        info = self.loaded_modules[module_id]
        endpoints = []
        for route in info.router.routes:
            # route 可能是 APIRoute 或 Route
            if hasattr(route, "methods") and hasattr(route, "path"):
                methods = list(route.methods)
                path = route.path
                # 组装完整路径：api_prefix + path（但 route.path 可能已经包含前缀？router 定义时 prefix 已经拼接到 route.path）
                # 实际上，在 APIRouter 中，route.path 是相对于 router 前缀的，但通过 include_router 后，最终路径是 api_prefix + route.path
                full_path = info.api_prefix + ("" if route.path.startswith("/") else "/") + route.path
                endpoint = {
                    "path": full_path,
                    "methods": methods,
                    "summary": getattr(route, "summary", ""),
                    "description": getattr(route, "description", ""),
                }
                # 提取参数
                parameters = []
                for dep in route.dependant.dependencies:
                    # 可以解析 query/path 参数
                    pass
                # 简化版本：不做深度解析
                endpoints.append(endpoint)
        return endpoints

    def auto_load_manifest(self):
        """启动时自动加载 manifest 中 enabled 且 auto_load 的模块"""
        for mod in self.manifest:
            if mod.get("enabled", False) and mod.get("auto_load", True):
                try:
                    self.load_module(mod["path"], mod["id"], mod.get("api_prefix"))
                except Exception as e:
                    # 记录日志但继续
                    logger.error(f"Failed to auto-load module {mod['id']}: {e}")