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
        self.tree_data = {}  # Ağaç veri yapısı
        self.folder_stats = {}  # Klasör istatistikleri
        self._thumb_cache = {} # PIL Thumbnail cache (PIL.Image nesneleri tutar)
        # self._thumb_cache = {} # (Bu daha sonra taşınacak)


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
        
    def build_tree_structure(self, root_path):
        """Ağaç veri yapısını oluştur"""
        self.tree_data = {}
        
        try:
            items = os.listdir(root_path)
            folders = [item for item in items if os.path.isdir(os.path.join(root_path, item))]
            
            for folder in sorted(folders):
                folder_path = os.path.join(root_path, folder)
                self.tree_data[folder_path] = {
                    'name': folder,
                    'path': folder_path,
                    'children': self.get_children(folder_path),
                    'level': 0,
                    'parent': None
                }
                
        except PermissionError:
            logger.warning(f"Klasöre erişim izni yok: {root_path}")
        except Exception as e:
            logger.error(f"Ağaç yapısı oluşturma hatası: {e}", exc_info=True)

    def get_children(self, folder_path, level=1):
        """Klasörün alt klasörlerini al"""
        children = {}
        try:
            items = os.listdir(folder_path)
            folders = [item for item in items if os.path.isdir(os.path.join(folder_path, item))]
            
            for folder in sorted(folders):
                child_path = os.path.join(folder_path, folder)
                children[child_path] = {
                    'name': folder,
                    'path': child_path,
                    'children': self.get_children(child_path, level + 1),
                    'level': level,
                    'parent': folder_path
                }
                
        except PermissionError:
            logger.warning(f"Klasöre erişim izni yok: {folder_path}")
        except Exception as e:
            logger.error(f"Alt klasör alma hatası: {e}", exc_info=True)
            
        return children

    def calculate_folder_stats(self):
        """Klasör istatistiklerini hesapla"""
        logger.info("Klasör istatistikleri hesaplanıyor...")
        self.folder_stats = {}
        
        # Tüm klasörleri recursive olarak işle
        self.calculate_stats_recursive(self.tree_data)
        
    def calculate_stats_recursive(self, folders):
        """Klasör istatistiklerini recursive olarak hesapla"""
        for folder_path, folder_info in folders.items():
            try:
                # Resim dosyalarını say
                resim_uzantilari = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')
                resim_sayisi = 0
                toplam_boyut = 0
                
                for dosya in os.listdir(folder_path):
                    if dosya.lower().endswith(resim_uzantilari):
                        resim_sayisi += 1
                        try:
                            toplam_boyut += os.path.getsize(os.path.join(folder_path, dosya))
                        except:
                            pass
                
                self.folder_stats[folder_path] = {
                    'resim_sayisi': resim_sayisi,
                    'toplam_boyut': toplam_boyut
                }
                
                # Alt klasörleri de işle
                if folder_info['children']:
                    self.calculate_stats_recursive(folder_info['children'])
                
            except Exception as e:
                logger.warning(f"Klasör istatistiği hesaplanamadı: {folder_path} - {e}")
                self.folder_stats[folder_path] = {'resim_sayisi': 0, 'toplam_boyut': 0}
