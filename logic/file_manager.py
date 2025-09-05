import os
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Gecerli gorsel dosya uzantilari
GECERLI_UZANTILAR = (".jpg", ".jpeg", ".png", ".gif", ".bmp")

def _setup_logger():
    """Folder utils icin logger kurulumu - File logging ile"""
    logger = logging.getLogger('FolderUtils')
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "file_manager.log"),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        error_handler = RotatingFileHandler(
            os.path.join(log_dir, "errors.log"),
            maxBytes=5*1024*1024,
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
    
    return logger

_logger = _setup_logger()

def set_log_level(level):
    """Logger seviyesini degistirir."""
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    
    if level.upper() in level_map:
        _logger.setLevel(level_map[level.upper()])
        _logger.info(f"Log seviyesi {level.upper()} olarak ayarlandi")
    else:
        _logger.warning(f"Gecersiz log seviyesi: {level}")
