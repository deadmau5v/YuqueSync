import os
from typing import Any

def get_config() -> dict[str, Any]:
    """
    从环境变量获取配置，如果环境变量不存在则使用默认值
    """
    config = {
        "yuque": {
            "base_url": os.getenv("YUQUE_BASE_URL", "https://www.yuque.com"),
            "token": os.getenv("YUQUE_TOKEN", ""),
            "session": os.getenv("YUQUE_SESSION", ""),
        },
        "save_path": os.getenv("SAVE_PATH", "/data"),
        "monitor_interval_minutes": int(os.getenv("MONITOR_INTERVAL_MINUTES", "10")),
    }
    
    return config

def save_config(config_data: dict[str, Any]) -> bool:
    """
    环境变量模式下不支持保存配置
    """
    print("警告: 环境变量模式下不支持保存配置，请直接设置环境变量")
    return False