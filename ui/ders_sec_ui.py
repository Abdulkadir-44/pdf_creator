import customtkinter as ctk
from tkinter import filedialog
import os
import logging

# Yeni loglama sistemi: Bu modülün kendi logger'ını al.
# Adı otomatik olarak 'ui.ders_sec_ui' olacaktır.
logger = logging.getLogger(__name__)

# Görsel sabitler
BG_COLOR = "#f2f2f2"
SCROLL_BG = "#e6e6e6"
BTN_BG = "#4a90e2"
BTN_FG = "#ffffff"

class DersSecmePenceresi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG_COLOR)
        self.controller = controller
        self.current_buttons = []
        self.ana_klasor_yolu = None  # Ana klasör yolunu saklamak için
        logger.info("DersSecmePenceresi frame'i başlatılıyor")
        self.setup_ui()

    def setup_ui(self):
        """UI elementlerini oluştur"""
        self.btn_font = ctk.CTkFont(family="Segoe UI", size=11, weight="bold")

        # Başlık
        title_label = ctk.CTkLabel(
            self,
            text="📂 Ders Seçimi",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#2d3436"
        )
        title_label.pack(pady=10)

        # Üst kontrol frame'i
        control_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        control_frame.pack(pady=10)

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

        # Scrollable alan
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color=SCROLL_BG)
        self.scroll_frame.pack(fill="both", expand=True, padx=30, pady=(20, 30))

        # Başlangıç mesajı
        self.show_initial_message()
        logger.info("UI kurulumu tamamlandı")

    def show_initial_message(self):
        """Başlangıç mesajını göster"""
        logger.debug("Başlangıç mesajı gösteriliyor")
        message_label = ctk.CTkLabel(
            self.scroll_frame,
            text="🔍 Lütfen üstteki 'Ana Klasör Seç' butonuna tıklayarak\nsoru klasörünüzü seçin.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#6c757d",
            justify="center"
        )
        message_label.pack(pady=50)

    def ana_klasoru_sec(self):
        """Ana klasörü seç ve ders butonlarını göster"""
        logger.info("Ana klasör seçme işlemi başlatıldı.")
        klasor_yolu = filedialog.askdirectory(title="Ana Soru Klasörünü Seçin")
        if klasor_yolu:
            logger.info(f"Klasör seçildi: {klasor_yolu}")
            self.ana_klasor_yolu = klasor_yolu
            self.goster_ders_butonlari(klasor_yolu)
        else:
            logger.info("Klasör seçme işlemi kullanıcı tarafından iptal edildi.")

    def goster_ders_butonlari(self, ana_klasor):
        """Ders butonlarını göster"""
        logger.info(f"Ders butonları '{ana_klasor}' yolu için oluşturuluyor.")
        
        # Scroll frame'i temizle
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.current_buttons.clear()
        logger.debug("Scroll frame temizlendi.")

        try:
            # Klasörleri al (dersler)
            klasorler = [d for d in os.listdir(ana_klasor) 
                         if os.path.isdir(os.path.join(ana_klasor, d))]
            
            logger.info(f"Bulunan ders sayısı: {len(klasorler)}")
            
            if not klasorler:
                logger.warning(f"Seçilen klasörde alt klasör (ders) bulunamadı: {ana_klasor}")
                self.show_empty_folder_message()
                return

            # Her ders için buton oluştur
            for ders in klasorler:
                logger.debug(f"Ders butonu oluşturuluyor: {ders}")
                buton = ctk.CTkButton(
                    self.scroll_frame,
                    text=f"📚 {ders}",
                    font=self.btn_font,
                    fg_color="#7bc96f",
                    text_color="#ffffff",
                    hover_color="#5aa75f",
                    width=250,
                    height=50,
                    command=lambda d=ders: self.konu_baslik_ekranini_ac(ana_klasor, d)
                )
                self.current_buttons.append(buton)

            logger.info(f"Toplam {len(self.current_buttons)} ders butonu oluşturuldu.")
            self.relayout_buttons()

        except PermissionError:
            logger.error(f"Klasöre erişim izni hatası: {ana_klasor}", exc_info=True)
            self.show_error_message(f"Klasöre erişim izni yok:\n{ana_klasor}")
        except FileNotFoundError:
            logger.error(f"Klasör bulunamadı: {ana_klasor}", exc_info=True)
            self.show_error_message(f"Klasör bulunamadı:\n{ana_klasor}")
        except Exception:
            logger.error("Ders butonları gösterilirken beklenmedik bir hata oluştu.", exc_info=True)
            self.show_error_message("Beklenmedik bir hata oluştu.")

    def show_empty_folder_message(self):
        """Boş klasör mesajı göster"""
        logger.info("Kullanıcıya boş klasör mesajı gösteriliyor.")
        message_label = ctk.CTkLabel(
            self.scroll_frame,
            text="🔭 Seçilen klasörde ders klasörü bulunamadı.\n\nLütfen soru klasörlerinizi içeren\nana klasörü seçtiğinizden emin olun.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#e74c3c",
            justify="center"
        )
        message_label.pack(pady=50)

    def show_error_message(self, message):
        """Hata mesajı göster"""
        logger.warning(f"Kullanıcıya hata mesajı gösteriliyor: {message}")
        error_label = ctk.CTkLabel(
            self.scroll_frame,
            text=f"❌ {message}",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#e74c3c",
            justify="center"
        )
        error_label.pack(pady=50)

    def konu_baslik_ekranini_ac(self, ana_klasor, secilen_ders):
        """Konu başlık seçme ekranını aç"""
        logger.info(f"Konu başlık ekranına geçiliyor - Ders: '{secilen_ders}'")
        ders_klasor_yolu = os.path.join(ana_klasor, secilen_ders)
        self.controller.show_frame("KonuBaslikSecme", 
                                  ders_klasor_yolu=ders_klasor_yolu,
                                  ders_adi=secilen_ders)

    def ana_menuye_don(self):
        """Ana menüye dön"""
        logger.info("Ana menüye dönme komutu verildi.")
        self.controller.ana_menuye_don()

    def relayout_buttons(self):
        """Butonları pencere boyutuna göre yeniden düzenle"""
        if not self.current_buttons:
            logger.debug("Yeniden düzenlenecek buton bulunamadı.")
            return

        logger.debug("Butonlar yeniden düzenleniyor...")

        # Önceki grid ayarlarını temizle
        for widget in self.scroll_frame.winfo_children():
            if isinstance(widget, ctk.CTkButton):
                 widget.grid_forget()

        # Buton düzenleme parametreleri
        padding = 15
        margin = 30
        btn_width_px = 250

        # Pencere genişliğine göre kolon sayısını hesapla
        try:
            frame_width = self.scroll_frame.winfo_width()
            if frame_width <= 1:  # Henüz render olmamışsa
                frame_width = 800
                logger.debug(f"Frame genişliği render olmamış, varsayılan değer kullanılıyor: {frame_width}px")
        except Exception:
            frame_width = 800
            logger.warning("Frame genişliği hesaplanırken hata, varsayılan değer kullanılıyor: 800px", exc_info=True)

        usable_width = frame_width - 2 * margin
        max_columns = max(1, usable_width // (btn_width_px + padding))
        
        logger.debug(f"Frame Genişliği: {frame_width}px, Kullanılabilir Genişlik: {usable_width}px, Sütun Sayısı: {max_columns}")

        # Grid konfigürasyonu
        for col in range(max_columns):
            self.scroll_frame.grid_columnconfigure(col, weight=1)

        # Butonları yerleştir
        for idx, btn in enumerate(self.current_buttons):
            row = idx // max_columns
            col = idx % max_columns
            btn.grid(row=row, column=col, padx=padding//2, pady=10, sticky="ew")

        logger.info(f"Buton düzenlemesi tamamlandı - {len(self.current_buttons)} buton, {max_columns} sütun ile yerleştirildi.")