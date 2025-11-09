import os
import json
import logging

# Yeni loglama sistemi: Bu modülün kendi logger'ını al.
# Adı otomatik olarak 'logic.answer_utils' olacaktır.
logger = logging.getLogger(__name__)

def get_answer_for_image(image_path):
    """
    GÜNCELLENDİ (HİBRİT SİSTEM):
    Dosya yolunda 'test' kelimesi varsa cevabı dosya adından ('1-A.png') okur.
    Dosya yolunda 'yazili' kelimesi varsa cevabı 'cevaplar.json' dosyasından okur.
    """
    try:
        # Dosya yolunu küçük harfe çevirerek 'test' veya 'yazili' ara
        # (Windows/Linux/Mac yolları için os.path.normpath ile normalize edelim)
        normalized_path = os.path.normpath(image_path).lower()
        
        # Yoldaki ayırıcıları standart hale getir (Windows '\' vs Linux '/')
        normalized_path = normalized_path.replace(os.sep, '/')

        # --- TEST MODU (Dosya Adından Oku) ---
        if '/test/' in normalized_path:
            # 1. Dosya adını ve uzantısını ayır (örn: "1-A.png" -> "1-A" ve ".png")
            filename_with_ext = os.path.basename(image_path)
            file_root, file_ext = os.path.splitext(filename_with_ext)
            
            # 2. Dosya adında '-' (tire) olup olmadığını kontrol et
            if '-' in file_root:
                # 3. Dosya adını SADECE EN SON tire'den böl
                parts = file_root.rsplit('-', 1)
                
                if len(parts) >= 2:
                    # 4. Son parçayı (cevabı) al, boşlukları temizle ve BÜYÜK harfe çevir
                    answer = parts[-1].strip().upper()
                    return answer
                else:
                    logger.warning(f"TEST modu: Dosya '{filename_with_ext}' cevap formatı bozuk (tire'den sonrası yok).")
                    return "?"
            else:
                # 5. Dosya adında '-' (tire) yoksa (örn: "soru.png")
                logger.warning(f"TEST modu: Dosya '{filename_with_ext}' cevap formatına uymuyor (tire '-' yok).")
                return "?"

        # --- YAZILI MODU (JSON'dan Oku) ---
        elif '/yazili/' in normalized_path:
            folder_path = os.path.dirname(image_path)
            metadata_path = os.path.join(folder_path, "cevaplar.json")
            
            if os.path.exists(metadata_path):
                with open(metadata_path, "r", encoding="utf-8") as f:
                    answers = json.load(f)
                
                filename = os.path.basename(image_path)
                # JSON'dan cevabı al
                answer = answers.get(filename, "?")
                
                if answer == "?":
                    logger.warning(f"YAZILI modu: Dosya '{filename}' cevap metadata'sında bulunamadı.")
                
                return answer
            else:
                logger.warning(f"YAZILI modu: Metadata dosyası bulunamadı: {os.path.basename(folder_path)}/cevaplar.json")
                return "?"

        # --- HİÇBİRİ DEĞİLSE (veya format bozuksa) ---
        else:
            logger.error(f"Cevap okunamadı: Dosya yolu '{image_path}' ne 'test' ne de 'yazili' içeriyor.")
            return "?"
            
    except json.JSONDecodeError as e:
        logger.error(f"YAZILI modu: JSON dosyası bozuk veya okunamıyor: {metadata_path}", exc_info=True)
        return "?"
    except Exception as e:
        # 7. Beklenmedik bir hata olursa ASLA ÇÖKME
        logger.error(f"Cevap okunurken beklenmedik bir hata oluştu: {image_path}", exc_info=True)
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