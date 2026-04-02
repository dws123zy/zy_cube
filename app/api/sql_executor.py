"""
SQL 执行器 API（内置模块）
提供基于 SQLAlchemy 的多数据源 SQL 执行能力，支持权限控制、分页查询。
内置 DuckDB 演示数据源。
"""
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import config
from app.core.dependencies import get_current_user_from_token

import logging
logger = logging.getLogger(__name__)


# 创建 router
router = APIRouter(prefix="/sql", tags=["sql"])

# 全局数据源存储
_datasources: Dict[str, Dict[str, Any]] = {}

def _create_duckdb_demo(db_path: Path):
    """创建 DuckDB 演示数据库和测试表"""
    try:
        import duckdb
        conn = duckdb.connect(str(db_path))
        # 创建订单表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                order_no VARCHAR(50),
                customer VARCHAR(100),
                amount DECIMAL(10,2),
                status VARCHAR(20)
            )
        """)
        # 清空并插入测试数据
        conn.execute("DELETE FROM orders")
        conn.execute("""
            INSERT INTO orders (id, order_no, customer, amount, status) VALUES
                (1, 'ORD001', '张三', 1500.00, 'completed'),
                (2, 'ORD002', '李四', 2300.50, 'pending'),
                (3, 'ORD003', '王五', 890.00, 'completed'),
                (4, 'ORD004', '赵六', 3200.00, 'cancelled'),
                (5, 'ORD005', '钱七', 670.25, 'completed')
        """)
        conn.close()
        print(f"✅ 已创建 DuckDB 演示数据库: {db_path}")
    except ImportError:
        print("⚠️ 未安装 duckdb，跳过创建演示数据库。请运行: uv pip install duckdb duckdb-engine")
    except Exception as e:
        print(f"❌ 创建 DuckDB 演示数据库失败: {e}")

def load_datasources() -> None:
    """加载数据源配置文件，如果不存在则创建默认配置并生成 DuckDB 演示数据库"""
    conf_path = config.conf_dir / "datasources.yaml"
    if not conf_path.exists():
        conf_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建 DuckDB 演示数据库
        duckdb_path = config.conf_dir / "duckdb_demo.duckdb"
        _create_duckdb_demo(duckdb_path)

        # 默认配置包含 DuckDB 数据源
        default_config = {
            "datasources": [
                {
                    "id": "demo_duckdb",
                    "name": "演示 DuckDB",
                    "url": f"duckdb:///{duckdb_path.as_posix()}",
                    "permissions": ["select", "insert", "update", "delete"],
                    "db_type": "duckdb"
                }
            ]
        }
        with open(conf_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, allow_unicode=True)
        print(f"⚠️ 已创建示例配置文件: {conf_path}，包含 DuckDB 演示数据源。")

    # 读取配置文件
    try:
        with open(conf_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return

    _datasources.clear()
    for ds in data.get("datasources", []):
        ds_id = ds.get("id")
        if not ds_id:
            continue
        try:
            engine = create_engine(ds["url"], pool_pre_ping=True)
            _datasources[ds_id] = {
                "name": ds.get("name", ds_id),
                "engine": engine,
                "permissions": set(ds.get("permissions", [])),
                "db_type": ds.get("db_type", "unknown")
            }
        except Exception as e:
            print(f"❌ 创建数据源 {ds_id} 引擎失败: {e}")
            continue

    print(f"✅ 已加载 {len(_datasources)} 个数据源")

def _get_sql_type(sql: str) -> str:
    """根据 SQL 语句第一个单词判断操作类型"""
    first_word = re.sub(r'^\s*', '', sql).split()[0].lower()
    mapping = {
        'select': 'select',
        'insert': 'insert',
        'update': 'update',
        'delete': 'delete',
        'replace': 'insert',
        'call': 'select',
    }
    return mapping.get(first_word, 'unknown')

def _add_pagination(sql: str, page: int, page_size: int) -> str:
    """为 SELECT 语句添加 LIMIT 和 OFFSET 子句"""
    return f"{sql} LIMIT :limit OFFSET :offset"

def _execute_query(engine: Engine, sql: str, params: Dict, page: int, page_size: int):
    """执行查询（带分页）"""
    # 计算总条数
    count_sql = f"SELECT COUNT(*) FROM ({sql}) AS subquery"
    with engine.connect() as conn:
        count_result = conn.execute(text(count_sql), params)
        total = count_result.scalar()

        # 分页查询
        paginated_sql = _add_pagination(sql, page, page_size)
        exec_params = {**params, 'limit': page_size, 'offset': (page - 1) * page_size}
        result = conn.execute(text(paginated_sql), exec_params)

        rows = [dict(zip(result.keys(), row)) for row in result.fetchall()]
        return rows, total

def _execute_non_query(engine: Engine, sql: str, params: Dict) -> int:
    """执行非查询语句（增删改）"""
    with engine.begin() as conn:
        result = conn.execute(text(sql), params)
        return result.rowcount

# ==================== API 模型 ====================
class ExecuteRequest(BaseModel):
    datasource_id: str = Field(..., description="数据源ID")
    sql: str = Field(..., description="SQL语句（支持命名占位符）")
    params: Optional[Dict[str, Any]] = Field(None, description="SQL参数")
    page: Optional[int] = Field(1, ge=1, description="页码（仅SELECT有效）")
    page_size: Optional[int] = Field(20, ge=1, le=1000, description="每页大小")

class ExecuteResponse(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

# ==================== API 端点 ====================
@router.post("/execute", description="执行SQL语句，支持多数据源、权限控制、分页查询")
async def execute_sql(
    req: ExecuteRequest,
    current_user=Depends(get_current_user_from_token)
) -> ExecuteResponse:
    # 1. 检查数据源
    ds = _datasources.get(req.datasource_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"数据源 {req.datasource_id} 不存在")

    # 2. 判断 SQL 类型
    sql_type = _get_sql_type(req.sql)
    if sql_type == 'unknown':
        raise HTTPException(status_code=400, detail="无法识别的SQL语句类型")

    # 3. 权限检查
    if sql_type not in ds["permissions"]:
        raise HTTPException(status_code=403, detail=f"无权限执行 {sql_type} 操作")

    # 4. 参数处理
    params = req.params or {}
    engine = ds["engine"]

    try:
        if sql_type == 'select':
            rows, total = _execute_query(engine, req.sql, params, req.page, req.page_size)
            return ExecuteResponse(
                code=200,
                message="查询成功",
                data={
                    "list": rows,
                    "total": total,
                    "page": req.page,
                    "page_size": req.page_size
                }
            )
        else:
            affected = _execute_non_query(engine, req.sql, params)
            return ExecuteResponse(
                code=200,
                message="执行成功",
                data={"affected_rows": affected}
            )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"数据库执行错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"未知错误: {str(e)}")

# 模块加载时自动加载数据源
load_datasources()