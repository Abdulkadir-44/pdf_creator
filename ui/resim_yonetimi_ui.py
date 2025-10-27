import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import os
import shutil
from PIL import Image, ImageTk
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Görsel sabitler
BG_COLOR = "#f2f2f2"
SCROLL_BG = "#e6e6e6"
BTN_BG = "#4a90e2"
BTN_FG = "#ffffff"
TREE_BG = "#ffffff"
SELECTED_BG = "#e3f2fd"

# Görsel doğrulama yardımcı fonksiyonu
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')

def is_image_file(path):
    """
    Sadece gerçek görüntü dosyaları True döndürür.
    Uzantı ve dosya içeriğini kontrol eder.
    """
    try:
        p = str(path).lower()
        if not p.endswith(IMAGE_EXTS):
            return False
        from PIL import Image
        with Image.open(path) as im:
            im.verify()  # Görsel açılabiliyor mu test et
        return True
    except Exception:
        return False


class ResimYonetimiPenceresi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG_COLOR)
        self.controller = controller
        self.ana_klasor_yolu = None
        self.current_images = []
        self.selected_folder = None
        self.tree_data = {}  # Ağaç veri yapısı
        self.expanded_folders = set()  # Açık olan klasörler
        self.folder_stats = {}  # Klasör istatistikleri
        self.search_text = ""  # Arama metni
        self.selected_images = []  # Seçilen resimler listesi
        self._thumb_cache = {}      # thumbnail cache
        self.search_timer = None  # Arama timer'ı
        self.search_results = []  # Arama sonuçları
        self._count_cache = {}
        self._size_cache = {}
        logger.info("ResimYonetimiPenceresi frame'i başlatılıyor")
        self.setup_ui()
    
    def setup_ui(self):
        """UI elementlerini oluştur"""
        self.btn_font = ctk.CTkFont(family="Segoe UI", size=11, weight="bold")

        # Başlık
        title_label = ctk.CTkLabel(
            self,
            text="🖼️ Resim Yönetimi",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#2d3436"
        )
        title_label.pack(pady=10)

        # Üst kontrol frame'i
        control_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        control_frame.pack(pady=10, fill="x", padx=20)

        # Ana menüye dön butonu
        ana_menu_btn = ctk.CTkButton(
            control_frame,
            text="🏠 Ana Menü",
            font=self.btn_font,
            fg_color=BTN_BG,
            text_color=BTN_FG,
            hover_color="#357ABD",
            width=150,
            height=35,
            command=self.ana_menuye_don
        )
        ana_menu_btn.pack(side="left", padx=10)

        # Klasör seç butonu
        klasor_btn = ctk.CTkButton(
            control_frame,
            text="📂 Ana Klasör Seç",
            font=self.btn_font,
            fg_color=BTN_BG,
            text_color=BTN_FG,
            hover_color="#357ABD",
            width=200,
            height=35,
            command=self.ana_klasoru_sec
        )
        klasor_btn.pack(side="left", padx=10)

        # Resim yükle butonu
        self.resim_yukle_btn = ctk.CTkButton(
            control_frame,
            text="🖼️ Resim Yükle",
            font=self.btn_font,
            fg_color="#6c757d",  # Başlangıçta gri
            text_color=BTN_FG,
            hover_color="#5a6268",
            width=150,
            height=35,
            command=self.resim_yukle,
            state="disabled"
        )
        self.resim_yukle_btn.pack(side="left", padx=10)

        # Ana içerik frame'i (2 sütunlu)
        content_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=2)
        content_frame.grid_rowconfigure(0, weight=1)

        # Sol panel - Klasör ağacı
        left_panel = ctk.CTkFrame(content_frame, fg_color=TREE_BG)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_panel.grid_rowconfigure(2, weight=3)  # Ağaç kısmı (3 birim)
        left_panel.grid_rowconfigure(3, weight=1)  # Detay kısmı (1 birim)

        # Klasör ağacı başlığı
        tree_title = ctk.CTkLabel(
            left_panel,
            text="📁 Klasör Hiyerarşisi",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#2d3436"
        )
        tree_title.pack(pady=10)

        # Arama ve filtreleme frame'i
        search_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        search_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Arama çubuğu ve loading indicator
        search_input_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_input_frame.pack(fill="x", pady=(0, 5))

        self.search_entry = ctk.CTkEntry(
            search_input_frame,
            placeholder_text="🔍 Klasör ara... (min 2 karakter)",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            height=30
        )
        self.search_entry.pack(side="left", fill="x", expand=True)
        self.search_entry.bind("<KeyRelease>", self.on_search_change)

        # Loading indicator
        self.search_loading_label = ctk.CTkLabel(
            search_input_frame,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            width=30
        )
        self.search_loading_label.pack(side="right", padx=(5, 0))

        # Treeview frame'i
        tree_frame = ctk.CTkFrame(left_panel, fg_color=TREE_BG)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Treeview oluştur
        self.tree_view = ttk.Treeview(
            tree_frame,
            show="tree",
            height=12
        )

        style = ttk.Style()
        style.configure("Treeview", 
                       background=TREE_BG,
                       foreground="#2d3436",
                       fieldbackground=TREE_BG,
                       borderwidth=0,
                       font=("Segoe UI", 10))

        style.configure("Treeview.Heading",
                       background="#e0e0e0",
                       foreground="#2d3436",
                       font=("Segoe UI", 10, "bold"))

        style.map("Treeview",
                 background=[('selected', SELECTED_BG)],
                 foreground=[('selected', '#2d3436')])

        self.tree_view.heading("#0", text="Klasör Adı", anchor="w")        
        self.tree_view.column("#0", width=250, minwidth=200)

        # Scrollbar ekle
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_view.yview)
        self.tree_view.configure(yscrollcommand=scrollbar.set)

        # Pack
        self.tree_view.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Selection event
        self.tree_view.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Detay paneli oluştur
        self.create_detail_panel(left_panel)

        # Sağ panel - Seçilen resimler görüntüleme
        right_panel = ctk.CTkFrame(content_frame, fg_color=SCROLL_BG)
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_rowconfigure(1, weight=1)

        # Resim paneli başlığı
        image_title = ctk.CTkLabel(
            right_panel,
            text="🖼️ Seçilen Resimler",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#2d3436"
        )
        image_title.pack(pady=10)

        # Seçilen resimler görüntüleme scroll frame'i
        self.selected_images_scroll = ctk.CTkScrollableFrame(right_panel, fg_color=SCROLL_BG)
        self.selected_images_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Başlangıç mesajı
        self.show_initial_message()
        logger.info("Resim yönetimi UI kurulumu tamamlandı")
    
    def _clear_caches(self):
        self._count_cache.clear()
        self._size_cache.clear()

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

    def _get_ctk_thumb(self, path, max_size=(180, 180)):
        """Path'ten CTkImage thumbnail üretir ve cache'ler."""
        try:
            if path in self._thumb_cache:
                return self._thumb_cache[path]
            img = Image.open(path)
            img.thumbnail(max_size, Image.LANCZOS)
            cimg = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self._thumb_cache[path] = cimg
            return cimg
        except Exception as e:
            logger.warning(f"Thumbnail üretilemedi: {path} -> {e}")
            return None

    def _open_preview(self, path):
        """Tam boyuta yakın önizleme (modal) — ortalanmış, 'popup' hissi, yeniden boyutlandırılamaz, kapat butonsuz."""
        try:
            # Üst pencere
            top = ctk.CTkToplevel(self)
            top.title(os.path.basename(path))
            top.transient(self.winfo_toplevel())
            top.grab_set()
            top.focus_set()
            top.resizable(False, False)          # Yeniden boyutlandırmayı kapat
            top.bind("<Escape>", lambda e: top.destroy())  # ESC ile kapat
    
            # Ekran boyutuna göre pencereyi 'pop-up' gibi daha küçük ayarla
            top.update_idletasks()
            sw = top.winfo_screenwidth()
            sh = top.winfo_screenheight()
    
            # Genişlik: ekranın %60'ı (min 720, max 1000)
            w = max(720, min(int(sw * 0.60), 1000))
            # Yükseklik: ekranın %55'i (min 420, max 640) -> üst/alt boşluk kalsın
            h = max(420, min(int(sh * 0.55), 640))
    
            # Konum: tam ortaya ama biraz yukarı kaydır
            x = max(0, (sw - w) // 2)
            y_center = (sh - h) // 2
            y = max(20, y_center - 40)  # "pop-up" hissi için biraz yukarı
            top.geometry(f"{w}x{h}+{x}+{y}")
    
            # Görseli pencereye sığdır (pencere kenar boşluklarını düş)
            img = Image.open(path)
            iw, ih = img.size
            max_w = w - 40                  # sağ/sol 20'şer px boşluk
            max_h = h - 120                 # üst/alt boşluk + dosya adı yüksekliği
            scale = min(max_w / iw, max_h / ih, 1.0)
            if scale < 1.0:
                img = img.resize((int(iw * scale), int(ih * scale)), Image.LANCZOS)
            cimg = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
    
            # İç çerçeve
            frame = ctk.CTkFrame(top, fg_color="transparent")
            frame.pack(fill="both", expand=True, padx=16, pady=16)
    
            # Ortalamak için grid
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)  # üst boşluk
            frame.grid_rowconfigure(1, weight=0)  # görsel
            frame.grid_rowconfigure(2, weight=0)  # dosya adı
            frame.grid_rowconfigure(3, weight=1)  # alt boşluk
    
            # Görsel (ortada)
            lbl = ctk.CTkLabel(frame, image=cimg, text="")
            lbl.image = cimg  # GC koruması
            lbl.grid(row=1, column=0, pady=(0, 10), sticky="n")
    
            # Dosya adı
            info = ctk.CTkLabel(
                frame,
                text=os.path.basename(path),
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#2d3436"
            )
            info.grid(row=2, column=0, sticky="n")
    
            # Not: Ayrı "Kapat" butonu yok; kullanıcı çarpı ile veya ESC ile kapatır.
        except Exception as e:
            logger.error(f"Önizleme açılamadı: {e}", exc_info=True)

    def on_tree_select(self, event):
        """Treeview'da klasör seçildiğinde - GÜNCELLENDİ"""
        selection = self.tree_view.selection()
        if not selection:
            return

        item_id = selection[0]
        folder_path = self.get_folder_path_from_item(item_id)

        if folder_path:
            # Seçimi kaydet
            self.selected_folder = folder_path

            # Detay panelini güncelle
            self.update_detail_panel(folder_path)

            # BUTON DURUMU: sadece Kolay/Orta/Zor için aktif
            self._update_upload_button_state()

            # Mevcut davranışını koru
            self.klasor_secildi(folder_path)

    def get_folder_path_from_item(self, item_id):
        """TreeView item ID'sinden klasör yolunu al"""
        # Item'ın text'ini al
        item_text = self.tree_view.item(item_id, "text")

        # İkonları temizle
        for icon in ["🎯", "📂", "📋", "⭐", "📁"]:
            item_text = item_text.replace(icon, "").strip()

        # Parent'ları takip ederek tam yolu bul
        parent_id = self.tree_view.parent(item_id)
        path_parts = [item_text]

        while parent_id:
            parent_text = self.tree_view.item(parent_id, "text")
            for icon in ["🎯", "📂", "📋", "⭐", "📁"]:
                parent_text = parent_text.replace(icon, "").strip()
            path_parts.insert(0, parent_text)
            parent_id = self.tree_view.parent(parent_id)

        # Ana klasör yolu ile birleştir
        if self.ana_klasor_yolu:
            full_path = os.path.join(self.ana_klasor_yolu, *path_parts)
            return full_path if os.path.exists(full_path) else None

        return None
            
    def show_initial_message(self):
        """Başlangıç mesajını göster"""
        logger.debug("Başlangıç mesajı gösteriliyor")
        message_label = ctk.CTkLabel(
            self.selected_images_scroll,
            text="🔍 Lütfen üstteki 'Ana Klasör Seç' butonuna tıklayarak\nsoru klasörünüzü seçin.\n\nResim yüklemek için 'Resim Yükle' butonunu kullanın.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#6c757d",
            justify="center"
        )
        message_label.pack(pady=50)

    def ana_klasoru_sec(self):
        """Ana klasörü seç ve klasör ağacını göster"""
        logger.info("Ana klasör seçme işlemi başlatıldı.")
        klasor_yolu = filedialog.askdirectory(title="Ana Soru Klasörünü Seçin")
        if klasor_yolu:
            logger.info(f"Klasör seçildi: {klasor_yolu}")
            self.ana_klasor_yolu = klasor_yolu

            # Tüm cache'leri temizle
            self._clear_caches()

            self.goster_klasor_agaci(klasor_yolu)
        else:
            logger.info("Klasör seçme işlemi kullanıcı tarafından iptal edildi.")
          
    def goster_klasor_agaci(self, ana_klasor):
        """Klasör ağacını göster"""
        logger.info(f"Klasör ağacı '{ana_klasor}' yolu için oluşturuluyor.")
        
        try:
            # Ağaç veri yapısını oluştur
            self.build_tree_structure(ana_klasor)
            self.calculate_folder_stats()
            
            # Ağaç yapısını göster
            self.display_tree()
            logger.info("Klasör ağacı başarıyla oluşturuldu.")
        except Exception as e:
            logger.error(f"Klasör ağacı oluşturulurken hata: {e}", exc_info=True)
            self.show_error_message("Klasör ağacı oluşturulurken hata oluştu.")

    def build_tree_structure(self, root_path):
        """Ağaç veri yapısını oluştur"""
        self.tree_data = {}
        self.expanded_folders.clear()
        
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

    def display_tree(self):
        """Treeview'ı populate et"""
        # Treeview'ı temizle
        for item in self.tree_view.get_children():
            self.tree_view.delete(item)

        search_text = self.search_entry.get().strip()

        # Arama modu
        if search_text and len(search_text) >= 2:
            self.populate_treeview_with_search()
        else:
            # Normal mod - Ana klasörleri göster
            self.populate_treeview_normal()

        # <<< EKLENDİ
        self._update_upload_button_state()

    def populate_treeview_normal(self):
        """Normal modda Treeview'ı populate et"""
        for folder_path, folder_info in self.tree_data.items():
            self.add_folder_to_treeview("", folder_path, folder_info)

    def populate_treeview_with_search(self):
        """Arama modunda Treeview'ı populate et"""
        if not self.search_results:
            return
        
        # Eşleşen klasörleri hiyerarşik olarak ekle
        parent_items = {}  # parent_path -> item_id mapping
        
        for result in self.search_results:
            folder_path = result['path']
            folder_info = result['info']
            match_type = result['match_type']
            parent_path = result['parent_path']
            
            # Parent ID'yi bul
            parent_id = ""
            if parent_path:
                # Parent path'i string olarak birleştir
                parent_key = "|".join(parent_path)
                parent_id = parent_items.get(parent_key, "")
            
            # Klasörü ekle
            item_id = self.add_folder_to_treeview(parent_id, folder_path, folder_info, match_type)
            
            # Bu item'ı parent olarak kaydet
            current_key = "|".join(parent_path + [folder_path])
            parent_items[current_key] = item_id

    def add_folder_to_treeview(self, parent_id, folder_path, folder_info, match_type="normal"):
        folder_name = folder_info['name']
        children = folder_info['children']

        # Başlığı (🎯 📁 📋 ⭐) koruyabilirsin; sadece status kaldırıldı
        if match_type in ['exact', 'partial']:
            display_name = f"🎯 {folder_name}"
        elif match_type == 'child':
            display_name = f"📁 {folder_name}"
        elif match_type == 'grandchild':
            display_name = f"📋 {folder_name}"
        elif match_type == 'great_grandchild':
            display_name = f"⭐ {folder_name}"
        else:
            display_name = f"📁 {folder_name}"

        level = self.get_folder_level(folder_path)
        modified_val = self.get_last_modified(folder_path) if level == "DERS" else ""

        item_id = self.tree_view.insert(
            parent_id, "end",
            text=display_name,
            
        )

        if not self.search_entry.get().strip() and children:
            for child_path, child_info in children.items():
                self.add_folder_to_treeview(item_id, child_path, child_info)

        return item_id

    def klasor_secildi(self, klasor_yolu):
        """Klasör seçildiğinde"""
        logger.info(f"Klasör seçildi: {klasor_yolu}")
        self.selected_folder = klasor_yolu
        
    def on_search_change(self, event):
        """Arama değiştiğinde filtrele (debounced)"""
        # Önceki timer'ı iptal et
        if self.search_timer:
            self.after_cancel(self.search_timer)
        
        # Loading göster
        self.search_loading_label.configure(text="⏳")
        
        # 300ms sonra arama yap
        self.search_timer = self.after(300, self.perform_search)

    def perform_search(self):
        """Gerçek arama işlemini yap"""
        search_text = self.search_entry.get().strip()
        
        # Loading'i temizle
        self.search_loading_label.configure(text="")
        
        # Minimum karakter kontrolü
        if len(search_text) < 2:
            if len(search_text) > 0:
                self.search_loading_label.configure(text="⚠️ Min 2 karakter")
            else:
                self.search_loading_label.configure(text="")
            self.search_results = []
            self.display_tree()
            return
        
        # Arama yap
        self.search_results = self.search_folders_recursive(search_text.lower())
        
        # Sonuçları göster
        self.display_tree()
        
        # Sonuç sayısını göster
        self.search_loading_label.configure(text="")

    def search_folders_recursive(self, search_text):
        """Hiyerarşik arama yap - eşleşen klasörün tüm alt yapısını göster"""
        matched_folders = []
        self.search_recursive_helper(search_text, self.tree_data, matched_folders, [])
        
        # Eşleşen klasörlerin alt yapısını da ekle
        enhanced_results = []
        for result in matched_folders:
            enhanced_results.append(result)
            # Bu klasörün alt klasörlerini de ekle
            self.add_children_to_results(result['path'], result['info'], enhanced_results)
        return enhanced_results

    def add_children_to_results(self, folder_path, folder_info, results):
        """Eşleşen klasörün alt klasörlerini sonuçlara ekle"""
        if not folder_info['children']:
            return
        
        # Alt klasörleri ekle
        for child_path, child_info in folder_info['children'].items():
            # Alt klasörü sonuçlara ekle
            results.append({
                'path': child_path,
                'info': child_info,
                'parent_path': [folder_path],
                'match_type': 'child'
            })
            
            # Bu alt klasörün de çocukları varsa onları da ekle
            if child_info['children']:
                for grandchild_path, grandchild_info in child_info['children'].items():
                    results.append({
                        'path': grandchild_path,
                        'info': grandchild_info,
                        'parent_path': [folder_path, child_path],
                        'match_type': 'grandchild'
                    })
                    
                    # Büyük torunları da ekle (test/yazılı altındaki kolay/orta/zor)
                    if grandchild_info['children']:
                        for great_grandchild_path, great_grandchild_info in grandchild_info['children'].items():
                            results.append({
                                'path': great_grandchild_path,
                                'info': great_grandchild_info,
                                'parent_path': [folder_path, child_path, grandchild_path],
                                'match_type': 'great_grandchild'
                            })

    def search_recursive_helper(self, search_text, folders, matched_folders, parent_path):
        """Recursive arama yardımcı fonksiyonu"""
        for folder_path, folder_info in folders.items():
            folder_name = folder_info['name']
            
            # Klasör adında arama yap
            if search_text in folder_name.lower():
                matched_folders.append({
                    'path': folder_path,
                    'info': folder_info,
                    'parent_path': parent_path.copy(),
                    'match_type': 'exact' if search_text == folder_name.lower() else 'partial'
                })
            
            # Alt klasörlerde de ara
            if folder_info['children']:
                new_parent_path = parent_path + [folder_path]
                self.search_recursive_helper(search_text, folder_info['children'], matched_folders, new_parent_path)

    def klasor_secildi(self, klasor_yolu):
        """Klasör seçildiğinde"""
        logger.info(f"Klasör seçildi: {klasor_yolu}")
        self.selected_folder = klasor_yolu

    def format_file_size(self, size_bytes):
        """Dosya boyutunu formatla"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def resim_yukle(self):
        """Yalnızca görsel dosyaları seçtir ve doğrula (kopyalama onayında yapılacak)."""
        # Sadece Kolay/Orta/Zor içinde izin ver
        if not self.selected_folder or os.path.basename(os.path.normpath(self.selected_folder)) not in {"Kolay", "Orta", "Zor"}:
            messagebox.showwarning("Uyarı", "Lütfen önce Kolay/Orta/Zor klasörlerinden birini seçin.")
            return

        logger.info("Resim seçimi başlatıldı.")

        # "Tüm Dosyalar" filtresini özellikle KALDIRDIK
        dosyalar = filedialog.askopenfilenames(
            title="Yüklenecek Resimleri Seçin",
            filetypes=[
                ("Resim Dosyaları", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.webp"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("WEBP", "*.webp"),
                ("GIF", "*.gif"),
                ("BMP", "*.bmp"),
                ("TIFF", "*.tiff"),
            ]
        )
        if not dosyalar:
            return

        logger.info(f"Seçilen dosya sayısı: {len(dosyalar)}")

        gecersizler = []
        for src in dosyalar:
            try:
                dosya_adi = os.path.basename(src)

                # SADECE GERÇEK GÖRSELLERİ KABUL ET
                if not is_image_file(src):
                    gecersizler.append(dosya_adi)
                    continue

                # Aynı isim zaten bekleyen listede varsa ekleme
                if any(dosya_adi == it[1] for it in self.selected_images):
                    continue

                # Bekleyen listeye ekle (henüz KOPYALAMA YAPMIYORUZ)
                self.selected_images.append((src, dosya_adi))
            except Exception as e:
                logger.error(f"Seçime eklenemedi: {src} - {e}", exc_info=True)

        # Kullanıcıya bilgi ver
        if gecersizler:
            try:
                msg = "Aşağıdaki dosyalar görüntü olmadığı için eklenmedi:\n\n- " + "\n- ".join(gecersizler[:10])
                if len(gecersizler) > 10:
                    msg += "\n\n(…)"
                messagebox.showwarning("Görsel Olmayan Dosyalar Atlandı", msg)
            except Exception:
                pass

        # Bekleyenleri göster (thumbnail'lar üretilecek)
        self.show_selected_images()
    
    def _on_remove_selected_image(self, index: int):
        """Bekleyen yüklemelerden birini kaldır (diskte değişiklik yok)"""
        try:
            if 0 <= index < len(self.selected_images):
                src_path, _ = self.selected_images[index]
                self.selected_images.pop(index)
                self._thumb_cache.pop(src_path, None)
                self.show_selected_images()
        except Exception as e:
            logger.error(f"Bekleyen öğe kaldırılamadı: {e}", exc_info=True)

    def commit_selected_images(self):
        """Bekleyen dosyaları seçili zorluk klasörüne kopyala (son kontrol dahil)."""
        try:
            if not self.selected_folder or os.path.basename(os.path.normpath(self.selected_folder)) not in {"Kolay", "Orta", "Zor"}:
                messagebox.showwarning("Uyarı", "Lütfen önce Kolay/Orta/Zor klasörlerinden birini seçin.")
                return

            if not self.selected_images:
                messagebox.showinfo("Bilgi", "Yüklenecek resim yok.")
                return

            if not messagebox.askyesno(
                "Onay",
                f"{len(self.selected_images)} dosyayı\n'{self.get_relative_path(self.selected_folder)}'\nklasörüne kopyalamak istiyor musunuz?"
            ):
                return

            kopyalanan = 0

            for src_path, dosya_adi in list(self.selected_images):
                try:
                    # Son güvenlik: Her ihtimale karşı gerçekten görsel mi?
                    if not is_image_file(src_path):
                        logger.warning(f"Görsel olmayan dosya kopyalamadan çıkarıldı: {dosya_adi}")
                        continue

                    hedef_yol = os.path.join(self.selected_folder, dosya_adi)

                    if os.path.exists(hedef_yol):
                        if not messagebox.askyesno("Dosya Mevcut", f"'{dosya_adi}' zaten var. Üzerine yazılsın mı?"):
                            continue

                    shutil.copy2(src_path, hedef_yol)
                    kopyalanan += 1

                except Exception as e:
                    logger.error(f"Kopyalama hatası: {src_path} -> {e}", exc_info=True)

            # Bekleyen listeyi ve cache'leri temizle
            self.selected_images.clear()
            self._thumb_cache.clear()
            self._clear_caches()

            self.show_selected_images()

            # İstatistikler ve ağaç görünümü yenilensin
            self.calculate_folder_stats()
            self.display_tree()

            messagebox.showinfo("Tamamlandı", f"{kopyalanan} dosya kopyalandı.")

        except Exception as e:
            logger.error(f"Yüklemeyi onaylama hatası: {e}", exc_info=True)
            messagebox.showerror("Hata", "Yükleme sırasında bir hata oluştu.")
     
    def clear_selected_images(self):
        """Bekleyen tüm dosyaları kaldır (diskte değişiklik yok)"""
        try:
            if not self.selected_images:
                return
            if not messagebox.askyesno("Onay", "Bekleyen tüm dosyalar kaldırılacak. Emin misiniz?"):
                return
            self.selected_images.clear()
            self.show_selected_images()
        except Exception as e:
            logger.error(f"Bekleyen liste temizlenemedi: {e}", exc_info=True)

    def show_selected_images(self):
        """Sağ panelde bekleyen yüklemeleri thumbnail'larla göster (henüz kopyalanmadı)."""
        try:
            container = getattr(self, "selected_images_scroll", None)
            if container is None or not container.winfo_exists():
                container = getattr(self, "detail_scroll", self)

            # Temizle
            for w in container.winfo_children():
                w.destroy()

            # Başlık
            ctk.CTkLabel(
                container,
                text="Bekleyen Yüklemeler (Önizleme)",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                text_color="#2d3436"
            ).pack(anchor="w", pady=(0, 6), padx=2)

            if not self.selected_images:
                ctk.CTkLabel(
                    container,
                    text="Seçilmiş resim yok.",
                    font=ctk.CTkFont(family="Segoe UI", size=10),
                    text_color="#6c757d"
                ).pack(anchor="w", padx=2)
                return

            # Grid düzeni: 3 sütun
            cards_frame = ctk.CTkFrame(container, fg_color="transparent")
            cards_frame.pack(fill="x", padx=2, pady=(2, 8))

            cols = 3
            for i in range(cols):
                cards_frame.grid_columnconfigure(i, weight=1)

            for idx, (src_path, dosya_adi) in enumerate(self.selected_images):
                col = idx % cols
                row = idx // cols

                card = ctk.CTkFrame(cards_frame, corner_radius=8)
                card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)

                # Thumbnail
                thumb = self._get_ctk_thumb(src_path, max_size=(180, 180))
                if thumb is not None:
                    img_lbl = ctk.CTkLabel(card, image=thumb, text="")
                    img_lbl.image = thumb  # GC koruması
                else:
                    img_lbl = ctk.CTkLabel(
                        card,
                        text="(Önizleme yok)",
                        font=ctk.CTkFont(size=10),
                        text_color="#6c757d"
                    )
                img_lbl.pack(padx=10, pady=(10, 6))

                # Ad + boyut
                try:
                    size_text = self._format_size(os.path.getsize(src_path))
                except Exception:
                    size_text = "-"
                meta_lbl = ctk.CTkLabel(
                    card,
                    text=f"{dosya_adi}\n{size_text}",
                    font=ctk.CTkFont(family="Segoe UI", size=9),
                    text_color="#2d3436",
                    justify="center"
                )
                meta_lbl.pack(padx=8, pady=(0, 8))

                # Butonlar
                btn_row = ctk.CTkFrame(card, fg_color="transparent")
                btn_row.pack(pady=(0, 10))

                ctk.CTkButton(
                    btn_row, text="Önizle",
                    width=90,
                    command=lambda p=src_path: self._open_preview(p)
                ).pack(side="left", padx=(0, 6))

                ctk.CTkButton(
                    btn_row, text="Kaldır",
                    width=90, fg_color="#dc3545",
                    command=lambda i=idx: self._on_remove_selected_image(i)
                ).pack(side="left")

            # Alt aksiyonlar: Onayla / Temizle
            btns = ctk.CTkFrame(container, fg_color="transparent")
            btns.pack(fill="x", pady=(8, 0))

            ctk.CTkButton(
                btns, text="Yüklemeyi Onayla",
                command=self.commit_selected_images
            ).pack(side="left", padx=(0, 8))

            ctk.CTkButton(
                btns, text="Listeyi Temizle",
                fg_color="#6c757d",
                command=self.clear_selected_images
            ).pack(side="left")

        except Exception as e:
            logger.error(f"Seçili resimleri göstermek başarısız: {e}", exc_info=True)

    def create_selected_image_widget(self, resim_yolu, dosya_adi, index):
        """Seçilen resim widget'ı oluştur"""
        try:
            # Resim frame'i
            image_frame = ctk.CTkFrame(self.selected_images_scroll, fg_color="white")
            
            # Grid pozisyonu hesapla (3 sütunlu grid)
            row = index // 3
            col = index % 3
            image_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Grid ağırlık ayarları
            self.selected_images_scroll.grid_columnconfigure(col, weight=1)

            # Resmi yükle ve boyutlandır
            pil_image = Image.open(resim_yolu)
            # Daha büyük thumbnail boyutu
            pil_image.thumbnail((200, 200), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(pil_image)

            # Resim label'ı
            image_label = ctk.CTkLabel(
                image_frame,
                image=photo,
                text=""
            )
            image_label.image = photo  # Referansı sakla
            image_label.pack(pady=10)

            # Dosya adı
            name_label = ctk.CTkLabel(
                image_frame,
                text=dosya_adi,
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color="#2d3436",
                wraplength=180
            )
            name_label.pack(pady=(0, 5))

            # Sil butonu
            delete_btn = ctk.CTkButton(
                image_frame,
                text="🗑️ Kaldır",
                font=ctk.CTkFont(family="Segoe UI", size=10),
                fg_color="#dc3545",
                text_color="white",
                hover_color="#c82333",
                width=80,
                height=25,
                command=lambda path=resim_yolu, name=dosya_adi, idx=index: self.remove_selected_image(path, name, idx)
            )
            delete_btn.pack(pady=(0, 10))

        except Exception as e:
            logger.error(f"Seçilen resim widget'ı oluşturulurken hata: {e}", exc_info=True)

    def remove_selected_image(self, resim_yolu, dosya_adi, index):
        """Seçilen resimden kaldır"""
        if messagebox.askyesno("Onay", f"'{dosya_adi}' resmini seçilenlerden kaldırmak istediğinizden emin misiniz?"):
            try:
                # Listedeki resmi kaldır
                self.selected_images.pop(index)
                # Görüntüyü yenile
                self.show_selected_images()
                logger.info(f"Resim seçilenlerden kaldırıldı: {dosya_adi}")
            except Exception as e:
                logger.error(f"Resim kaldırılırken hata: {e}", exc_info=True)
                messagebox.showerror("Hata", "Resim kaldırılırken hata oluştu.")

    def show_no_selected_images_message(self):
        """Seçilen resim bulunamadı mesajı göster"""
        logger.info("Kullanıcıya seçilen resim bulunamadı mesajı gösteriliyor.")
        message_label = ctk.CTkLabel(
            self.selected_images_scroll,
            text="🔍 Henüz resim seçilmedi.\n\nResim yüklemek için 'Resim Yükle' butonunu kullanın.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#6c757d",
            justify="center"
        )
        message_label.pack(pady=50)

    def resim_sil(self, resim_yolu, dosya_adi):
        """Resim sil"""
        if messagebox.askyesno("Onay", f"'{dosya_adi}' dosyasını silmek istediğinizden emin misiniz?"):
            try:
                os.remove(resim_yolu)
                logger.info(f"Resim silindi: {dosya_adi}")
                
                # Seçilen resimler listesinden de kaldır
                self.selected_images = [(path, name) for path, name in self.selected_images if path != resim_yolu]
                
                # Seçilen resimleri yeniden göster
                self.show_selected_images()
                
                # Klasör istatistiklerini güncelle
                self.calculate_folder_stats()
                self.display_tree()
                
                messagebox.showinfo("Başarılı", "Resim başarıyla silindi.")
            except Exception as e:
                logger.error(f"Resim silinirken hata: {e}", exc_info=True)
                messagebox.showerror("Hata", "Resim silinirken hata oluştu.")

    def show_error_message(self, message):
        """Hata mesajı göster"""
        logger.warning(f"Kullanıcıya hata mesajı gösteriliyor: {message}")
        messagebox.showerror("Hata", message)

    def ana_menuye_don(self):
        """Ana menüye dön"""
        logger.info("Ana menüye dönme komutu verildi.")
        self.controller.ana_menuye_don()
    
    def count_images(self, folder_path):
        """Bir klasördeki (sadece o klasör) resim sayısını döndür"""
        if not os.path.exists(folder_path):
            return 0
        
        resim_uzantilari = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')
        count = 0
        
        try:
            for dosya in os.listdir(folder_path):
                dosya_yolu = os.path.join(folder_path, dosya)
                if os.path.isfile(dosya_yolu) and dosya.lower().endswith(resim_uzantilari):
                    count += 1
        except Exception as e:
            logger.error(f"Resim sayma hatası: {folder_path} - {e}")
        
        return count

    def count_all_images_recursive(self, folder_path):
        """Klasör ve TÜM alt klasörlerdeki resim sayısını döndür"""
        if not os.path.exists(folder_path):
            return 0
        
        total = 0
        resim_uzantilari = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')
        
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(resim_uzantilari):
                        total += 1
        except Exception as e:
            logger.error(f"Recursive resim sayma hatası: {folder_path} - {e}")
        
        return total

    def get_folder_level(self, folder_path):
        """Klasörün hangi seviyede olduğunu belirle"""
        if not self.ana_klasor_yolu:
            return "UNKNOWN"
        
        try:
            relative = os.path.relpath(folder_path, self.ana_klasor_yolu)
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
            from datetime import datetime
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
      
    def is_zorluk_folder(self, folder_path: str) -> bool:
        """Seçilen klasör Kolay/Orta/Zor seviyelerinden biri mi?"""
        if not folder_path:
            return False
        last = os.path.basename(os.path.normpath(folder_path))
        return last in {"Kolay", "Orta", "Zor"}

    def _update_upload_button_state(self):
        """Resim Yükle butonunu sadece Kolay/Orta/Zor seçiliyken aktif et"""
        is_zorluk = False
        if self.selected_folder:
            last = os.path.basename(os.path.normpath(self.selected_folder))
            is_zorluk = last in {"Kolay", "Orta", "Zor"}

        # aktif/pasif + renk
        self.resim_yukle_btn.configure(
            state=("normal" if is_zorluk else "disabled"),
            fg_color=("#28a745" if is_zorluk else "#6c757d")
        )
        
    def get_ders_status(self, folder_path):
        """DERS seviyesi durum ikonu"""
        total_images = self.count_all_images_recursive(folder_path)
        
        if total_images == 0:
            return "❌"  # Hiç resim yok
        
        # Alt konuları kontrol et
        try:
            konular = [d for d in os.listdir(folder_path) 
                      if os.path.isdir(os.path.join(folder_path, d))]
            
            for konu in konular:
                konu_path = os.path.join(folder_path, konu)
                konu_images = self.count_all_images_recursive(konu_path)
                if konu_images == 0:
                    return "⚠️"  # En az bir konu boş
            
            return "✅"  # Her konu dolu
        except:
            return "⚠️"

    def get_konu_status(self, folder_path):
        """KONU seviyesi durum ikonu"""
        test_path = os.path.join(folder_path, "Test")
        yazili_path = os.path.join(folder_path, "Yazılı")
        
        test_images = self.count_all_images_recursive(test_path) if os.path.exists(test_path) else 0
        yazili_images = self.count_all_images_recursive(yazili_path) if os.path.exists(yazili_path) else 0
        
        if test_images == 0 and yazili_images == 0:
            return "❌"  # Hiç resim yok
        
        # Test veya Yazılı boşsa
        if test_images == 0 or yazili_images == 0:
            return "⚠️"
        
        # Her ikisi de var, zorluk seviyelerini kontrol et
        test_status = self.get_tur_status(test_path)
        yazili_status = self.get_tur_status(yazili_path)
        
        if test_status == "✅" and yazili_status == "✅":
            return "✅"
        else:
            return "⚠️"

    def get_tur_status(self, folder_path):
        """TÜR seviyesi (Test/Yazılı) durum ikonu"""
        zorluklar = ["Kolay", "Orta", "Zor"]
        dolu_sayisi = 0
        
        for zorluk in zorluklar:
            zorluk_path = os.path.join(folder_path, zorluk)
            if os.path.exists(zorluk_path):
                image_count = self.count_images(zorluk_path)
                if image_count > 0:
                    dolu_sayisi += 1
        
        if dolu_sayisi == 0:
            return "❌"  # Hiç resim yok
        elif dolu_sayisi == 3:
            return "✅"  # Hepsi dolu
        else:
            return "⚠️"  # Bazıları boş

    def get_zorluk_status(self, folder_path):
        """ZORLUK seviyesi durum ikonu"""
        image_count = self.count_images(folder_path)
        return "✅" if image_count > 0 else "❌"

    def create_detail_panel(self, parent):
        """Seçili klasör detay panelini oluştur"""
        # Detay frame'i
        detail_frame = ctk.CTkFrame(parent, fg_color="#f8f9fa", corner_radius=10)
        detail_frame.pack(fill="x", padx=10, pady=10)
        detail_frame.pack_propagate(False)
        detail_frame.grid_columnconfigure(0, weight=1)
        detail_frame.grid_rowconfigure(1, weight=1)
        
        # Başlık
        title_label = ctk.CTkLabel(
            detail_frame,
            text="📊 SEÇİLİ KLASÖR DETAYLARI",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#2d3436"
        )
        title_label.grid(row=0, column=0, pady=(10, 5), sticky="w", padx=10)
        
        # Detay scrollable frame
        self.detail_scroll = ctk.CTkScrollableFrame(
            detail_frame,
            fg_color="transparent",
            height=150
        )
        self.detail_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Başlangıç mesajı
        self.show_detail_initial_message()

    def show_detail_initial_message(self):
        """Detay paneli başlangıç mesajı"""
        for widget in self.detail_scroll.winfo_children():
            widget.destroy()
        
        message = ctk.CTkLabel(
            self.detail_scroll,
            text="📂 Detayları görmek için\nbir klasör seçin",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#6c757d",
            justify="center"
        )
        message.pack(pady=20)

    def update_detail_panel(self, folder_path):
        """Seçili klasörün detaylarını göster"""
        # Temizle
        for widget in self.detail_scroll.winfo_children():
            widget.destroy()
        
        # Seviyeyi belirle
        level = self.get_folder_level(folder_path)
        
        # Seviyeye göre detayları göster
        if level == "DERS":
            self.show_ders_details(folder_path)
        elif level == "KONU":
            self.show_konu_details(folder_path)
        elif level == "TUR":
            self.show_tur_details(folder_path)
        elif level == "ZORLUK":
            self.show_zorluk_details(folder_path)
        else:
            self.show_detail_initial_message()

    def create_detail_row(self, icon, label, value, text_color="#2d3436"):
        """Detay satırı oluştur"""
        row_frame = ctk.CTkFrame(self.detail_scroll, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)

        # ✅ Label - DAHA BÜYÜK
        label_text = ctk.CTkLabel(
            row_frame,
            text=f"{icon} {label}:",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),  # ← 10'dan 11'e
            text_color="#6c757d",
            anchor="w",
            width=120
        )
        label_text.pack(side="left", padx=(0, 5))

        # ✅ Value - DAHA BÜYÜK
        value_text = ctk.CTkLabel(
            row_frame,
            text=str(value),
            font=ctk.CTkFont(family="Segoe UI", size=11),  # ← 10'dan 11'e
            text_color=text_color,
            anchor="w"
        )
        value_text.pack(side="left", fill="x", expand=True)
    
    def show_ders_details(self, folder_path):
        """Ders seviyesi detayları"""
        ders_adi = os.path.basename(folder_path)

        # Başlık
        title = ctk.CTkLabel(
            self.detail_scroll,
            text=f"📚 DERS: {ders_adi}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#2d3436"
        )
        title.pack(pady=(5, 10))

        # Yol
        relative_path = self.get_relative_path(folder_path)
        self.create_detail_row("📍", "Yol", relative_path)

        # Ayırıcı
        ctk.CTkLabel(
            self.detail_scroll,
            text="─" * 40,
            text_color="#e0e0e0",
            font=ctk.CTkFont(size=8)
        ).pack(pady=5)

        # İstatistikler
        try:
            konular = [
                d for d in os.listdir(folder_path)
                if os.path.isdir(os.path.join(folder_path, d))
            ]

            total_images = self.count_all_images_recursive_cached(folder_path)
            total_size = self.get_folder_size_cached(folder_path)
            last_modified = self.get_last_modified(folder_path)

            self.create_detail_row("📂", "Toplam Konu", len(konular))
            self.create_detail_row("📷", "Toplam Resim", total_images)
            self.create_detail_row("💾", "Toplam Boyut", self.format_file_size(total_size))
            self.create_detail_row("📅", "Son Güncelleme", last_modified)

            # Ayırıcı
            ctk.CTkLabel(
                self.detail_scroll,
                text="─" * 40,
                text_color="#e0e0e0",
                font=ctk.CTkFont(size=8)
            ).pack(pady=5)

            # Konu dağılımı
            ctk.CTkLabel(
                self.detail_scroll,
                text="📋 Konu Dağılımı:",
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                text_color="#2d3436"
            ).pack(anchor="w", pady=(5, 5))

            for konu in sorted(konular):
                konu_path = os.path.join(folder_path, konu)
                konu_images = self.count_all_images_recursive_cached(konu_path)
                self.create_detail_row("📁", konu, f"{konu_images} resim", text_color="#2d3436")

        except Exception as e:
            logger.error(f"Ders detayları gösterme hatası: {e}")
        
    def show_konu_details(self, folder_path):
        """Konu seviyesi detayları"""
        konu_adi = os.path.basename(folder_path)
        ders_adi = os.path.basename(os.path.dirname(folder_path))

        # Başlık
        title = ctk.CTkLabel(
            self.detail_scroll,
            text=f"📖 KONU: {konu_adi}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#2d3436"
        )
        title.pack(pady=(5, 5))

        subtitle = ctk.CTkLabel(
            self.detail_scroll,
            text=f"📚 Ders: {ders_adi}",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color="#6c757d"
        )
        subtitle.pack(pady=(0, 10))

        # Yol
        relative_path = self.get_relative_path(folder_path)
        self.create_detail_row("📍", "Yol", relative_path)

        # Ayırıcı
        ctk.CTkLabel(
            self.detail_scroll,
            text="─" * 40,
            text_color="#e0e0e0",
            font=ctk.CTkFont(size=8)
        ).pack(pady=5)

        # İstatistikler
        try:
            total_images = self.count_all_images_recursive_cached(folder_path)
            total_size = self.get_folder_size_cached(folder_path)
            last_modified = self.get_last_modified(folder_path)

            self.create_detail_row("📷", "Toplam Resim", total_images)
            self.create_detail_row("💾", "Toplam Boyut", self.format_file_size(total_size))
            self.create_detail_row("📅", "Son Güncelleme", last_modified)

            # Ayırıcı
            ctk.CTkLabel(
                self.detail_scroll,
                text="─" * 40,
                text_color="#e0e0e0",
                font=ctk.CTkFont(size=8)
            ).pack(pady=5)

            # Test/Yazılı dağılımı
            ctk.CTkLabel(
                self.detail_scroll,
                text="📋 Test/Yazılı Dağılımı:",
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                text_color="#2d3436"
            ).pack(anchor="w", pady=(5, 5))

            for tur in ["Test", "Yazılı"]:
                tur_path = os.path.join(folder_path, tur)
                if os.path.exists(tur_path):
                    # Tür başlığı
                    ctk.CTkLabel(
                        self.detail_scroll,
                        text=f"  📁 {tur}:",
                        font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                        text_color="#2d3436"
                    ).pack(anchor="w", pady=(5, 2))

                    # Zorluk seviyeleri
                    for zorluk in ["Kolay", "Orta", "Zor"]:
                        zorluk_path = os.path.join(tur_path, zorluk)
                        if os.path.exists(zorluk_path):
                            zorluk_images = self.count_images(zorluk_path)
                            status = "✅" if zorluk_images > 0 else "❌"
                            color = "#28a745" if status == "✅" else "#dc3545"

                            ctk.CTkLabel(
                                self.detail_scroll,
                                text=f"    {status} {zorluk}: {zorluk_images} resim",
                                font=ctk.CTkFont(family="Segoe UI", size=9),
                                text_color=color,
                                anchor="w"
                            ).pack(anchor="w", pady=1)

        except Exception as e:
            logger.error(f"Konu detayları alınırken hata: {e}")

    def show_tur_details(self, folder_path):
        """Tür (Test/Yazılı) seviyesi detayları"""
        tur_adi = os.path.basename(folder_path)
        konu_adi = os.path.basename(os.path.dirname(folder_path))

        # Başlık
        title = ctk.CTkLabel(
            self.detail_scroll,
            text=f"📁 TÜR: {tur_adi}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#2d3436"
        )
        title.pack(pady=(5, 5))

        subtitle = ctk.CTkLabel(
            self.detail_scroll,
            text=f"📖 Konu: {konu_adi}",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color="#6c757d"
        )
        subtitle.pack(pady=(0, 10))

        # Yol
        relative_path = self.get_relative_path(folder_path)
        self.create_detail_row("📍", "Yol", relative_path)

        # Ayırıcı
        ctk.CTkLabel(
            self.detail_scroll,
            text="─" * 40,
            text_color="#e0e0e0",
            font=ctk.CTkFont(size=8)
        ).pack(pady=5)

        # İstatistikler
        try:
            total_images = self.count_all_images_recursive_cached(folder_path)
            total_size = self.get_folder_size_cached(folder_path)
            last_modified = self.get_last_modified(folder_path)

            self.create_detail_row("📷", "Toplam Resim", total_images)
            self.create_detail_row("💾", "Toplam Boyut", self.format_file_size(total_size))
            self.create_detail_row("📅", "Son Güncelleme", last_modified)

            # Ayırıcı
            ctk.CTkLabel(
                self.detail_scroll,
                text="─" * 40,
                text_color="#e0e0e0",
                font=ctk.CTkFont(size=8)
            ).pack(pady=5)

            # Zorluk dağılımı
            ctk.CTkLabel(
                self.detail_scroll,
                text="📊 Zorluk Dağılımı:",
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                text_color="#2d3436"
            ).pack(anchor="w", pady=(5, 5))

            bos_seviyeler = []
            for zorluk in ["Kolay", "Orta", "Zor"]:
                zorluk_path = os.path.join(folder_path, zorluk)
                if os.path.exists(zorluk_path):
                    zorluk_images = self.count_images(zorluk_path)
                    zorluk_size = self.get_folder_size_cached(zorluk_path)
                    status = "✅" if zorluk_images > 0 else "❌"

                    if zorluk_images == 0:
                        bos_seviyeler.append(zorluk)

                    color = "#28a745" if status == "✅" else "#dc3545"
                    self.create_detail_row(
                        status,
                        zorluk,
                        f"{zorluk_images} resim ({self.format_file_size(zorluk_size)})",
                        text_color=color
                    )

            # Eksik uyarısı
            if bos_seviyeler:
                ctk.CTkLabel(
                    self.detail_scroll,
                    text="─" * 40,
                    text_color="#e0e0e0",
                    font=ctk.CTkFont(size=8)
                ).pack(pady=5)

                warning_frame = ctk.CTkFrame(self.detail_scroll, fg_color="#fff3cd", corner_radius=5)
                warning_frame.pack(fill="x", pady=5, padx=5)

                warning_text = f"💡 Öneri: {', '.join(bos_seviyeler)} seviye{'sine' if len(bos_seviyeler) == 1 else 'lerine'} resim ekleyin"
                ctk.CTkLabel(
                    warning_frame,
                    text=warning_text,
                    font=ctk.CTkFont(family="Segoe UI", size=9),
                    text_color="#856404",
                    wraplength=300
                ).pack(pady=5, padx=5)

        except Exception as e:
            logger.error(f"Tür detayları gösterme hatası: {e}")
        
    def show_zorluk_details(self, folder_path):
        """Zorluk seviyesi detayları (Kolay/Orta/Zor)"""
        zorluk_adi = os.path.basename(folder_path)

        # Başlık
        title = ctk.CTkLabel(
            self.detail_scroll,
            text=f"⭐ ZORLUK: {zorluk_adi}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#2d3436"
        )
        title.pack(pady=(5, 10))

        # Yol
        relative_path = self.get_relative_path(folder_path)
        self.create_detail_row("📍", "Yol", relative_path)

        # Ayırıcı
        ctk.CTkLabel(
            self.detail_scroll,
            text="─" * 40,
            text_color="#e0e0e0",
            font=ctk.CTkFont(size=8)
        ).pack(pady=5)

        try:
            total_images = self.count_images(folder_path)
            total_size = self.get_folder_size_cached(folder_path)
            last_modified = self.get_last_modified(folder_path)

            self.create_detail_row("📷", "Toplam Resim", total_images)
            self.create_detail_row("💾", "Toplam Boyut", self.format_file_size(total_size))
            self.create_detail_row("📅", "Son Güncelleme", last_modified)

        except Exception as e:
            logger.error(f"Zorluk detayları gösterme hatası: {e}")
        
