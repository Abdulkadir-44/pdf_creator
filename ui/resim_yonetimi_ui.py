import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import os
import shutil
from PIL import Image, ImageTk
import logging

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
        self.ana_klasor_yolu = None
        self.current_images = []
        self.selected_folder = None
        self.tree_data = {}  # Ağaç veri yapısı
        self.expanded_folders = set()  # Açık olan klasörler
        self.folder_stats = {}  # Klasör istatistikleri
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
            fg_color="#6c757d",
            text_color=BTN_FG,
            hover_color="#5a6268",
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
            text="📷 Resim Yükle",
            font=self.btn_font,
            fg_color="#28a745",
            text_color=BTN_FG,
            hover_color="#218838",
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
        left_panel.grid_rowconfigure(2, weight=1)

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
            columns=("stats",),
            show="tree headings",
            height=20
        )
        
        # Treeview stil ayarları
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
        
        # Treeview başlıkları
        self.tree_view.heading("#0", text="Klasör Adı", anchor="w")
        self.tree_view.heading("stats", text="İstatistik", anchor="w")
        self.tree_view.column("#0", width=200, minwidth=150)
        self.tree_view.column("stats", width=150, minwidth=120)
        
        # Scrollbar ekle
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_view.yview)
        self.tree_view.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.tree_view.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Selection event
        self.tree_view.bind("<<TreeviewSelect>>", self.on_tree_select)

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

    def on_tree_select(self, event):
        """Treeview'da klasör seçildiğinde"""
        selection = self.tree_view.selection()
        if selection:
            item_id = selection[0]
            folder_path = self.tree_view.item(item_id, "values")[0] if self.tree_view.item(item_id, "values") else None
            if folder_path:
                self.klasor_secildi(folder_path)

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
            self.resim_yukle_btn.configure(state="normal")
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
        """Treeview'a klasör ekle"""
        folder_name = folder_info['name']
        children = folder_info['children']
        
        # İstatistik bilgisi
        stats = self.folder_stats.get(folder_path, {})
        resim_sayisi = stats.get('resim_sayisi', 0)
        toplam_boyut = stats.get('toplam_boyut', 0)
        
        if resim_sayisi > 0:
            boyut_text = self.format_file_size(toplam_boyut)
            stats_text = f"📊 {resim_sayisi} ({boyut_text})"
        else:
            stats_text = "📁 Boş"
        
        # Klasör path'ini desktop'tan başlat
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            if folder_path.startswith(desktop_path):
                relative_path = os.path.relpath(folder_path, desktop_path)
                stats_text = f"{stats_text} | 📂 {relative_path}"
        except:
            pass
        
        # Klasör adını stilize et
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
        
        # Treeview'a ekle
        item_id = self.tree_view.insert(
            parent_id, "end",
            text=display_name,
            values=(folder_path, stats_text)
        )
        
        # Alt klasörleri de ekle (sadece arama modunda değilse)
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
        """Resim yükle"""
        if not self.selected_folder:
            messagebox.showwarning("Uyarı", "Lütfen önce bir klasör seçin.")
            return

        logger.info("Resim yükleme işlemi başlatıldı.")
        dosyalar = filedialog.askopenfilenames(
            title="Yüklenecek Resimleri Seçin",
            filetypes=[
                ("Resim Dosyaları", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
                ("PNG Dosyaları", "*.png"),
                ("JPEG Dosyaları", "*.jpg *.jpeg"),
                ("Tüm Dosyalar", "*.*")
            ]
        )

        if dosyalar:
            logger.info(f"Seçilen dosya sayısı: {len(dosyalar)}")
            
            # Seçilen resimleri listeye ekle
            for dosya in dosyalar:
                try:
                    dosya_adi = os.path.basename(dosya)
                    hedef_yol = os.path.join(self.selected_folder, dosya_adi)
                    
                    # Aynı isimde dosya varsa uyar
                    if os.path.exists(hedef_yol):
                        if not messagebox.askyesno("Dosya Mevcut", f"'{dosya_adi}' dosyası zaten mevcut. Üzerine yazılsın mı?"):
                            continue
                    
                    shutil.copy2(dosya, hedef_yol)
                    logger.info(f"Resim kopyalandı: {dosya_adi}")
                    
                    # Seçilen resimler listesine ekle
                    self.selected_images.append((hedef_yol, dosya_adi))
                    
                except Exception as e:
                    logger.error(f"Resim kopyalanırken hata: {e}", exc_info=True)
                    messagebox.showerror("Hata", f"'{os.path.basename(dosya)}' kopyalanırken hata oluştu.")

            # Seçilen resimleri göster
            self.show_selected_images()
            
            # Klasör istatistiklerini güncelle
            self.calculate_folder_stats()
            self.display_tree()
            
            messagebox.showinfo("Başarılı", f"{len(dosyalar)} resim başarıyla yüklendi ve seçildi.")

    def show_selected_images(self):
        """Seçilen resimleri göster"""
        logger.info(f"Seçilen resimler gösteriliyor: {len(self.selected_images)} resim")
        
        # Scroll frame'i temizle
        for widget in self.selected_images_scroll.winfo_children():
            widget.destroy()
        
        if not self.selected_images:
            self.show_no_selected_images_message()
            return
        
        # Resimleri grid layout ile göster
        for i, (resim_yolu, dosya_adi) in enumerate(self.selected_images):
            self.create_selected_image_widget(resim_yolu, dosya_adi, i)

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
