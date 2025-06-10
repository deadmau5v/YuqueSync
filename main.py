# -*- coding: utf-8 -*-
import asyncio
import logging
import argparse
import sys
import os
from yuque import download_all, download_and_monitor
from config import get_config, save_config

# 设置Windows环境下的UTF-8编码支持
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('yuque_monitor.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description='语雀文档下载与监控工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 下载命令
    download_parser = subparsers.add_parser('download', help='下载所有文档')
    
    # 监控命令
    monitor_parser = subparsers.add_parser('monitor', help='监控文档更新')
    monitor_parser.add_argument(
        '--interval', '-i', type=int, help='监控间隔时间（分钟）'
    )
    
    # 设置配置命令
    config_parser = subparsers.add_parser('config', help='设置配置')
    config_parser.add_argument(
        '--interval', '-i', type=int, help='设置监控间隔时间（分钟）'
    )
    
    return parser.parse_args()

async def main():
    args = parse_args()
    
    # 根据命令执行对应操作
    if args.command == 'download':
        logger.info("开始下载所有文档...")
        await download_all()
        logger.info("所有文档下载完成！")
    
    elif args.command == 'monitor':
        interval = args.interval if args.interval else get_config().get("monitor_interval_minutes", 60)
        logger.info(f"开始监控文档更新，间隔时间: {interval}分钟")
        if args.interval:
            logger.info(f"使用命令行指定的间隔时间: {args.interval}分钟")
        await download_and_monitor(interval)
    
    elif args.command == 'config':
        if args.interval:
            config = get_config()
            config["monitor_interval_minutes"] = args.interval
            if save_config(config):
                logger.info(f"监控间隔时间已更新为: {args.interval}分钟")
            else:
                logger.error("配置保存失败")
        else:
            logger.info("当前配置:")
            config = get_config()
            logger.info(f"  监控间隔时间: {config.get('monitor_interval_minutes', 60)}分钟")
            logger.info(f"  保存路径: {config.get('save_path')}")
    
    else:
        logger.error("未知命令，请使用 --help 查看帮助")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"程序运行出错: {e}")
        sys.exit(1) 