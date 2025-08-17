import os
import json
import logging
from datetime import datetime

# Logger kurulumu
def _setup_logger():
    """Answer utils için logger kurulumu"""
    logger = logging.getLogger('AnswerUtils')
    logger.setLevel(logging.INFO)
    
    # Eğer handler yoksa ekle (tekrar eklenmesini önler)
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter - dosya ve satır bilgisi ile
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

# Global logger instance
_logger = _setup_logger()

def get_answer_for_image(image_path):
    """
    Görsel dosyası için cevap bilgisini döndürür.
    Metadata yaklaşımını kullanır: Her zorluk seviyesi klasöründe bir cevaplar.json dosyası arar.
    
    Args:
        image_path (str): Görsel dosyasının tam yolu
        
    Returns:
        str: Görsel için cevap (A, B, C, D, E) veya bulunamazsa "?"
    """
    _logger.debug(f"Cevap aranıyor: {os.path.basename(image_path)}")
    
    try:
        # Görsel dosyasının bulunduğu klasörü al
        folder_path = os.path.dirname(image_path)
        metadata_path = os.path.join(folder_path, "cevaplar.json")
        
        _logger.debug(f"Metadata dosyası kontrol ediliyor: {os.path.basename(metadata_path)}")
        
        # Metadata dosyası varsa oku
        if os.path.exists(metadata_path):
            _logger.debug("Metadata dosyası bulundu")
            
            with open(metadata_path, "r", encoding="utf-8") as f:
                answers = json.load(f)
                
            # Dosya adını al ve cevabı bul
            filename = os.path.basename(image_path)
            answer = answers.get(filename, "?")
            
            if answer != "?":
                _logger.debug(f"Cevap bulundu - {filename}: {answer}")
            else:
                _logger.warning(f"Dosya metadata'da bulunamadı: {filename}")
            
            return answer
        else:
            _logger.warning(f"Metadata dosyası bulunamadı: {os.path.basename(folder_path)}/cevaplar.json")
            return "?"
        
    except json.JSONDecodeError as e:
        _logger.error(f"JSON dosyası bozuk: {e}")
        return "?"
    except FileNotFoundError as e:
        _logger.error(f"Dosya bulunamadı: {e}")
        return "?"
    except Exception as e:
        _logger.error(f"Beklenmeyen cevap okuma hatası: {e}")
        return "?"

def create_answer_metadata(folder_path, answers_dict):
    """
    Belirtilen klasöre cevaplar.json dosyası oluşturur veya günceller.
    
    Args:
        folder_path (str): Metadata dosyasının oluşturulacağı klasör yolu
        answers_dict (dict): Dosya adı -> cevap eşleştirmelerini içeren sözlük
        
    Returns:
        bool: İşlem başarılıysa True, değilse False
    """
    _logger.info(f"Metadata oluşturuluyor: {os.path.basename(folder_path)} ({len(answers_dict)} cevap)")
    
    try:
        metadata_path = os.path.join(folder_path, "cevaplar.json")
        
        # Mevcut bir dosya varsa, içeriğini oku ve güncelle
        existing_answers = {}
        if os.path.exists(metadata_path):
            _logger.debug("Mevcut metadata dosyası bulundu, güncelleniyor")
            
            with open(metadata_path, "r", encoding="utf-8") as f:
                existing_answers = json.load(f)
        else:
            _logger.debug("Yeni metadata dosyası oluşturuluyor")
        
        # Yeni cevapları ekle/güncelle
        updated_count = 0
        new_count = 0
        
        for filename, answer in answers_dict.items():
            if filename in existing_answers:
                if existing_answers[filename] != answer:
                    updated_count += 1
                    _logger.debug(f"Cevap güncellendi - {filename}: {existing_answers[filename]} -> {answer}")
            else:
                new_count += 1
                _logger.debug(f"Yeni cevap eklendi - {filename}: {answer}")
        
        existing_answers.update(answers_dict)
        
        # Dosyaya kaydet
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(existing_answers, f, ensure_ascii=False, indent=4)
        
        _logger.info(f"Metadata başarıyla kaydedildi - Yeni: {new_count}, Güncellenen: {updated_count}, Toplam: {len(existing_answers)}")
        return True
        
    except PermissionError as e:
        _logger.error(f"Dosya yazma izni yok: {e}")
        return False
    except json.JSONDecodeError as e:
        _logger.error(f"Mevcut JSON dosyası bozuk: {e}")
        return False
    except Exception as e:
        _logger.error(f"Metadata oluşturma hatası: {e}")
        return False

