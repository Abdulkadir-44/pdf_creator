import customtkinter as ctk
import tkinter as tk
import os
import sys
from tkinter import filedialog
import logging
from datetime import datetime
from logic.answer_utils import get_answer_for_image
from logic.pdf_generator import PDFCreator
from ui.widgets.tooltip import ToolTip
from ui.dialog_yoneticisi import DialogYoneticisi
from ui.parametre_sayfasi.parametre_secim_formu import ParametreSecimFormu
from ui.parametre_sayfasi.onizleme_ekrani import OnizlemeEkrani
from ui.parametre_sayfasi.kontrol_paneli import KontrolPaneli
from logic.onizleme_cizici import OnizlemeCizici
from ui.parametre_sayfasi.sayfa_basligi import SayfaBasligi
from logic.oturum_yoneticisi import OturumYoneticisi

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
        self.parametre_formu = None # Yeni form sınıfı için bir tutucu
        self.onizleme_ekrani = None # YENİ: Önizleme ekranı sınıfı için tutucu
        self.kontrol_paneli = None  # YENİ: Sağ kontrol paneli sınıfı için tutucu
        self.sayfa_basligi = None   # YENİ: Başlık (Header) sınıfı için tutucu
        self.konu_soru_dagilimi = {}  # Her konudan kaç soru seçileceği
        self.soru_tipi_var = tk.StringVar(value="Soru tipi seçin...")
        self.zorluk_var = tk.StringVar(value="Zorluk seviyesi seçin...")
        self.cevap_anahtari_var = tk.StringVar(value="Cevap anahtarı eklensin mi?")

        
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
        
        # Dialog Yöneticisini BAŞLAT (UI'dan ÖNCE)
        self.dialog_yoneticisi = DialogYoneticisi(self)
        
        # YENİ: Oturum Yöneticisini (Beyin) başlat
        self.oturum_yoneticisi = OturumYoneticisi(self)
        
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

        # Header bölümü ekle (Yeni Sınıf ile)
        header_callbacks = {
            'on_ana_menu': self.ana_menuye_don,
            'on_konu_secimi': self.konu_baslik_sayfasina_don
        }
        self.sayfa_basligi = SayfaBasligi(
            parent=self.main_container, # 'main_container'ın İÇİNE
            controller=self,
            ders_adi=self.ders_adi,
            callbacks=header_callbacks
        )


        # Mevcut main_frame kodunu main_container'ın içine al:
        self.main_frame = ctk.CTkFrame(self.main_container, corner_radius=20, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=(10, 10))

        # YENİ: Bu, Ekran 1 (Form) veya Ekran 2 (Önizleme) 
        # arasında geçiş yapacak olan "ana içerik" çerçevesidir.
        self.icerik_cercevesi = ctk.CTkFrame(
            self.main_frame, 
            corner_radius=15, 
            fg_color="#f8f9fa", # Form'un varsayılan rengiyle başla
            border_width=1, 
            border_color="#e9ecef"
        )
        self.icerik_cercevesi.pack(fill="both", expand=True, padx=10, pady=5)

        # ESKİ: self.create_selection_widgets()
        # YENİ:
        self.goster_parametre_formu() # Başlangıçta Form Ekranını Göster
        self.logger.info("UI kurulumu tamamlandı")
    
    def goster_parametre_formu(self):
        """
        Form ekranını (ParametreSecimFormu) oluşturur ve gösterir.
        Bu, 'geri_don' veya ilk açılışta çağrılır.
        """
        self.logger.debug("Parametre seçim formu gösteriliyor...")
        
        # 1. Önceki içeriği (Önizleme ekranı vs.) temizle
        for widget in self.icerik_cercevesi.winfo_children():
            widget.destroy()

        # 2. Varsa eski form nesnesini de temizle
        if self.parametre_formu:
            self.parametre_formu.destroy()
            self.parametre_formu = None
        
        # 3. İçerik çerçevesini formun arka plan rengine ayarla
        self.icerik_cercevesi.configure(fg_color="#f8f9fa", border_color="#e9ecef")

        # 4. Yeni formu 'self.icerik_cercevesi'nin içine oluştur
        self.parametre_formu = ParametreSecimFormu(
            parent_frame=self.icerik_cercevesi, # 'self.icerik_cercevesi'nin içine
            controller=self,                  # Ana sınıfı (kendisini) controller olarak ver
            on_devam_et_callback=self._form_onaylandi_callback # Başarı sinyali
        )
        self.parametre_formu.pack(fill="both", expand=True) # Formu doldur

    def _form_onaylandi_callback(self, konu_soru_dagilimi):
        """
        ParametreSecimFormu'ndan 'Devam Et' sinyali geldiğinde çağrılır.
        Akışı 'Beyin'e (OturumYoneticisi) yönlendirir.
        """
        self.logger.info("Form onayı alındı. Önizleme akışına geçiliyor.")

        # Formdan gelen 'konu_soru_dagilimi' state'ini ana sınıfa kaydet
        self.konu_soru_dagilimi = konu_soru_dagilimi

        # Diğer değişkenler (soru_tipi, zorluk) zaten ana sınıftaki
        # tk.StringVar'lar aracılığıyla güncellendi.
        soru_tipi = self.soru_tipi_var.get()
        zorluk = self.zorluk_var.get()

        # İşi "Beyin"e delege et
        self.oturum_yoneticisi._proceed_to_preview(soru_tipi, zorluk)
       

    def _refresh_preview_left_now(self):
        """Sadece sol panel (önizleme) yeniden çizilir, sağ taraf dokunulmaz."""
        try:
            if hasattr(self, 'onizleme_ekrani') and self.onizleme_ekrani:
                # ✅ YENİ: Sadece PDF önizlemesini yenile
                self.refresh_pdf_preview_only() # <-- Argümanı sildik
            else:
                # İlk kez çalışıyorsa tüm önizlemeyi başlat
                self.gorsel_onizleme_alani_olustur()
        except Exception as e:
            print("Önizleme yenilenemedi:", e)

    def refresh_pdf_preview_only(self):
        """SADECE sol PDF önizleme panelini yeniler..."""
        
        # --- GÜNCELLENMİŞ BLOK ---
        if not hasattr(self, 'onizleme_ekrani') or not self.onizleme_ekrani:
            self.logger.warning("refresh_pdf_preview_only: OnizlemeEkrani bulunamadı.")
            return

        # Gerekli referansları 'self.onizleme_ekrani' nesnesinden al
        pdf_container = self.onizleme_ekrani.pdf_container
        # --- BLOK GÜNCELLENDİ ---
    
        try:
            # Sadece sol paneli temizle
            for widget in pdf_container.winfo_children():
                widget.destroy()

            # Soru tipine göre sayfa başı soru sayısı
            # DİKKAT: _get_sorular_per_sayfa haritadan değil, seçimden okur.
            # Bu, _replan_and_refresh_ui çağrılmadığında sorun olabilir.
            # Şimdilik orijinal mantığı koruyoruz.
            
            # --- HARİTADAN OKUMA (DAHA GÜVENLİ) ---
            if not self.sayfa_haritasi:
                 self.sayfa_haritasi = [ [ [], [] ] ]
            toplam_sayfa = len(self.sayfa_haritasi)
            # --- BİTTİ ---

            if not hasattr(self, 'current_page'):
                self.current_page = 0
            
            # Sayfa taşmasını engelle
            if self.current_page >= toplam_sayfa:
                self.current_page = max(0, toplam_sayfa - 1)

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
                        command=lambda: self.change_page_pdf_only(-1), # Düzgün olanı çağır
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
                        command=lambda: self.change_page_pdf_only(1), # Düzgün olanı çağır
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

            # --- SIRALI NUMARALANDIRMA İÇİN OFFSET HESAPLAMA ---
            global_offset = 0
            for i in range(self.current_page):
                onceki_sayfa_sutunlari = self.sayfa_haritasi[i]
                global_offset += sum(len(sutun) for sutun in onceki_sayfa_sutunlari)

            # Mevcut sayfa için görselleri al (Haritadan)
            bu_sayfanin_sutunlari = self.sayfa_haritasi[self.current_page]

            # PDF sayfası önizlemesi oluştur (Yeni Çizici Sınıfı ile)
            constants = {
                'BASLIK_PT_MAX': self.BASLIK_PT_MAX,
                'BASLIK_PT_MIN': self.BASLIK_PT_MIN,
                'TITLE_MAX_W_RATIO': self.TITLE_MAX_W_RATIO
            }
            cizici = OnizlemeCizici(
                soru_tipi=self.soru_tipi_var.get(),
                baslik_text=self.baslik_text_var.get(),
                logger=self.logger,
                constants_dict=constants
            )
            pdf_preview = cizici.generate_preview_image(
                bu_sayfanin_sutunlari, global_offset, self.current_page
            )

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
            self.logger.error(f"PDF önizleme yenileme hatası: {e}", exc_info=True)
    
    def change_page_pdf_only(self, direction):
        """Sayfa değiştir - SADECE sol paneli yenile"""
        
        # --- GÜNCELLENMİŞ BLOK ---
        if not self.sayfa_haritasi:
             self.sayfa_haritasi = [ [ [], [] ] ]
        toplam_sayfa = len(self.sayfa_haritasi)
        # --- BİTTİ ---

        new_page = self.current_page + direction
        if 0 <= new_page < toplam_sayfa:
            self.current_page = new_page
            self.logger.debug(f"Sayfa değişti (Sadece PDF): {new_page + 1}/{toplam_sayfa}")

            # ✅ Sadece sol paneli yenile
            self.refresh_pdf_preview_only() # ARTIK ARGÜMAN ALMIYOR
            
        # --- ESKİ BOZUK ÇAĞRI SİLİNDİ ---
        # self.refresh_pdf_preview_only(self._last_pdf_container)
          
    def _refresh_preview_debounced(self, delay_ms=500):
        """Metin değiştiğinde 400 ms gecikmeyle yalnız sol önizlemeyi yeniler."""
        try:
            if self._title_typing_job:
                self.after_cancel(self._title_typing_job)
        except Exception:
            pass
        self._title_typing_job = self.after(delay_ms, self._refresh_preview_left_now)

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


    def gorsel_onizleme_alani_olustur(self):
        """Görsel önizleme alanını (Ekran 2) oluşturur."""
        self.logger.info("Önizleme alanı oluşturuluyor")

        # YENİ: Form sınıfını hafızadan kaldır
        if self.parametre_formu:
            self.parametre_formu.destroy()
            self.parametre_formu = None

        # Form içeriğini temizle (zaten üstteki destroy yapıyor ama garanti)
        for widget in self.icerik_cercevesi.winfo_children():
            widget.destroy()

        # YENİ: Önizleme ekranı için 'icerik_cercevesi'nin arka planını değiştir
        self.icerik_cercevesi.configure(fg_color="transparent", border_width=0)

        # 1. Önizleme Ekranı İskeletini Oluştur
        self.onizleme_ekrani = OnizlemeEkrani(
            parent_frame=self.icerik_cercevesi,
            controller=self
        )
        self.onizleme_ekrani.pack(fill="both", expand=True, padx=5, pady=5)

        # 2. İskeletin içini doldur
        self.display_images_new(
            self.onizleme_ekrani.pdf_container, 
            self.onizleme_ekrani.controls_container
        )
        
        # --- HATALI KISIM SİLİNDİ ---
        # (Burada 'self.display_images_new(pdf_container, controls_container)'
        #  adlı ikinci, hatalı bir çağrı vardı. Kaldırıldı.)
        
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

        # --- GÜNCELLEME: 'create_page_preview' yerine YENİ ÇİZİCİ SINIFINI KULLAN ---
        constants = {
            'BASLIK_PT_MAX': self.BASLIK_PT_MAX,
            'BASLIK_PT_MIN': self.BASLIK_PT_MIN,
            'TITLE_MAX_W_RATIO': self.TITLE_MAX_W_RATIO
        }
        cizici = OnizlemeCizici(
            soru_tipi=self.soru_tipi_var.get(),
            baslik_text=self.baslik_text_var.get(),
            logger=self.logger,
            constants_dict=constants
        )
        pdf_preview = cizici.generate_preview_image(
            bu_sayfanin_sutunlari, global_offset, self.current_page
        )

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

        # 1. Önceki paneli (varsa) yok et
        if self.kontrol_paneli and self.kontrol_paneli.winfo_exists():
            self.kontrol_paneli.destroy()
            self.kontrol_paneli = None

        # 2. Sinyal (Callback) sözlüğünü tanımla
        callbacks = {
            'on_guncelle': self.gorseli_guncelle_new,
            'on_kaldir': self.gorseli_kaldir_new,
            'on_pdf_olustur': self.pdf_olustur,
            'on_geri_don': self.geri_don
        }

        # 3. Yeni KontrolPaneli sınıfını oluştur
        self.kontrol_paneli = KontrolPaneli(
            parent=controls_container,      # 'controls_container'ın İÇİNE
            controller=self,                # Ana sınıfı (kendisini) controller olarak ver
            callbacks=callbacks,            # Sinyal sözlüğünü ver
            bu_sayfanin_sutunlari=bu_sayfanin_sutunlari, # Veriyi ver
            global_offset=global_offset     # Numaralandırma bilgisini ver
        )
        # Yeni paneli 'controls_container'ın içine yerleştir
        self.kontrol_paneli.pack(fill="both", expand=True)
        
    # --- İŞ MANTIĞI (BEYİN) DELEGE FONKSİYONLARI ---

    def _replan_and_refresh_ui(self):
        """Planı yeniden hesapla ve UI'ı yenile (Beyin'i çağır)"""
        self.oturum_yoneticisi._replan_and_refresh_ui()

    def gorseli_guncelle_new(self, index):
        """Görseli güncelle (Beyin'i çağır)"""
        self.oturum_yoneticisi.gorseli_guncelle_new(index)

    def gorseli_kaldir_new(self, index):
        """Görseli kaldır (Beyin'i çağır)"""
        self.oturum_yoneticisi.gorseli_kaldir_new(index)

    def find_topic_from_path(self, gorsel_path):
        """Konu bul (Beyin'i çağır)"""
        return self.oturum_yoneticisi.find_topic_from_path(gorsel_path)
    
    def _get_sorular_per_sayfa(self):
        """Sayfa başı soru sayısı (Beyin'i çağır)"""
        return self.oturum_yoneticisi._get_sorular_per_sayfa()

    def pdf_olustur(self):
        """PDF oluştur (Beyin'i çağır)"""
        self.oturum_yoneticisi.pdf_olustur()

    def basit_pdf_olustur(self):
        """Basit PDF oluştur (Beyin'i çağır)"""
        self.oturum_yoneticisi.basit_pdf_olustur()

    def _proceed_to_preview(self, soru_tipi, zorluk):
        """Önizlemeye geç (Beyin'i çağır)"""
        self.oturum_yoneticisi._proceed_to_preview(soru_tipi, zorluk)

    def _havuzu_sifirla(self):
        """Kullanılan sorular havuzunu sıfırla (Beyin'i çağır)"""
        self.oturum_yoneticisi._havuzu_sifirla()
        
    def secili_gorselleri_al(self, soru_tipi, zorluk):
        """Görselleri al (Beyin'i çağır)"""
        return self.oturum_yoneticisi.secili_gorselleri_al(soru_tipi, zorluk)
                          
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
                                   
                     
    def geri_don(self):
        """Soru parametre seçim ekranına (Ekran 1) geri dön"""
        try:
            self.logger.info("Geri dön butonuna tıklandı")

            # *** YENİ: Geri dönüşte havuzu sıfırla (yeni seçim için) ***
            self._havuzu_sifirla()
            self.logger.info("Geri dönüş - Havuz sıfırlandı")
            
            # Ekran 2'yi (Önizleme) yok et
            if self.onizleme_ekrani:
                self.onizleme_ekrani.destroy()
                self.onizleme_ekrani = None

            # Kontrol paneli referansını da temizle
            self.kontrol_paneli = None

            # Ekran 1'i (Form) göster
            self.goster_parametre_formu()

            # YENİ: Sadece form gösterme fonksiyonunu çağır
            self.goster_parametre_formu()

            self.logger.debug("Seçim ekranına geri dönüldü")

        except Exception as e:
            self.logger.error(f"Geri dönüş hatası: {e}")
            self.konu_baslik_sayfasina_don()
                        

if __name__ == "__main__":
    root = ctk.CTk()
    root.state('zoomed')
    app = SoruParametresiSecmePenceresi(root, None, ".")
    root.mainloop()