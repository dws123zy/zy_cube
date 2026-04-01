# ZY_Cube 卓越魔方

[中文](#中文) | [English](#english)

---

## 中文

### 项目简介

ZY_Cube 可以无限扩展的 AI 开发平台，解决AI开发大型项目难的痛点，让AI开发每个小模块，由平台加载，集合成一个可以无限扩展的庞大项目。
平台是基于 FastAPI 的动态应用框架，允许热加载/卸载独立的 Python 后端子模块和 HTML 前端页面。所有子模块相互隔离，通过统一认证和文件服务构成一个可无限扩展的 AI 开发平台。项目采用开源方式发布，适用于企业内部快速集成各类 AI 功能。

**核心能力：**

- 动态加载指定目录下的 Python 模块，自动将其路由注册到 FastAPI
- 热加载/卸载模块，不影响其他运行中的模块
- 递归获取文件树及元数据，用于前端展示和文件选择
- 基于 Token 的用户认证（配置文件存储用户信息，密码明文）
- 提供三个核心 Web 页面：登录、主工作台、模块管理
- 支持跨系统跳转（URL 传递 Token）和 postMessage 通信
- 所有配置、模块、前端应用、日志均外置于项目目录，便于升级
- 提供子模块接口元数据获取能力，支持通过 API 查询子模块的 OpenAPI 片段或简化端点信息

---

### 技术栈

- 后端：Python 3.12 + FastAPI + Uvicorn
- 包管理：uv
- 认证：python-jose (JWT)
- 前端：原生 HTML/CSS/JS（企业级简约时尚风格）
- 缓存：内存字典

---

### 安装与运行

#### 1. 克隆项目
```bash
git clone <repository-url>
cd zy_cube
```

#### 2. 安装依赖
使用 uv 管理依赖（确保已安装 uv）：

```bash
uv sync
```

#### 3. 配置外部目录（可选）
默认外部目录为项目根目录的上一级 ../。您可以通过修改 examples/conf/config.yaml 并复制到 ../conf/config.yaml 来自定义。首次运行会自动创建默认配置。

#### 4. 启动服务
```bash
uv run uvicorn app.main:app --reload
```
服务默认运行在 http://localhost:8000。

#### 5. 登录
如果 ../conf/users.json 不存在，使用默认管理员账号：admin / admin

如果已配置外部用户文件，请使用文件中定义的用户登录

### 使用指南

#### 工作台
左侧文件树：显示外部 web_dir 目录下的文件结构，点击 .html 文件会在右侧标签页中打开

右侧标签页：使用 iframe 嵌入 HTML 应用，并通过 postMessage 自动传递 Token，使子页面可调用 API

#### 模块管理
进入模块管理页面（左上角菜单或直接访问 /web/modules_mgr.html）

查看已加载模块，可进行卸载、重载操作

加载新模块：填写模块路径（例如 ../mod/demo_module），模块 ID 和 API 前缀可选

#### 模块开发
在 mod_dir（默认 ../mod）下创建模块文件夹

编写 api.py，暴露一个 APIRouter 实例

示例代码见 examples/mod/demo_module/api.py

### 目录结构
```text
zy_cube/                     # 项目内部
├── app/                     # 应用代码
│   ├── core/                # 核心模块
│   ├── api/                 # API 路由
│   └── web/                 # 内部前端静态文件
├── examples/                # 配置与模块示例
│   ├── conf/                # 配置示例
│   ├── mod/                 # 模块示例
│   └── web/                 # 前端示例
├── doc/                     # 详细文档
├── pyproject.toml
└── README.md

外部目录（默认 ../）          # 用户数据目录
├── conf/                    # 配置文件（config.yaml, users.json, modules_manifest.json）
├── mod/                     # 子模块目录
├── web/                     # HTML 应用目录
└── log/                     # 日志目录
```

### 文档
详细文档位于 doc/ 目录：

framework_intro.md - 框架介绍与快速开始

module_development_guide.md - 子模块开发指南

api_reference.md - API 参考文档

### 许可证

Apache 2.0


## English

### Introduction
ZY_Cube is an infinitely scalable AI development platform designed to address the pain points associated with building large-scale AI projects. It enables individual AI modules to be loaded by the platform and assembled into a massively expandable system.
Built on FastAPI, the platform is a dynamic application framework that supports the hot-loading and unloading of independent Python backend sub-modules and HTML frontend pages. All sub-modules are mutually isolated, unified through centralized authentication and file services to form an infinitely scalable AI development ecosystem.
Released as an open-source project, ZY_Cube is ideal for enterprises seeking to rapidly integrate various AI functionalities internally.

Key Features:

Dynamically load Python modules from a specified directory and automatically register their routes with FastAPI

Hot load/unload modules without affecting other running modules

Recursively retrieve file tree and metadata for front-end display and file selection

Token-based user authentication (user information stored in config file, plaintext passwords)

Three core web pages: login, main dashboard, module management

Support cross-system navigation (pass token via URL) and postMessage communication

All configurations, modules, front-end apps, and logs are externalized for easy upgrades

Provide module interface metadata retrieval, allowing query of submodule OpenAPI fragments or simplified endpoint information via API

### Technology Stack
Backend: Python 3.12 + FastAPI + Uvicorn

Package Management: uv

Authentication: python-jose (JWT)

Frontend: Native HTML/CSS/JS (enterprise minimalist style)

Cache: In-memory dictionary

### Installation & Running

#### 1. Clone the repository
```bash
git clone <repository-url>
cd zy_cube
```

#### 2. Install dependencies
Use uv to manage dependencies:

```bash
uv sync
```

#### 3. Configure external directory (optional)
The default external directory is ../ relative to the project root. You can customize by copying examples/conf/config.yaml to ../conf/config.yaml and editing it. The first run will create default configurations automatically.

#### 4. Start the server
```bash
uv run uvicorn app.main:app --reload
```
The server runs at http://localhost:8000 by default.

#### 5. Login
If ../conf/users.json does not exist, use the default admin account: admin / admin

If an external user file exists, log in with the credentials defined there

### Usage Guide

#### Dashboard
Left file tree: displays the file structure of the external web_dir. Clicking an .html file opens it in a tab on the right.

Right tab area: embeds HTML apps in iframes and automatically passes the token via postMessage, allowing child pages to call APIs.

#### Module Management
Go to the module management page (top-left menu or directly visit /web/modules_mgr.html)

View loaded modules, unload or reload them

Load a new module: fill in the module path (e.g., ../mod/demo_module); module ID and API prefix are optional

#### Module Development
Create a module folder under mod_dir (default ../mod)

Write api.py that exposes an APIRouter instance

See examples/mod/demo_module/api.py for an example

### Directory Structure
```text
zy_cube/                     # Internal project directory
├── app/                     # Application code
│   ├── core/                # Core modules
│   ├── api/                 # API routes
│   └── web/                 # Internal frontend static files
├── examples/                # Example configurations and modules
│   ├── conf/                # Config examples
│   ├── mod/                 # Module examples
│   └── web/                 # Frontend examples
├── doc/                     # Detailed documentation
├── pyproject.toml
└── README.md

External directory (default ../)  # User data directory
├── conf/                    # Configuration files (config.yaml, users.json, modules_manifest.json)
├── mod/                     # Submodule directory
├── web/                     # HTML applications directory
└── log/                     # Log files directory
```
### Documentation
Detailed documentation is located in the doc/ directory:

framework_intro.md - Framework introduction and quick start

module_development_guide.md - Submodule development guide

api_reference.md - API reference

### License
Apache 2.0