def validate_answers_metadata(folder_path):
    """
    Cevaplar.json dosyasını doğrular ve eksik/fazla kayıtları raporlar.
    
    Args:
        folder_path (str): Kontrol edilecek klasör yolu
        
    Returns:
        dict: Validasyon sonuçları
    """
    _logger.info(f"Metadata validasyonu başlatılıyor: {os.path.basename(folder_path)}")
    
    try:
        metadata_path = os.path.join(folder_path, "cevaplar.json")
        
        if not os.path.exists(metadata_path):
            _logger.warning("Metadata dosyası bulunamadı")
            return {
                "status": "missing",
                "message": "cevaplar.json dosyası bulunamadı"
            }
        
        # JSON dosyasını oku
        with open(metadata_path, "r", encoding="utf-8") as f:
            answers = json.load(f)
        
        # Klasördeki görsel dosyalarını al
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
        image_files = [f for f in os.listdir(folder_path) 
                      if f.lower().endswith(image_extensions)]
        
        # Eksik ve fazla kayıtları bul
        missing_answers = [f for f in image_files if f not in answers]
        extra_answers = [f for f in answers.keys() if f not in image_files]
        
        # Geçersiz cevapları kontrol et
        valid_answers = {'A', 'B', 'C', 'D', 'E', '?'}
        invalid_answers = {f: ans for f, ans in answers.items() 
                          if ans not in valid_answers}
        
        # Sonuçları raporla
        if missing_answers:
            _logger.warning(f"{len(missing_answers)} dosya için cevap eksik: {missing_answers[:3]}...")
        
        if extra_answers:
            _logger.warning(f"{len(extra_answers)} fazla cevap kaydı: {extra_answers[:3]}...")
        
        if invalid_answers:
            _logger.error(f"{len(invalid_answers)} geçersiz cevap: {list(invalid_answers.items())[:3]}...")
        
        status = "valid"
        if missing_answers or extra_answers or invalid_answers:
            status = "invalid"
        
        result = {
            "status": status,
            "total_images": len(image_files),
            "total_answers": len(answers),
            "missing_answers": missing_answers,
            "extra_answers": extra_answers,
            "invalid_answers": invalid_answers
        }
        
        _logger.info(f"Validasyon tamamlandı - Durum: {status}, Görseller: {len(image_files)}, Cevaplar: {len(answers)}")
        return result
        
    except json.JSONDecodeError as e:
        _logger.error(f"JSON dosyası bozuk: {e}")
        return {
            "status": "corrupted",
            "message": f"JSON dosyası bozuk: {str(e)}"
        }
    except Exception as e:
        _logger.error(f"Validasyon hatası: {e}")
        return {
            "status": "error",
            "message": f"Validasyon hatası: {str(e)}"
        }

def get_folder_answer_stats(folder_path):
    """
    Klasör için cevap istatistiklerini döndürür.
    
    Args:
        folder_path (str): Analiz edilecek klasör yolu
        
    Returns:
        dict: Cevap istatistikleri
    """
    _logger.debug(f"Cevap istatistikleri hesaplanıyor: {os.path.basename(folder_path)}")
    
    try:
        metadata_path = os.path.join(folder_path, "cevaplar.json")
        
        if not os.path.exists(metadata_path):
            _logger.warning("İstatistik için metadata dosyası bulunamadı")
            return {"error": "Metadata dosyası bulunamadı"}
        
        with open(metadata_path, "r", encoding="utf-8") as f:
            answers = json.load(f)
        
        # Cevap dağılımını hesapla
        answer_counts = {}
        for answer in answers.values():
            answer_counts[answer] = answer_counts.get(answer, 0) + 1
        
        # İstatistikleri hesapla
        total = len(answers)
        stats = {
            "total_questions": total,
            "answer_distribution": answer_counts,
            "missing_answers": answer_counts.get("?", 0)
        }
        
        # Yüzdelik hesapla
        if total > 0:
            stats["percentages"] = {
                answer: round((count / total) * 100, 1) 
                for answer, count in answer_counts.items()
            }
        
        _logger.debug(f"İstatistikler - Toplam: {total}, Dağılım: {answer_counts}")
        return stats
        
    except Exception as e:
        _logger.error(f"İstatistik hesaplama hatası: {e}")
        return {"error": f"İstatistik hatası: {str(e)}"}

# Logger seviyesini değiştirmek için yardımcı fonksiyon
def set_log_level(level):
    """
    Logger seviyesini değiştirir.
    
    Args:
        level (str): 'DEBUG', 'INFO', 'WARNING', 'ERROR'
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    
    if level.upper() in level_map:
        _logger.setLevel(level_map[level.upper()])
        _logger.info(f"Log seviyesi {level.upper()} olarak ayarlandı")
    else:
        _logger.warning(f"Geçersiz log seviyesi: {level}")