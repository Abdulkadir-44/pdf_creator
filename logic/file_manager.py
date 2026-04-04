import os
import logging
from datetime import datetime

# Gecerli gorsel dosya uzantilari
GECERLI_UZANTILAR = (".jpg", ".jpeg", ".png", ".gif", ".bmp")

# Diger modullerle ayni sekilde root logger'dan miras al
_logger = logging.getLogger(__name__)
