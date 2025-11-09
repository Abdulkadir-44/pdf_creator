import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """
    Proje genelindeki loglama sistemini merkezi olarak kurar.
    Logları 'general.log' ve 'errors.log' dosyalarına,
    belirtilen özel formatla yazar.
    Bu fonksiyonun projenin başlangıcında SADECE BİR KEZ çağrılması yeterlidir.
    """
    
    
    app_data_path = os.getenv('APPDATA')
    if not app_data_path:
        
        app_data_path = os.path.dirname(os.path.abspath(__file__)) 

    # 'C:\Users\abdul\AppData\Roaming\SoruOtomasyonSistemi\logs' yolunu oluştur
    log_dir = os.path.join(app_data_path, "SoruOtomasyonSistemi", "logs")
    # --- YENİ KOD BİTTİ ---
    
    os.makedirs(log_dir, exist_ok=True)
    
    # Kök logger'ı (root logger) yapılandırıyoruz.
    # Diğer tüm logger'lar bu ayarları miras alacak.
    root_logger = logging.getLogger()
    
    
    if root_logger.handlers:
        return

    root_logger.setLevel(logging.DEBUG) 

    
    log_format = (
        "%(asctime)s | %(name)-20s | %(funcName)-25s | %(levelname)-8s | %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"
    
    formatter = logging.Formatter(log_format, date_format)

    # --- Genel Loglar için Handler (general.log) ---
    general_log_path = os.path.join(log_dir, "general.log")
    general_handler = RotatingFileHandler(
        general_log_path, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    general_handler.setLevel(logging.INFO) # Genel loglara INFO ve üzerini yaz
    general_handler.setFormatter(formatter)
    
    # --- Hata Logları için Handler (errors.log) ---
    error_log_path = os.path.join(log_dir, "errors.log")
    error_handler = RotatingFileHandler(
        error_log_path, maxBytes=2*1024*1024, backupCount=3, encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR) # Hata loglarına sadece ERROR ve üzerini yaz
    error_handler.setFormatter(formatter)
    
    # Handler'ları kök logger'a ekle
    root_logger.addHandler(general_handler)
    root_logger.addHandler(error_handler)
    
    root_logger.info("Loglama sistemi başarıyla kuruldu.")