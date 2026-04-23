"""
FastAPI 应用入口
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .core.config import config
from .core.logger import setup_logging
from .core.loader import ModuleLoader
from .api import auth, modules, files, module_metadata
from .core.dependencies import get_current_user_from_token
from app.api import sql_executor  # 导入 SQL 执行器路由
from app.api import user_manager

# 初始化日志
setup_logging()

import logging
logger = logging.getLogger(__name__)


# 加载配置（如果尚未加载）
config.load()

# 创建 FastAPI 应用
app = FastAPI(
    title="ZY_Cube",
    description="Dynamic application framework",
    version="2.0.0"
)

# CORS 配置（允许所有来源，可配置）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化模块加载器
loader = ModuleLoader(app)

# 注册 API 路由
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(modules.router, prefix="/api", tags=["modules"])
app.include_router(files.router, prefix="/api", tags=["files"])
app.include_router(module_metadata.router, prefix="/api", tags=["module_metadata"])
app.include_router(sql_executor.router, prefix="/api", tags=["sql"])
app.include_router(user_manager.router, prefix="/api", tags=["user_management"])

# 内部 Web 目录（框架自带页面）
internal_web_dir = Path(__file__).parent / "web"
if internal_web_dir.exists():
    # 挂载框架核心页面
    app.mount("/web", StaticFiles(directory=internal_web_dir), name="web_internal")

    # 挂载静态资源（CSS, JS等）
    internal_static_dir = internal_web_dir / "static"
    if internal_static_dir.exists():
        app.mount("/static", StaticFiles(directory=internal_static_dir), name="static")
    else:
        print(f"Warning: Static directory not found: {internal_static_dir}")
else:
    print(f"Warning: Internal web directory not found: {internal_web_dir}")

# 外部 Web 目录（用户放置 HTML 应用的目录）
external_web_dir = config.web_dir
external_web_dir.mkdir(parents=True, exist_ok=True)
app.mount("/webapps", StaticFiles(directory=external_web_dir), name="webapps")

# 外部公共库目录（用于存放 Vue、ECharts 等 JS 库）
weblib_dir = config.external_root / "weblib"
weblib_dir.mkdir(parents=True, exist_ok=True)
app.mount("/weblib", StaticFiles(directory=weblib_dir), name="weblib")
logger.info(f"Weblib directory: {weblib_dir} mounted at /weblib")

# 根路径重定向
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/web/login.html")

# 启动时自动加载模块
@app.on_event("startup")
async def startup_event():
    # 确保外部目录存在
    config.conf_dir.mkdir(parents=True, exist_ok=True)
    config.mod_dir.mkdir(parents=True, exist_ok=True)
    config.log_dir.mkdir(parents=True, exist_ok=True)

    # 如果配置了自动加载，加载 manifest 中的模块
    if config.get("module_auto_load", True):
        loader.auto_load_manifest()

# 将 loader 实例挂载到 app 上，以便在 API 中使用
app.state.loader = loader

# 调试
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    logger.warning("欢迎使用卓越魔方平台")