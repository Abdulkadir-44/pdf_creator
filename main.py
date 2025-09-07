from logger_config import setup_logging 
import logging                       
from ui.main_ui import AnaPencere

setup_logging() 
logger = logging.getLogger(__name__) 

if __name__ == "__main__":
    logger.info("========================================")
    logger.info("Soru Otomasyon Sistemi Uygulaması Başlatılıyor...") 
    logger.info("========================================")
    
    app = AnaPencere()
    app.mainloop()
    
    logger.info("Uygulama Kapatıldı.") # <--- EKLENDİ