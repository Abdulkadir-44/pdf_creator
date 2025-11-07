# logic/resim_yonetimi_beyni.py

import os
import logging
from PIL import Image
import shutil  
from datetime import datetime 

logger = logging.getLogger(__name__)
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')

class ResimYonetimiBeyni:
    
    def __init__(self):
        logger.info("Resim Yönetimi Beyni başlatıldı.")
        
        # --- ÖNBELLEKLER ARTIK BURADA ---
        self._count_cache = {}
        self._size_cache = {}
        self.ana_klasor_yolu = None
        self._thumb_cache = {} # PIL Thumbnail cache (PIL.Image nesneleri tutar)


    def set_ana_klasor(self, path: str):
        """Beynin ana klasörü bilmesini sağlar ve önbelleği temizler."""
        self.ana_klasor_yolu = path
        self._clear_caches()
        logger.info(f"Beyin için ana klasör ayarlandı: {path}")
    
    def get_folder_level(self, folder_path):
        """Klasörün hangi seviyede olduğunu belirle"""
        # self.ana_klasor_yolu'nun "beyin" sınıfında set edilmiş olmasını bekler
        if not self.ana_klasor_yolu:
            return "UNKNOWN"
        
        try:
            # os import'unun dosyanın en üstünde olduğundan emin olun
            relative = os.path.relpath(folder_path, self.ana_klasor_yolu)
            
            # Eğer path'ler aynıysa, relpath '.' döner.
            if relative == ".":
                return "ROOT" # Veya "DERS" klasörünün üstü için bir ad
            
            depth = len(relative.split(os.sep))
            
            if depth == 1:
                return "DERS"
            elif depth == 2:
                return "KONU"
            elif depth == 3:
                return "TUR"
            elif depth == 4:
                return "ZORLUK"
            else:
                return "UNKNOWN"
        except:
            return "UNKNOWN"

    def is_zorluk_folder(self, folder_path: str) -> bool:
        """Seçilen klasör Kolay/Orta/Zor seviyelerinden biri mi?"""
        if not folder_path:
            return False
        # os import'unun dosyanın en üstünde olduğundan emin olun
        last = os.path.basename(os.path.normpath(folder_path))
        return last in {"Kolay", "Orta", "Zor"}
            
    def _clear_caches(self):
        """Tüm istatistik önbelleklerini temizler."""
        self._count_cache.clear()
        self._size_cache.clear()
        self._thumb_cache.clear()
        logger.debug("Beyin önbellekleri (sayım, boyut) temizlendi.")

    def _has_subfolders(self, folder_path: str) -> bool:
        """
        Bir klasörün HİÇ alt klasörü olup olmadığını HIZLICA kontrol eder.
        Dosyaları saymaz, sadece bir alt klasör bulduğu an True döner.
        """
        try:
            for item in os.listdir(folder_path):
                if os.path.isdir(os.path.join(folder_path, item)):
                    return True # Bir tane bile bulduysa, [+] gerekir
            return False # Döngü bitti, hiç alt klasör yok
        except Exception:
            return False # Erişim hatası vb.
        
    def get_pil_thumbnail(self, path: str, max_size: tuple = (180, 180)):
        """
        Bir resmin PIL.Image thumbnail'ını üretir ve cache'ler.
        CTK BİLMEZ. Sadece PIL bilir.
        """
        if path in self._thumb_cache:
            return self._thumb_cache[path]
        
        try:
            img = Image.open(path)
            # Kodunuzda LANCZOS kullanılıyor, onu koruyoruz
            img.thumbnail(max_size, Image.LANCZOS) 
            self._thumb_cache[path] = img
            return img
        except Exception as e:
            logger.warning(f"PIL thumbnail üretilemedi: {path} -> {e}")
            return None

    def kopyala_resim(self, src_path: str, hedef_yol: str):
        """Sadece kopyalama işini yapar."""
        # Not: Gelecekte (Aşama 3) bu fonksiyonu bir thread'de çalıştıracağız.
        shutil.copy2(src_path, hedef_yol) #'daki mantık
        logger.info(f"Kopyalandı: {src_path} -> {hedef_yol}")

    def sil_resim(self, resim_yolu: str):
        """Sadece silme işini yapar."""
        os.remove(resim_yolu) #'deki mantık
        logger.info(f"Silindi: {resim_yolu}")
        
    def remove_from_thumb_cache(self, path: str):
        """Tek bir öğeyi thumbnail cache'ten kaldırır."""
        return self._thumb_cache.pop(path, None)
    
    def count_all_images_recursive_cached(self, folder_path):
        if folder_path in self._count_cache:
            return self._count_cache[folder_path]
        val = self.count_all_images_recursive(folder_path)
        self._count_cache[folder_path] = val
        return val

    def get_folder_size_cached(self, folder_path):
        if folder_path in self._size_cache:
            return self._size_cache[folder_path]
        val = self.get_folder_size(folder_path)
        self._size_cache[folder_path] = val
        return val

    def _format_size(self, n):
        try:
            for unit in ["B", "KB", "MB", "GB"]:
                if n < 1024.0:
                    return f"{n:.0f} {unit}" if unit == "B" else f"{n:.2f} {unit}"
                n /= 1024.0
        except Exception:
            pass
        return "-"

    def count_images(self, folder_path):
        """Bir klasördeki (sadece o klasör) resim sayısını döndür"""
        if not os.path.exists(folder_path):
            return 0
        
        count = 0
        try:
            for dosya in os.listdir(folder_path):
                dosya_yolu = os.path.join(folder_path, dosya)
                if os.path.isfile(dosya_yolu) and dosya.lower().endswith(IMAGE_EXTS):
                    count += 1
        except Exception as e:
            logger.error(f"Resim sayma hatası: {folder_path} - {e}")
        
        return count

    def count_all_images_recursive(self, folder_path):
        """Klasör ve TÜM alt klasörlerdeki resim sayısını döndür"""
        if not os.path.exists(folder_path):
            return 0
        
        total = 0
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(IMAGE_EXTS):
                        total += 1
        except Exception as e:
            logger.error(f"Recursive resim sayma hatası: {folder_path} - {e}")
        
        return total

    def get_folder_size(self, folder_path):
        """Klasörün toplam boyutunu byte cinsinden döndür"""
        total_size = 0
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"Klasör boyutu hesaplama hatası: {folder_path} - {e}")
        
        return total_size

    def get_last_modified(self, folder_path):
        """Klasörün son güncellenme tarihini formatlanmış döndür"""
        try:
            timestamp = os.path.getmtime(folder_path)
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%d.%m.%Y %H:%M")
        except:
            return "Bilinmiyor"

    def get_relative_path(self, folder_path):
        """Desktop'tan başlayan göreli yolu döndür"""
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            if folder_path.startswith(desktop_path):
                return os.path.relpath(folder_path, desktop_path)
            else:
                return folder_path
        except:
            return folder_path
    
    def is_image_file(self, path: str) -> bool:
        
        try:
            p = str(path).lower()
            if not p.endswith(IMAGE_EXTS):
                return False
            with Image.open(path) as im:
                im.verify()
            return True
        except Exception:
            return False
    
    def _has_subfolders(self, folder_path: str) -> bool:
        """
        Bir klasörün HİÇ alt klasörü olup olmadığını HIZLICA kontrol eder.
        (Bunu zaten eklemiştik, ama burada da kullanılacak. Eğer eklemediysen ekle.)
        """
        try:
            for item in os.listdir(folder_path):
                if os.path.isdir(os.path.join(folder_path, item)):
                    return True 
            return False 
        except Exception:
            return False 

    def search_folders_and_parents(self, search_text: str) -> list:
        """
        Diskte arama yapar ve eşleşen klasörleri + ebeveynlerini döndürür.
        """
        if not self.ana_klasor_yolu:
            return []

        # --- DÜZELTME 1: Ana yolu BİR KEZ normalleştir ---
        norm_ana_klasor_yolu = os.path.normpath(self.ana_klasor_yolu)

        search_text_lower = search_text.lower()
        results_map = {} 

        # --- DÜZELTME 2: Normalleştirilmiş yolu kullan ---
        for root, dirs, files in os.walk(norm_ana_klasor_yolu, topdown=True):
            relative_root = os.path.relpath(root, norm_ana_klasor_yolu)
            
            # Eğer '.' değilse (yani ana klasörün kendisi değilse)
            if relative_root != '.':
                depth = len(relative_root.split(os.sep))
                
                # Dediğin gibi: Sadece Ders (depth=1) ve Konu (depth=2)
                # seviyelerinin altındaki klasörleri (Test/Zorluk) arama.
                if depth >= 2:
                    dirs.clear() # os.walk'un daha derine inmesini engelle
                    continue     # Bu 'root'u atla, bir sonraki 'root'a geç
                
            for dir_name in dirs:
                if search_text_lower in dir_name.lower():
                    
                    current_path = os.path.join(root, dir_name)
                    has_children = self._has_subfolders(current_path)

                    # --- DÜZELTME 3: Normalleştirilmiş yola göre 'relative' al ---
                    relative_path = os.path.relpath(current_path, norm_ana_klasor_yolu)
                    
                    parts = relative_path.split(os.sep)
                    results_map[current_path] = {
                        'path': current_path,
                        'name': dir_name,
                        'has_children': has_children,
                        'parts': parts
                    }
                    
                    parent_path = root
                    
                    # --- DÜZELTME 4 (En önemlisi): Karşılaştırmayı normalleştir ---
                    while os.path.normpath(parent_path) != norm_ana_klasor_yolu:
                        if parent_path in results_map:
                            break 

                        parent_name = os.path.basename(parent_path)
                        
                        # --- DÜZELTME 5: Normalleştirilmiş yola göre 'relative' al ---
                        relative_path = os.path.relpath(parent_path, norm_ana_klasor_yolu)
                        
                        parts = relative_path.split(os.sep)
                        # --- EĞER . (dot) DÖNERSE ATLA ---
                        if parts == ['.']:
                            break
                            
                        results_map[parent_path] = {
                            'path': parent_path,
                            'name': parent_name,
                            'has_children': False,
                            'parts': parts
                        }
                        parent_path = os.path.dirname(parent_path)

        sorted_results = sorted(results_map.values(), key=lambda x: len(x['parts']))
        return sorted_results
    
    def get_sadece_alt_klasorler(self, folder_path: str) -> list:
        """
        Sadece BİR alt seviyedeki klasörleri getirir.
        YENİ: Artık (isim, tam_yol, alt_klasoru_var_mi) döndürür.
        """
        if not os.path.exists(folder_path):
            return []
        
        children = []
        try:
            for item in os.listdir(folder_path):
                child_path = os.path.join(folder_path, item)
                if os.path.isdir(child_path):
                    
                    # --- DEĞİŞİKLİK BURADA ---
                    # Bu yeni alt klasörün KENDİ alt klasörü var mı?
                    has_children = self._has_subfolders(child_path)
                    
                    # (İsim, Tam Yol, AltKlasoruVarMi) tuple'ı olarak ekliyoruz
                    children.append((item, child_path, has_children))
            
            # İsimlere göre alfabetik sırala
            children.sort(key=lambda x: x[0].lower())
            return children
        
        except PermissionError:
            logger.warning(f"Bu klasöre erişim izni yok: {folder_path}")
            return []
        except Exception as e:
            logger.error(f"Alt klasörler alınamadı: {folder_path} - {e}")
            return []