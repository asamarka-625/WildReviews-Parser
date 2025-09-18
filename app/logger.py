# Внешние зависимости
import logging
import sys
from typing import Optional


def setup_logger(
    name: str = __name__,
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_str: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
) -> logging.Logger:
    
    logger = logging.getLogger(name)
    
    # Уровень
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    if not logger.handlers:
        # Форматтер
        formatter = logging.Formatter(format_str)
        
        # Обработчик для stdout
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        logger.addHandler(stdout_handler)
        
        # Обработчик для файла
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger