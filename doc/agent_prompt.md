智能体提示词（Agent Prompt）

1. 框架简介
ZY_Cube 是一个基于 FastAPI 的动态应用框架，允许热加载/卸载独立的 Python 后端子模块和 HTML 前端页面。你作为开发智能体，将基于该框架为项目开发新的后端模块和前端应用，这些新功能通过框架的模块系统加载运行。

1.1 核心能力（供你使用）
动态加载 Python 子模块（自动注册路由）

统一用户认证（JWT Token）

文件树服务（浏览外部 web 目录下的 HTML 文件）

模块元数据查询（获取模块的 OpenAPI 片段和端点列表）

1.2 开发原则
所有新开发的后端模块放入 ../mod/ 目录，前端应用放入 ../web/ 目录。

后端模块必须暴露 FastAPI APIRouter 实例，并为每个接口添加 description 参数，让其他开发者（或 AI）清楚接口用途。

前端应用通过 Authorization: Bearer <token> 调用 API，支持 URL 参数和 postMessage 传递 token。

模块如有第三方依赖，必须在 requirements.txt 中列出。

2. 开发新后端模块
2.1 模块结构
在 ../mod/ 下创建一个新文件夹（例如 my_ai_tool），文件夹内必须包含 api.py 文件，该文件暴露一个 router 对象。

text
../mod/my_ai_tool/
├── api.py          # 必须
├── requirements.txt   # 可选，模块额外依赖
└── README.md          # 可选，模块说明
2.2 api.py 编写规范（重要）
python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.dependencies import get_current_user_from_token

# 重要：prefix 必须设置为空字符串，框架会在加载时自动添加 /api/{module_id} 前缀
router = APIRouter(prefix="", tags=["my_ai_tool"])

class MyRequest(BaseModel):
    text: str

@router.post("/process", description="处理文本并返回结果")
async def process(request: MyRequest, user=Depends(get_current_user_from_token)):
    """
    对输入文本进行处理（例如大写转换）。
    """
    return {"result": request.text.upper()}
说明：

prefix=""：模块内部路由不包含任何前缀，最终访问路径为 /api/{module_id}/process。

description：每个接口必须提供，用一句话说明功能。

认证：使用 Depends(get_current_user_from_token) 保护需要认证的接口（默认都需认证）。

Pydantic 模型：定义请求体可自动生成 OpenAPI 文档。

2.3 第三方依赖
如果模块需要使用第三方库（如 pillow、numpy），必须在模块目录下创建 requirements.txt，列出依赖。

示例 requirements.txt：

text
pillow
用户需手动安装依赖（可在项目虚拟环境中执行 uv pip install -r ../mod/my_ai_tool/requirements.txt）。

2.4 安全与路径
模块路径必须在配置白名单内（默认 ../mod 已允许），无需额外操作。

模块运行在同一进程，代码需可信。

3. 开发新前端应用
3.1 目录位置
前端应用（HTML/JS/CSS）放在 ../web/ 目录下，可以是单个 .html 文件，也可以是子文件夹（如 ../web/my_app/index.html）。

3.2 认证与 Token 获取
页面必须从以下方式获取 token：

localStorage：登录后保存。

URL 参数：跨系统跳转时 ?token=xxx。

postMessage：当页面被嵌入 iframe 时，父页面通过 postMessage({ type: 'auth', token: token }, '*') 传递。

示例代码：

html
<!DOCTYPE html>
<html>
<head>
    <title>我的应用</title>
</head>
<body>
    <h1>我的应用</h1>
    <div id="result"></div>
    <script>
        let token = localStorage.getItem('token') || new URLSearchParams(location.search).get('token');
        window.addEventListener('message', (e) => {
            if (e.data.type === 'auth') token = e.data.token;
        });
        async function callAPI() {
            const res = await fetch('/api/my_ai_tool/process', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text: 'hello' })
            });
            const data = await res.json();
            document.getElementById('result').innerText = JSON.stringify(data);
        }
        callAPI();
    </script>
</body>
</html>
3.3 利用框架已有功能（可选）
获取文件内容（仅限 .html/.htm）：GET /api/files/content?path=relative/path&root=web

列出已加载模块（需 admin 角色）：GET /api/modules/list

获取模块 OpenAPI 片段：GET /api/modules/{module_id}/openapi

这些接口可帮助你动态获取模块信息，用于生成前端调用代码或展示文档。

4. 开发示例
4.1 文本处理模块（无第三方依赖）
模块代码（../mod/text_tool/api.py）：

python
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.dependencies import get_current_user_from_token

router = APIRouter(prefix="", tags=["text_tool"])

class TextRequest(BaseModel):
    text: str

@router.post("/upper", description="将文本转换为大写")
async def to_upper(req: TextRequest, user=Depends(get_current_user_from_token)):
    return {"result": req.text.upper()}

@router.post("/reverse", description="反转文本")
async def reverse(req: TextRequest, user=Depends(get_current_user_from_token)):
    return {"result": req.text[::-1]}
前端测试页面（../web/text_tool.html）：

html
<!DOCTYPE html>
<html>
<head>
    <title>文本工具</title>
</head>
<body>
    <textarea id="text" rows="4" cols="50"></textarea><br>
    <button onclick="call('upper')">转大写</button>
    <button onclick="call('reverse')">反转</button>
    <div id="result"></div>
    <script>
        let token = localStorage.getItem('token');
        async function call(action) {
            const text = document.getElementById('text').value;
            const res = await fetch(`/api/text_tool/${action}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await res.json();
            document.getElementById('result').innerText = JSON.stringify(data);
        }
    </script>
</body>
</html>
4.2 图片处理模块（依赖 Pillow）
模块结构：

text
../mod/img_tool/
├── api.py
├── requirements.txt
└── README.md
requirements.txt：

text
pillow
api.py：

python
from fastapi import APIRouter, Depends, File, UploadFile
from PIL import Image
from io import BytesIO
from app.core.dependencies import get_current_user_from_token

router = APIRouter(prefix="", tags=["img_tool"])

@router.post("/size", description="获取上传图片的尺寸")
async def get_image_size(file: UploadFile = File(...), user=Depends(get_current_user_from_token)):
    content = await file.read()
    img = Image.open(BytesIO(content))
    return {"width": img.width, "height": img.height}
前端页面（../web/img_tool.html）：

html
<!DOCTYPE html>
<html>
<head>
    <title>图片尺寸查询</title>
</head>
<body>
    <input type="file" id="fileInput">
    <button onclick="upload()">获取尺寸</button>
    <div id="result"></div>
    <script>
        let token = localStorage.getItem('token');
        async function upload() {
            const file = document.getElementById('fileInput').files[0];
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch('/api/img_tool/size', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });
            const data = await res.json();
            document.getElementById('result').innerText = `宽: ${data.width}, 高: ${data.height}`;
        }
    </script>
</body>
</html>

5. 注意事项
所有后端接口必须添加 description 参数，用一句话说明功能，便于其他开发者（或 AI）理解和使用。

router.prefix 必须为空字符串，框架会自动添加 /api/{module_id} 前缀，避免路径重复。

模块路径必须是目录，不能直接指向文件。

卸载模块时，路由会从应用中移除，可能需要刷新前端页面才能更新。

第三方依赖必须在 requirements.txt 中声明，用户需手动安装。

6. 总结
作为 ZY_Cube 框架的开发智能体，你应遵循上述规范，生成可直接部署的后端模块和前端应用代码。充分利用框架的认证、模块元数据等能力，快速实现 AI 功能。如有疑问，可参考项目 doc/ 目录下的完整文档。