import os
import logging
from datetime import datetime

# Gecerli gorsel dosya uzantilari
GECERLI_UZANTILAR = (".jpg", ".jpeg", ".png", ".gif", ".bmp")

# Diger modullerle ayni sekilde root logger'dan miras al
_logger = logging.getLogger(__name__)

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
