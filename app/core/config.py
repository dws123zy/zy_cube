"""
配置管理模块
负责加载和管理 YAML 配置文件，并提供配置访问接口
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """全局配置管理类"""
    
    def __init__(self):
        self._config: Dict[str, Any] = {}
        self._config_path: Optional[Path] = None
        self._loaded = False
    
    def load(self, config_path: Optional[str] = None) -> None:
        """
        加载配置文件
        :param config_path: 配置文件路径，如果为 None 则使用默认路径
        """
        if config_path is None:
            # 默认配置文件路径：../conf/config.yaml
            base_dir = Path(__file__).parent.parent.parent.parent
            config_path = base_dir / "conf" / "config.yaml"
        else:
            config_path = Path(config_path)
        
        self._config_path = config_path
        
        if not config_path.exists():
            # 如果配置文件不存在，创建默认配置
            self._create_default_config()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
        
        # 合并默认值
        self._merge_defaults()
        self._loaded = True
    
    def _create_default_config(self) -> None:
        """创建默认配置文件"""
        # 确保目录存在
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            "external_root": "../",
            "conf_dir": "conf",
            "mod_dir": "mod",
            "web_dir": "web",
            "web_lib": "weblib",
            "log_dir": "log",
            "web_url_prefix": "/webapps",
            "allowed_extensions": [".html", ".htm"],
            "jwt_secret_key": "your-secret-key-change-in-production",
            "jwt_algorithm": "HS256",
            "token_expire_minutes": 480,
            "module_auto_load": True,
            "module_allowed_paths": ["../mod"],
            "log_level": "INFO",
            "log_max_bytes": 10485760,
            "log_backup_count": 5,
        }
        
        with open(self._config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
    
    def _merge_defaults(self) -> None:
        """合并默认配置，确保所有必需的键都存在"""
        defaults = {
            "external_root": "../",
            "conf_dir": "conf",
            "mod_dir": "mod",
            "web_dir": "web",
            "web_lib": "weblib",
            "log_dir": "log",
            "web_url_prefix": "/webapps",
            "allowed_extensions": [".html", ".htm"],
            "jwt_secret_key": "your-secret-key-change-in-production",
            "jwt_algorithm": "HS256",
            "token_expire_minutes": 480,
            "module_auto_load": True,
            "module_allowed_paths": ["../mod"],
            "log_level": "INFO",
            "log_max_bytes": 10485760,
            "log_backup_count": 5,
        }
        
        for key, default_value in defaults.items():
            if key not in self._config:
                self._config[key] = default_value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        if not self._loaded:
            self.load()
        return self._config.get(key, default)
    
    @property
    def external_root(self) -> Path:
        """外部根目录的绝对路径"""
        root = self.get("external_root")
        if root.startswith('/') or (len(root) > 1 and root[1] == ':'):
            # 绝对路径
            return Path(root)
        else:
            # 相对路径，相对于当前工作目录
            return Path.cwd() / root
    
    @property
    def conf_dir(self) -> Path:
        """配置目录绝对路径"""
        return self.external_root / self.get("conf_dir")
    
    @property
    def mod_dir(self) -> Path:
        """模块目录绝对路径"""
        return self.external_root / self.get("mod_dir")
    
    @property
    def web_dir(self) -> Path:
        """Web文件目录绝对路径"""
        return self.external_root / self.get("web_dir")
    
    @property
    def log_dir(self) -> Path:
        """日志目录绝对路径"""
        return self.external_root / self.get("log_dir")
    
    @property
    def modules_manifest_file(self) -> Path:
        """模块清单文件路径"""
        return self.conf_dir / "modules_manifest.json"
    
    def __repr__(self) -> str:
        return f"Config(loaded={self._loaded}, path={self._config_path})"


# 全局配置实例
config = Config()