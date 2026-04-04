"""
日志配置模块
提供统一的日志配置服务
"""

import logging
import logging.handlers
import os
from pathlib import Path


def get_log_dir() -> Path:
    """获取日志目录"""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    return log_dir


def setup_logging(
    name: str = "ontology-platform",
    level: int = logging.INFO,
    log_file: str = None,
    console: bool = True,
    format_string: str = None
) -> logging.Logger:
    """
    配置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径（可选）
        console: 是否输出到控制台
        format_string: 自定义格式字符串
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()
    
    # 默认格式
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(format_string)
    
    # 文件处理器
    if log_file:
        log_path = Path(log_file)
    else:
        log_path = get_log_dir() / f"{name}.log"
    
    # 使用 RotatingFileHandler 实现日志轮转
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


# 默认日志配置
default_logger = setup_logging()


if __name__ == "__main__":
    # 测试日志配置
    logger = setup_logging("test")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
