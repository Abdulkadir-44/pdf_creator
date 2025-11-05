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

# --- Basit Tooltip Yardımcısı (tkinter ile) ---
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 22
        y = self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text, justify="left",
            background="#ffffe0", relief="solid", borderwidth=1,
            font=("Segoe UI", 9)
        )
        label.pack(ipadx=4, ipady=2)

    def hide(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


# Oturum bazlı yazılı bilgilendirme gösterim bayrağı
YAZILI_INFO_SHOWN = False

# Modern tema ayarları
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

class SoruParametresiSecmePenceresi(ctk.CTkFrame):
    def __init__(self, parent, controller, unite_klasor_yolu=None, ders_adi=None, secilen_konular=None):
        super().__init__(parent, fg_color="#f0f2f5")
        self.controller = controller
        self.unite_klasor_yolu = unite_klasor_yolu  # Artık kullanılmıyor ama uyumluluk için
        self.ders_adi = ders_adi
        self.colors = {
            'primary': '#4361ee',
            'primary_hover': '#3730a3',
            'light': '#ffffff',
            'bg': '#f0f2f5'
        }
        self.sayfa_haritasi = []
        self.secilen_konular = secilen_konular or {}  # {konu_adi: klasor_yolu}
        self.secilen_gorseller = []
        self.konu_soru_dagilimi = {}  # Her konudan kaç soru seçileceği
        
        self.baslik_text_var = tk.StringVar(value="")  
        self.BASLIK_PT_MAX = 40
        self.BASLIK_PT_MIN = 25
        self.TITLE_MAX_W_RATIO = 0.85   # sayfa genişliğinin %80’i içine sığdır
        self._title_typing_job = None   # debounce timer
        self._title_trace_id = None
        
        # Logger'ı kur
        self.logger = self._setup_logger()
        self.logger.info(f"SoruParametresiSecmePenceresi başlatıldı - Ders: {ders_adi}, Konu sayısı: {len(self.secilen_konular)}")
        
        # Oturum bazlı kullanılan sorular takibi
        self.kullanilan_sorular = {}  # {konu_adi: set()} format

        # Kullanılan soruları başlat
        for konu_adi in self.secilen_konular.keys():
            self.kullanilan_sorular[konu_adi] = set()
        
        # UI'ı oluştur
        self.setup_ui()

    def _setup_logger(self):
        """Merkezi log sistemini kullan: sadece modül logger'ını döndür."""
        return logging.getLogger(__name__)

    def setup_ui(self):
        """Ana UI'ı oluştur"""
        self.logger.debug("UI kurulumu başlatılıyor")

        # Ana container ekle
        self.main_container = ctk.CTkFrame(self, fg_color=self.colors['bg'], corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        # Header bölümü ekle
        self.create_header()

        # Mevcut main_frame kodunu main_container'ın içine al:
        self.main_frame = ctk.CTkFrame(self.main_container, corner_radius=20, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(10, 10))  # üst padding azaltıldı
    
        # Form container
        self.form_frame = ctk.CTkFrame(
            self.main_frame, 
            corner_radius=15, 
            fg_color="#f8f9fa", 
            border_width=1, 
            border_color="#e9ecef"
        )
        self.form_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.create_selection_widgets()
        self.logger.info("UI kurulumu tamamlandı")

    def _havuzu_sifirla(self):
        """Kullanılan sorular havuzunu sıfırla"""
        try:
            # Mevcut seçili konulara göre havuzu yeniden kur
            self.kullanilan_sorular = {konu_adi: set() for konu_adi in self.secilen_konular.keys()}
            self.logger.debug("Kullanılan sorular havuzu sıfırlandı")
        except Exception as e:
            self.logger.error(f"Havuz sıfırlama hatası: {e}")

    def _open_dropdown_safely(self, cb):
        try:
            if cb and cb.winfo_exists() and hasattr(cb, "_open_dropdown_menu"):
                cb._open_dropdown_menu()
        except Exception:
            pass

    def _bind_combobox_open(self, cb):
        try:
            # Tüm widget alanına tıklamayı bağla (ikon + input)
            cb.bind("<Button-1>", lambda e: self._open_dropdown_safely(cb))
            # Odak alınca da açılmasını istersen (opsiyonel):
            # cb.bind("<FocusIn>", lambda e: self._open_dropdown_safely(cb))
        except Exception:
            pass
    
    def _refresh_preview_left_now(self):
        """Sadece sol panel (önizleme) yeniden çizilir, sağ taraf dokunulmaz."""
        try:
            if hasattr(self, "_last_pdf_container") and self._last_pdf_container:
                # ✅ YENİ: Sadece PDF önizlemesini yenile
                self.refresh_pdf_preview_only(self._last_pdf_container)
            else:
                # İlk kez çalışıyorsa tüm önizlemeyi başlat
                self.gorsel_onizleme_alani_olustur()
        except Exception as e:
            print("Önizleme yenilenemedi:", e)
    
    def refresh_pdf_preview_only(self, pdf_container):
        """SADECE sol PDF önizleme panelini yeniler (sağ panel dokunulmaz)"""
        try:
            # Sadece sol paneli temizle
            for widget in pdf_container.winfo_children():
                widget.destroy()

            # Soru tipine göre sayfa başı soru sayısı
            sorular_per_sayfa = self._get_sorular_per_sayfa()
            toplam_sayfa = math.ceil(len(self.secilen_gorseller) / sorular_per_sayfa)

            if not hasattr(self, 'current_page'):
                self.current_page = 0

            # Sayfa navigasyon (varsa)
            if toplam_sayfa > 1:
                nav_frame = ctk.CTkFrame(pdf_container, fg_color="#ffffff", corner_radius=6, height=35)
                nav_frame.pack(anchor="ne", padx=10, pady=5)
                nav_frame.pack_propagate(False)

                # Önceki sayfa butonu
                if self.current_page > 0:
                    prev_btn = ctk.CTkButton(
                        nav_frame,
                        text="◀",
                        command=lambda: self.change_page_pdf_only(-1),
                        width=30, height=25,
                        font=ctk.CTkFont(size=10, weight="bold"),
                        fg_color="#007bff",
                        hover_color="#0056b3"
                    )
                    prev_btn.pack(side="left", padx=2, pady=5)

                # Sayfa bilgisi
                page_info = ctk.CTkLabel(
                    nav_frame,
                    text=f"{self.current_page + 1}/{toplam_sayfa}",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color="#495057"
                )
                page_info.pack(side="left", padx=8, pady=5)

                # Sonraki sayfa butonu
                if self.current_page < toplam_sayfa - 1:
                    next_btn = ctk.CTkButton(
                        nav_frame,
                        text="▶",
                        command=lambda: self.change_page_pdf_only(1),
                        width=30, height=25,
                        font=ctk.CTkFont(size=10, weight="bold"),
                        fg_color="#007bff",
                        hover_color="#0056b3"
                    )
                    next_btn.pack(side="left", padx=2, pady=5)

            # PDF önizleme alanı
            preview_frame = ctk.CTkScrollableFrame(
                pdf_container, 
                fg_color="#e9ecef", 
                corner_radius=8
            )
            preview_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

            # Mevcut sayfa için görselleri al
            start_idx = self.current_page * sorular_per_sayfa
            end_idx = min(start_idx + sorular_per_sayfa, len(self.secilen_gorseller))
            sayfa_gorselleri = self.secilen_gorseller[start_idx:end_idx]

            # PDF sayfası önizlemesi oluştur
            pdf_preview = self.create_page_preview(sayfa_gorselleri, start_idx)

            if pdf_preview:
                pdf_label = tk.Label(
                    preview_frame,
                    image=pdf_preview,
                    bg="#e9ecef"
                )
                pdf_label.image = pdf_preview
                pdf_label.pack(expand=True, pady=5)
            else:
                error_label = ctk.CTkLabel(
                    preview_frame,
                    text="PDF önizlemesi oluşturulamadı",
                    font=ctk.CTkFont(size=14),
                    text_color="#dc3545"
                )
                error_label.pack(expand=True, pady=50)

        except Exception as e:
            self.logger.error(f"PDF önizleme yenileme hatası: {e}")
    
    def change_page_pdf_only(self, direction):
        """Sayfa değiştir - SADECE sol paneli yenile"""
        sorular_per_sayfa = self._get_sorular_per_sayfa()
        toplam_sayfa = math.ceil(len(self.secilen_gorseller) / sorular_per_sayfa)

        new_page = self.current_page + direction
        if 0 <= new_page < toplam_sayfa:
            self.current_page = new_page
            self.logger.debug(f"Sayfa değişti: {new_page + 1}/{toplam_sayfa}")

            # ✅ Sadece sol paneli yenile
            self.refresh_pdf_preview_only(self._last_pdf_container)
            
    def _refresh_preview_debounced(self, delay_ms=500):
        """Metin değiştiğinde 400 ms gecikmeyle yalnız sol önizlemeyi yeniler."""
        try:
            if self._title_typing_job:
                self.after_cancel(self._title_typing_job)
        except Exception:
            pass
        self._title_typing_job = self.after(delay_ms, self._refresh_preview_left_now)

    def _draw_title_on_image(self, image):
        """Şablon imajının üst-ortasına başlığı çizer (tek font, tek marjin)."""
        if image is None:
            return
        from PIL import ImageDraw, ImageFont

        text_raw = (self.baslik_text_var.get() or "").strip()
        # Önce küçük 'i'leri 'İ' yap, SONRA büyük harfe çevir.
        text = text_raw.replace('i', 'İ').upper() or "QUIZ"
        TOP_MARGIN = 50
        W, H = image.size
        max_w = int(W * self.TITLE_MAX_W_RATIO)

        draw = ImageDraw.Draw(image)

        def try_font(pt):
            try:
                return ImageFont.truetype("arial.ttf", pt)
            except Exception:
                try:
                    return ImageFont.truetype("DejaVuSans.ttf", pt)
                except Exception:
                    return ImageFont.load_default()

        pt = self.BASLIK_PT_MAX
        font = try_font(pt)
        w = draw.textbbox((0, 0), text, font=font)[2]
        while pt > self.BASLIK_PT_MIN and w > max_w:
            pt -= 1
            font = try_font(pt)
            w = draw.textbbox((0, 0), text, font=font)[2]

        if w > max_w and len(text) > 5:
            t = text
            while len(t) > 5:
                t = t[:-2] + "…"
                w = draw.textbbox((0, 0), t, font=font)[2]
                if w <= max_w:
                    text = t
                    break

        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (W - tw) // 2
        y = TOP_MARGIN

        draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0))
        draw.text((x, y), text, font=font, fill="darkred")

    def _unbind_combobox_open_in(self, container):
        """Verilen container içindeki tüm CTkComboBox'lardan güvenli tıklama bağını kaldır."""
        try:
            for child in container.winfo_children():
                try:
                    if isinstance(child, ctk.CTkComboBox):
                        child.unbind("<Button-1>")
                    # İç içe frame'leri de tara
                    if hasattr(child, "winfo_children"):
                        self._unbind_combobox_open_in(child)
                except Exception:
                    continue
        except Exception:
            pass

    def create_header(self):
        """Modern header tasarımı"""
        # Header frame
        header_frame = ctk.CTkFrame(
            self.main_container, 
            height=100,  # Daha ince (120'den 100'e düşürüldü)
            corner_radius=0,
            fg_color=self.colors['primary']
        )
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        # Header içeriği
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(expand=True, fill="both", padx=40, pady=15)  # pady azaltıldı

        # Sol taraf - Navigasyon butonları
        left_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        left_frame.pack(side="left", fill="y")

        # Ana Menü butonu
        home_btn = ctk.CTkButton(
            left_frame,
            text="Ana Menü",
            width=100,
            height=36,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#5a6fee",
            border_width=2,
            border_color=self.colors['light'],
            text_color=self.colors['light'],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.ana_menuye_don
        )
        home_btn.pack(side="left", padx=(0, 10))

        # Konu Seçimi butonu
        back_btn = ctk.CTkButton(
            left_frame,
            text="← Konu Seçimi",
            width=110,
            height=36,
            corner_radius=8,
            fg_color="transparent",
            hover_color="#5a6fee",
            border_width=2,
            border_color=self.colors['light'],
            text_color=self.colors['light'],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self.konu_baslik_sayfasina_don
        )
        back_btn.pack(side="left")

        # Sağ taraf - Başlık
        right_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        right_frame.pack(side="right", fill="y")

        title_label = ctk.CTkLabel(
            right_frame,
            text=f"{self.ders_adi}",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),  # Boyut küçültüldü
            text_color=self.colors['light']
        )
        title_label.pack(anchor="e")

        subtitle_label = ctk.CTkLabel(
            right_frame,
            text="Soru Parametre Seçimi",
            font=ctk.CTkFont(family="Segoe UI", size=13),  # Boyut küçültüldü
            text_color="#e0e0e0"
        )
        subtitle_label.pack(anchor="e", pady=(3, 0))
    
    def create_selection_widgets(self):
        """Seçim widget'larını oluştur - Geliştirilmiş tasarım"""
        self.logger.debug("Seçim widget'ları oluşturuluyor")

        

        # Ana horizontal container
        main_horizontal_frame = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        main_horizontal_frame.pack(fill="both", expand=True, padx=30, pady=(5, 10))

        # Sol taraf - Input'lar
        left_input_frame = ctk.CTkFrame(
            main_horizontal_frame, 
            fg_color="#ffffff",
            corner_radius=16,
            border_width=1,
            border_color="#e2e8f0"
        )
        left_input_frame.pack(side="left", fill="y", padx=(0, 25), ipadx=30, ipady=10)

        # Sol taraf başlığı
        left_title_label = ctk.CTkLabel(
            left_input_frame, 
            text="Soru Parametreleri",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#1a202c"
        )
        left_title_label.pack(pady=(10, 10), anchor="w",padx=(10,0))

        # Soru Tipi Seçimi
        self.soru_tipi_var = tk.StringVar()
        self.soru_tipi_menu = ctk.CTkComboBox(
            left_input_frame,
            variable=self.soru_tipi_var,
            values=["Test", "Yazili"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            width=320,
            height=45,
            corner_radius=12,
            border_width=2,
            border_color="#e2e8f0",
            button_color="#667eea",
            button_hover_color="#5a6fd8",
            dropdown_hover_color="#f7fafc",
            state="readonly"
        )
        self.soru_tipi_menu.set("Soru tipi seçin...")
        self.soru_tipi_menu.pack(anchor="w", pady=(0, 15), padx=(10, 0)) 
        self._bind_combobox_open(self.soru_tipi_menu)

        # Zorluk Seçimi
        self.zorluk_var = tk.StringVar()
        self.zorluk_menu = ctk.CTkComboBox(
            left_input_frame,
            variable=self.zorluk_var,
            values=["Kolay", "Orta", "Zor"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            width=320,
            height=45,
            corner_radius=12,
            border_width=2,
            border_color="#e2e8f0",
            button_color="#48bb78",
            button_hover_color="#38a169",
            dropdown_hover_color="#f7fafc",
            state="readonly"
        )
        self.zorluk_menu.set("Zorluk seviyesi seçin...")
        self.zorluk_menu.pack(anchor="w", pady=(0, 15), padx=(10, 0))
        self._bind_combobox_open(self.zorluk_menu)

        # Cevap Anahtarı Seçimi
        self.cevap_anahtari_var = tk.StringVar()
        self.cevap_anahtari_menu = ctk.CTkComboBox(
            left_input_frame,
            variable=self.cevap_anahtari_var,
            values=["Evet", "Hayır"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            width=320,
            height=45,
            corner_radius=12,
            border_width=2,
            border_color="#e2e8f0",
            button_color="#ed8936",
            button_hover_color="#dd6b20",
            dropdown_hover_color="#f7fafc",
            state="readonly"
        )
        self.cevap_anahtari_menu.set("Cevap anahtarı eklensin mi?")
        self.cevap_anahtari_menu.pack(anchor="w", pady=(0, 15), padx=(10, 0))
        self._bind_combobox_open(self.cevap_anahtari_menu)

        # Küçük ipucu etiketi (sayfa başı limit bilgisi)
        hint_label = ctk.CTkLabel(
            left_input_frame,
            text="Bilgi: Program Test şablonunda sayfa başına maks 10 soru,\nYazılı şablonunda ise maks 2 soru yerleştirecektir.",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#495057"
        )
        hint_label.pack(side="left", pady=(2, 8), padx=(10, 0))

        # Toplam soru sayısı
        # self.total_frame = ctk.CTkFrame(
        #     left_input_frame, 
        #     fg_color="#ebf8ff",
        #     corner_radius=12,
        #     border_width=1,
        #     border_color="#90cdf4"
        # )
        # self.total_frame.pack(fill="x", pady=(5, 0),padx=(10,10))

        # self.total_label = ctk.CTkLabel(
        #     self.total_frame,
        #     text="Toplam Soru Sayısı: 0",
        #     font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
        #     text_color="#2b6cb0"
        # )
        # self.total_label.pack(pady=10,padx=(10,10))

        # Sağ taraf - Konu Dağılımı
        right_distribution_frame = ctk.CTkFrame(
            main_horizontal_frame, 
            fg_color="#ffffff",
            corner_radius=16,
            border_width=1,
            border_color="#e2e8f0"
        )
        right_distribution_frame.pack(side="right", fill="both", expand=True, ipadx=30, ipady=10)

        # Konu dağılımı başlığı
        dist_label = ctk.CTkLabel(
            right_distribution_frame, 
            text="Konu Başına Soru Sayısı",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#1a202c"
        )
        dist_label.pack(pady=(10, 10), anchor="w",padx=(10,0))

        # Scrollable frame
        self.topics_frame = ctk.CTkScrollableFrame(
            right_distribution_frame,
            fg_color="#f7fafc",
            corner_radius=12,
            border_width=1,
            border_color="#e2e8f0",
            height=280,
            scrollbar_button_color="#cbd5e0",
            scrollbar_button_hover_color="#a0aec0"
        )
        self.topics_frame.pack(fill="both", expand=True, padx=5)

        self.konu_entry_vars = {}

        for konu_adi in self.secilen_konular.keys():
            # Her konu için frame
            konu_frame = ctk.CTkFrame(
                self.topics_frame, 
                fg_color="#ffffff",
                corner_radius=10,
                border_width=1,
                border_color="#e2e8f0"
            )
            konu_frame.pack(fill="x", pady=2, padx=8, ipady=8, ipadx=12)

            # Konu adı
            konu_label = ctk.CTkLabel(
                konu_frame,
                text=konu_adi,
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                text_color="#e53e3e"
            )
            konu_label.pack(side="left", anchor="w",padx=(10,10))

            # Sağ taraf için container
            right_container = ctk.CTkFrame(konu_frame, fg_color="transparent")
            right_container.pack(side="right", padx=(10, 0))

            # Soru sayısı girişi
            var = tk.StringVar(value="1")
            self.konu_entry_vars[konu_adi] = var

            entry = ctk.CTkEntry(
                right_container,
                textvariable=var,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
                width=65,
                height=32,
                corner_radius=8,
                border_width=2,
                border_color="#e2e8f0",
                fg_color="#ffffff"
            )
            entry.pack(side="right", padx=(12, 0))

            # Hızlı seçim butonları
            button_colors = ["#4299e1", "#48bb78", "#ed8936", "#9f7aea"]
            hover_colors = ["#3182ce", "#38a169", "#dd6b20", "#805ad5"]

            for j, num in enumerate([1, 2, 3, 5]):
                btn = ctk.CTkButton(
                    right_container,
                    text=str(num),
                    width=32,
                    height=32,
                    corner_radius=8,
                    fg_color=button_colors[j],
                    hover_color=hover_colors[j],
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    text_color="#ffffff",
                    command=lambda n=num, v=var: v.set(str(n))
                )
                btn.pack(side="right", padx=(0, 4))

        # Toplam seçili soru sayacı (sağ panelde alt kısımda)
        self.total_label = ctk.CTkLabel(
            right_distribution_frame,
            text="Toplam Seçilen Soru: 0",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#2b6cb0"
        )
        self.total_label.pack(anchor="e", pady=(8, 4), padx=(0, 16))

        # Entry değişikliklerini izle
        for var in self.konu_entry_vars.values():
            try:
                var.trace_add('write', lambda *_: self.update_total())
            except Exception:
                try:
                    var.trace('w', lambda *_: self.update_total())
                except Exception:
                    pass
        # İlk değer için güncelle
        self.update_total()

        # Devam Et butonu
        devam_btn = ctk.CTkButton(
            self.form_frame,
            text="Devam Et",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            width=200,
            height=50,
            corner_radius=16,
            fg_color="#48bb78",
            hover_color="#38a169",
            text_color="#ffffff",
            command=self.devam_et
        )
        devam_btn.pack(pady=(10, 10))
    
    def ana_menuye_don(self):
        """Ana menüye dön"""
        self.logger.info("Ana menüye dönülüyor")
        self.controller.ana_menuye_don()

    def konu_baslik_sayfasina_don(self):
        """Konu başlık seçim sayfasına dön"""
        self.logger.info("Konu başlık seçim sayfasına dönülüyor")
        self.controller.show_frame("KonuBaslikSecme", 
                                 ders_klasor_yolu=os.path.dirname(list(self.secilen_konular.values())[0]),
                                 ders_adi=self.ders_adi)

    def devam_et(self):
        """Seçimleri doğrula ve önizleme ekranını göster"""
        self.logger.info("Devam et butonuna tıklandı")
        
        # Seçimleri al
        soru_tipi = self.soru_tipi_var.get()
        zorluk = self.zorluk_var.get()
        cevap_anahtari = self.cevap_anahtari_var.get()
    
        self.logger.debug(f"Seçimler - Tip: {soru_tipi}, Zorluk: {zorluk}, Cevap Anahtarı: {cevap_anahtari}")
    
        # Validasyon
        if "seçin" in soru_tipi.lower() or "seçin" in zorluk.lower() or "eklensin" in cevap_anahtari.lower():
            self.logger.warning("Eksik seçim tespit edildi")
            self.show_error("Lütfen tüm seçimleri yapın!\n- Soru tipi\n- Zorluk seviyesi\n- Cevap anahtarı")
            return

        # Soru dağılımını kontrol et
        try:
            toplam_soru = 0
            soru_dagilimi = {}
            
            for konu_adi, var in self.konu_entry_vars.items():
                try:
                    sayi = int(var.get())
                    if sayi > 0:
                        soru_dagilimi[konu_adi] = sayi
                        toplam_soru += sayi
                except ValueError:
                    self.show_error(f"{konu_adi} için geçerli bir soru sayısı girin!")
                    return
            
            if toplam_soru == 0:
                self.show_error("En az bir konu için soru sayısı belirtmelisiniz!")
                return
            
            self.konu_soru_dagilimi = soru_dagilimi
            self.logger.info(f"Toplam {toplam_soru} soru seçildi")

        except Exception as e:
            self.logger.error(f"Soru dağılımı kontrolü hatası: {e}")
            self.show_error("Soru sayıları kontrol edilirken hata oluştu!")
            return

        # Her konu için soru mevcudiyeti kontrolü - Sadece boş klasör kontrolü
        bos_konular = []
        for konu_adi, istenen_sayi in soru_dagilimi.items():
            mevcut_sayi = self.get_available_questions(konu_adi, soru_tipi, zorluk)
            if mevcut_sayi == 0:  # Sadece tamamen boş klasörleri kontrol et
                bos_konular.append(konu_adi)

        if bos_konular:
            self.logger.warning("Boş klasörler tespit edildi")
            if len(bos_konular) == 1:
                uyari_mesaji = f"'{bos_konular[0]}' konusunda seçilen zorluk seviyesinde ({zorluk}) soru bulunamadı!\n\nFarklı bir zorluk seviyesi seçin veya bu konuyu atlayın."
            else:
                konu_listesi = "', '".join(bos_konular)
                uyari_mesaji = f"Şu konularda seçilen zorluk seviyesinde ({zorluk}) soru bulunamadı:\n\n'{konu_listesi}'\n\nFarklı bir zorluk seviyesi seçin veya bu konuları atlayın."

            self.show_error(uyari_mesaji)
            return

        # Yetersiz soru kontrolü (istenen sayıdan az olanlar)
        eksik_konular = []
        for konu_adi, istenen_sayi in soru_dagilimi.items():
            mevcut_sayi = self.get_available_questions(konu_adi, soru_tipi, zorluk)
            if 0 < mevcut_sayi < istenen_sayi:  # Soru var ama yetersiz
                eksik_konular.append(f"{konu_adi}: {istenen_sayi} istendi, {mevcut_sayi} mevcut")

        if eksik_konular:
            self.logger.warning("Yetersiz soru bulunan konular var")
            hata_mesaji = "Bazı konularda yeterli soru yok:\n\n" + "\n".join(eksik_konular)
            self.show_error(hata_mesaji)
            return

        # Sayfa bilgilendirmesi (yazılı, oturum bazlı). Diyalog kapandıktan sonra devam et.
        if soru_tipi.lower() == "yazili" and toplam_soru > 2:
            global YAZILI_INFO_SHOWN
            if not YAZILI_INFO_SHOWN:
                self.logger.info("Yazılı için çoklu sayfa bilgilendirmesi (oturum bazlı) gösteriliyor")
                YAZILI_INFO_SHOWN = True
                # Mevcut ekrandaki combobox tıklama bağlarını kaldırarak fokus hatasını önle
                self._unbind_combobox_open_in(self.form_frame)
                self.show_multipage_info(toplam_soru, on_close=lambda: self._proceed_to_preview(soru_tipi, zorluk))
                return

        # Bilgilendirme gerekmiyorsa doğrudan devam
        self._proceed_to_preview(soru_tipi, zorluk)

    def get_available_questions(self, konu_adi, soru_tipi, zorluk):
        """Bir konu için mevcut soru sayısını döndür"""
        try:
            konu_path = self.secilen_konular[konu_adi]
            klasor_yolu = os.path.join(konu_path, soru_tipi.lower(), zorluk.lower())
            
            if not os.path.exists(klasor_yolu):
                return 0
                
            gorseller = [f for f in os.listdir(klasor_yolu) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            
            return len(gorseller)
        except Exception as e:
            self.logger.error(f"Mevcut soru sayısı hesaplama hatası - {konu_adi}: {e}")
            return 0

    def secili_gorselleri_al(self, soru_tipi, zorluk):
        """Her konudan belirtilen sayıda rastgele görsel seç - Kullanılan takibi ile"""
        try:
            # *** YENİ: Her yeni PDF oluşturma işleminde havuzu sıfırla ***
            self._havuzu_sifirla()
            self.logger.info("Yeni PDF oluşturma başlıyor - Havuz sıfırlandı")
            
            tum_gorseller = []

            for konu_adi, sayi in self.konu_soru_dagilimi.items():
                konu_path = self.secilen_konular[konu_adi]
                klasor_yolu = os.path.join(konu_path, soru_tipi.lower(), zorluk.lower())

                if os.path.exists(klasor_yolu):
                    gorseller = [f for f in os.listdir(klasor_yolu) 
                               if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]

                    import random
                    if len(gorseller) >= sayi:
                        secilen = random.sample(gorseller, sayi)
                    else:
                        secilen = gorseller

                    # *** YENİ: Seçilen soruları kullanılan listesine ekle ***
                    for gorsel in secilen:
                        self.kullanilan_sorular[konu_adi].add(gorsel)
                        # Tam yol ile ekle
                        tum_gorseller.append(os.path.join(klasor_yolu, gorsel))

                    self.logger.debug(f"{konu_adi}: {len(secilen)} görsel seçildi ve kullanılan listesine eklendi")

            # Listeyi karıştır
            import random
            random.shuffle(tum_gorseller)

            self.logger.info(f"Toplam {len(tum_gorseller)} görsel seçildi ve karıştırıldı")
            return tum_gorseller

        except Exception as e:
            self.logger.error(f"Görsel seçme hatası: {e}")
            return []
    
    def gorsel_onizleme_alani_olustur(self):
        """Görsel önizleme alanını oluştur - Yeni tasarım"""
        self.logger.info("Önizleme alanı oluşturuluyor")

        # Form içeriğini temizle
        # Önce combobox tıklama bağlarını kaldır (yok olmuş widget referansları hatasını önler)
        self._unbind_combobox_open_in(self.form_frame)
        for widget in self.form_frame.winfo_children():
            widget.destroy()

        # Ana container - minimal padding
        main_container = ctk.CTkFrame(self.form_frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=5, pady=5)

        # Ana içerik alanı - yan yana düzen
        content_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        # Sol taraf - PDF önizleme
        pdf_container = ctk.CTkFrame(content_frame, fg_color="#f8f9fa", corner_radius=10)
        pdf_container.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Sağ taraf - Kontroller (sabit 400px)
        controls_container = ctk.CTkFrame(content_frame, fg_color="#ffffff", corner_radius=10, width=400)
        controls_container.pack(side="right", fill="y", padx=(5, 0))
        controls_container.pack_propagate(False)

        # PDF önizlemesini göster
        self.display_images_new(pdf_container, controls_container)

        # 🔹 Gelecekte sadece sol paneli yenileyebilmek için referansları sakla
        self._last_pdf_container = pdf_container
        self._last_controls_container = controls_container
    
    def display_images_new(self, pdf_container, controls_container):
        """
        Yeni tasarımla görselleri göster (ARTIK SÜTUNLU HARİTADAN OKUYOR)
        Sıralı numaralandırma için 'global_offset' hesaplar.
        """
        self.logger.debug("Yeni tasarımla görsel display başlatılıyor (Sütunlu Harita + Sıralı No Modu)")
        
        if controls_container is None:
            if hasattr(self, '_last_controls_container'):
                controls_container = self._last_controls_container
            else:
                self.logger.error("Kontrol paneli referansı (controls_container) bulunamadı!")
                return

        # Container'ları temizle
        for widget in pdf_container.winfo_children():
            widget.destroy()
        for widget in controls_container.winfo_children():
            widget.destroy()

        # --- YENİ PLANLANMIŞ MATEMATİK ---
        if not self.sayfa_haritasi:
            self.logger.warning("display_images_new: Gösterilecek sayfa haritası bulunamadı!")
            self.sayfa_haritasi = [ [ [], [] ] ] # Boş bir sayfa (sol ve sağ sütun boş)
            
        toplam_sayfa = len(self.sayfa_haritasi)
        
        if not hasattr(self, 'current_page') or self.current_page >= toplam_sayfa:
            self.current_page = max(0, toplam_sayfa - 1)
        
        # --- YENİ SIRALI NUMARALANDIRMA İÇİN OFFSET HESAPLAMA ---
        global_offset = 0
        for i in range(self.current_page):
            # Önceki sayfadaki tüm sütunlardaki soruları topla
            onceki_sayfa_sutunlari = self.sayfa_haritasi[i]
            global_offset += sum(len(sutun) for sutun in onceki_sayfa_sutunlari)
        
        self.logger.info(f"Sayfa {self.current_page + 1} için global_offset: {global_offset}")

        # Sayfa navigasyon
        if toplam_sayfa > 1:
            nav_frame = ctk.CTkFrame(pdf_container, fg_color="#ffffff", corner_radius=6, height=35)
            nav_frame.pack(anchor="ne", padx=10, pady=5)
            nav_frame.pack_propagate(False)
            
            if self.current_page > 0:
                prev_btn = ctk.CTkButton(
                    nav_frame, text="◀",
                    command=lambda: self.change_page_new(pdf_container, controls_container, -1),
                    width=30, height=25, font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color="#007bff", hover_color="#0056b3"
                )
                prev_btn.pack(side="left", padx=2, pady=5)
                
            page_info = ctk.CTkLabel(
                nav_frame, text=f"{self.current_page + 1}/{toplam_sayfa}",
                font=ctk.CTkFont(size=11, weight="bold"), text_color="#495057"
            )
            page_info.pack(side="left", padx=8, pady=5)
            
            if self.current_page < toplam_sayfa - 1:
                next_btn = ctk.CTkButton(
                    nav_frame, text="▶",
                    command=lambda: self.change_page_new(pdf_container, controls_container, 1),
                    width=30, height=25, font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color="#007bff", hover_color="#0056b3"
                )
                next_btn.pack(side="left", padx=2, pady=5)


        # PDF önizleme alanı
        preview_frame = ctk.CTkScrollableFrame(
            pdf_container, 
            fg_color="#e9ecef", 
            corner_radius=8
        )
        preview_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # --- YENİ GÖRSEL ALMA KISMI (SÜTUNLU HARİTADAN) ---
        bu_sayfanin_sutunlari = self.sayfa_haritasi[self.current_page]

        # PDF sayfası önizlemesi oluştur
        pdf_preview = self.create_page_preview(bu_sayfanin_sutunlari, global_offset)

        if pdf_preview:
            pdf_label = tk.Label(
                preview_frame,
                image=pdf_preview,
                bg="#e9ecef"
            )
            pdf_label.image = pdf_preview
            pdf_label.pack(expand=True, pady=5)
        else:
            error_text = "PDF önizlemesi oluşturulamadı"
            # Sütunlardaki toplam soru sayısına bak
            total_questions_on_page = sum(len(col) for col in bu_sayfanin_sutunlari)
            if total_questions_on_page == 0:
                error_text = "Bu sayfada soru yok."
            error_label = ctk.CTkLabel(
                preview_frame,
                text=error_text,
                font=ctk.CTkFont(size=14),
                text_color="#dc3545"
            )
            error_label.pack(expand=True, pady=50)

        # Sağ taraf kontroller
        self.create_controls_panel(controls_container, bu_sayfanin_sutunlari, pdf_container, global_offset)
        
    def _replan_and_refresh_ui(self):
        """
        'self.secilen_gorseller' listesi değiştiğinde (sil/güncelle) çağrılır.
        Tüm 'sayfa_haritasi'nı (SÜTUNLU olarak) yeniden hesaplar ve UI'ı komple yeniler.
        """
        try:
            self.logger.info("'self.secilen_gorseller' değişti, plan yeniden hesaplanıyor...")
            
            # 1. YENİDEN PLANLA (SÜTUNLU BEYNİ ÇAĞIR)
            pdf_planner = PDFCreator()
            pdf_planner.gorsel_listesi = self.secilen_gorseller # Güncel listeyi ver
            
            soru_tipi = self.soru_tipi_var.get().lower()
            
            if soru_tipi == "test":
                # 'planla_test_duzeni' artık SÜTUNLU harita üretiyor
                self.sayfa_haritasi = pdf_planner.planla_test_duzeni() 
            else:
                # Yazılı için basit planlama (SÜTUNLU formata uydur)
                soru_listesi = [
                    {'index': i, 'path': path, 'total_height': 500, 'final_size': (500, 400)} # Tahmini boyut
                    for i, path in enumerate(self.secilen_gorseller)
                ]
                # Yazılı 1 sütunludur, bu yüzden [ [Sayfa1_Sutun1], [Boş_Sutun2] ] formatına getir
                sayfa_listesi = []
                for i in range(0, len(soru_listesi), 2): # Sayfa başına 2 soru
                    sayfa_sorulari = soru_listesi[i:i+2]
                    sayfa_listesi.append([ sayfa_sorulari, [] ]) # [ [Soru1, Soru2], [] ]
                self.sayfa_haritasi = sayfa_listesi

            # 2. Sayfa taşmasını engelle
            toplam_sayfa = len(self.sayfa_haritasi)
            if not self.sayfa_haritasi: # Eğer son soru da silindiyse
                self.sayfa_haritasi = [ [ [], [] ] ] # Boş bir sayfa (sol ve sağ sütun boş)
                toplam_sayfa = 1
            
            if self.current_page >= toplam_sayfa:
                self.current_page = max(0, toplam_sayfa - 1)
            
            # 3. UI'ı (Sol+Sağ Panel) Yenile
            if hasattr(self, '_last_pdf_container') and self._last_pdf_container.winfo_exists():
                self.display_images_new(self._last_pdf_container, self._last_controls_container)
                self.logger.info("Plan ve UI başarıyla yenilendi.")
            else:
                self.logger.warning("_replan_and_refresh_ui: UI referansları bulunamadı, yenilenemedi.")
        
        except Exception as e:
            self.logger.error(f"Yeniden planlama ve UI yenileme hatası: {e}", exc_info=True)
            
    def refresh_pdf_preview_only(self, pdf_container):
        """SADECE sol PDF önizleme panelini yeniler (SÜTUNLU HARİTADAN OKUR + OFFSET HESAPLAR)"""
        try:
            # Sadece sol paneli temizle
            for widget in pdf_container.winfo_children():
                widget.destroy()

            # --- YENİ PLANLANMIŞ MATEMATİK ---
            if not self.sayfa_haritasi:
                self.logger.warning("refresh_pdf_preview_only: Harita boş.")
                self.sayfa_haritasi = [ [ [], [] ] ] # Boş bir sayfa (sol ve sağ sütun boş)
            
            toplam_sayfa = len(self.sayfa_haritasi)

            if not hasattr(self, 'current_page') or self.current_page >= toplam_sayfa:
                self.current_page = max(0, toplam_sayfa - 1)
                
            # --- YENİ SIRALI NUMARALANDIRMA İÇİN OFFSET HESAPLAMA ---
            global_offset = 0
            for i in range(self.current_page):
                onceki_sayfa_sutunlari = self.sayfa_haritasi[i]
                global_offset += sum(len(sutun) for sutun in onceki_sayfa_sutunlari)
            
            # Sayfa navigasyon (varsa)
            if toplam_sayfa > 1:
                nav_frame = ctk.CTkFrame(pdf_container, fg_color="#ffffff", corner_radius=6, height=35)
                nav_frame.pack(anchor="ne", padx=10, pady=5)
                nav_frame.pack_propagate(False)

                if self.current_page > 0:
                    prev_btn = ctk.CTkButton(
                        nav_frame, text="◀",
                        command=lambda: self.change_page_new(self._last_pdf_container, self._last_controls_container, -1),
                        width=30, height=25, font=ctk.CTkFont(size=10, weight="bold"),
                        fg_color="#007bff", hover_color="#0056b3"
                    )
                    prev_btn.pack(side="left", padx=2, pady=5)

                page_info = ctk.CTkLabel(
                    nav_frame, text=f"{self.current_page + 1}/{toplam_sayfa}",
                    font=ctk.CTkFont(size=11, weight="bold"), text_color="#495057"
                )
                page_info.pack(side="left", padx=8, pady=5)

                if self.current_page < toplam_sayfa - 1:
                    next_btn = ctk.CTkButton(
                        nav_frame, text="▶",
                        command=lambda: self.change_page_new(self._last_pdf_container, self._last_controls_container, 1),
                        width=30, height=25, font=ctk.CTkFont(size=10, weight="bold"),
                        fg_color="#007bff", hover_color="#0056b3"
                    )
                    next_btn.pack(side="left", padx=2, pady=5)

            # PDF önizleme alanı
            preview_frame = ctk.CTkScrollableFrame(
                pdf_container, 
                fg_color="#e9ecef", 
                corner_radius=8
            )
            preview_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

            # --- YENİ GÖRSEL ALMA KISMI (SÜTUNLU HARİTADAN) ---
            bu_sayfanin_sutunlari = self.sayfa_haritasi[self.current_page]

            # PDF sayfası önizlemesi oluştur (Offset ile)
            pdf_preview = self.create_page_preview(bu_sayfanin_sutunlari, global_offset)

            if pdf_preview:
                pdf_label = tk.Label(
                    preview_frame,
                    image=pdf_preview,
                    bg="#e9ecef"
                )
                pdf_label.image = pdf_preview
                pdf_label.pack(expand=True, pady=5)
            else:
                error_text = "PDF önizlemesi oluşturulamadı"
                total_questions_on_page = sum(len(col) for col in bu_sayfanin_sutunlari)
                if total_questions_on_page == 0:
                    error_text = "Bu sayfada soru yok."
                error_label = ctk.CTkLabel(
                    preview_frame,
                    text=error_text,
                    font=ctk.CTkFont(size=14),
                    text_color="#dc3545"
                )
                error_label.pack(expand=True, pady=50)

        except Exception as e:
            self.logger.error(f"PDF önizleme yenileme hatası: {e}", exc_info=True)
    
    def create_controls_panel(self, controls_container, bu_sayfanin_sutunlari, pdf_container, global_offset):
        """
        Sağ kontrol panelini oluşturur.
        ARTIK SIRALI NUMARALANDIRMA ('global_offset + i + 1') kullanır.
        Sütunları düzleştirir.
        """
        # ÜST: Başlık Girişi (Entry)
        title_bar = ctk.CTkFrame(controls_container, fg_color="transparent")
        title_bar.pack(fill="x", padx=15, pady=(15, 10))
        
        title_entry = ctk.CTkEntry(
            title_bar,
            textvariable=self.baslik_text_var,
            placeholder_text="Lütfen başlık girin",
            height=36
        )
        title_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        if not getattr(self, "_title_trace_id", None):
            self._title_trace_id = self.baslik_text_var.trace_add(
                "write",
                lambda *args: self._refresh_preview_debounced(450)
            )
        def _on_destroy(_):
            try:
                if getattr(self, "_title_trace_id", None):
                    self.baslik_text_var.trace_remove("write", self._title_trace_id)
                    self._title_trace_id = None
            except Exception:
                pass
        title_entry.bind("<Destroy>", _on_destroy)

        # --- Scrollable frame ---
        scroll_frame = ctk.CTkScrollableFrame(
            controls_container,
            fg_color="#f8f9fa",
            corner_radius=8
        )
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # --- YENİ DÜZLEŞTİRME: Sütunları [SoruA, SoruC, SoruB, SoruD] şeklinde tek liste yap
        # 'planla_test_duzeni' sütunları PDF'e göre sıralar (Sol sütun önce dolar)
        # Bu yüzden bu sıralama PDF'teki sıralı numara ile %100 eşleşir.
        bu_sayfanin_soru_bilgileri_duz = []
        for sutun in bu_sayfanin_sutunlari:
            bu_sayfanin_soru_bilgileri_duz.extend(sutun)
        
        # --- Her soru için kontrol kartı ---
        for i, soru_info in enumerate(bu_sayfanin_soru_bilgileri_duz):
            
            gorsel_path = soru_info['path']
            
            # BUTONLAR İÇİN GÜVENLİ İNDİS (HÂLÂ GEREKLİ)
            gercek_global_index = soru_info['index'] 

            card = ctk.CTkFrame(
                scroll_frame,
                fg_color="#ffffff",
                corner_radius=10,
            )
            card.pack(fill="x", padx=10, pady=(8, 8))
    
            # <<< SIRALI NUMARA ÇÖZÜMÜ >>>
            soru_no = global_offset + i + 1
            
            try:
                cevap = get_answer_for_image(gorsel_path)
            except Exception:
                cevap = "?"
    
            try:
                konu_adi_tam = self.find_topic_from_path(gorsel_path) or "Bilinmeyen"
            except Exception:
                konu_adi_tam = "Bilinmeyen"
    
            # Üst satır (soru no & cevap)
            top_frame = ctk.CTkFrame(card, fg_color="transparent")
            top_frame.pack(fill="x", padx=15, pady=(15, 5))
    
            # 'soru_no' artık sıralı (1, 2, 3...)
            ctk.CTkLabel(
                top_frame, text=f"Soru {soru_no}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#2c3e50"
            ).pack(side="left")
    
            ctk.CTkLabel(
                top_frame, text=f"Cevap: {cevap}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#495057"
            ).pack(side="right")
    
            # Orta satır — i ikon + kısa konu + küçük butonlar
            header = ctk.CTkFrame(card, fg_color="transparent", height=44)
            header.pack(fill="x", padx=15, pady=(6, 6))
            header.pack_propagate(False)
            header.grid_columnconfigure(0, weight=0)
            header.grid_columnconfigure(1, weight=1)
            header.grid_columnconfigure(2, weight=0)
            
            info_icon = ctk.CTkLabel(
                header, text="🛈",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color="#334155",
                cursor="hand2"
            )
            info_icon.grid(row=0, column=0, sticky="w", padx=(0, 6))
            try:
                info_icon.bind("<Enter>", lambda e, t=konu_adi_tam: info_icon.configure(text=t))
                info_icon.bind("<Leave>", lambda e: info_icon.configure(text="🛈"))
            except Exception:
                pass
                
            MAX_LEN = 25
            konu_kisa = konu_adi_tam if len(konu_adi_tam) <= MAX_LEN else (konu_adi_tam[:MAX_LEN] + "…")
            ctk.CTkLabel(
                header, text=konu_kisa,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#1e293b"
            ).grid(row=0, column=1, sticky="w")
                
            btn_row = ctk.CTkFrame(header, fg_color="transparent")
            btn_row.grid(row=0, column=2, sticky="e")
    
            # --- BUTONLAR GÜVENLİ İNDİSİ KULLANMAYA DEVAM EDİYOR ---
            ctk.CTkButton(
                btn_row, text="🔄", width=34, height=30,
                fg_color="#e2e8f0", text_color="#1f2937",
                hover_color="#cbd5e1",
                command=lambda idx=gercek_global_index: self.gorseli_guncelle_new(idx)
            ).pack(side="left", padx=(0, 6))
    
            ctk.CTkButton(
                btn_row, text="🗑", width=34, height=30,
                fg_color="#fee2e2", text_color="#991b1b",
                hover_color="#fecaca",
                command=lambda idx=gercek_global_index: self.gorseli_kaldir_new(idx)
            ).pack(side="left")
    
        # --- Alt butonlar ---
        buttons_frame = ctk.CTkFrame(controls_container, fg_color="transparent", height=60)
        buttons_frame.pack(fill="x", padx=15, pady=(0, 15))
        buttons_frame.pack_propagate(False)
    
        button_container = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        button_container.pack(expand=True)
        
        ctk.CTkButton(
            button_container, text="PDF Oluştur",
            command=self.pdf_olustur,
            font=ctk.CTkFont(size=14, weight="bold"),
            width=160, height=40, corner_radius=10,
            fg_color="#28a745", hover_color="#218838"
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(
            button_container, text="Geri",
            command=self.geri_don,
            font=ctk.CTkFont(size=14, weight="bold"),
            width=100, height=40, corner_radius=10,
            fg_color="#6c757d", hover_color="#5a6268"
        ).pack(side="left")
    
    def change_page_new(self, pdf_container, controls_container, direction):
        """Yeni tasarımda sayfa değiştir (HARİTADAN OKUR)"""
        
        # --- YENİ PLANLANMIŞ MATEMATİK ---
        toplam_sayfa = len(self.sayfa_haritasi) # Plana bak

        new_page = self.current_page + direction
        if 0 <= new_page < toplam_sayfa:
            old_page = self.current_page
            self.current_page = new_page
            self.logger.debug(f"Sayfa değişti: {old_page + 1} -> {new_page + 1}")

            # 'display_images_new' fonksiyonu hem solu (PDF) hem sağı (Kontroller)
            # güncel haritaya göre yeniden çizer ve GEREKLİ offset'i hesaplar.
            self.display_images_new(pdf_container, controls_container)
    
    def gorseli_guncelle_new(self, index):
        """Yeni tasarımda görsel güncelle - YENİDEN PLANLAMA İLE"""
        try:
            if 0 <= index < len(self.secilen_gorseller):
                mevcut_gorsel_path = self.secilen_gorseller[index]
                mevcut_konu = self.find_topic_from_path(mevcut_gorsel_path)
                
                if not mevcut_konu:
                    self.show_error("Görselin hangi konudan geldiği bulunamadı!")
                    return
    
                soru_tipi = self.soru_tipi_var.get()
                zorluk = self.zorluk_var.get()
                konu_path = self.secilen_konular[mevcut_konu]
                klasor_yolu = os.path.join(konu_path, soru_tipi.lower(), zorluk.lower())
    
                # Klasördeki tüm görselleri al
                tum_gorseller = [f for f in os.listdir(klasor_yolu) 
                               if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
    
                if not tum_gorseller:
                    self.show_error("Güncellenecek görsel bulunamadı!")
                    return
    
                # *** YENİ: Kullanılmamış görselleri bul ***
                kullanilmamis_gorseller = [
                    f for f in tum_gorseller 
                    if f not in self.kullanilan_sorular[mevcut_konu]
                ]
    
                if not kullanilmamis_gorseller:
                    # *** YENİ: Havuz tükendi, kullanıcıya sor (parametresiz) ***
                    self.show_havuz_tukendi_dialog(mevcut_konu, index)
                    return
    
                # Rastgele yeni görsel seç
                import random
                yeni_gorsel_dosya = random.choice(kullanilmamis_gorseller)
                yeni_gorsel_path = os.path.join(klasor_yolu, yeni_gorsel_dosya)
                
                # *** YENİ: Eski görseli kullanılan listesinde tut, yenisini ekle ***
                eski_gorsel_dosya = os.path.basename(mevcut_gorsel_path)
                self.kullanilan_sorular[mevcut_konu].add(yeni_gorsel_dosya)
                
                # Güncelle
                self.secilen_gorseller[index] = yeni_gorsel_path
                self.logger.info(f"Görsel güncellendi: {eski_gorsel_dosya} -> {yeni_gorsel_dosya}")
    
                # --- ESKİ YENİLEMEYİ SİL ---
                # self.refresh_pdf_preview_only(pdf_container)
                
                # --- YENİ SENKRONİZASYONU EKLE ---
                self._replan_and_refresh_ui()
    
        except Exception as e:
            self.logger.error(f"Görsel güncelleme hatası: {e}")
            self.show_error("Görsel güncellerken bir hata oluştu!")
    
    def gorseli_kaldir_new(self, index):
        """Yeni tasarımda görsel kaldır - YENİDEN PLANLAMA İLE"""
        try:
            if 0 <= index < len(self.secilen_gorseller):
                kaldirilan_gorsel_path = self.secilen_gorseller.pop(index)

                # *** YENİ: Silinen görseli kullanılan listesinde tut ***
                kaldirilan_konu = self.find_topic_from_path(kaldirilan_gorsel_path)
                if kaldirilan_konu:
                    kaldirilan_dosya = os.path.basename(kaldirilan_gorsel_path)
                    # Silinen soru kullanılan listesinde kalır (tekrar gelmez)
                    self.logger.info(f"Silinen görsel kullanılan listesinde tutuldu: {kaldirilan_dosya}")

                self.logger.info(f"Görsel kaldırıldı: {os.path.basename(kaldirilan_gorsel_path)}")

                if not self.secilen_gorseller:
                    self.show_notification(
                        "Uyarı",
                        "Tüm görseller kaldırıldı!\nYeni seçim yapmak için 'Geri' butonuna tıklayın.",
                        geri_don=False 
                    )
                    # Ekranı boşaltmak için yine de planı yenile
                    self._replan_and_refresh_ui()
                    return

                # --- ESKİ YENİLEMEYİ VE SAYFA KONTROLÜNÜ SİL ---
                # sorular_per_sayfa = self._get_sorular_per_sayfa()
                # ...
                # self.refresh_pdf_preview_only(pdf_container)
                
                # --- YENİ SENKRONİZASYONU EKLE ---
                self._replan_and_refresh_ui()

        except Exception as e:
            self.logger.error(f"Görsel kaldırma hatası: {e}")
            self.show_error("Görsel kaldırılırken bir hata oluştu!")
    def show_havuz_tukendi_dialog(self, konu_adi, index):
        """Havuz tükendiğinde kullanıcıya sor"""

        dialog_window = ctk.CTkToplevel(self.master)
        dialog_window.title("Soru Havuzu Tükendi")
        dialog_window.geometry("450x300")
        dialog_window.resizable(False, False)
        dialog_window.transient(self.master)
        dialog_window.grab_set()

        # Merkeze yerleştir
        self.master.update_idletasks()
        x = self.master.winfo_x() + self.master.winfo_width()//2 - 225
        y = self.master.winfo_y() + self.master.winfo_height()//2 - 150
        dialog_window.geometry(f"+{x}+{y}")

        # İkon
        icon_label = ctk.CTkLabel(
            dialog_window,
            text="🔄",
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack(pady=20)

        # Mesaj
        message = f"'{konu_adi}' konusundaki tüm sorular kullanıldı.\n\nSoru havuzunu sıfırlayarak baştan başlamak ister misiniz?"
        message_label = ctk.CTkLabel(
            dialog_window,
            text=message,
            font=ctk.CTkFont(size=14),
            justify="center",
            wraplength=400
        )
        message_label.pack(pady=20, padx=20)

        # Butonlar
        button_frame = ctk.CTkFrame(dialog_window, fg_color="transparent")
        button_frame.pack(pady=20)

        def sifirla_ve_guncelle():
            # Havuzu sıfırla
            self.kullanilan_sorular[konu_adi] = set()
            dialog_window.destroy()
            # Güncellemeyi tekrar dene (artık pdf_container parametresi olmadan)
            self.gorseli_guncelle_new(index)

        def iptal():
            dialog_window.destroy()

        # Evet butonu
        evet_btn = ctk.CTkButton(
            button_frame,
            text="Evet, Sıfırla",
            command=sifirla_ve_guncelle,
            font=ctk.CTkFont(size=14, weight="bold"),
            width=120,
            height=40,
            fg_color="#28a745",
            hover_color="#218838"
        )
        evet_btn.pack(side="left", padx=10)

        # Hayır butonu
        hayir_btn = ctk.CTkButton(
            button_frame,
            text="Hayır",
            command=iptal,
            font=ctk.CTkFont(size=14, weight="bold"),
            width=80,
            height=40,
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        hayir_btn.pack(side="left", padx=10)                             
    def find_topic_from_path(self, gorsel_path):
        """Görsel yolundan hangi konudan geldiğini bul"""
        try:
            for konu_adi, konu_path in self.secilen_konular.items():
                if konu_path in gorsel_path:
                    return konu_adi
            return None
        except Exception as e:
            self.logger.error(f"Konu bulma hatası: {e}")
            return None
    
    def _get_sorular_per_sayfa(self):
        """Soru tipine göre sayfa başı soru sayısını döndür"""
        soru_tipi = self.soru_tipi_var.get().lower()
        return 2 if soru_tipi == "yazili" else 8

    def create_page_preview(self, bu_sayfanin_sutunlari, global_offset):
        """
        Bir sayfa için PDF önizlemesi oluşturur.
        ARTIK 'bu_sayfanin_sutunlari' (örn: [ [sol_liste], [sağ_liste] ]) alır.
        """
        self.logger.debug(f"Sayfa önizlemesi oluşturuluyor - {sum(len(s) for s in bu_sayfanin_sutunlari)} görsel, offset: {global_offset}")

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
            self._draw_title_on_image(template_copy)
            self.logger.debug(f"Şablon yüklendi - Boyut: {template_copy.size}")

            # Soru tipine göre layout hesapla
            template_width, template_height = template_copy.size
            
            # 'bu_sayfanin_sutunlari' listesini (örn: [ [sol_liste], [sağ_liste] ])
            # ve 'global_offset'i aktar
            if soru_tipi == "yazili":
                # Yazılı modu 1 sütunludur, bu yüzden sütunları düzleştirip gönder
                sayfa_gorselleri_bilgileri_duz = []
                for sutun in bu_sayfanin_sutunlari:
                    sayfa_gorselleri_bilgileri_duz.extend(sutun)
                self._create_yazili_preview(template_copy, sayfa_gorselleri_bilgileri_duz, template_width, template_height, global_offset)
            else:
                # --- NİZAM (GÖRSELLİK) ÇÖZÜMÜ BURADA ÇAĞRILIYOR ---
                self._create_test_preview_BestFit(template_copy, bu_sayfanin_sutunlari, template_width, template_height, global_offset)

            # Önizleme için boyutlandır (oranı koru)
            preview_width = 600
            preview_height = int(2000 * preview_width / 1414) # A4 Oranı
            
            resampling_filter = Image.Resampling.LANCZOS if hasattr(Image.Resampling, "LANCZOS") else Image.ANTIALIAS
            template_copy = template_copy.resize((preview_width, preview_height), resampling_filter)

            self.logger.debug("Sayfa önizlemesi başarıyla oluşturuldu")
            return ImageTk.PhotoImage(template_copy)

        except Exception as e:
            self.logger.error(f"Sayfa önizleme hatası: {e}", exc_info=True)
            return None
        
    def _create_yazili_preview(self, sayfa_gorselleri_bilgileri_duz, template_width, template_height, global_offset):
        """Yazılı şablonu önizleme layout'u (ARTIK DOĞRU SIRALI NUMARA)"""
        self.logger.debug("Yazılı önizleme layout'u uygulanıyor")
        
        top_margin = int(template_height * 0.1)
        left_margin = int(template_width * 0.05)
        right_margin = int(template_width * 0.05)
        bottom_margin = int(template_height * 0.05)
        usable_width = template_width - left_margin - right_margin
        usable_height = template_height - top_margin - bottom_margin
        
        max_soru = 2 # Yazılı için 2 soru
        soru_ve_cevap_yuksekligi = usable_height // max_soru 
        yazili_soru_height = int(soru_ve_cevap_yuksekligi * 0.7) 
        yazili_soru_width = usable_width  # Tam genişlik

        self.logger.debug(f"Yazılı layout boyutları - Genişlik: {yazili_soru_width}, Yükseklik: {yazili_soru_height}")

        # Görselleri yerleştir
        for i, soru_info in enumerate(sayfa_gorselleri_bilgileri_duz):
            if i >= max_soru:
                self.logger.warning(f"Yazılı önizlemede maksimum {max_soru} soru gösterilebilir.")
                break
                
            try:
                gorsel_path = soru_info['path']
                # <<< SIRALI NUMARA ÇÖZÜMÜ >>>
                soru_no = global_offset + i + 1
                
                x = left_margin
                y = top_margin + i * soru_ve_cevap_yuksekligi

                soru_img = Image.open(gorsel_path)
                
                # Oranı koruyarak sığdır
                img_ratio = soru_img.width / soru_img.height
                final_width = yazili_soru_width
                final_height = int(final_width / img_ratio)

                if final_height > yazili_soru_height:
                    final_height = yazili_soru_height
                    final_width = int(final_height * img_ratio)
                
                # Sığdırılan resmi ortala
                paste_x = x + (yazili_soru_width - final_width) // 2
                
                resampling_filter = Image.Resampling.LANCZOS if hasattr(Image.Resampling, "LANCZOS") else Image.ANTIALIAS
                soru_img = soru_img.resize((final_width, final_height), resampling_filter)
                template_copy.paste(soru_img, (int(paste_x), int(y)))

                # Soru numarası ekle (ARTIK 'soru_no' DOĞRU)
                draw = ImageDraw.Draw(template_copy)
                try:
                    font = ImageFont.truetype("arialbd.ttf", 30) # Biraz daha büyük
                except:
                    try:
                        font = ImageFont.truetype("arial.ttf", 30)
                    except:
                        font = ImageFont.load_default()

                # Numarayı sol üste (sorunun değil, alanın sol üstüne) koy
                draw.text((x, y), f"{soru_no}.", fill="#333333", font=font)
                
                self.logger.debug(f"Yazılı soru {soru_no} yerleştirildi - Boyut: {final_width}x{final_height}")

            except Exception as e:
                self.logger.error(f"Yazılı soru {i+1} yerleştirme hatası: {e}", exc_info=True)
                
    def _create_test_preview_BestFit(self, template_copy, bu_sayfanin_sutunlari, template_width, template_height, global_offset):
        """
        Test şablonu önizleme layout'u (NİZAMİ GÖRÜNÜM + SIRALI NUMARA)
        'planla_test_duzeni'nden gelen SÜTUNLU haritayı okur ve çizer.
        HATASIZ VERSİYON.
        """
        self.logger.debug(f"Test önizleme (BestFit NİZAMİ) layout'u uygulanıyor - {sum(len(s) for s in bu_sayfanin_sutunlari)} soru")

        # --- 1. PDF GENERATOR İLE AYNI SABİTLERİ TANIMLA ---
        A4_W, A4_H = 595.27, 841.89
        template_W, template_H = template_width, template_height
        
        scale_factor = template_H / A4_H 
        
        top_margin = 50 * scale_factor
        bottom_margin = 5 * scale_factor
        left_margin = 20 * scale_factor
        right_margin = 20 * scale_factor
        col_gap = 40 * scale_factor
        cols = 2
        
        # --- NUMARA BOYUTU DÜZELTMESİ ---
        soru_numara_font_size = int(12 * scale_factor) # 16'dan 12'ye düşürüldü
        
        soru_spacing = 8 * scale_factor
        image_spacing = 10 * scale_factor

        col_width = (template_W - left_margin - right_margin - col_gap) / cols
        
        current_x_positions = [left_margin + i * (col_width + col_gap) for i in range(cols)]
        
        # PIL (0,0 sol üst) mantığıyla Y (dikey) pozisyonları (Tepeden başlar)
        current_y_positions_tepe = [top_margin for _ in range(cols)] 

        yerlestirildi_sayaci = 0 # Bu, 'global_offset'e eklenecek sıralı sayaçtır
        
        draw = ImageDraw.Draw(template_copy)
        try:
            numara_font = ImageFont.truetype("arialbd.ttf", soru_numara_font_size)
        except:
            try:
                numara_font = ImageFont.truetype("arial.ttf", soru_numara_font_size)
            except:
                numara_font = ImageFont.load_default()

        # --- 2. SÜTUNLU PLANI ÇİZ ---
        for sutun_index in range(cols):
            sutun_sorulari = bu_sayfanin_sutunlari[sutun_index]
            img_x = current_x_positions[sutun_index]
            
            for soru_info in sutun_sorulari:
                
                scaled_width = soru_info['final_size'][0] * scale_factor
                scaled_height = soru_info['final_size'][1] * scale_factor
                
                pil_y_top = current_y_positions_tepe[sutun_index] + soru_spacing
                
                try:
                    soru_img = Image.open(soru_info['path'])
                    resampling_filter = Image.Resampling.LANCZOS if hasattr(Image.Resampling, "LANCZOS") else Image.ANTIALIAS
                    soru_img = soru_img.resize((int(scaled_width), int(scaled_height)), resampling_filter)
                    
                    template_copy.paste(soru_img, (int(img_x), int(pil_y_top)))
                    
                    soru_no = global_offset + yerlestirildi_sayaci + 1
                    
                    numara_x = img_x - (15 * scale_factor)
                    numara_y = pil_y_top 
                    if soru_no >= 10:
                        numara_x -= (5 * scale_factor) 
                        
                    draw.text((numara_x, numara_y), f"{soru_no}.", fill="#333333", font=numara_font)

                except Exception as e:
                    self.logger.error(f"PIL Gorsel cizim hatasi: {soru_info['path']}", exc_info=True)
                    continue

                current_y_positions_tepe[sutun_index] = pil_y_top + scaled_height + image_spacing
                yerlestirildi_sayaci += 1
                
        self.logger.info(f"Test önizleme (BestFit NİZAMİ) tamamlandi - {yerlestirildi_sayaci} soru yerlestirildi")
                   
    def geri_don(self):
        """Soru parametre seçim ekranına geri dön"""
        try:
            self.logger.info("Geri dön butonuna tıklandı")
            
            # *** YENİ: Geri dönüşte havuzu sıfırla (yeni seçim için) ***
            self._havuzu_sifirla()
            self.logger.info("Geri dönüş - Havuz sıfırlandı")
            
            # Form içeriğini temizle ve seçim widget'larını yeniden oluştur
            for widget in self.form_frame.winfo_children():
                widget.destroy()

            self.create_selection_widgets()
            self.logger.debug("Seçim ekranına geri dönüldü")

        except Exception as e:
            self.logger.error(f"Geri dönüş hatası: {e}")
            # Hata durumunda konu başlık seçimine dön
            self.konu_baslik_sayfasina_don()

    def pdf_olustur(self):
        """PDF oluştur ve kullanıcıya bildir (ARTIK 'HARİTA' GÖNDERİYOR)"""
        self.logger.info(f"PDF oluşturma başlatıldı - {self.ders_adi}")
        
        try:
            try:
                import reportlab
                self.logger.debug("Reportlab modülü mevcut")
            except ImportError:
                self.logger.error("Reportlab modülü bulunamadı")
                self.show_notification(
                    "Eksik Modül",
                    "PDF oluşturmak için 'reportlab' modülü gerekli.\n\nÇözüm: Terminal'e şunu yazın:\npip install reportlab"
                )
                return
            try:
                self.logger.debug("PDFCreator import edildi")
            except ImportError as e:
                self.logger.error(f"PDFCreator import hatası: {e}")
                self.basit_pdf_olustur()
                return
            try:
                cevap_bilgisi_mevcut = True
                self.logger.debug("Cevap bilgisi modülü mevcut")
            except ImportError:
                cevap_bilgisi_mevcut = False
                self.logger.warning("Cevap bilgisi modülü bulunamadı")


            # PDF oluştur
            pdf = PDFCreator()
            pdf.soru_tipi = self.soru_tipi_var.get()

            # Başlık oluştur
            konu_listesi = ", ".join(list(self.konu_soru_dagilimi.keys())[:3])
            if len(self.konu_soru_dagilimi) > 3:
                konu_listesi += f" ve {len(self.konu_soru_dagilimi)-3} konu daha"

            baslik = f"{self.ders_adi} - {konu_listesi} - {self.soru_tipi_var.get()} - {self.zorluk_var.get()}"
            pdf.baslik_ekle(baslik)

            self.logger.debug(f"PDF'e geçen soru tipi: {self.soru_tipi_var.get()}")

            # Görselleri ekle (Ana listeyi 'gorsel_listesi'ne kopyala)
            pdf.gorsel_listesi = self.secilen_gorseller[:]
            
            cevaplar = []
            for idx, gorsel in enumerate(self.secilen_gorseller, 1):
                try:
                    cevap = get_answer_for_image(gorsel)
                    cevaplar.append(cevap)
                except Exception as e:
                    self.logger.error(f"Görsel {idx} için cevap alınamadı: {e}")
            
            # Cevap anahtarı kontrolü
            cevap_anahtari_isteniyor = self.cevap_anahtari_var.get() == "Evet"
            self.logger.info(f"Cevap anahtarı kontrolü: {cevap_anahtari_isteniyor}")

            if cevap_anahtari_isteniyor and cevaplar:
                pdf.cevap_anahtari_ekle(cevaplar)
                try:
                    bilinmeyen = sum(1 for c in cevaplar if str(c).strip() == "?")
                    if bilinmeyen > 0:
                        oran = int(100 * bilinmeyen / max(1, len(cevaplar)))
                        info = f"Cevap anahtarında {bilinmeyen}/{len(cevaplar)} soru için cevap bulunamadı (%{oran})."
                        self.logger.warning(info)
                        try:
                            self._show_dialog("Cevap Anahtarı Uyarısı", info, "#ffc107")
                        except Exception:
                            pass
                except Exception:
                    pass
            elif not cevap_anahtari_isteniyor:
                self.logger.info("Cevap anahtarı kullanıcı tercihi ile eklenmedi")
            

            # Kaydetme konumu sor
            cikti_dosya = filedialog.asksaveasfilename(
                title="PDF'i Nereye Kaydetmek İstersiniz?",
                defaultextension=".pdf",
                filetypes=[("PDF Dosyası", "*.pdf")],
                initialfile=f"{self.ders_adi}_{self.soru_tipi_var.get()}_{self.zorluk_var.get()}_{len(self.secilen_gorseller)}_soru.pdf"
            )

            if cikti_dosya:
                self.logger.info(f"PDF kaydediliyor: {cikti_dosya}")
                
                # --- TEK BEYİN ÇÖZÜMÜ ---
                # Önizleme için kullandığımız 'sayfa_haritasi'nı (planı)
                # 'kaydet' fonksiyonuna parametre olarak gönderiyoruz.
                if pdf.kaydet(cikti_dosya, self.sayfa_haritasi):
                    kayit_yeri = f"{os.path.basename(os.path.dirname(cikti_dosya))}/{os.path.basename(cikti_dosya)}"
                    
                    self.logger.info(f"PDF başarıyla oluşturuldu: {os.path.basename(cikti_dosya)}")
                    
                    self.show_notification(
                        "PDF Başarıyla Oluşturuldu!",
                        f"Kayıt Yeri: {kayit_yeri}\n\n{len(self.secilen_gorseller)} soru PDF formatında kaydedildi\n\nKonu Dağılımı:\n" + 
                        "\n".join([f"• {konu}: {sayi} soru" for konu, sayi in self.konu_soru_dagilimi.items()])
                    )
                else:
                    self.logger.error("PDF kaydedilemedi")
                    self.show_notification(
                        "PDF Oluşturulamadı",
                        "PDF oluşturulurken bir hata oluştu.\nLütfen tekrar deneyin."
                    )
            else:
                self.logger.info("Kullanıcı PDF kaydetmeyi iptal etti")

        except Exception as e:
            self.logger.error(f"PDF oluşturma genel hatası: {e}")
            self.show_notification(
                "Hata",
                f"Beklenmeyen bir hata oluştu:\n{str(e)}\n\nLütfen konsolu kontrol edin."
            )
    
    def basit_pdf_olustur(self):
        """Basit PDF oluşturma - PDFCreator sınıfı import edilemediğinde"""
        self.logger.warning("Basit PDF oluşturma moduna geçildi")
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.lib import colors

            # Kaydetme konumu sor
            cikti_dosya = filedialog.asksaveasfilename(
                title="PDF'i Nereye Kaydetmek İstersiniz?",
                defaultextension=".pdf",
                filetypes=[("PDF Dosyası", "*.pdf")],
                initialfile=f"{self.ders_adi}_{self.soru_tipi_var.get()}_{self.zorluk_var.get()}_{len(self.secilen_gorseller)}_soru.pdf"
            )

            if not cikti_dosya:
                self.logger.info("Basit PDF kaydetme iptal edildi")
                return

            # PDF oluştur
            story = []
            styles = getSampleStyleSheet()

            # Başlık ekle
            konu_listesi = ", ".join(list(self.konu_soru_dagilimi.keys())[:2])
            if len(self.konu_soru_dagilimi) > 2:
                konu_listesi += f" ve diğerleri"
            
            baslik_text = f"{self.ders_adi} - {konu_listesi} - {self.soru_tipi_var.get()} - {self.zorluk_var.get()}"
            baslik = Paragraph(baslik_text, styles["Title"])
            story.append(baslik)
            story.append(Spacer(1, 0.5*inch))

            # Görselleri ekle
            for gorsel_yolu in self.secilen_gorseller:
                try:
                    img = Image(gorsel_yolu, width=6*inch, height=4*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.3*inch))
                except Exception as e:
                    self.logger.error(f"Basit PDF görsel ekleme hatası: {e}")

            # PDF'i kaydet
            doc = SimpleDocTemplate(cikti_dosya, pagesize=letter)
            doc.build(story)

            self.logger.info(f"Basit PDF başarıyla oluşturuldu: {os.path.basename(cikti_dosya)}")

            self.show_notification(
                "PDF Başarıyla Oluşturuldu!",
                f"Kayıt Yeri: {os.path.basename(cikti_dosya)}\n\n{len(self.secilen_gorseller)} soru PDF formatında kaydedildi"
            )

        except Exception as e:
            self.logger.error(f"Basit PDF oluşturma hatası: {e}")
            self.show_notification(
                "Hata",
                f"PDF oluşturulurken hata: {str(e)}"
            )

    def show_error(self, message):
        """Hata mesajını göster"""
        self.logger.warning(f"Hata mesajı gösteriliyor: {message}")
        self._show_dialog("Uyarı", message, "#dc3545")

    def show_notification(self, title, message, geri_don=False):
        """Bildirim göster"""
        self.logger.info(f"Bildirim gösteriliyor - {title}: {message[:50]}...")
        
        notify_window = ctk.CTkToplevel(self.master)
        notify_window.title(title)
        notify_window.geometry("500x350")
        notify_window.resizable(False, False)
        notify_window.transient(self.master)
        notify_window.grab_set()

        self.master.update_idletasks()
        master_x = self.master.winfo_x()
        master_y = self.master.winfo_y()
        master_width = self.master.winfo_width()
        master_height = self.master.winfo_height()

        modal_width = 500
        modal_height = 350

        x = master_x + (master_width // 2) - (modal_width // 2)
        y = master_y + (master_height // 2) - (modal_height // 2)
        notify_window.geometry(f"{modal_width}x{modal_height}+{x}+{y}")

        icon_label = ctk.CTkLabel(
            notify_window,
            text="✅" if "Başarıyla" in title else "⚠️",
            font=ctk.CTkFont(size=48),
            text_color="#27ae60" if "Başarıyla" in title else "#e74c3c"
        )
        icon_label.pack(pady=20)

        message_label = ctk.CTkLabel(
            notify_window,
            text=message,
            font=ctk.CTkFont(size=12),
            justify="center",
            wraplength=450
        )
        message_label.pack(pady=10, padx=20)

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

    def show_multipage_info(self, istenen_sayi, on_close=None):
        """Yazılı çoklu sayfa bilgilendirmesi göster. on_close: kapatınca çağrılır."""
        import math
        sayfa_sayisi = math.ceil(istenen_sayi / 2)
        
        message = (
            f"Yazılı şablonunda görsel kalitesi için\n"
            f"sayfa başına maksimum 2 soru yerleştirilir.\n\n"
            f"Seçtiğiniz soru sayısı: {istenen_sayi}\n"
            f"Oluşacak sayfa sayısı: {sayfa_sayisi}\n\n"
            f"Kaliteli PDF için bu şekilde devam edilecek."
        )
    
        # Bilgilendirme penceresi (sadece "Tamam" butonu)
        try:
            dialog_window = ctk.CTkToplevel(self.controller)
            dialog_window.title("Yazılı PDF Bilgisi")
            dialog_window.geometry("480x320")
            dialog_window.resizable(False, False)
            dialog_window.transient(self.controller)
            dialog_window.grab_set()

            # Ortala
            try:
                x = int(self.controller.winfo_x() + self.controller.winfo_width()/2 - 240)
                y = int(self.controller.winfo_y() + self.controller.winfo_height()/2 - 160)
                dialog_window.geometry(f"+{x}+{y}")
            except:
                pass

            icon_label = ctk.CTkLabel(dialog_window, text="ℹ️", font=ctk.CTkFont(size=48), text_color="#17a2b8")
            icon_label.pack(pady=(24, 10))

            message_label = ctk.CTkLabel(
                dialog_window, text=message, font=ctk.CTkFont(size=15, weight="bold"),
                justify="center", wraplength=420, text_color="#2c3e50"
            )
            message_label.pack(padx=20)

            def _close():
                try:
                    dialog_window.destroy()
                finally:
                    if callable(on_close):
                        on_close()

            ok_btn = ctk.CTkButton(
                dialog_window, text="Tamam", width=110, height=38, corner_radius=10,
                fg_color="#17a2b8", hover_color=self._darken_color("#17a2b8"), command=_close
            )
            ok_btn.pack(pady=20)
        except Exception:
            # Diyalog oluşturulamazsa yine de devam et
            if callable(on_close):
                on_close()

    def _darken_color(self, hex_color):
        """Rengi koyulaştır"""
        color_map = {
             "#27ae60": "#229954",
             "#e74c3c": "#c0392b",
             "#dc3545": "#c82333",
             "#ffc107": "#e0a800",
             "#17a2b8": "#138496"
        }
        return color_map.get(hex_color, hex_color)

    def _proceed_to_preview(self, soru_tipi, zorluk):
        """Bilgilendirme sonrası güvenle önizleme akışına geç."""
        try:
            self.secilen_gorseller = self.secili_gorselleri_al(soru_tipi, zorluk)
            
            if not self.secilen_gorseller:
                self.logger.error("Hiç görsel seçilemedi")
                self.show_error("Seçilen konularda görsel bulunamadı!")
                return

            # --- YENİ EKLENEN PLANLAMA ADIMI ---
            self.logger.info("BestFit planlaması başlatılıyor...")
            pdf_planner = PDFCreator()
            pdf_planner.gorsel_listesi = self.secilen_gorseller
            
            if soru_tipi.lower() == "test":
                # 'pdf_generator'dan gelen YENİ BEYİN fonksiyonunu çağır
                self.sayfa_haritasi = pdf_planner.planla_test_duzeni()
            else:
                # Yazılı modu için basit planlama (2'li gruplar)
                # 'planla_test_duzeni'nin formatına benzetiyoruz
                self.logger.info("Yazılı (basit) planlaması başlatılıyor...")
                soru_listesi = [
                    {'index': i, 'path': path, 'total_height': 500} # Yükseklik tahmini
                    for i, path in enumerate(self.secilen_gorseller)
                ]
                self.sayfa_haritasi = [soru_listesi[i:i+2] for i in range(0, len(soru_listesi), 2)]
            # --- PLANLAMA BİTTİ ---

            if self.sayfa_haritasi:
                self.logger.info(f"{len(self.secilen_gorseller)} görsel {len(self.sayfa_haritasi)} sayfaya planlandı.")
                self.current_page = 0 # Sayfayı sıfırla
                self.gorsel_onizleme_alani_olustur() # Önizlemeyi oluştur
            else:
                self.logger.error("Hiç görsel seçilemedi (planlama sonucu boş)")
                self.show_error("Seçilen konularda görsel bulunamadı!")

        except Exception as e:
            self.logger.error(f"Önizleme akışında hata: {e}", exc_info=True)
            self.show_error(f"Önizleme oluşturulurken hata oluştu: {e}")
            
    def update_total(self):
        """Toplam seçilen soru sayısını canlı güncelle"""
        try:
            toplam = 0
            for var in self.konu_entry_vars.values():
                try:
                    val = int(var.get())
                    if val > 0:
                        toplam += val
                except Exception:
                    continue
            if hasattr(self, 'total_label') and self.total_label.winfo_exists():
                self.total_label.configure(text=f"Toplam Seçilen Soru: {toplam}")
        except Exception:
            pass

if __name__ == "__main__":
    root = ctk.CTk()
    root.state('zoomed')
    app = SoruParametresiSecmePenceresi(root, None, ".")
    root.mainloop()