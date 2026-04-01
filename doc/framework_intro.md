# ZY_Cube 框架简介 (Framework Introduction)

ZY_Cube 是一个基于 FastAPI 的动态应用框架，支持热加载/卸载独立的 Python 后端子模块和静态 HTML 页面。

ZY_Cube is a dynamic application framework built on FastAPI that allows hot-loading/unloading of Python submodules and static HTML pages.

---

## 核心特性 (Key Features)

- **动态模块加载/卸载** (Dynamic module loading/unloading)：无需重启服务即可添加或移除功能模块。
- **文件树浏览与内容服务** (File tree browsing and content serving)：递归获取外部 web 目录结构，支持预览 HTML 文件。
- **基于 JWT 的认证** (JWT-based authentication)：支持用户配置文件，默认提供 admin/admin 账户。
- **模块元数据 API** (Module metadata API)：可获取已加载模块的 OpenAPI 片段和简化端点信息，便于前端自动对接。
- **Web UI** (Web UI)：提供登录、工作台（文件树+标签页）、模块管理三个核心页面，简约企业风格。
- **外部化配置** (External configuration)：所有配置、模块、前端页面、日志均外置于项目目录，便于升级和维护。

---

## 快速开始 (Quick Start)

1. 克隆仓库 (Clone the repository)
2. 安装依赖 (Install dependencies)：`uv sync`
3. 启动服务 (Run the server)：`uv run uvicorn app.main:app --reload`
4. 访问 http://localhost:8000
5. 使用默认账号登录 (Login with default credentials)：`admin` / `admin`（如果未配置外部 `users.json`）

更多详细信息请参考模块开发指南 (For more details, see the module development guide).