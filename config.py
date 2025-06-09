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
        "export_format": os.getenv("EXPORT_FORMAT", "pdf").lower(),  # 支持 pdf 或 markdown
    }
    
    # 验证导出格式
    if config["export_format"] not in ["pdf", "markdown"]:
        print(f"警告: 不支持的导出格式 '{config['export_format']}'，将使用默认格式 'pdf'")
        config["export_format"] = "pdf"
    
    return config

def save_config(config_data: dict[str, Any]) -> bool:
    """
    环境变量模式下不支持保存配置
    """
    print("警告: 环境变量模式下不支持保存配置，请直接设置环境变量")
    return False