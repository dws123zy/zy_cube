"""
日志模块
配置日志输出到文件和控制台
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from .config import config


def setup_logging() -> None:
    """
    配置全局日志系统
    - 输出到文件：log_dir/zy_cube.log
    - 输出到控制台（INFO级别）
    - 使用RotatingFileHandler，自动轮转
    """
    log_dir = config.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / "zy_cube.log"
    log_level = config.get("log_level", "INFO").upper()
    max_bytes = config.get("log_max_bytes", 10485760)
    backup_count = config.get("log_backup_count", 5)
    
    # 创建日志格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 文件处理器（轮转）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, log_level))
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)  # 控制台始终INFO
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # 避免重复日志（如果多次调用setup_logging）
    root_logger.propagate = False
    
    # 记录启动日志
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器
    :param name: 记录器名称，通常使用 __name__
    """
    return logging.getLogger(name)