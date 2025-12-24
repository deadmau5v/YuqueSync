# -*- coding: utf-8 -*-
import os
from typing import Any
from dotenv import load_dotenv

def load_env():
    """
    加载环境变量
    """
    try:
        load_dotenv()
    except:
        print("跳过加载 .env")
        pass
        

def get_config() -> dict[str, Any]:
    """
    从环境变量获取配置，如果环境变量不存在则使用默认值
    """
    load_env()

    # 读取环境变量
    yuque_base_url = os.getenv("YUQUE_BASE_URL", "https://www.yuque.com")
    yuque_token = os.getenv("YUQUE_TOKEN", "")
    yuque_session = os.getenv("YUQUE_SESSION", "")
    save_path = os.getenv("SAVE_PATH", "/data")
    monitor_interval = os.getenv("MONITOR_INTERVAL_MINUTES", "10")
    export_format = os.getenv("EXPORT_FORMAT", "pdf").lower()

    # 验证必需的配置
    if not yuque_token:
        print("警告: YUQUE_TOKEN 未设置或为空")
    if not yuque_session:
        print("警告: YUQUE_SESSION 未设置或为空")

    config = {
        "yuque": {
            "base_url": yuque_base_url,
            "token": yuque_token,
            "session": yuque_session,
        },
        "save_path": save_path,
        "monitor_interval_minutes": int(monitor_interval),
        "export_format": export_format,
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