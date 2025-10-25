import customtkinter as ctk
import tkinter as tk
import os
import logging
from datetime import datetime
import math

# Yeni loglama sistemi: Bu modülün kendi logger'ını al.
# Adı otomatik olarak 'ui.konu_baslik_sec_ui' olacaktır.
logger = logging.getLogger(__name__)

class KonuBaslikSecmePenceresi(ctk.CTkFrame):
    def __init__(self, parent, controller, ders_klasor_yolu, ders_adi):
        super().__init__(parent, fg_color="#f0f2f5")
        self.controller = controller
        self.ders_klasor_yolu = ders_klasor_yolu
        self.ders_adi = ders_adi
        self.secilen_konular = {}
        
        # Renk Paleti
        self.colors = {
            'primary': '#4361ee',
            'primary_hover': '#3730a3',
            'secondary': '#7209b7',
            'success': '#228b22',
            'danger': '#ff006e',
            'warning': '#ffbe0b',
            'dark': '#2b2d42',
            'light': '#ffffff',
            'bg': '#f0f2f5',
            'card_bg': '#ffffff',
            'text_primary': '#2b2d42',
            'text_secondary': '#6c757d',
            'border': '#dee2e6',
            'hover_bg': '#f8f9fa',
            'selected_bg': '#e7f3ff'
        }
        
        logger.info(f"KonuBaslikSecmePenceresi başlatıldı - Ders: {ders_adi}")
        
        self.konu_listesi = self.get_konu_listesi()
        self.setup_ui()

    def setup_ui(self):
        """Ana UI'ı oluştur"""
        logger.debug("UI kurulumu başlatılıyor")
        
        # Ana container - gölge efekti için
        self.main_container = ctk.CTkFrame(self, fg_color=self.colors['bg'], corner_radius=0)
        self.main_container.pack(fill="both", expand=True)
        
        # Header bölümü
        self.create_header()
        
        # İçerik bölümü
        self.create_content_area()

    def create_header(self):
        """Modern header tasarımı"""
        header_frame = ctk.CTkFrame(
            self.main_container, 
            height=120, 
            corner_radius=0,
            fg_color=self.colors['primary']
        )
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(expand=True, fill="both", padx=40, pady=20)

        left_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        left_frame.pack(side="left", fill="y")

        home_btn = ctk.CTkButton(
            left_frame,
            text="Ana Menü",
            width=100, height=36, corner_radius=8, fg_color="transparent", hover_color="#5a6fee",
            border_width=2, border_color=self.colors['light'], text_color=self.colors['light'],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.ana_menuye_don
        )
        home_btn.pack(side="left", padx=(0, 10))

        back_btn = ctk.CTkButton(
            left_frame,
            text="← Ders Seçimi",
            width=110, height=36, corner_radius=8, fg_color="transparent", hover_color="#5a6fee",
            border_width=2, border_color=self.colors['light'], text_color=self.colors['light'],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.ders_sec_sayfasina_don
        )
        back_btn.pack(side="left")

        right_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        right_frame.pack(side="right", fill="y")

        title_label = ctk.CTkLabel(
            right_frame, text=f"📚 {self.ders_adi}",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=self.colors['light']
        )
        title_label.pack(anchor="e")

        subtitle_label = ctk.CTkLabel(
            right_frame, text="Konu Başlığı Seçimi",
            font=ctk.CTkFont(family="Segoe UI", size=14), text_color="#e0e0e0"
        )
        subtitle_label.pack(anchor="e", pady=(5, 0))
    
    def create_content_area(self):
        """Ana içerik alanı"""
        content_frame = ctk.CTkFrame(self.main_container, fg_color=self.colors['bg'], corner_radius=0)
        content_frame.pack(fill="both", expand=True, padx=30, pady=20)

        main_content = ctk.CTkFrame(content_frame, fg_color="transparent")
        main_content.pack(fill="both", expand=True)
    
        left_panel = ctk.CTkFrame(
            main_content, fg_color=self.colors['card_bg'], corner_radius=15,
            border_width=1, border_color=self.colors['border']
        )
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.create_left_panel_content(left_panel)
        
        right_panel = ctk.CTkFrame(
            main_content, fg_color=self.colors['card_bg'], corner_radius=15, width=350,
            border_width=1, border_color=self.colors['border']
        )
        right_panel.pack(side="right", fill="y", padx=(10, 0))
        right_panel.pack_propagate(False)
        
        self.create_right_panel_content(right_panel)

    def create_left_panel_content(self, panel):
        """Sol panel içeriği"""
        header_frame = ctk.CTkFrame(panel, fg_color="transparent", height=60)
        header_frame.pack(fill="x", padx=20, pady=(15, 0))
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame, text="📋 Konu Listesi",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=self.colors['text_primary']
        )
        title_label.pack(side="left", pady=10)
        
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right", pady=10)
        
        select_all_btn = ctk.CTkButton(
            btn_frame, text="Tümünü Seç", width=90, height=32, corner_radius=8,
            fg_color=self.colors['success'], hover_color="#05e090", text_color=self.colors['light'],
            font=ctk.CTkFont(size=12, weight="bold"), command=self.select_all
        )
        select_all_btn.pack(side="left", padx=2)
        
        clear_all_btn = ctk.CTkButton(
            btn_frame, text="Temizle", width=80, height=32, corner_radius=8,
            fg_color=self.colors['danger'], hover_color="#e0005a", text_color=self.colors['light'],
            font=ctk.CTkFont(size=12, weight="bold"), command=self.clear_all
        )
        clear_all_btn.pack(side="left", padx=2)
        
        self.create_search_section(panel)
        self.create_filter_buttons(panel)
        self.create_topics_list(panel)
    
    def create_search_section(self, parent):
        """Modern arama bölümü"""
        search_frame = ctk.CTkFrame(parent, fg_color=self.colors['hover_bg'], corner_radius=10)
        search_frame.pack(fill="x", padx=20, pady=(10, 15))
        
        search_icon = ctk.CTkLabel(
            search_frame, text="🔍", font=ctk.CTkFont(size=16), text_color=self.colors['text_secondary']
        )
        search_icon.pack(side="left", padx=(15, 5))
        
        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_frame, textvariable=self.search_var, placeholder_text="Konu ara...",
            font=ctk.CTkFont(family="Segoe UI", size=13), height=40, corner_radius=0,
            fg_color=self.colors['hover_bg'], border_width=0
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_timer = None
        self.search_entry.bind('<KeyRelease>', self.on_search_keypress)

    def create_filter_buttons(self, parent):
        """Filtre butonları"""
        filter_frame = ctk.CTkFrame(parent, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        filters = [("Tümü", "all", True), ("Çok Sorulu (50+)", "many", False),
                   ("Az Sorulu (<20)", "few", False), ("Sorusuz", "none", False)]
        
        self.filter_buttons = {}
        self.active_filter = "all"
        
        for text, filter_type, is_active in filters:
            btn = ctk.CTkButton(
                filter_frame, text=text, height=28, corner_radius=14,
                fg_color=self.colors['primary'] if is_active else "transparent",
                hover_color=self.colors['primary_hover'] if is_active else self.colors['hover_bg'],
                text_color=self.colors['light'] if is_active else self.colors['text_secondary'],
                border_width=1 if not is_active else 0, border_color=self.colors['border'],
                font=ctk.CTkFont(size=11), command=lambda f=filter_type: self.apply_filter(f)
            )
            btn.pack(side="left", padx=3)
            self.filter_buttons[filter_type] = btn

    def apply_filter(self, filter_type):
        """Filtreleme uygula"""
        for f_type, btn in self.filter_buttons.items():
            is_active = f_type == filter_type
            btn.configure(
                fg_color=self.colors['primary'] if is_active else "transparent",
                hover_color=self.colors['primary_hover'] if is_active else self.colors['hover_bg'],
                text_color=self.colors['light'] if is_active else self.colors['text_secondary'],
                border_width=0 if is_active else 1
            )
        self.active_filter = filter_type
        self.filter_topics()

    def filter_topics(self):
        """Konuları filtrele"""
        search_text = self.search_var.get().lower()
        for konu_adi, item_frame in self.topic_items.items():
            konu_info = next((k for k in self.konu_listesi if k['adi'] == konu_adi), None)
            if not konu_info: continue
            
            soru_sayisi = konu_info['toplam_soru']
            
            filter_pass = False
            if self.active_filter == "all": filter_pass = True
            elif self.active_filter == "many": filter_pass = soru_sayisi >= 50
            elif self.active_filter == "few": filter_pass = 0 < soru_sayisi < 20
            elif self.active_filter == "none": filter_pass = soru_sayisi == 0
            
            search_pass = not search_text or search_text in konu_adi.lower()
            
            if filter_pass and search_pass:
                item_frame.pack(fill="x", padx=5, pady=2)
            else:
                item_frame.pack_forget()

    def create_topics_list(self, parent):
        """Konu listesi"""
        self.scroll_frame = ctk.CTkScrollableFrame(parent, fg_color="#f5f5f5", corner_radius=0)
        self.scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.checkbox_vars = {}
        self.checkboxes = {}
        self.topic_items = {}
        
        if not self.konu_listesi:
            self.show_empty_message()
            return
        
        for konu_info in self.konu_listesi[:50]:
            self.create_topic_item(konu_info)
        
        if len(self.konu_listesi) > 50:
            self.create_load_more_button()

    def create_topic_item(self, konu_info):
        """Modern konu öğesi - detaylı soru dağılımı ile"""
        konu_adi = konu_info['adi']
        detay_bilgisi = self.calculate_detailed_questions(konu_info['yol'])
        toplam_soru = sum(sum(tip.values()) for tip in detay_bilgisi.values())

        var = tk.BooleanVar()
        self.checkbox_vars[konu_adi] = var

        item_frame = ctk.CTkFrame(self.scroll_frame, fg_color=self.colors['hover_bg'], corner_radius=10, height=120)
        item_frame.pack(fill="x", padx=5, pady=3)
        item_frame.pack_propagate(False)

        top_frame = ctk.CTkFrame(item_frame, fg_color="transparent", height=40)
        top_frame.pack(fill="x", padx=10, pady=(8, 5))
        top_frame.pack_propagate(False)

        checkbox = ctk.CTkCheckBox(
            top_frame, text="", variable=var, width=24, height=24, corner_radius=6,
            fg_color=self.colors['primary'], hover_color=self.colors['primary_hover'],
            command=lambda k=konu_adi: self.on_checkbox_change(k)
        )
        checkbox.pack(side="left", pady=8)

        info_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=(10, 0))

        ctk.CTkLabel(
            info_frame, text=konu_adi, font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=self.colors['text_primary'], anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            info_frame, text=f"Toplam: {toplam_soru} soru", font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.get_count_color(toplam_soru), anchor="w"
        ).pack(anchor="w")

        detail_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        detail_frame.pack(fill="x", padx=10, pady=(0, 8))

        test_card = ctk.CTkFrame(detail_frame, fg_color="#e8f4fd", corner_radius=8, height=55)
        test_card.pack(side="left", fill="x", expand=True, padx=(0, 5))
        test_card.pack_propagate(False)
        ctk.CTkLabel(test_card, text="Test", font=ctk.CTkFont(size=11, weight="bold"), text_color="#1976d2").pack(pady=(5, 2))
        ctk.CTkLabel(test_card, text=f"K:{detay_bilgisi['test']['kolay']} O:{detay_bilgisi['test']['orta']} Z:{detay_bilgisi['test']['zor']}",
                     font=ctk.CTkFont(size=13), text_color="#1976d2").pack(padx=(0, 5))

        yazili_card = ctk.CTkFrame(detail_frame, fg_color="#f3e5f5", corner_radius=8, height=55)
        yazili_card.pack(side="right", fill="x", expand=True, padx=(5, 0))
        yazili_card.pack_propagate(False)
        ctk.CTkLabel(yazili_card, text="Yazili", font=ctk.CTkFont(size=11, weight="bold"), text_color="#7b1fa2").pack(pady=(5, 2))
        ctk.CTkLabel(yazili_card, text=f"K:{detay_bilgisi['yazili']['kolay']} O:{detay_bilgisi['yazili']['orta']} Z:{detay_bilgisi['yazili']['zor']}",
                      font=ctk.CTkFont(size=13), text_color="#7b1fa2").pack(padx=(0, 5))

        self.checkboxes[konu_adi] = checkbox
        self.topic_items[konu_adi] = item_frame
    
    def calculate_detailed_questions(self, konu_path):
        """Detaylı soru sayılarını hesapla"""
        detay = {'test': {'kolay': 0, 'orta': 0, 'zor': 0}, 'yazili': {'kolay': 0, 'orta': 0, 'zor': 0}}
        try:
            for soru_tipi in ['test', 'yazili']:
                soru_tipi_path = os.path.join(konu_path, soru_tipi)
                if os.path.exists(soru_tipi_path):
                    for zorluk in ['kolay', 'orta', 'zor']:
                        zorluk_path = os.path.join(soru_tipi_path, zorluk)
                        if os.path.exists(zorluk_path):
                            gorseller = [f for f in os.listdir(zorluk_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
                            detay[soru_tipi][zorluk] = len(gorseller)
        except Exception as e:
            logger.warning(f"Detaylı soru hesaplama hatası - {konu_path}: {e}")
        return detay
    
    def get_count_color(self, count):
        """Soru sayısına göre renk"""
        if count == 0: return self.colors['text_secondary']
        elif count < 20: return self.colors['warning']
        elif count < 50: return self.colors['primary']
        else: return self.colors['success']

    def update_item_color(self, frame, var):
        """Öğe rengini güncelle"""
        frame.configure(fg_color=self.colors['selected_bg'] if var.get() else self.colors['hover_bg'])
    
    def create_load_more_button(self):
        """Daha fazla yükle butonu"""
        remaining = len(self.konu_listesi) - 50
        self.load_more_btn = ctk.CTkButton(
            self.scroll_frame, text=f"↓ {remaining} konu daha göster", height=40, corner_radius=10,
            fg_color=self.colors['primary'], hover_color=self.colors['primary_hover'],
            font=ctk.CTkFont(size=13, weight="bold"), command=self.load_more_topics
        )
        self.load_more_btn.pack(pady=15)

    def load_more_topics(self):
        """Daha fazla konu yükle"""
        self.load_more_btn.destroy()
        for konu_info in self.konu_listesi[50:]:
            self.create_topic_item(konu_info)
        info_label = ctk.CTkLabel(self.scroll_frame, text=f"✓ Tüm {len(self.konu_listesi)} konu yüklendi",
                                  font=ctk.CTkFont(size=12), text_color=self.colors['success'])
        info_label.pack(pady=10)
        self.after(3000, lambda: info_label.destroy() if info_label.winfo_exists() else None)

    def create_right_panel_content(self, panel):
        """Sağ panel içeriği"""
        header_frame = ctk.CTkFrame(panel, fg_color=self.colors['primary'], corner_radius=0)
        header_frame.pack(fill="x")
        ctk.CTkLabel(header_frame, text="✅ Seçilen Konular", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                     text_color=self.colors['light']).pack(pady=15)
        
        self.selected_frame = ctk.CTkScrollableFrame(panel, fg_color="transparent", corner_radius=0)
        self.selected_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        bottom_frame = ctk.CTkFrame(panel, fg_color="transparent")
        bottom_frame.pack(fill="x", pady=15)
        
        self.continue_btn = ctk.CTkButton(
            bottom_frame, text="Devam Et →", height=45, corner_radius=10,
            fg_color=self.colors['text_secondary'], hover_color=self.colors['text_primary'],
            font=ctk.CTkFont(size=14, weight="bold"), state="disabled", command=self.devam_et
        )
        self.continue_btn.pack(padx=20)
        self.update_selected_list()

    def update_selected_list(self):
        """Seçilen konular listesini güncelle"""
        for widget in self.selected_frame.winfo_children():
            widget.destroy()
        
        selected = [k for k, v in self.checkbox_vars.items() if v.get()]
        
        if not selected:
            ctk.CTkLabel(self.selected_frame, text="Henüz konu\nseçilmedi", font=ctk.CTkFont(size=13),
                         text_color=self.colors['text_secondary']).pack(expand=True, pady=50)
            self.continue_btn.configure(state="disabled", fg_color=self.colors['text_secondary'])
        else:
            for konu_adi in selected:
                self.create_selected_item(konu_adi)
            self.continue_btn.configure(state="normal", fg_color=self.colors['success'],
                                        hover_color="#05e090", text_color=self.colors['dark'])

    def create_selected_item(self, konu_adi):
        """Seçilen konu öğesi"""
        item_frame = ctk.CTkFrame(self.selected_frame, fg_color=self.colors['hover_bg'], corner_radius=8)
        item_frame.pack(fill="x", pady=3)
        ctk.CTkLabel(item_frame, text=konu_adi, font=ctk.CTkFont(size=12), text_color=self.colors['text_primary']).pack(side="left", padx=(10, 5), pady=8)
        ctk.CTkButton(item_frame, text="×", width=24, height=24, corner_radius=12,
                      fg_color=self.colors['danger'], hover_color="#e0005a", font=ctk.CTkFont(size=18),
                      command=lambda k=konu_adi: self.remove_topic(k)).pack(side="right", padx=5)

    def remove_topic(self, konu_adi):
        """Konuyu seçimden kaldır"""
        if konu_adi in self.checkbox_vars:
            self.checkbox_vars[konu_adi].set(False)
            self.on_checkbox_change(konu_adi)

    def on_checkbox_change(self, konu_adi):
        """Checkbox değişimi"""
        var = self.checkbox_vars[konu_adi]
        if var.get():
            konu_info = next((k for k in self.konu_listesi if k['adi'] == konu_adi), None)
            if konu_info:
                self.secilen_konular[konu_adi] = konu_info['yol']
        elif konu_adi in self.secilen_konular:
            del self.secilen_konular[konu_adi]
        
        if konu_adi in self.topic_items:
            self.update_item_color(self.topic_items[konu_adi], var)
        self.update_selected_list()

    def on_search_keypress(self, event):
        """Arama"""
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(300, self.filter_topics)

    def select_all(self):
        """Tümünü seç"""
        for konu_info in self.konu_listesi:
             if konu_info['adi'] in self.checkbox_vars:
                self.checkbox_vars[konu_info['adi']].set(True)
                self.secilen_konular[konu_info['adi']] = konu_info['yol']
                if konu_info['adi'] in self.topic_items:
                    self.update_item_color(self.topic_items[konu_info['adi']], self.checkbox_vars[konu_info['adi']])
        self.update_selected_list()
        logger.info("Tüm konular seçildi")

    def clear_all(self):
        """Tümünü temizle"""
        for var in self.checkbox_vars.values():
            var.set(False)
        self.secilen_konular.clear()
        for konu_adi, item_frame in self.topic_items.items():
            self.update_item_color(item_frame, self.checkbox_vars[konu_adi])
        self.update_selected_list()
        logger.info("Tüm seçimler temizlendi")

    def show_empty_message(self):
        """Boş liste mesajı"""
        empty_container = ctk.CTkFrame(self.scroll_frame, fg_color=self.colors['hover_bg'], corner_radius=15)
        empty_container.pack(expand=True, fill="both", pady=50, padx=20)
        ctk.CTkLabel(empty_container, text="📭", font=ctk.CTkFont(size=48)).pack(pady=(30, 10))
        ctk.CTkLabel(empty_container, text=f"{self.ders_adi} klasöründe\nkonu başlığı bulunamadı",
                     font=ctk.CTkFont(size=14, weight="bold"), text_color=self.colors['text_primary']).pack(pady=10)
        ctk.CTkLabel(empty_container, text="Lütfen klasör yapısını kontrol edin",
                     font=ctk.CTkFont(size=12), text_color=self.colors['text_secondary']).pack(pady=(0, 30))

    def get_konu_listesi(self):
        """Konu listesini al"""
        konu_listesi = []
        try:
            if not os.path.exists(self.ders_klasor_yolu):
                logger.error(f"Ders klasörü bulunamadı: {self.ders_klasor_yolu}")
                return []
            
            for item in os.listdir(self.ders_klasor_yolu):
                konu_path = os.path.join(self.ders_klasor_yolu, item)
                if os.path.isdir(konu_path):
                    toplam_soru = self.calculate_total_questions(konu_path)
                    konu_listesi.append({'adi': item, 'yol': konu_path, 'toplam_soru': toplam_soru})
            
            konu_listesi.sort(key=lambda x: x['adi'].lower())
            logger.info(f"{len(konu_listesi)} konu başlığı bulundu")
            return konu_listesi
        except Exception as e:
            logger.error(f"Konu listesi alınırken hata: {e}", exc_info=True)
            return []

    def calculate_total_questions(self, konu_path):
        """Toplam soru sayısını hesapla"""
        toplam = 0
        try:
            for soru_tipi in ['test', 'yazili']:
                soru_tipi_path = os.path.join(konu_path, soru_tipi)
                if os.path.exists(soru_tipi_path):
                    for zorluk in ['kolay', 'orta', 'zor']:
                        zorluk_path = os.path.join(soru_tipi_path, zorluk)
                        if os.path.exists(zorluk_path):
                            gorseller = [f for f in os.listdir(zorluk_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
                            toplam += len(gorseller)
        except Exception as e:
            logger.warning(f"Soru sayısı hesaplama hatası - {konu_path}: {e}")
        return toplam

    def devam_et(self):
        """Devam et"""
        if not self.secilen_konular:
            self.show_error("Lütfen en az bir konu seçin!")
            return

        logger.info(f"{len(self.secilen_konular)} konu seçildi, Soru Parametre ekranına geçiliyor.")
        self.controller.show_frame("SoruParametre", ders_adi=self.ders_adi, secilen_konular=self.secilen_konular)
    
    def ana_menuye_don(self):
        """Ana menüye dön"""
        logger.info("Ana menüye dönülüyor.")
        self.controller.ana_menuye_don()

    def ders_sec_sayfasina_don(self):
        """Ders seçim sayfasına dön"""
        logger.info("Ders seçim sayfasına dönülüyor.")
        self.controller.show_frame("UniteSecme")

    def show_error(self, message):
        """Modern hata mesajı"""
        overlay = ctk.CTkFrame(self, fg_color=("#000000", "#1a1a1a"))
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.configure(fg_color=self.colors['dark'])
        overlay.lower(self.main_container)


        
        error_frame = ctk.CTkFrame(overlay, fg_color=self.colors['card_bg'], corner_radius=15, width=400, height=200)
        error_frame.place(relx=0.5, rely=0.5, anchor="center")
        error_frame.pack_propagate(False)
        
        ctk.CTkLabel(error_frame, text="⚠️", font=ctk.CTkFont(size=48), text_color=self.colors['danger']).pack(pady=(30, 15))
        ctk.CTkLabel(error_frame, text=message, font=ctk.CTkFont(size=14), text_color=self.colors['text_primary']).pack(pady=10)
        ctk.CTkButton(error_frame, text="Tamam", width=100, height=35, corner_radius=8,
                      fg_color=self.colors['primary'], hover_color=self.colors['primary_hover'],
                      command=overlay.destroy).pack(pady=(15, 0))
        
        logger.warning(f"Kullanıcıya hata mesajı gösterildi: {message}")