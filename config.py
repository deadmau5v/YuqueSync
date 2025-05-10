from typing import Any
import yaml
import os

def get_config() -> dict[str, Any]:
    with open("./config.yaml", "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    
    # 设置默认值
    if "monitor_interval_minutes" not in config_data:
        config_data["monitor_interval_minutes"] = 60

    return config_data

def save_config(config_data: dict[str, Any]) -> bool:
    """
    保存配置到文件
    
    :param config_data: 配置数据
    :return: 是否成功
    """
    try:
        with open("./config.yaml", "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {e}")
        return False