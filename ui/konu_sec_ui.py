import customtkinter as ctk
import tkinter as tk
import os
import sys
from PIL import Image, ImageTk
import math
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont
import logging
from datetime import datetime
from logic.answer_utils import get_answer_for_image
from logic.pdf_generator import PDFCreator

# Modern tema ayarları
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

class KonuSecmePenceresi(ctk.CTkFrame):
    def __init__(self, parent, controller, unite_klasor_yolu, on_questions_selected=None):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.unite_klasor_yolu = unite_klasor_yolu
        self.on_questions_selected = on_questions_selected
        self.secilen_gorseller = []
        
        # Logger'ı kur
        self.logger = self._setup_logger()
        self.logger.info("KonuSecmePenceresi başlatıldı")
        
        # UI'ı oluştur
        self.setup_ui()

    def _setup_logger(self):
        """Logger kurulumu"""
        logger = logging.getLogger('KonuSecmeUI')
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

    def setup_ui(self):
        """Ana UI'ı oluştur"""
        self.logger.debug("UI kurulumu başlatılıyor")
        
        # Ana container
        self.main_frame = ctk.CTkFrame(self, corner_radius=20, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=30, pady=30)

        # Başlık
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="📚 Konu, Zorluk ve Soru Sayısı Seçimi",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#2d3436"
        )
        title_label.pack(pady=(0, 20))

        # Form container
        self.form_frame = ctk.CTkFrame(
            self.main_frame, 
            corner_radius=15, 
            fg_color="#f8f9fa", 
            border_width=1, 
            border_color="#e9ecef"
        )
        self.form_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.create_selection_widgets()
        self.logger.info("UI kurulumu tamamlandı")

    def create_selection_widgets(self):
        """Seçim widget'larını oluştur"""
        self.logger.debug("Seçim widget'ları oluşturuluyor")
        
        # Navigasyon butonları
        nav_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        nav_frame.pack(fill="x", padx=40, pady=(20, 10))

        ana_menu_btn = ctk.CTkButton(
            nav_frame,
            text="🏠 Ana Menü",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=120,
            height=35,
            corner_radius=10,
            fg_color="#6c757d",
            hover_color="#5a6268",
            text_color="#ffffff",
            command=self.ana_menuye_don
        )
        ana_menu_btn.pack(side="left")

        unite_sec_btn = ctk.CTkButton(
            nav_frame,
            text="⬅ Ünite Seçimi",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=120,
            height=35,
            corner_radius=10,
            fg_color="#6c757d",
            hover_color="#5a6268",
            text_color="#ffffff",
            command=self.unite_sec_sayfasina_don
        )
        unite_sec_btn.pack(side="left", padx=(10, 0))

        # Konu Seçimi
        konu_label = ctk.CTkLabel(
            self.form_frame, 
            text="📖 Konu Seçin:",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#495057"
        )
        konu_label.pack(pady=(30, 10), anchor="w", padx=40)

        self.konu_var = tk.StringVar()
        konu_values = self.get_konu_klasorleri()
        self.konu_menu = ctk.CTkComboBox(
            self.form_frame,
            variable=self.konu_var,
            values=konu_values,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            width=400,
            height=40,
            corner_radius=10,
            state="readonly"
        )
        self.konu_menu.set("Konu seçin...")
        self.konu_menu.pack(pady=(0, 20), padx=40)
        
        # Input alanına tıklandığında dropdown'ı açmak için olay bağlama
        self.konu_menu._entry.bind("<Button-1>", lambda e: self.konu_menu._open_dropdown_menu())

        # Soru Tipi Seçimi
        tip_label = ctk.CTkLabel(
            self.form_frame, 
            text="📝 Soru Tipi:",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#495057"
        )
        tip_label.pack(pady=(10, 10), anchor="w", padx=40)

        self.soru_tipi_var = tk.StringVar()
        self.soru_tipi_menu = ctk.CTkComboBox(
            self.form_frame,
            variable=self.soru_tipi_var,
            values=["Test", "Yazili"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            width=400,
            height=40,
            corner_radius=10,
            state="readonly"
        )
        self.soru_tipi_menu.set("Soru tipi seçin...")
        self.soru_tipi_menu.pack(pady=(0, 20), padx=40)

        # Input alanına tıklandığında dropdown'ı açmak için olay bağlama
        self.soru_tipi_menu._entry.bind("<Button-1>", lambda e: self.soru_tipi_menu._open_dropdown_menu())

        # Zorluk Seçimi
        zorluk_label = ctk.CTkLabel(
            self.form_frame, 
            text="⚡ Zorluk Seviyesi:",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#495057"
        )
        zorluk_label.pack(pady=(10, 10), anchor="w", padx=40)

        self.zorluk_var = tk.StringVar()
        self.zorluk_menu = ctk.CTkComboBox(
            self.form_frame,
            variable=self.zorluk_var,
            values=["Kolay", "Orta", "Zor"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            width=400,
            height=40,
            corner_radius=10,
            state="readonly"
        )
        self.zorluk_menu.set("Zorluk seviyesi seçin...")
        self.zorluk_menu.pack(pady=(0, 20), padx=40)
        
        # Input alanına tıklandığında dropdown'ı açmak için olay bağlama
        self.zorluk_menu._entry.bind("<Button-1>", lambda e: self.zorluk_menu._open_dropdown_menu())

        # Soru Sayısı Seçimi
        soru_label = ctk.CTkLabel(
            self.form_frame, 
            text="🔢 Soru Sayısı:",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#495057"
        )
        soru_label.pack(pady=(10, 10), anchor="w", padx=40)

        self.soru_sayisi_var = tk.StringVar()
    
        # Giriş alanı ve spin butonları için frame
        soru_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        soru_frame.pack(pady=(0, 30), padx=40, fill="x")

        # Giriş alanı
        self.soru_entry = ctk.CTkEntry(
            soru_frame,
            textvariable=self.soru_sayisi_var,
            font=ctk.CTkFont(family="Segoe UI", size=14),
            width=100,
            height=40,
            corner_radius=10,
            placeholder_text="Sayı girin..."
        )
        self.soru_entry.pack(side="left")

        # Hızlı seçim butonları
        for num in [1, 2, 3, 5, 10]:
            btn = ctk.CTkButton(
                soru_frame,
                text=str(num),
                width=40,
                height=35,
                corner_radius=8,
                fg_color="#6c757d",
                hover_color="#5a6268",
                command=lambda n=num: self._set_soru_sayisi(n)
            )
            btn.pack(side="left", padx=(10, 0))

        # Devam Et butonu
        devam_btn = ctk.CTkButton(
            self.form_frame,
            text="✅ Devam Et",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            width=150,
            height=45,
            corner_radius=12,
            fg_color="#28a745",
            hover_color="#218838",
            text_color="#ffffff",
            command=self.devam_et
        )
        devam_btn.pack(pady=(0, 30))

    def _set_soru_sayisi(self, num):
        """Soru sayısını ayarla ve log kaydet"""
        self.soru_sayisi_var.set(str(num))
        self.logger.debug(f"Soru sayısı {num} olarak ayarlandı")

    def get_konu_klasorleri(self):
        """Konu klasörlerini al"""
        try:
            self.logger.debug(f"Konu klasörleri alınıyor: {self.unite_klasor_yolu}")
            klasorler = [d for d in os.listdir(self.unite_klasor_yolu) 
                        if os.path.isdir(os.path.join(self.unite_klasor_yolu, d))]
            
            if klasorler:
                self.logger.info(f"{len(klasorler)} konu klasörü bulundu")
                return klasorler
            else:
                self.logger.warning("Hiç konu klasörü bulunamadı")
                return ["(Klasör boş)"]
        except Exception as e:
            self.logger.error(f"Konu klasörleri alma hatası: {e}")
            return ["(Hata oluştu)"]

    def ana_menuye_don(self):
        """Ana menüye dön"""
        self.logger.info("Ana menüye dönülüyor")
        self.controller.ana_menuye_don()

    def unite_sec_sayfasina_don(self):
        """Ünite seçim sayfasına dön"""
        self.logger.info("Ünite seçim sayfasına dönülüyor")
        self.controller.show_frame("UniteSecme")

    def devam_et(self):
        """Seçimleri doğrula ve önizleme ekranını göster"""
        self.logger.info("Devam et butonuna tıklandı")
        
        # Seçimleri al
        secilen_konu = self.konu_var.get()
        soru_tipi = self.soru_tipi_var.get()
        zorluk = self.zorluk_var.get()

        self.logger.debug(f"Seçimler - Konu: {secilen_konu}, Tip: {soru_tipi}, Zorluk: {zorluk}")

        # Validasyon
        if any("seçin" in var.get().lower() for var in [self.konu_var, self.soru_tipi_var, self.zorluk_var]):
            self.logger.warning("Eksik seçim tespit edildi")
            self.show_error("Lütfen konu, soru tipi ve zorluk seviyesini seçin!")
            return
            
        # Soru sayısı validasyonu
        try:
            soru_sayisi = int(self.soru_sayisi_var.get())
            if soru_sayisi <= 0:
                raise ValueError
            self.logger.debug(f"Soru sayısı validasyonu başarılı: {soru_sayisi}")
        except (ValueError, AttributeError):
            self.logger.warning("Geçersiz soru sayısı girişi")
            self.show_error("Lütfen geçerli bir soru sayısı girin!")
            return

        # Seçilen klasör yolunu oluştur
        secilen_konu_path = os.path.join(self.unite_klasor_yolu, secilen_konu, soru_tipi.lower(), zorluk.lower())
        self.logger.debug(f"Klasör yolu: {secilen_konu_path}")

        # Klasördeki maksimum soru sayısını kontrol et
        try:
            gorseller = [f for f in os.listdir(secilen_konu_path) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            max_soru = len(gorseller)
            
            self.logger.info(f"Klasörde {max_soru} görsel bulundu")

            if soru_sayisi > max_soru:
                self.logger.warning(f"İstenen soru sayısı ({soru_sayisi}) mevcut soruları ({max_soru}) aşıyor")
                self.show_error(f"Seçtiğiniz zorluk seviyesinde sadece {max_soru} soru bulunuyor!")
                return
            # Yazılı için bilgilendirme
            if soru_tipi.lower() == "yazili" and soru_sayisi > 2:
                self.logger.info("Yazılı için çoklu sayfa bilgilendirmesi gösteriliyor")
                self.show_multipage_info(soru_sayisi)

        except Exception as e:
            self.logger.error(f"Klasör okuma hatası: {e}")
            self.show_error("Seçilen klasörde görsel bulunamadı!")
            return

        # Rastgele görselleri seç
        self.secilen_gorseller = self.rastgele_gorseller_sec(secilen_konu_path, soru_sayisi)

        if self.secilen_gorseller:
            self.logger.info(f"{len(self.secilen_gorseller)} görsel seçildi, önizleme ekranı açılıyor")
            self.gorsel_onizleme_alani_olustur()
        else:
            self.logger.error("Hiç görsel seçilemedi")
            self.show_error("Seçilen klasörde görsel bulunamadı!")
  
    def rastgele_gorseller_sec(self, klasor_yolu, adet):
        """Belirtilen klasörden rastgele görsel seç"""
        try:
            self.logger.debug(f"Rastgele görsel seçimi başlatılıyor - Yol: {klasor_yolu}, Adet: {adet}")
            
            if not os.path.exists(klasor_yolu):
                self.logger.error(f"Klasör bulunamadı: {klasor_yolu}")
                return []
                
            gorseller = [f for f in os.listdir(klasor_yolu) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            
            if not gorseller:
                self.logger.warning("Klasörde uygun görsel bulunamadı")
                return []

            import random
            if len(gorseller) <= adet:
                secilen = [os.path.join(klasor_yolu, f) for f in gorseller]
                self.logger.info(f"Tüm görseller seçildi ({len(secilen)} adet)")
            else:
                secilen = [os.path.join(klasor_yolu, f) 
                          for f in random.sample(gorseller, adet)]
                self.logger.info(f"Rastgele {adet} görsel seçildi")
            
            return secilen
        except Exception as e:
            self.logger.error(f"Görsel seçme hatası: {e}")
            return []

    def gorsel_onizleme_alani_olustur(self):
        """Görsel önizleme alanını oluştur"""
        self.logger.info("Önizleme alanı oluşturuluyor")
        
        # Form içeriğini temizle
        for widget in self.form_frame.winfo_children():
            widget.destroy()

        # Seçim bilgilerini al
        secilen_konu = self.konu_var.get()
        zorluk = self.zorluk_var.get()
        
        # Başlık
        onizleme_label = ctk.CTkLabel(
            self.form_frame, 
            text="📷 Seçilen Soruların Önizlemesi",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#495057"
        )
        onizleme_label.pack(pady=(20, 10))

        # Bilgi etiketi
        info_label = ctk.CTkLabel(
            self.form_frame,
            text=f"📚 {secilen_konu} | 📝 {self.soru_tipi_var.get()} | ⚡ {zorluk} | 🔢 {len(self.secilen_gorseller)} soru",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#6c757d"
        )
        info_label.pack(pady=(0, 15))

        # Scrollable frame
        scrollable_frame = ctk.CTkScrollableFrame(
            self.form_frame,
            fg_color="#ffffff",
            corner_radius=10
        )
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Görselleri göster
        self.display_images(scrollable_frame)

        # Butonlar
        button_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        button_frame.pack(pady=20)

        # PDF oluştur butonu
        pdf_btn = ctk.CTkButton(
            button_frame,
            text="📄 PDF Oluştur",
            command=lambda: self.pdf_olustur(secilen_konu, self.soru_tipi_var.get(), zorluk),
            font=ctk.CTkFont(size=16, weight="bold"),
            width=200,
            height=45,
            fg_color="#28a745",
            hover_color="#218838"
        )
        pdf_btn.pack(side="left", padx=10)

        # Geri butonu
        back_btn = ctk.CTkButton(
            button_frame,
            text="⬅ Geri",
            command=self.geri_don,
            font=ctk.CTkFont(size=16, weight="bold"),
            width=120,
            height=45,
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        back_btn.pack(side="left", padx=10)

    def gorseli_kaldir(self, index, parent_frame):
        """Seçilen görseli listeden kaldır ve önizlemeyi güncelle"""
        try:
            # Görseli listeden kaldır
            if 0 <= index < len(self.secilen_gorseller):
                kaldirilan_gorsel = self.secilen_gorseller.pop(index)
                self.logger.info(f"Görsel kaldırıldı: {os.path.basename(kaldirilan_gorsel)} (İndex: {index})")

                # Eğer hiç görsel kalmadıysa uyarı göster
                if not self.secilen_gorseller:
                    self.logger.warning("Tüm görseller kaldırıldı")
                    self.show_notification(
                        "⚠️ Uyarı",
                        "Tüm görseller kaldırıldı!\nYeni seçim yapmak için 'Geri' butonuna tıklayın.",
                        geri_don=False 
                    )
                    return

                # Önizlemeyi güncelle
                for widget in parent_frame.winfo_children():
                    widget.destroy()

                # Sayfa kontrolü yap
                sorular_per_sayfa = self._get_sorular_per_sayfa()
                toplam_sayfa = math.ceil(len(self.secilen_gorseller) / sorular_per_sayfa)
                if hasattr(self, 'current_page') and self.current_page >= toplam_sayfa:
                    self.current_page = max(0, toplam_sayfa - 1)

                self.display_images(parent_frame)
                self.guncelle_bilgi_etiketi()

        except Exception as e:
            self.logger.error(f"Görsel kaldırma hatası: {e}")
            self.show_error("Görsel kaldırılırken bir hata oluştu!")

    def gorseli_guncelle(self, index, parent_frame):
        """Seçilen görseli güncelle"""
        try:
            self.logger.debug(f"Görsel güncelleniyor: İndex {index}")
            
            if 0 <= index < len(self.secilen_gorseller):
                # Mevcut klasör yolunu al
                secilen_konu = self.konu_var.get()
                soru_tipi = self.soru_tipi_var.get()
                zorluk = self.zorluk_var.get()
                klasor_yolu = os.path.join(self.unite_klasor_yolu, secilen_konu, soru_tipi.lower(), zorluk.lower())

                # Klasördeki tüm görselleri al
                tum_gorseller = [f for f in os.listdir(klasor_yolu) 
                               if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]

                if not tum_gorseller:
                    self.logger.warning("Güncellenecek görsel bulunamadı")
                    self.show_error("Güncellenecek görsel bulunamadı!")
                    return

                # Mevcut seçili görsellerin dosya adlarını al
                secili_gorsel_adlari = [os.path.basename(g) for g in self.secilen_gorseller]

                # Kullanılabilir görseller (seçili olmayanlar)
                kullanilabilir_gorseller = [
                    os.path.join(klasor_yolu, f) for f in tum_gorseller 
                    if f not in secili_gorsel_adlari
                ]

                if not kullanilabilir_gorseller:
                    self.logger.warning("Güncellenecek başka görsel kalmadı")
                    self.show_error("Güncellenecek başka görsel kalmadı!")
                    return

                # Rastgele yeni bir görsel seç
                import random
                eski_gorsel = os.path.basename(self.secilen_gorseller[index])
                yeni_gorsel = random.choice(kullanilabilir_gorseller)
                yeni_gorsel_ad = os.path.basename(yeni_gorsel)

                # Görseli güncelle
                self.secilen_gorseller[index] = yeni_gorsel
                self.logger.info(f"Görsel güncellendi: {eski_gorsel} -> {yeni_gorsel_ad}")

                # Önizlemeyi yenile
                for widget in parent_frame.winfo_children():
                    widget.destroy()

                self.display_images(parent_frame)

        except Exception as e:
            self.logger.error(f"Görsel güncelleme hatası: {e}")
            self.show_error("Görsel güncellerken bir hata oluştu!")

    def guncelle_bilgi_etiketi(self):
        """Bilgi etiketindeki soru sayısını güncelle"""
        try:
            # form_frame'deki ikinci widget'ı bul (info_label)
            widgets = self.form_frame.winfo_children()
            if len(widgets) >= 2:
                info_widget = widgets[1]  # İkinci widget bilgi etiketi olmalı
                if hasattr(info_widget, 'configure'):
                    secilen_konu = self.konu_var.get()
                    soru_tipi = self.soru_tipi_var.get()
                    zorluk = self.zorluk_var.get()
                    info_widget.configure(
                        text=f"📚 {secilen_konu} | 📝 {soru_tipi} | ⚡ {zorluk} | 🔢 {len(self.secilen_gorseller)} soru"
                    )
                    self.logger.debug("Bilgi etiketi güncellendi")
        except Exception as e:
            self.logger.error(f"Bilgi etiketi güncelleme hatası: {e}")

    def _get_sorular_per_sayfa(self):
        """Soru tipine göre sayfa başı soru sayısını döndür"""
        soru_tipi = self.soru_tipi_var.get().lower()
        return 2 if soru_tipi == "yazili" else 8

    def display_images(self, parent_frame):
        """Görselleri sayfa sayfa PDF şablonunda göster"""
        self.logger.debug("Görseller display edilmeye başlanıyor")
        
        # Soru tipine göre sayfa başı soru sayısı
        sorular_per_sayfa = self._get_sorular_per_sayfa()
        toplam_sayfa = math.ceil(len(self.secilen_gorseller) / sorular_per_sayfa)
        
        self.logger.debug(f"Sayfa başı soru: {sorular_per_sayfa}, Toplam sayfa: {toplam_sayfa}")
 
        if not hasattr(self, 'current_page'):
            self.current_page = 0
 
        # Sayfa navigasyon butonları
        nav_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        nav_frame.pack(pady=10, fill="x")
 
        if toplam_sayfa > 1:
            # Önceki sayfa butonu
            if self.current_page > 0:
                prev_btn = ctk.CTkButton(
                    nav_frame,
                    text="⬅ Önceki Sayfa",
                    command=lambda: self.change_page(parent_frame, -1),
                    width=120
                )
                prev_btn.pack(side="left", padx=10)
 
            # Sayfa bilgisi
            page_info = ctk.CTkLabel(
                nav_frame,
                text=f"Sayfa {self.current_page + 1} / {toplam_sayfa}",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            page_info.pack(side="left", padx=20)
 
            # Sonraki sayfa butonu
            if self.current_page < toplam_sayfa - 1:
                next_btn = ctk.CTkButton(
                    nav_frame,
                    text="Sonraki Sayfa ➡",
                    command=lambda: self.change_page(parent_frame, 1),
                    width=120
                )
                next_btn.pack(side="left", padx=10)
 
        # Mevcut sayfa için görselleri al
        start_idx = self.current_page * sorular_per_sayfa
        end_idx = min(start_idx + sorular_per_sayfa, len(self.secilen_gorseller))
        sayfa_gorselleri = self.secilen_gorseller[start_idx:end_idx]

        # DEBUG ekleyin:
        print(f"DEBUG - Önizleme sayfa {self.current_page + 1}:")
        for i, gorsel in enumerate(sayfa_gorselleri):
            print(f"  {i}: {os.path.basename(gorsel)}")
        
        # Logger ile de aynı bilgiyi loglayın
        self.logger.debug(f"Sayfa {self.current_page + 1} için {len(sayfa_gorselleri)} görsel gösteriliyor")
 
        # PDF sayfası önizlemesi oluştur
        pdf_preview = self.create_page_preview(sayfa_gorselleri, start_idx)
 
        if pdf_preview:
            # Ana container - PDF ve butonları yan yana yerleştirmek için
            main_container = ctk.CTkFrame(parent_frame, fg_color="transparent")
            main_container.pack(pady=20, padx=10, fill="both", expand=True)
 
            # PDF önizleme container (sol taraf)
            preview_container = ctk.CTkFrame(main_container, fg_color="#d1d1d1", corner_radius=10)
            preview_container.pack(side="left", fill="both", expand=True, padx=(0, 10))
 
            # PDF görselini göster
            pdf_label = tk.Label(
                preview_container,
                image=pdf_preview,
                bg="#d1d1d1"
            )
            pdf_label.image = pdf_preview  # Referansı koru
            pdf_label.pack(pady=20)
 
            # Butonlar container (sağ taraf)
            buttons_container = ctk.CTkFrame(main_container, fg_color="#f8f9fa", corner_radius=10, width=250)
            buttons_container.pack(side="right", fill="y", padx=(10, 0))
            buttons_container.pack_propagate(False)  # Sabit genişlik için
 
            # Her soru için butonlar
            self.create_question_buttons_vertical(buttons_container, sayfa_gorselleri, start_idx, parent_frame)
        else:
            self.logger.error("PDF önizlemesi oluşturulamadı")
    
    def change_page(self, parent_frame, direction):
        """Sayfa değiştir"""
        sorular_per_sayfa = self._get_sorular_per_sayfa()
        toplam_sayfa = math.ceil(len(self.secilen_gorseller) / sorular_per_sayfa)

        new_page = self.current_page + direction
        if 0 <= new_page < toplam_sayfa:
            old_page = self.current_page
            self.current_page = new_page
            self.logger.debug(f"Sayfa değiştirildi: {old_page + 1} -> {new_page + 1}")

            # Sayfayı yenile
            for widget in parent_frame.winfo_children():
                widget.destroy()

            self.display_images(parent_frame)

    def create_question_buttons_vertical(self, parent_container, sayfa_gorselleri, start_idx, main_parent_frame):
        """Soruların yanında dikey olarak butonlar oluştur"""
        self.logger.debug(f"{len(sayfa_gorselleri)} soru için butonlar oluşturuluyor")
        
        # Başlık
        title_label = ctk.CTkLabel(
            parent_container,
            text="🔧 Soru İşlemleri",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#495057"
        )
        title_label.pack(pady=(20, 10))

        # Scrollable frame butonlar için
        scrollable_buttons = ctk.CTkScrollableFrame(
            parent_container,
            fg_color="transparent",
            corner_radius=0
        )
        scrollable_buttons.pack(fill="both", expand=True, padx=10, pady=(0, 20))

        # Her soru için buton grubu
        for i, gorsel_path in enumerate(sayfa_gorselleri):
            # Her soru için frame
            question_frame = ctk.CTkFrame(scrollable_buttons, fg_color="#ffffff", corner_radius=8)
            question_frame.pack(fill="x", pady=5, padx=5)

            # Soru numarası ve bilgisi
            soru_no = start_idx + i + 1
            try:
                cevap = get_answer_for_image(gorsel_path)
                self.logger.debug(f"Soru {soru_no} cevabı alındı: {cevap}")
            except Exception as e:
                cevap = "?"
                self.logger.warning(f"Soru {soru_no} cevabı alınamadı: {e}")

            # Soru bilgisi
            info_label = ctk.CTkLabel(
                question_frame,
                text=f"Soru {soru_no}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#2c3e50"
            )
            info_label.pack(pady=(10, 5))

            # Cevap bilgisi
            answer_label = ctk.CTkLabel(
                question_frame,
                text=f"Cevap: {cevap}",
                font=ctk.CTkFont(size=12),
                text_color="#7f8c8d"
            )
            answer_label.pack(pady=(0, 10))

            # Butonlar için frame
            btn_frame = ctk.CTkFrame(question_frame, fg_color="transparent")
            btn_frame.pack(pady=(0, 10))

            # Güncelle butonu
            update_btn = ctk.CTkButton(
                btn_frame,
                text="🔄 Güncelle",
                width=80, height=30,
                font=ctk.CTkFont(size=11),
                fg_color="#3498db",
                hover_color="#2980b9",
                command=lambda idx=start_idx+i: self.gorseli_guncelle(idx, main_parent_frame)
            )
            update_btn.pack(side="left", padx=(0, 5))

            # Sil butonu
            remove_btn = ctk.CTkButton(
                btn_frame,
                text="🗑️ Sil",
                width=60, height=30,
                font=ctk.CTkFont(size=11),
                fg_color="#e74c3c",
                hover_color="#c0392b",
                command=lambda idx=start_idx+i: self.gorseli_kaldir(idx, main_parent_frame)
            )
            remove_btn.pack(side="left", padx=(5, 0))

    def create_page_preview(self, sayfa_gorselleri, start_idx):
        """Bir sayfa için PDF önizlemesi oluştur"""
        self.logger.debug(f"Sayfa önizlemesi oluşturuluyor - {len(sayfa_gorselleri)} görsel")

        try:
            # Soru tipine göre şablon seç
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            soru_tipi = self.soru_tipi_var.get().lower()
            self.logger.debug(f"Şablon seçimi - Soru tipi: {soru_tipi}")

            if soru_tipi == "test":
                template_name = "template.png"
            elif soru_tipi == "yazili":
                template_name = "template2.png"
            else:
                template_name = "template.png"

            template_path = os.path.join(current_dir, "templates", template_name)

            if not os.path.exists(template_path):
                self.logger.error(f"Şablon bulunamadı: {template_path}")
                return None

            # Şablonu aç
            template = Image.open(template_path).convert("RGB")
            template_copy = template.copy()
            self.logger.debug(f"Şablon yüklendi - Boyut: {template_copy.size}")

            # Soru tipine göre layout hesapla
            template_width, template_height = template_copy.size

            if soru_tipi == "yazili":
                self._create_yazili_preview(template_copy, sayfa_gorselleri, start_idx, template_width, template_height)
            else:
                self._create_test_preview(template_copy, sayfa_gorselleri, start_idx, template_width, template_height)

            # Önizleme için boyutlandır (oranı koru)
            preview_width = 600
            preview_height = int(2000 * preview_width / 1414)
            template_copy = template_copy.resize((preview_width, preview_height), Image.Resampling.LANCZOS)

            self.logger.debug("Sayfa önizlemesi başarıyla oluşturuldu")
            return ImageTk.PhotoImage(template_copy)

        except Exception as e:
            self.logger.error(f"Sayfa önizleme hatası: {e}")
            return None

    def _create_yazili_preview(self, template_copy, sayfa_gorselleri, start_idx, template_width, template_height):
        """Yazılı şablonu önizleme layout'u"""
        self.logger.debug("Yazılı önizleme layout'u uygulanıyor")
        
        # Yazılı için dikey layout (1 sütun)
        top_margin = int(template_height * 0.1)
        left_margin = int(template_width * 0.05)
        right_margin = int(template_width * 0.05)
        bottom_margin = int(template_height * 0.05)

        # Kullanılabilir alan
        usable_width = template_width - left_margin - right_margin
        usable_height = template_height - top_margin - bottom_margin

        # Her soru için alan - soru + cevap alanı
        soru_ve_cevap_yuksekligi = usable_height // 3

        # Soru görseli için alan
        yazili_soru_height = int(soru_ve_cevap_yuksekligi * 0.6)
        yazili_soru_width = usable_width  # Tam genişlik

        self.logger.debug(f"Yazılı layout boyutları - Genişlik: {yazili_soru_width}, Yükseklik: {yazili_soru_height}")

        # Görselleri yerleştir
        for i, gorsel_path in enumerate(sayfa_gorselleri):
            if i >= 2:  # Yazılı için maksimum 3 soru
                self.logger.warning(f"Yazılı önizlemede maksimum 3 soru gösterilebilir, {len(sayfa_gorselleri)} soru var")
                break
                
            try:
                # Yazılı için dikey düzen
                x = left_margin
                y = top_margin + i * soru_ve_cevap_yuksekligi

                # Soruyu aç ve boyutlandır
                soru_img = Image.open(gorsel_path)

                # Yazılı için tam genişlik
                new_width = yazili_soru_width
                img_ratio = soru_img.width / soru_img.height
                new_height = int(yazili_soru_width / img_ratio)

                if new_height > yazili_soru_height:
                    new_height = yazili_soru_height

                soru_img = soru_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                template_copy.paste(soru_img, (x, y))

                # Soru numarası ekle
                draw = ImageDraw.Draw(template_copy)
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                except:
                    font = ImageFont.load_default()

                soru_no = start_idx + i + 1
                draw.text((x + 15, y + 30), f"{soru_no}.", fill="black", font=font)
                
                self.logger.debug(f"Yazılı soru {soru_no} yerleştirildi - Boyut: {new_width}x{new_height}")

            except Exception as e:
                self.logger.error(f"Yazılı soru {i+1} yerleştirme hatası: {e}")

    def _create_test_preview(self, template_copy, sayfa_gorselleri, start_idx, template_width, template_height):
        """Test şablonu önizleme layout'u"""
        self.logger.debug("Test önizleme layout'u uygulanıyor")
        
        # Test için 2x4 grid
        top_margin = 150
        left_margin = 50
        right_margin = 50
        bottom_margin = 100

        usable_width = template_width - left_margin - right_margin
        usable_height = template_height - top_margin - bottom_margin

        test_soru_width = usable_width // 2 - 20
        test_soru_height = usable_height // 4 - 40
        
        self.logger.debug(f"Test layout boyutları - Genişlik: {test_soru_width}, Yükseklik: {test_soru_height}")

        # Görselleri yerleştir
        for i, gorsel_path in enumerate(sayfa_gorselleri):
            if i >= 8:  # Test için maksimum 8 soru
                self.logger.warning(f"Test önizlemede maksimum 8 soru gösterilebilir, {len(sayfa_gorselleri)} soru var")
                break
                
            try:
                # Test için 2x4 grid
                row = i % 4
                col = i // 4

                x = left_margin + col * (test_soru_width + 20)
                y = top_margin + row * (test_soru_height + 40)

                # Soruyu aç ve boyutlandır
                soru_img = Image.open(gorsel_path)

                # Test için eski mantık
                soru_img.thumbnail((test_soru_width, test_soru_height), Image.Resampling.LANCZOS)
                img_w, img_h = soru_img.size
                paste_x = x + (test_soru_width - img_w) // 2
                paste_y = y + (test_soru_height - img_h) // 2

                template_copy.paste(soru_img, (paste_x, paste_y))

                # Soru numarası ekle
                draw = ImageDraw.Draw(template_copy)
                try:
                    font = ImageFont.truetype("arial.ttf", 20)
                except:
                    font = ImageFont.load_default()

                soru_no = start_idx + i + 1
                draw.text((x + 15, y + 30), f"{soru_no}.", fill="black", font=font)
                
                self.logger.debug(f"Test soru {soru_no} yerleştirildi - Grid: ({row+1},{col+1})")

            except Exception as e:
                self.logger.error(f"Test soru {i+1} yerleştirme hatası: {e}")

    def geri_don(self):
        """Konu seçim ekranına geri dön"""
        try:
            self.logger.info("Geri dön butonuna tıklandı")
            
            # Form içeriğini temizle ve seçim widget'larını yeniden oluştur
            for widget in self.form_frame.winfo_children():
                widget.destroy()

            self.create_selection_widgets()
            self.logger.debug("Seçim ekranına geri dönüldü")

        except Exception as e:
            self.logger.error(f"Geri dönüş hatası: {e}")
            # Hata durumunda ünite seçimine dön
            self.unite_sec_sayfasina_don()

    def pdf_olustur(self, konu, soru_tipi, zorluk):
        """PDF oluştur ve kullanıcıya bildir"""
        self.logger.info(f"PDF oluşturma başlatıldı - {konu}, {soru_tipi}, {zorluk}")
        
        try:
            # Reportlab modülü kontrolü
            try:
                import reportlab
                self.logger.debug("Reportlab modülü mevcut")
            except ImportError:
                self.logger.error("Reportlab modülü bulunamadı")
                self.show_notification(
                    "❌ Eksik Modül",
                    "📦 PDF oluşturmak için 'reportlab' modülü gerekli.\n\n"
                    "💡 Çözüm: Terminal'e şunu yazın:\n"
                    "pip install reportlab"
                )
                return

            # PDF generator kontrolü
            try:
                self.logger.debug("PDFCreator import edildi")
            except ImportError as e:
                self.logger.error(f"PDFCreator import hatası: {e}")
                self.basit_pdf_olustur(konu, soru_tipi, zorluk)
                return

            # Cevap bilgisini alma
            try:
                cevap_bilgisi_mevcut = True
                self.logger.debug("Cevap bilgisi modülü mevcut")
            except ImportError:
                cevap_bilgisi_mevcut = False
                self.logger.warning("Cevap bilgisi modülü bulunamadı")

            # PDF oluştur
            pdf = PDFCreator()
            pdf.soru_tipi = soru_tipi
            pdf.baslik_ekle(f"{konu} - {soru_tipi} - {zorluk} Seviyesi")

            self.logger.debug(f"PDF'e geçen soru tipi: {soru_tipi}")

            # Görselleri ve cevapları ekle
            cevaplar = []
            for idx, gorsel in enumerate(self.secilen_gorseller, 1):
                try:
                    if cevap_bilgisi_mevcut:
                        cevap = get_answer_for_image(gorsel)
                        cevaplar.append(cevap)
                    pdf.gorsel_ekle(gorsel)
                    self.logger.debug(f"Görsel {idx} PDF'e eklendi")
                except Exception as e:
                    self.logger.error(f"Görsel {idx} ekleme hatası: {e}")

            # Cevap anahtarını ekle
            if cevap_bilgisi_mevcut and cevaplar:
                pdf.cevap_anahtari_ekle(cevaplar)
                self.logger.debug(f"{len(cevaplar)} cevap anahtarı eklendi")

            # Kaydetme konumu sor
            cikti_dosya = filedialog.asksaveasfilename(
                title="PDF'i Nereye Kaydetmek İstersiniz?",
                defaultextension=".pdf",
                filetypes=[("PDF Dosyası", "*.pdf")],
                initialfile=f"{konu}_{soru_tipi}_{zorluk}_{len(self.secilen_gorseller)}_soru.pdf"
            )

            if cikti_dosya:
                self.logger.info(f"PDF kaydediliyor: {cikti_dosya}")
                
                if pdf.kaydet(cikti_dosya):
                    kayit_yeri = f"{os.path.basename(os.path.dirname(cikti_dosya))}/{os.path.basename(cikti_dosya)}"
                    
                    self.logger.info(f"PDF başarıyla oluşturuldu: {os.path.basename(cikti_dosya)}")
                    
                    # Başarılı bildirimi
                    self.show_notification(
                        "✅ PDF Başarıyla Oluşturuldu!",
                        f"📁 Kayıt Yeri: {kayit_yeri}\n\n"
                        f"✨ {len(self.secilen_gorseller)} soru PDF formatında kaydedildi"
                    )
                else:
                    self.logger.error("PDF kaydedilemedi")
                    self.show_notification(
                        "❌ PDF Oluşturulamadı",
                        "📄 PDF oluşturulurken bir hata oluştu.\n"
                        "Lütfen tekrar deneyin."
                    )
            else:
                self.logger.info("Kullanıcı PDF kaydetmeyi iptal etti")

        except Exception as e:
            self.logger.error(f"PDF oluşturma genel hatası: {e}")
            self.show_notification(
                "❌ Hata",
                f"Beklenmeyen bir hata oluştu:\n{str(e)}\n\nLütfen konsolu kontrol edin."
            )

    def basit_pdf_olustur(self, konu, soru_tipi, zorluk):
        """Basit PDF oluşturma - PDFCreator sınıfı import edilemediğinde"""
        self.logger.warning("Basit PDF oluşturma moduna geçildi")
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.lib import colors

            # Cevap bilgisini alma
            try:
                cevap_bilgisi_mevcut = True
            except ImportError:
                cevap_bilgisi_mevcut = False
                self.logger.warning("Basit PDF - Cevap bilgisi modülü bulunamadı")

            # Kaydetme konumu sor
            cikti_dosya = filedialog.asksaveasfilename(
                title="PDF'i Nereye Kaydetmek İstersiniz?",
                defaultextension=".pdf",
                filetypes=[("PDF Dosyası", "*.pdf")],
                initialfile=f"{konu}_{soru_tipi}_{zorluk}_{len(self.secilen_gorseller)}_soru.pdf"
            )

            if not cikti_dosya:
                self.logger.info("Basit PDF kaydetme iptal edildi")
                return

            # PDF oluştur
            story = []
            styles = getSampleStyleSheet()

            # Başlık ekle
            baslik = Paragraph(f"{konu} - {soru_tipi} - {zorluk} Seviyesi", styles["Title"])
            story.append(baslik)
            story.append(Spacer(1, 0.5*inch))

            # Görselleri ve cevapları ekle
            cevaplar = []
            for gorsel_yolu in self.secilen_gorseller:
                try:
                    img = Image(gorsel_yolu, width=6*inch, height=4*inch)
                    story.append(img)

                    # Cevap bilgisini ekle
                    if cevap_bilgisi_mevcut:
                        try:
                            cevap = get_answer_for_image(gorsel_yolu)
                            cevaplar.append(cevap)
                            cevap_stili = styles["Normal"]
                            cevap_stili.alignment = 1  # Ortalama
                            cevap_paragraf = Paragraph(f"Cevap: {cevap}", cevap_stili)
                            story.append(cevap_paragraf)
                        except Exception as e:
                            self.logger.error(f"Basit PDF cevap alma hatası: {e}")

                    story.append(Spacer(1, 0.3*inch))
                except Exception as e:
                    self.logger.error(f"Basit PDF görsel ekleme hatası: {e}")

            # Cevap anahtarını ekle
            if cevap_bilgisi_mevcut and cevaplar:
                story.append(Spacer(1, 0.5*inch))
                story.append(Paragraph("CEVAP ANAHTARI", styles["Heading1"]))
                story.append(Spacer(1, 0.2*inch))

                # Cevapları tablo formatında göster
                data = []
                for i, cevap in enumerate(cevaplar, 1):
                    data.append([f"{i}. Soru", cevap])

                tablo = Table(data, colWidths=[1*inch, 1*inch])
                tablo.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))

                story.append(tablo)

            # PDF'i kaydet
            doc = SimpleDocTemplate(cikti_dosya, pagesize=letter)
            doc.build(story)

            self.logger.info(f"Basit PDF başarıyla oluşturuldu: {os.path.basename(cikti_dosya)}")

            self.show_notification(
                "✅ PDF Başarıyla Oluşturuldu!",
                f"📁 Kayıt Yeri: {os.path.basename(cikti_dosya)}\n\n"
                f"✨ {len(self.secilen_gorseller)} soru PDF formatında kaydedildi"
            )

        except Exception as e:
            self.logger.error(f"Basit PDF oluşturma hatası: {e}")
            self.show_notification(
                "❌ Hata",
                f"PDF oluşturulurken hata: {str(e)}"
            )

    def show_error(self, message):
        """Hata mesajını göster"""
        self.logger.warning(f"Hata mesajı gösteriliyor: {message}")
        self._show_dialog("⚠️ Uyarı", message, "#dc3545")

    def show_notification(self, title, message, geri_don=False):
        """Bildirim göster"""
        self.logger.info(f"Bildirim gösteriliyor - {title}: {message[:50]}...")
        
        notify_window = ctk.CTkToplevel(self.master)
        notify_window.title(title)
        notify_window.geometry("400x250")
        notify_window.resizable(False, False)
        notify_window.transient(self.master)
        notify_window.grab_set()

        self.master.update_idletasks()
        master_x = self.master.winfo_x()
        master_y = self.master.winfo_y()
        master_width = self.master.winfo_width()
        master_height = self.master.winfo_height()

        modal_width = 400
        modal_height = 250

        x = master_x + (master_width // 2) - (modal_width // 2)
        y = master_y + (master_height // 2) - (modal_height // 2)
        notify_window.geometry(f"{modal_width}x{modal_height}+{x}+{y}")

        icon_label = ctk.CTkLabel(
            notify_window,
            text=title.split()[0],
            font=ctk.CTkFont(size=48),
            text_color="#27ae60" if "✅" in title else "#e74c3c"
        )
        icon_label.pack(pady=20)

        message_label = ctk.CTkLabel(
            notify_window,
            text=message,
            font=ctk.CTkFont(size=14),
            justify="center",
            wraplength=350
        )
        message_label.pack(pady=10)

        def geri_don_ve_kapat():
            notify_window.destroy()
            if geri_don:
                self.geri_don()

        ok_btn = ctk.CTkButton(
            notify_window,
            text="Tamam",
            command=geri_don_ve_kapat
        )
        ok_btn.pack(pady=20)

    def _show_dialog(self, title, message, color):
        """Genel dialog gösterme metodu"""
        self.logger.debug(f"Dialog gösteriliyor: {title}")
        
        dialog_window = ctk.CTkToplevel(self.controller)
        dialog_window.title(title)
        dialog_window.geometry("450x300")
        dialog_window.resizable(False, False)
        dialog_window.transient(self.controller)
        dialog_window.grab_set()

        # Pencereyi ortala
        try:
            x = int(self.controller.winfo_x() + self.controller.winfo_width()/2 - 225)
            y = int(self.controller.winfo_y() + self.controller.winfo_height()/2 - 150)
            dialog_window.geometry(f"+{x}+{y}")
        except:
            pass  # Merkezleme başarısız olursa devam et

        # İkon
        icon_text = title.split()[0] if title else "ℹ️"
        icon_label = ctk.CTkLabel(
            dialog_window,
            text=icon_text,
            font=ctk.CTkFont(size=48),
            text_color=color
        )
        icon_label.pack(pady=20)

        # Mesaj
        message_label = ctk.CTkLabel(
            dialog_window,
            text=message,
            font=ctk.CTkFont(size=14),
            justify="center",
            wraplength=400
        )
        message_label.pack(pady=10, padx=20)

        # Tamam butonu
        ok_btn = ctk.CTkButton(
            dialog_window,
            text="Tamam",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=100,
            height=35,
            fg_color=color,
            hover_color=self._darken_color(color),
            command=dialog_window.destroy
        )
        ok_btn.pack(pady=20)

    def _darken_color(self, hex_color):
        """Rengi koyulaştır"""
        color_map = {
            "#27ae60": "#229954",
            "#e74c3c": "#c0392b",
            "#dc3545": "#c82333"
        }
        return color_map.get(hex_color, hex_color)

    def show_quality_warning(self, istenen_sayi, max_sayi):
        """Yazılı kalite uyarısı göster"""
        message = (
            f"📋 Yazılı sınavlarda kaliteli görüntü için\n"
            f"sayfa başına maksimum 2 soru önerilir.\n\n"
            f"🎯 İstediğiniz: {istenen_sayi} soru\n"
            f"📚 Mevcut: {max_sayi} soru\n\n"
        f"Devam etmek istiyor musunuz?"
        )
        # Basit uyarı penceresi
        self._show_dialog("⚠️ Kalite Uyarısı", message, "#f39c12")

    def show_multipage_info(self, istenen_sayi):
        """Yazılı çoklu sayfa bilgilendirmesi göster"""
        import math
        sayfa_sayisi = math.ceil(istenen_sayi / 2)
        
        message = (
            f"📋 Yazılı şablonunda görsel kalitesi için\n"
            f"sayfa başına maksimum 2 soru yerleştirilir.\n\n"
        f"🎯 Seçtiğiniz soru sayısı: {istenen_sayi}\n"
        f"📄 Oluşacak sayfa sayısı: {sayfa_sayisi}\n\n"
        f"Kaliteli PDF için bu şekilde devam edilecek."
        )
    
        # Bilgilendirme penceresi (sadece "Tamam" butonu)
        self._show_dialog("📋 Yazılı PDF Bilgisi", message, "#17a2b8")

if __name__ == "__main__":
    root = ctk.CTk()
    root.state('zoomed')
    app = KonuSecmePenceresi(root, None, ".")
    root.mainloop()
            #