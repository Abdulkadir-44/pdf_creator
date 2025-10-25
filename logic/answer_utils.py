import os
import json
import logging

# Yeni loglama sistemi: Bu modülün kendi logger'ını al.
# Adı otomatik olarak 'logic.answer_utils' olacaktır.
logger = logging.getLogger(__name__)

def get_answer_for_image(image_path):
    """
    Gorsel dosyasi icin cevap bilgisini dondurur.
    Metadata yaklasimini kullanir: Her zorluk seviyesi klasorunde bir cevaplar.json dosyasi arar.
    """
    try:
        folder_path = os.path.dirname(image_path)
        metadata_path = os.path.join(folder_path, "cevaplar.json")
        
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                answers = json.load(f)
            
            filename = os.path.basename(image_path)
            answer = answers.get(filename, "?")
            
            if answer == "?":
                logger.warning(f"Dosya '{filename}' cevap metadata'sında bulunamadı.")
            
            return answer
        else:
            logger.warning(f"Metadata dosyası bulunamadı: {os.path.basename(folder_path)}/cevaplar.json")
            return "?"
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON dosyası bozuk veya okunamıyor: {metadata_path}", exc_info=True)
        return "?"
    except FileNotFoundError as e:
        logger.error(f"Dosya bulunamadı hatası: {e}", exc_info=True)
        return "?"
    except Exception as e:
        logger.error(f"Cevap okunurken beklenmedik bir hata oluştu: {e}", exc_info=True)
        return "?"

def set_log_level(level):
    """Logger seviyesini degistirir."""
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    
    log_level = level.upper()
    if log_level in level_map:
        logger.setLevel(level_map[log_level])
        logger.info(f"Log seviyesi {log_level} olarak ayarlandi.")
    else:
        logger.warning(f"Gecersiz log seviyesi belirtildi: {level}")