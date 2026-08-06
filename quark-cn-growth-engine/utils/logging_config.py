"""
日志配置
"""
import logging
import sys
from pathlib import Path


def setup_logging(level: int = logging.INFO):
    """配置全局日志"""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    console.setLevel(level)

    # 文件
    file_handler = logging.FileHandler(
        log_dir / "engine.log", encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(logging.DEBUG)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(console)
    root.addHandler(file_handler)

    # 降低第三方库日志等级
    for lib in ["httpx", "apscheduler", "urllib3", "asyncio"]:
        logging.getLogger(lib).setLevel(logging.WARNING)
