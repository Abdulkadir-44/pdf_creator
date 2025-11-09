import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import os
import shutil
from PIL import Image, ImageTk
import logging
import json
import threading
from datetime import datetime, timedelta
from logic.resim_yonetimi_beyni import ResimYonetimiBeyni

logger = logging.getLogger(__name__)

# Görsel sabitler
BG_COLOR = "#f2f2f2"
SCROLL_BG = "#e6e6e6"
BTN_BG = "#4a90e2"
BTN_FG = "#ffffff"
TREE_BG = "#ffffff"
SELECTED_BG = "#e3f2fd"



class ResimYonetimiPenceresi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG_COLOR)
        self.controller = controller
        self.beyin = ResimYonetimiBeyni()
        self.ana_klasor_yolu = None
        self.current_images = []
        self.selected_folder = None
        self.expanded_folders = set()  # Açık olan klasörler
        self.search_text = ""  # Arama metni
        self.selected_images = []  # Seçilen resimler listesi
        self.search_timer = None  # Arama timer'ı
        self.search_results = []  # Arama sonuçları

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
        
        #(TEMBEL YÜKLEME İÇİN) ---
        self.tree_view.bind("<<TreeviewOpen>>", self.on_folder_expand)

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
    
    def _get_ctk_thumb(self, path, max_size=(180, 180)):
        """
        Beyin'den PIL thumbnail alır ve onu CTkImage'a dönüştürür.
        Artık PIL veya Cache işi yapmaz.
        """
        try:
            # 1. PIL resmini Beyin'den iste
            pil_img = self.beyin.get_pil_thumbnail(path, max_size)
            
            if pil_img:
                # 2. CTkImage'a dönüştür ve döndür (importlar zaten var)
                return ctk.CTkImage(light_image=pil_img, 
                                    dark_image=pil_img, 
                                    size=pil_img.size)
            else:
                return None # Beyin üretemedi
        except Exception as e:
            logger.warning(f"CTkImage thumbnail'a dönüştürülemedi: {path} -> {e}")
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

    def on_folder_expand(self, event):
        """Kullanıcı bir klasörün [+] simgesine bastığında tetiklenir."""
        
        # 1. Hangi öğenin açıldığını al
        item_id = self.tree_view.focus() # 'focus()' hangi öğenin + simgesine basıldığını verir
        
        # 2. Bu öğenin altındaki ilk çocuğu bul (bizim "Yükleniyor..." satırımız)
        children = self.tree_view.get_children(item_id)
        if not children:
            return # Zaten alt öğesi yoksa (ya da çoktan yüklendiyse) bırak

        first_child_id = children[0]
        
        # 3. Bu ilk çocuğun "Yükleniyor..." satırı olup olmadığını kontrol et
        if self.tree_view.item(first_child_id, "text") == "Yükleniyor...":
            
            # 4. "Yükleniyor..." satırını SİL
            self.tree_view.delete(first_child_id)
            
            # 5. Asıl klasörün yolunu al (yeni hızlı fonksiyonumuzla)
            folder_path = self.get_folder_path_from_item(item_id)
            if not folder_path:
                return

            # 6. "Beyin"den SADECE BİR alt seviyeyi iste (Tembel Yükleme)
            yeni_alt_klasorler = self.beyin.get_sadece_alt_klasorler(folder_path)
            
            # 7. Gelen yeni klasörleri ağaca ekle
            for (klasor_adi, tam_yol, has_children) in yeni_alt_klasorler:
                self.add_folder_to_treeview(
                    parent_id=item_id,
                    folder_path=tam_yol,
                    folder_name=klasor_adi,
                    has_children=has_children 
                )
                
    def get_folder_path_from_item(self, item_id):
        """
        TreeView item ID'sinden klasör yolunu alır. (Hızlı versiyon)
        Artık 'values' içinde saklanan yolu doğrudan okur.
        """
        try:
            # 'values' listesinin ilk elemanında tam yolu saklamıştık
            values = self.tree_view.item(item_id, "values")
            if values:
                return str(values[0])
            else:
                # Eğer 'values' yoksa (belki "Yükleniyor..." satırıdır)
                return None
        except Exception:
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

            self.beyin.set_ana_klasor(klasor_yolu)
            self.expanded_folders.clear()

            self.goster_klasor_agaci(klasor_yolu)
        else:
            logger.info("Klasör seçme işlemi kullanıcı tarafından iptal edildi.")
          
    def goster_klasor_agaci(self, ana_klasor):
        """Klasör ağacının ilk seviyesini göstermek için display_tree'yi tetikler."""
        logger.info(f"Tembel Yükleme: '{ana_klasor}' yolu için ilk seviye gösteriliyor.")
        
        try:
            # Artık 'build' veya 'calculate' yok.
            # Sadece 'display_tree'ye ana klasörü veriyoruz.
            self.display_tree(ana_klasor) 
            logger.info("Klasör ağacı ilk seviyesi yüklendi.")
        except Exception as e:
            logger.error(f"Klasör ağacı oluşturulurken hata: {e}", exc_info=True)
            self.show_error_message(f"Klasör ağacı oluşturulurken hata oluştu:\n{e}")
            
    def display_tree(self, ana_klasor=None):
        """
        Treeview'ı populate et. (Tembel Yükleme için güncellendi)
        ana_klasor: None değilse, ilk yükleme yapılır.
        """
        # Treeview'ı temizle
        for item in self.tree_view.get_children():
            self.tree_view.delete(item)

        search_text = self.search_entry.get().strip()

        # ARAMA MODU (GEÇİCİ OLARAK DEVRE DIŞI - HENÜZ ÇALIŞMAZ)
        if search_text and len(search_text) >= 2:
            self.populate_treeview_with_search()
        
        # TEMBEL YÜKLEME (NORMAL MOD)
        elif ana_klasor:
            # Ana klasörün sadece BİR alt seviyesini beyinden al
            birinci_seviye_klasorler = self.beyin.get_sadece_alt_klasorler(ana_klasor)
        
            # DÜZELTİLMİŞ HALİ
            for (klasor_adi, tam_yol, has_children) in birinci_seviye_klasorler:
                self.add_folder_to_treeview(
                    parent_id="",
                    folder_path=tam_yol,
                    folder_name=klasor_adi,
                    has_children=has_children # <-- Artık 'has_children' tanımlı
                )
        
        self._update_upload_button_state()

    def populate_treeview_normal(self):
        """Arama silindiğinde normal moda dönmek için kullanılır."""
        # Bu fonksiyonun eski mantığı (tree_data'yı gezmek) artık display_tree içinde.
        # Bu fonksiyon, arama kutusu temizlendiğinde çağrılır.
        if self.ana_klasor_yolu:
            self.display_tree(self.ana_klasor_yolu)
            
    def populate_treeview_with_search(self):
        """
        Arama modunda Treeview'ı populate et (Tembel Yükleme'ye uygun)
        'search_results' listesini hiyerarşik olarak çizer. (Düzeltilmiş Versiyon)
        """
        if not self.search_results:
            logger.info("Arama sonucu bulunamadı, ağaç boş gösteriliyor.")
            self.tree_view.insert(
                parent="", # 'parent=""' olmalı (Hata burada olmuştu)
                index="end", 
                text=" 🚫 Eşleşen öge bulunamadı."
            )
            return
        
        # Hangi yolu (path) hangi item_id ile eklediğimizi takip eder
        added_items_map = {}  # {path: item_id}
        
        # Beyin'den gelen liste zaten hiyerarşik (Ders -> Konu -> Tur)
        for result in self.search_results:
            path = result['path']
            name = result['name']
            has_children = result['has_children']
            parts = result['parts']
            
            # Ebeveyni belirle
            parent_id = "" # Varsayılan olarak kök (örn: 'Coğrafya' için)
            
            if len(parts) > 1:
                # Bu bir çocuktur (örn: 'Dünya üzerindeki çöller')
                # Ebeveyninin 'parts' listesi, bu listenin 'sonuncusu hariç' halidir
                parent_parts = parts[:-1]
                
                # Ebeveynin tam yolunu oluştur (bu, map'teki key'imiz olacak)
                parent_path = os.path.join(self.ana_klasor_yolu, *parent_parts)
                
                if parent_path in added_items_map:
                    parent_id = added_items_map[parent_path]
                else:
                    # Bu bir 'yetim' (Bu durumun olmaması lazım, 
                    # çünkü Beyin ebeveynleri de ekliyor)
                    logger.warning(f"Yetim arama sonucu bulundu: {name}")
                    pass # parent_id = "" (kök) olarak kalır
            
            # Bu öğeyi (Coğrafya VEYA Dünya üzerindeki çöller) ekle
            # (eğer zaten eklenmediyse)
            if path not in added_items_map:
                item_id = self.add_folder_to_treeview(
                    parent_id=parent_id,
                    folder_path=path,
                    folder_name=name,
                    has_children=has_children
                )
                # Haritaya ekle ki, çocukları bunun altına eklenebilsin
                added_items_map[path] = item_id
                                    
    def add_folder_to_treeview(self, parent_id, folder_path, folder_name, has_children: bool):
        """
        Ağaca BİR klasör ekler ve "Tembel Yükleme" için sahte bir alt öğe bırakır.
        (Artık 'folder_info' veya 'match_type' almaz)
        """
        
        level = self.beyin.get_folder_level(folder_path)
        
        # İkonları seviyeye göre belirle
        icon = "📁"
        if level == "DERS": icon = "📚"
        elif level == "KONU": icon = "📖"
        elif level == "TUR": icon = "📋"
        elif level == "ZORLUK": icon = "⭐"
        
        display_name = f"{icon} {folder_name}"

        # Klasörü ağaca ekle
        item_id = self.tree_view.insert(
            parent_id, "end",
            text=display_name,
            # --- ÇOK ÖNEMLİ: Tam yolu 'values' içine saklıyoruz ---
            values=[folder_path] 
        )

        # --- TEMBEL YÜKLEME SİHRİ ---
        # Eğer bu bir 'Zorluk' klasörü değilse (daha alta inebilir)
        if level != "ZORLUK" and has_children:
            self.tree_view.insert(item_id, "end", text="Yükleniyor...")
        

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
        """
        Arama işlemini ARKA PLAN thread'inde başlatır.
        Ana arayüzü kilitlemez.
        """
        search_text = self.search_entry.get().strip()
        
        # Minimum karakter kontrolü
        if len(search_text) < 2:
            if len(search_text) > 0:
                self.search_loading_label.configure(text="⚠️ Min 2 karakter")
            else:
                self.search_loading_label.configure(text="")
            self.search_results = []
            self.display_tree(self.ana_klasor_yolu) # Normal moda dön
            return
        
        # --- YENİ THREADING MANTIĞI ---
        logger.info(f"'{search_text}' için ARKA PLANDA arama başlatılıyor...")
        self.search_loading_label.configure(text="⏳")
        
     
        
        # Yeni bir "işçi" thread başlat
        thread = threading.Thread(
            target=self._perform_search_async, # "İşçi" fonksiyonu
            args=(search_text,),              # Ona "search_text"i ver
            daemon=True # Ana uygulama kapanırsa bu thread'i de kapat
        )
        thread.start() # İşi başlat
        
    def _perform_search_async(self, search_text):
        """
        !!! BU FONKSİYON ARKA PLAN THREAD'İNDE ÇALIŞIR !!!
        !!! ASLA CTK/TKINTER WIDGET'LARINA (UI) DOKUNMAZ !!!
        """
        try:
            # 1. Ağır işi (os.walk) burada yap
            results_list = self.beyin.search_folders_and_parents(search_text)
            
            # 2. İşi bitirince, sonucu ANA THREAD'e güvenle gönder
            #    self.after(0, ...) komutu, _on_search_complete fonksiyonunu
            #    ana UI thread'inde çalıştırır.
            self.after(0, self._on_search_complete, results_list)
            
        except Exception as e:
            logger.error(f"Arama thread'i çöktü: {e}", exc_info=True)
            # Bir hata olsa bile UI'ı güncellemek için boş liste gönder
            self.after(0, self._on_search_complete, [])

    def _on_search_complete(self, results_list):
        """
        !!! BU FONKSİYON ANA UI THREAD'İNDE ÇALIŞIR !!!
        !!! UI GÜNCELLEMESİ BURADA GÜVENLİDİR !!!
        """
        logger.info(f"Arama tamamlandı, {len(results_list)} sonuç bulundu.")
        
        # 1. Sonucu al
        self.search_results = results_list
        
        # 2. UI'ı (Loading simgesi) güncelle
        self.search_loading_label.configure(text="")
        
        self.display_tree()
              
    def klasor_secildi(self, klasor_yolu):
        """Klasör seçildiğinde"""
        logger.info(f"Klasör seçildi: {klasor_yolu}")
        self.selected_folder = klasor_yolu

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
                if not self.beyin.is_image_file(src):
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
                self.beyin.remove_from_thumb_cache(src_path)
                self.show_selected_images()
        except Exception as e:
            logger.error(f"Bekleyen öğe kaldırılamadı: {e}", exc_info=True)

    def commit_selected_images(self):
        """
        Bekleyen dosyaları ARKA PLANDA seçili zorluk klasörüne kopyalar.
        (Kallavi Fonksiyon)
        """
        try:
            # 1. Kontroller (Bunlar hızlıdır, thread'e gerek yok)
            if not self.selected_folder or not self.beyin.is_zorluk_folder(self.selected_folder):
                messagebox.showwarning("Uyarı", "Lütfen önce Kolay/Orta/Zor klasörlerinden birini seçin.")
                return

            if not self.selected_images:
                messagebox.showinfo("Bilgi", "Yüklenecek resim yok.")
                return

            if not messagebox.askyesno(
                "Onay",
                f"{len(self.selected_images)} dosyayı\n'{self.beyin.get_relative_path(self.selected_folder)}'\nklasörüne kopyalamak istiyor musunuz?"
            ):
                return
            
            
            # 2. UI'ı "Kopyalanıyor..." moduna al
            # (Sağ paneli temizle ve bir mesaj göster)
            for w in self.selected_images_scroll.winfo_children():
                w.destroy()
            
            ctk.CTkLabel(
                self.selected_images_scroll,
                text=f"⏳ {len(self.selected_images)} resim kopyalanıyor, lütfen bekleyin...",
                font=ctk.CTkFont(family="Segoe UI", size=14),
                text_color="#2d3436"
            ).pack(pady=50)
            
            # 3. Arka plan "işçi" thread'ini başlat
            # (Kopyalanacak listeyi ve hedefi işçiye veriyoruz)
            thread = threading.Thread(
                target=self._commit_images_async,
                args=(list(self.selected_images), self.selected_folder), # O anki kopyayı ver
                daemon=True
            )
            thread.start()
            
            # 4. Ana listeyi hemen temizle (işçi kopyasını aldı)
            self.selected_images.clear()

        except Exception as e:
            logger.error(f"Yüklemeyi onaylama hatası: {e}", exc_info=True)
            messagebox.showerror("Hata", "Yükleme sırasında bir hata oluştu.")
            

    def _commit_images_async(self, images_to_copy_list, hedef_klasor):
        """
        !!! BU FONKSİYON ARKA PLAN THREAD'İNDE ÇALIŞIR !!!
        Ağır 'shutil.copy2' işini yapar.
        """
        kopyalanan = 0
        hatalar = 0
        
        for src_path, dosya_adi in images_to_copy_list:
            try:
                # (Bu kontroller hızlı, burada kalabilir)
                if not self.beyin.is_image_file(src_path):
                    continue
                
                hedef_yol = os.path.join(hedef_klasor, dosya_adi)
                
                # Ağır iş: shutil.copy2
                self.beyin.kopyala_resim(src_path, hedef_yol)
                kopyalanan += 1

            except Exception as e:
                logger.error(f"Kopyalama thread'i hatası: {src_path} -> {e}", exc_info=True)
                hatalar += 1
        
        # İş bitince, sonucu (başarı/hata sayısı) ana thread'e yolla
        self.after(0, self._on_commit_complete, kopyalanan, hatalar)

    def _on_commit_complete(self, kopyalanan_sayisi, hata_sayisi):
        """
        !!! BU FONKSİYON ANA UI THREAD'İNDE ÇALIŞIR !!!
        Kopyalama bitince UI'ı günceller.
        """
        logger.info(f"Kopyalama tamamlandı. Başarılı: {kopyalanan_sayisi}, Hata: {hata_sayisi}")
        
        # 1. UI'ı güncelle (Mesajı göster)
        # (Sağ paneli temizle)
        for w in self.selected_images_scroll.winfo_children():
            w.destroy()
        
        self.show_initial_message() # Başlangıç mesajını göster
        
        if hata_sayisi > 0:
            messagebox.showwarning("Kopyalama Tamamlandı", f"{kopyalanan_sayisi} dosya kopyalandı.\n{hata_sayisi} dosyada hata oluştu (detaylar log'da).")
        else:
            messagebox.showinfo("Tamamlandı", f"{kopyalanan_sayisi} dosya başarıyla kopyalandı.")

        # 2. Cache'leri temizle ve ağacı yenile
        self.beyin._clear_caches()
        if self.ana_klasor_yolu:
            self.display_tree(self.ana_klasor_yolu) # Tembel yükleme
            
        # 3. Detay panelini de (eğer bir yer seçiliyse) yenile
        if self.selected_folder:
            self.update_detail_panel(self.selected_folder)
            
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

                # 1. Karta SABİT YÜKSEKLİK ver (örn: 320px)
                card = ctk.CTkFrame(cards_frame, corner_radius=8, height=320)
                card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)

                card.grid_rowconfigure(0, weight=1) # Resim alanı genişlesin
                card.grid_rowconfigure(1, weight=0) # Metin sabit
                card.grid_rowconfigure(2, weight=0) # Butonlar sabit
                card.grid_columnconfigure(0, weight=1) # Tek sütun

           
                img_frame = ctk.CTkFrame(card, fg_color="transparent", height=180)
                img_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 6))
                img_frame.pack_propagate(False) # Frame'in küçülmesini engelle

                thumb = self._get_ctk_thumb(src_path, max_size=(180, 180))
                if thumb is not None:
                    img_lbl = ctk.CTkLabel(img_frame, image=thumb, text="")
                    img_lbl.image = thumb  # GC koruması
                else:
                    img_lbl = ctk.CTkLabel(
                        img_frame,
                        text="(Önizleme yok)",
                        font=ctk.CTkFont(size=10),
                        text_color="#6c757d"
                    )
                
                # .pack() kullanarak resim çerçevesi içinde ortala
                img_lbl.pack(expand=True, anchor="center") 

                # --- Row 1: Metin Alanı ---
                try:
                    size_text = self.beyin._format_size(os.path.getsize(src_path))
                except Exception:
                    size_text = "-"
                meta_lbl = ctk.CTkLabel(
                    card,
                    text=f"{dosya_adi}\n{size_text}",
                    font=ctk.CTkFont(family="Segoe UI", size=9),
                    text_color="#2d3436",
                    justify="center",
                    height=30 # Metin için sabit yükseklik
                )
                meta_lbl.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 8))

                # --- Row 2: Buton Alanı ---
                # Butonları 'sticky="s"' (south/güney) ile en alta sabitliyoruz
                btn_row = ctk.CTkFrame(card, fg_color="transparent")
                btn_row.grid(row=2, column=0, sticky="s", pady=(0, 10))

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
            
    # def create_selected_image_widget(self, resim_yolu, dosya_adi, index):
    #     """Seçilen resim widget'ı oluştur"""
    #     try:
    #         # Resim frame'i
    #         image_frame = ctk.CTkFrame(self.selected_images_scroll, fg_color="white")
            
    #         # Grid pozisyonu hesapla (3 sütunlu grid)
    #         row = index // 3
    #         col = index % 3
    #         image_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
    #         # Grid ağırlık ayarları
    #         self.selected_images_scroll.grid_columnconfigure(col, weight=1)

    #         # Resmi yükle ve boyutlandır
    #         pil_image = Image.open(resim_yolu)
    #         # Daha büyük thumbnail boyutu
    #         pil_image.thumbnail((200, 200), Image.Resampling.LANCZOS)
    #         photo = ImageTk.PhotoImage(pil_image)

    #         # Resim label'ı
    #         image_label = ctk.CTkLabel(
    #             image_frame,
    #             image=photo,
    #             text=""
    #         )
    #         image_label.image = photo  # Referansı sakla
    #         image_label.pack(pady=10)

    #         # Dosya adı
    #         name_label = ctk.CTkLabel(
    #             image_frame,
    #             text=dosya_adi,
    #             font=ctk.CTkFont(family="Segoe UI", size=10),
    #             text_color="#2d3436",
    #             wraplength=180
    #         )
    #         name_label.pack(pady=(0, 5))

    #         # Sil butonu
    #         delete_btn = ctk.CTkButton(
    #             image_frame,
    #             text="🗑️ Kaldır",
    #             font=ctk.CTkFont(family="Segoe UI", size=10),
    #             fg_color="#dc3545",
    #             text_color="white",
    #             hover_color="#c82333",
    #             width=80,
    #             height=25,
    #             command=lambda path=resim_yolu, name=dosya_adi, idx=index: self.remove_selected_image(path, name, idx)
    #         )
    #         delete_btn.pack(pady=(0, 10))

    #     except Exception as e:
    #         logger.error(f"Seçilen resim widget'ı oluşturulurken hata: {e}", exc_info=True)

    # def remove_selected_image(self, resim_yolu, dosya_adi, index):
    #     """Seçilen resimden kaldır"""
    #     if messagebox.askyesno("Onay", f"'{dosya_adi}' resmini seçilenlerden kaldırmak istediğinizden emin misiniz?"):
    #         try:
    #             # Listedeki resmi kaldır
    #             self.selected_images.pop(index)
    #             # Görüntüyü yenile
    #             self.show_selected_images()
    #             logger.info(f"Resim seçilenlerden kaldırıldı: {dosya_adi}")
    #         except Exception as e:
    #             logger.error(f"Resim kaldırılırken hata: {e}", exc_info=True)
    #             messagebox.showerror("Hata", "Resim kaldırılırken hata oluştu.")

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

    def show_error_message(self, message):
        """Hata mesajı göster"""
        logger.warning(f"Kullanıcıya hata mesajı gösteriliyor: {message}")
        messagebox.showerror("Hata", message)

    def ana_menuye_don(self):
        """Ana menüye dön"""
        logger.info("Ana menüye dönme komutu verildi.")
        self.controller.ana_menuye_don()
      
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
        """
        Seçili klasörün detaylarını ARKA PLANDA yükler.
        (Kallavi Fonksiyon)
        """
        # 1. Temizle
        for widget in self.detail_scroll.winfo_children():
            widget.destroy()
        
        # 2. "Yükleniyor..." mesajı göster
        ctk.CTkLabel(
            self.detail_scroll,
            text="⏳ İstatistikler hesaplanıyor...",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#6c757d"
        ).pack(pady=20)
        
        # 3. Seviyeyi belirle
        level = self.beyin.get_folder_level(folder_path)
        
        # 4. Arka plan "işçi" thread'ini başlat
        thread = threading.Thread(
            target=self._load_details_async,
            args=(folder_path, level),
            daemon=True
        )
        thread.start()
    
    def _load_details_async(self, folder_path, level):
        """
        !!! BU FONKSİYON ARKA PLAN THREAD'İNDE ÇALIŞIR !!!
        Ağır 'Beyin' işini yapar.
        """
        try:
            data = {}
            if level == "DERS":
                # 'os.walk' ve 'os.listdir' burada, 'Beyin' içinde çağrılır
                data = self.beyin.get_ders_details_data(folder_path)
            elif level == "KONU":
                data = self.beyin.get_konu_details_data(folder_path)
            elif level == "TUR":
                # (Şimdilik anında yükle, veya 'get_tur_details_data' ekle)
                data = self.beyin.get_tur_details_data(folder_path) # (Beyin'e eklemelisin)
            elif level == "ZORLUK":
                # (Şimdilik anında yükle, veya 'get_zorluk_details_data' ekle)
                data = self.beyin.get_zorluk_details_data(folder_path) # (Beyin'e eklemelisin)
            
            # Sonucu ana thread'e geri yolla
            self.after(0, self._on_details_loaded, data, level)
            
        except Exception as e:
            logger.error(f"Detay yükleme thread'i çöktü: {e}", exc_info=True)
            self.after(0, self._on_details_loaded, None, None) # Hata durumunda

    def _on_details_loaded(self, data, level):
        """
        !!! BU FONKSİYON ANA UI THREAD'İNDE ÇALIŞIR !!!
        Hazır 'data'yı alıp UI'ı çizer.
        """
        # Temizle (Yükleniyor... mesajını sil)
        for widget in self.detail_scroll.winfo_children():
            widget.destroy()
            
        if data is None:
            ctk.CTkLabel(
                self.detail_scroll,
                text="❌ Detaylar yüklenemedi.",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#dc3545"
            ).pack(pady=20)
            return

        # 'data'yı kullanarak ilgili çizim fonksiyonunu çağır
        if level == "DERS":
            self.show_ders_details(data) # Artık 'data' alıyor
        elif level == "KONU":
            self.show_konu_details(data) # Artık 'data' alıyor
        elif level == "TUR":
            self.show_tur_details(data) # Artık 'data' alıyor
        elif level == "ZORLUK":
            self.show_zorluk_details(data) # Artık 'data' alıyor
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
    
    def show_konu_details(self, data):
        """Konu seviyesi detayları (Sadece UI çizer, 'data' bekler)"""
        
        # 1. Veriyi 'data' sözlüğünden al (Artık I/O yok)
        konu_adi = data.get('konu_adi', 'Bilinmiyor')
        ders_adi = data.get('ders_adi', 'Bilinmiyor')
        relative_path = data.get('relative_path', '-')
        total_images = data.get('total_images', 0)
        total_size_str = self.beyin._format_size(data.get('total_size', 0))
        last_modified = data.get('last_modified', '-')
        tur_stats = data.get('tur_stats', []) # Beyin'den gelen Test/Yazılı verisi

        # 2. UI'ı Çiz (Eski kodundan kopyalandı, I/O yok)
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

        self.create_detail_row("📍", "Yol", relative_path)

        # Ayırıcı
        ctk.CTkLabel(
            self.detail_scroll,
            text="─" * 40,
            text_color="#e0e0e0",
            font=ctk.CTkFont(size=8)
        ).pack(pady=5)

        # İstatistikler (Artık 'try' bloğuna gerek yok)
        self.create_detail_row("📷", "Toplam Resim", total_images)
        self.create_detail_row("💾", "Toplam Boyut", total_size_str)
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

        # 3. 'Beyin'den gelen hazır 'tur_stats' verisini çiz
        for tur_data in tur_stats:
            tur_adi = tur_data['ad']
            if tur_data['exists']:
                # Tür başlığı (Klasör var)
                ctk.CTkLabel(
                    self.detail_scroll,
                    text=f"  📁 {tur_adi}:",
                    font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                    text_color="#2d3436"
                ).pack(anchor="w", pady=(5, 2))

                # Zorluk seviyeleri
                for zorluk_data in tur_data['zorlukler']:
                    zorluk_adi = zorluk_data['ad']
                    if zorluk_data['exists']:
                        zorluk_images = zorluk_data['images']
                        status = "✅" if zorluk_images > 0 else "❌"
                        color = "#28a745" if status == "✅" else "#dc3545"
                        
                        ctk.CTkLabel(
                            self.detail_scroll,
                            text=f"    {status} {zorluk_adi}: {zorluk_images} resim",
                            font=ctk.CTkFont(family="Segoe UI", size=9),
                            text_color=color,
                            anchor="w"
                        ).pack(anchor="w", pady=1)
                    else:
                        # Zorluk klasörü yok
                        ctk.CTkLabel(
                            self.detail_scroll,
                            text=f"    ❌ {zorluk_adi}: (Klasör yok)",
                            font=ctk.CTkFont(family="Segoe UI", size=9),
                            text_color="#dc3545",
                            anchor="w"
                        ).pack(anchor="w", pady=1)
                        
            else:
                # Tür başlığı (Klasör yok)
                ctk.CTkLabel(
                    self.detail_scroll,
                    text=f"  📁 {tur_adi}:",
                    font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                    text_color="#6c757d" # Soluk renk
                ).pack(anchor="w", pady=(5, 2))
                
                # Klasörün olmadığını belirten mesaj
                ctk.CTkLabel(
                    self.detail_scroll,
                    text="    ❌ (Klasör bulunamadı)",
                    font=ctk.CTkFont(family="Segoe UI", size=9),
                    text_color="#dc3545",
                    anchor="w"
                ).pack(anchor="w", pady=1)

    def show_tur_details(self, data):
        """Tür (Test/Yazılı) seviyesi detayları (Sadece UI çizer, 'data' bekler)"""
        
        # 1. Veriyi 'data' sözlüğünden al
        tur_adi = data.get('tur_adi', 'Bilinmiyor')
        konu_adi = data.get('konu_adi', 'Bilinmiyor')
        relative_path = data.get('relative_path', '-')
        total_images = data.get('total_images', 0)
        total_size_str = self.beyin._format_size(data.get('total_size', 0))
        last_modified = data.get('last_modified', '-')
        zorluk_stats = data.get('zorluk_stats', []) # Beyin'den gelen Zorluk verisi

        # 2. UI'ı Çiz (Eski kodundan kopyalandı, I/O yok)
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

        self.create_detail_row("📍", "Yol", relative_path)

        # Ayırıcı
        ctk.CTkLabel(
            self.detail_scroll,
            text="─" * 40,
            text_color="#e0e0e0",
            font=ctk.CTkFont(size=8)
        ).pack(pady=5)

        # İstatistikler (Artık 'try' bloğuna gerek yok)
        self.create_detail_row("📷", "Toplam Resim", total_images)
        self.create_detail_row("💾", "Toplam Boyut", total_size_str)
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
        
        # 3. 'Beyin'den gelen hazır 'zorluk_stats' verisini çiz
        for zorluk_data in zorluk_stats:
            zorluk_adi = zorluk_data['ad']
            if zorluk_data['exists']:
                zorluk_images = zorluk_data['images']
                zorluk_size_str = self.beyin._format_size(zorluk_data['size'])
                status = "✅" if zorluk_images > 0 else "❌"

                if zorluk_images == 0:
                    bos_seviyeler.append(zorluk_adi)

                color = "#28a745" if status == "✅" else "#dc3545"
                self.create_detail_row(
                    status,
                    zorluk_adi,
                    f"{zorluk_images} resim ({zorluk_size_str})",
                    text_color=color
                )
            else:
                # Zorluk klasörü yok
                self.create_detail_row(
                    "❌",
                    zorluk_adi,
                    "(Klasör yok)",
                    text_color="#dc3545"
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

    def show_ders_details(self, data):
        """Ders seviyesi detayları (Sadece UI çizer, 'data' bekler)"""
        
        # 1. Veriyi 'data' sözlüğünden al (Artık I/O yok)
        ders_adi = data.get('ders_adi', 'Bilinmiyor')
        relative_path = data.get('relative_path', '-')
        konular = data.get('konular', [])
        total_images = data.get('total_images', 0)
        # _format_size 'beyin'de, onu çağırıyoruz
        total_size_str = self.beyin._format_size(data.get('total_size', 0))
        last_modified = data.get('last_modified', '-')

        # 2. UI'ı Çiz
        title = ctk.CTkLabel(
            self.detail_scroll,
            text=f"📚 DERS: {ders_adi}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#2d3436"
        )
        title.pack(pady=(5, 10))

        self.create_detail_row("📍", "Yol", relative_path)

        # Ayırıcı (SyntaxError düzeltilmiş hali)
        ctk.CTkLabel(
            self.detail_scroll,
            text="─" * 40,
            text_color="#e0e0e0",
            font=ctk.CTkFont(size=8)
        ).pack(pady=5)

        self.create_detail_row("📂", "Toplam Konu", len(konular))
        self.create_detail_row("📷", "Toplam Resim", total_images)
        self.create_detail_row("💾", "Toplam Boyut", total_size_str)
        self.create_detail_row("📅", "Son Güncelleme", last_modified)

        # Ayırıcı 2 (SyntaxError düzeltilmiş hali)
        ctk.CTkLabel(
            self.detail_scroll,
            text="─" * 40,
            text_color="#e0e0e0",
            font=ctk.CTkFont(size=8)
        ).pack(pady=5)

        ctk.CTkLabel(
            self.detail_scroll,
            text="📋 Konu Dağılımı:",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#2d3436"
        ).pack(anchor="w", pady=(5, 5))

        if not konular:
             ctk.CTkLabel(
                self.detail_scroll,
                text="  (Alt konu bulunamadı)",
                font=ctk.CTkFont(family="Segoe UI", size=9),
                text_color="#6c757d"
            ).pack(anchor="w", pady=1, padx=5)
        else:
            for konu_data in konular:
                self.create_detail_row("📁", konu_data['ad'], f"{konu_data['resim_sayisi']} resim", text_color="#2d3436")
                
    def show_zorluk_details(self, data):
        """Zorluk seviyesi detayları (Sadece UI çizer, 'data' bekler)"""
        
        # 1. Veriyi 'data' sözlüğünden al
        zorluk_adi = data.get('zorluk_adi', 'Bilinmiyor')
        relative_path = data.get('relative_path', '-')
        total_images = data.get('total_images', 0)
        total_size_str = self.beyin._format_size(data.get('total_size', 0))
        last_modified = data.get('last_modified', '-')

        # 2. UI'ı Çiz (Eski kodundan kopyalandı, I/O yok)
        title = ctk.CTkLabel(
            self.detail_scroll,
            text=f"⭐ ZORLUK: {zorluk_adi}",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#2d3436"
        )
        title.pack(pady=(5, 10))

        self.create_detail_row("📍", "Yol", relative_path)

        # Ayırıcı
        ctk.CTkLabel(
            self.detail_scroll,
            text="─" * 40,
            text_color="#e0e0e0",
            font=ctk.CTkFont(size=8)
        ).pack(pady=5)

        # İstatistikler (Artık 'try' bloğuna gerek yok)
        self.create_detail_row("📷", "Toplam Resim", total_images)
        self.create_detail_row("💾", "Toplam Boyut", total_size_str)
        self.create_detail_row("📅", "Son Güncelleme", last_modified)