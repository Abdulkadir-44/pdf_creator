import os
import json

def get_answer_for_image(image_path):
    """
    Görsel dosyası için cevap bilgisini döndürür.
    Metadata yaklaşımını kullanır: Her zorluk seviyesi klasöründe bir cevaplar.json dosyası arar.
    
    Args:
        image_path (str): Görsel dosyasının tam yolu
        
    Returns:
        str: Görsel için cevap (A, B, C, D, E) veya bulunamazsa "?"
    """
    print(f"DEBUG - get_answer_for_image çağrıldı: {image_path}")
    try:
        # Görsel dosyasının bulunduğu klasörü al
        folder_path = os.path.dirname(image_path)
        print(f"DEBUG - Klasör yolu: {folder_path}")
        metadata_path = os.path.join(folder_path, "cevaplar.json")
        print(f"DEBUG - Metadata dosya yolu: {metadata_path}")
        
        # Metadata dosyası varsa oku
        if os.path.exists(metadata_path):
            print(f"DEBUG - Metadata dosyası bulundu: {metadata_path}")
            with open(metadata_path, "r", encoding="utf-8") as f:
                answers = json.load(f)
                # Dosya adını al ve cevabı bul
                filename = os.path.basename(image_path)
                print(f"DEBUG - Aranan dosya adı: {filename}")
                answer = answers.get(filename, "?")
                print(f"DEBUG - Bulunan cevap: {answer}")
                return answer
        else:
            print(f"DEBUG - Metadata dosyası bulunamadı: {metadata_path}")
        
        return "?"
    except Exception as e:
        print(f"DEBUG - HATA: Cevap bilgisi okuma hatası: {e}")
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
    try:
        metadata_path = os.path.join(folder_path, "cevaplar.json")
        
        # Mevcut bir dosya varsa, içeriğini oku ve güncelle
        existing_answers = {}
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                existing_answers = json.load(f)
        
        # Yeni cevapları ekle/güncelle
        existing_answers.update(answers_dict)
        
        # Dosyaya kaydet
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(existing_answers, f, ensure_ascii=False, indent=4)
        
        return True
    except Exception as e:
        print(f"Metadata oluşturma hatası: {e}")
        return False