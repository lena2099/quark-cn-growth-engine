"""
配置加载工具
"""
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

load_dotenv()


def load_config(config_path: str = None) -> dict:
    """加载配置文件"""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "settings.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # 环境变量注入
    _inject_env_vars(config)

    return config


def _inject_env_vars(config: dict):
    """将环境变量注入配置"""
    # 数据库
    if os.getenv("DATABASE_URL"):
        config["database"]["postgres_url"] = os.getenv("DATABASE_URL")
    if os.getenv("REDIS_URL"):
        config["database"]["redis_url"] = os.getenv("REDIS_URL")

    # 通知
    if os.getenv("WECHAT_WEBHOOK"):
        config["notifications"]["wechat_work_webhook"] = os.getenv("WECHAT_WEBHOOK")
    if os.getenv("FEISHU_WEBHOOK"):
        config["notifications"]["feishu_webhook"] = os.getenv("FEISHU_WEBHOOK")

    # 邮件
    if os.getenv("QUARK_EMAIL"):
        config["outreach"]["email"]["from_address"] = os.getenv("QUARK_EMAIL")
    if os.getenv("SMTP_HOST"):
        config["outreach"]["email"]["smtp_host"] = os.getenv("SMTP_HOST")
    if os.getenv("SMTP_PASSWORD"):
        config["outreach"]["email"]["smtp_password"] = os.getenv("SMTP_PASSWORD")
