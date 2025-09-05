import os
import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

def _setup_logger():
    """Answer utils icin logger kurulumu - File logging ile"""
    logger = logging.getLogger('AnswerUtils')
    logger.setLevel(logging.INFO)
    
    # Eger handler yoksa ekle (tekrar eklenmesini onler)
    if not logger.handlers:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # File handler - rotating logs
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "answer_utils.log"),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Error handler - sadece hatalar
        error_handler = RotatingFileHandler(
            os.path.join(log_dir, "errors.log"),
            maxBytes=5*1024*1024,
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        error_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
    
    return logger

# Global logger instance
_logger = _setup_logger()

def get_answer_for_image(image_path):
    """
    Gorsel dosyasi icin cevap bilgisini dondurur.
    Metadata yaklasimini kullanir: Her zorluk seviyesi klasorunde bir cevaplar.json dosyasi arar.
    """
    # _logger.debug(f"Cevap araniyor: {os.path.basename(image_path)}")  # Fazlalık
    
    try:
        folder_path = os.path.dirname(image_path)
        metadata_path = os.path.join(folder_path, "cevaplar.json")
        
        # _logger.debug(f"Metadata dosyasi kontrol ediliyor: {os.path.basename(metadata_path)}")  # Fazlalık
        
        if os.path.exists(metadata_path):
            # _logger.debug("Metadata dosyasi bulundu")  # Fazlalık
            
            with open(metadata_path, "r", encoding="utf-8") as f:
                answers = json.load(f)
                
            filename = os.path.basename(image_path)
            answer = answers.get(filename, "?")
            
            if answer == "?":
                _logger.warning(f"Dosya metadata'da bulunamadi: {filename}")
            # else:
                # _logger.debug(f"Cevap bulundu - {filename}: {answer}")  # Fazlalık
            
            return answer
        else:
            _logger.warning(f"Metadata dosyasi bulunamadi: {os.path.basename(folder_path)}/cevaplar.json")
            return "?"
        
    except json.JSONDecodeError as e:
        _logger.error(f"JSON dosyasi bozuk: {e}")
        return "?"
    except FileNotFoundError as e:
        _logger.error(f"Dosya bulunamadi: {e}")
        return "?"
    except Exception as e:
        _logger.error(f"Beklenmeyen cevap okuma hatasi: {e}")
        return "?"

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
