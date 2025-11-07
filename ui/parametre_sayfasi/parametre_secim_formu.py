# ui/parametre_secim_formu.py

import customtkinter as ctk
import tkinter as tk
import os
import logging

# Ana dosyadan 'YAZILI_INFO_SHOWN' global değişkenini buraya da taşıyoruz.
# İşlevselliği bozmamak için bu global değişkeni koruyoruz.
YAZILI_INFO_SHOWN = False

"""
Soru Otomasyon Sistemi - Parametre Seçim Formu Bileşeni

Bu modül, SoruParametresiSecmePenceresi'nin "Ekran 1"ini yönetir.
Kullanıcıdan soru tipi, zorluk, cevap anahtarı ve konu başına
soru adetlerini alan formu oluşturur ve doğrular.

Ana Sınıf:
- ParametreSecimFormu: 
  Tüm form widget'larını (ComboBox, Entry, Button) oluşturur.
  'Devam Et' butonuna basıldığında doğrulamayı yapar ve
  ana 'controller'a 'on_devam_et_callback' sinyalini gönderir.
"""

class ParametreSecimFormu(ctk.CTkFrame):
    """
    Soru parametrelerinin seçildiği Ekran 1 (Form) bileşeni.
    
    Metodlar:
    - __init__(self, parent_frame, controller, on_devam_et_callback):
        Sınıfı başlatır, ana controller'dan gerekli referansları
        (logger, dialog_yoneticisi, StringVars) alır.
        
    - create_selection_widgets(self):
        Tüm ComboBox, Entry ve butonları oluşturup ekrana çizer.
        
    - update_total(self):
        Entry'lerdeki değerlere göre toplam soru sayısını günceller.
        
    - devam_et(self):
        Formu doğrular. Hata varsa dialog gösterir.
        Başarılıysa, ana controller'a 'on_devam_et_callback' ile sinyal verir.
        
    - get_available_questions(self, ...):
        Doğrulama için bir konudaki mevcut soru sayısını kontrol eder.
        
    - _bind_combobox_open / _open_dropdown_safely:
        ComboBox'lar için yardımcı fonksiyonlar.
        
    - _unbind_combobox_open_in:
        'Yazılı Bilgi' dialogu gösterilmeden önce fokus hatasını önler.
    """
    
    def __init__(self, parent_frame, controller, on_devam_et_callback):
        """
        Formu başlatır.
        
        Args:
            parent_frame (ctk.CTkFrame): Bu formun içine yerleşeceği ana çerçeve.
            controller (SoruParametresiSecmePenceresi): Ana UI sınıfı.
            on_devam_et_callback (function): Doğrulama başarılı olduğunda 
                                             çağrılacak fonksiyon (sinyal).
        """
        
        # Formun kendisi için (ana dosyadan kopyalandı)
        super().__init__(
            parent_frame,
            corner_radius=15, 
            fg_color="#f8f9fa", 
            border_width=1, 
            border_color="#e9ecef"
        )
        
        self.controller = controller
        self.on_devam_et_callback = on_devam_et_callback
        
        # Gerekli referansları ve state'leri ana controller'dan al
        self.secilen_konular = self.controller.secilen_konular
        self.dialog_yoneticisi = self.controller.dialog_yoneticisi
        self.logger = self.controller.logger
        
        # 1. Adımda ana controller'da oluşturduğumuz paylaşılan değişkenleri al
        self.soru_tipi_var = self.controller.soru_tipi_var
        self.zorluk_var = self.controller.zorluk_var
        self.cevap_anahtari_var = self.controller.cevap_anahtari_var
        
        # Bu formun kendi içinde yönettiği state'ler
        self.konu_entry_vars = {}
        self.konu_soru_dagilimi = {} # 'devam_et'te doldurulacak
        
        # Formu çiz
        self.create_selection_widgets()

    def _open_dropdown_safely(self, cb):
        try:
            if cb and cb.winfo_exists() and hasattr(cb, "_open_dropdown_menu"):
                cb._open_dropdown_menu()
        except Exception:
            pass

    def _bind_combobox_open(self, cb):
        try:
            cb.bind("<Button-1>", lambda e: self._open_dropdown_safely(cb))
        except Exception:
            pass

    def _unbind_combobox_open_in(self, container):
        """Verilen container içindeki tüm CTkComboBox'lardan güvenli tıklama bağını kaldır."""
        try:
            for child in container.winfo_children():
                try:
                    if isinstance(child, ctk.CTkComboBox):
                        child.unbind("<Button-1>")
                    if hasattr(child, "winfo_children"):
                        self._unbind_combobox_open_in(child)
                except Exception:
                    continue
        except Exception:
            pass
            
    def create_selection_widgets(self):
        """Seçim widget'larını oluştur - Geliştirilmiş tasarım"""
        self.logger.debug("Seçim widget'ları oluşturuluyor (Form Sınıfı)")

        # Ana horizontal container
        # DİKKAT: 'self.form_frame' yerine 'self' (çünkü bu sınıfın kendisi o frame)
        main_horizontal_frame = ctk.CTkFrame(self, fg_color="transparent")
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
        # DİKKAT: self.soru_tipi_var = tk.StringVar() satırını sildik.
        self.soru_tipi_menu = ctk.CTkComboBox(
            left_input_frame,
            variable=self.soru_tipi_var, # Ana controller'dan gelen değişkeni kullan
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
        # DİKKAT: self.soru_tipi_menu.set(...) satırını sildik (Varsayılan değer controller'da)
        self.soru_tipi_menu.pack(anchor="w", pady=(0, 15), padx=(10, 0)) 
        self._bind_combobox_open(self.soru_tipi_menu)

        # Zorluk Seçimi
        # DİKKAT: self.zorluk_var = tk.StringVar() satırını sildik.
        self.zorluk_menu = ctk.CTkComboBox(
            left_input_frame,
            variable=self.zorluk_var, # Ana controller'dan gelen değişkeni kullan
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
        # DİKKAT: self.zorluk_menu.set(...) satırını sildik.
        self.zorluk_menu.pack(anchor="w", pady=(0, 15), padx=(10, 0))
        self._bind_combobox_open(self.zorluk_menu)

        # Cevap Anahtarı Seçimi
        # DİKKAT: self.cevap_anahtari_var = tk.StringVar() satırını sildik.
        self.cevap_anahtari_menu = ctk.CTkComboBox(
            left_input_frame,
            variable=self.cevap_anahtari_var, # Ana controller'dan gelen değişkeni kullan
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
        # DİKKAT: self.cevap_anahtari_menu.set(...) satırını sildik.
        self.cevap_anahtari_menu.pack(anchor="w", pady=(0, 15), padx=(10, 0))
        self._bind_combobox_open(self.cevap_anahtari_menu)

        # (Kalan tüm widget'lar aynı, referanslar 'self' olduğu için)

        hint_label = ctk.CTkLabel(
            left_input_frame,
            text="Bilgi: Program Test şablonunda sayfa başına maks 10 soru,\nYazılı şablonunda ise maks 2 soru yerleştirecektir.",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#495057"
        )
        hint_label.pack(side="left", pady=(2, 8), padx=(10, 0))

        # Sağ taraf - Konu Dağılımı
        right_distribution_frame = ctk.CTkFrame(
            main_horizontal_frame, 
            fg_color="#ffffff",
            corner_radius=16,
            border_width=1,
            border_color="#e2e8f0"
        )
        right_distribution_frame.pack(side="right", fill="both", expand=True, ipadx=30, ipady=10)

        dist_label = ctk.CTkLabel(
            right_distribution_frame, 
            text="Konu Başına Soru Sayısı",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#1a202c"
        )
        dist_label.pack(pady=(10, 10), anchor="w",padx=(10,0))

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
            konu_frame = ctk.CTkFrame(
                self.topics_frame, 
                fg_color="#ffffff",
                corner_radius=10,
                border_width=1,
                border_color="#e2e8f0"
            )
            konu_frame.pack(fill="x", pady=2, padx=8, ipady=8, ipadx=12)

            konu_label = ctk.CTkLabel(
                konu_frame,
                text=konu_adi,
                font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                text_color="#e53e3e"
            )
            konu_label.pack(side="left", anchor="w",padx=(10,10))

            right_container = ctk.CTkFrame(konu_frame, fg_color="transparent")
            right_container.pack(side="right", padx=(10, 0))

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

        self.total_label = ctk.CTkLabel(
            right_distribution_frame,
            text="Toplam Seçilen Soru: 0",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#2b6cb0"
        )
        self.total_label.pack(anchor="e", pady=(8, 4), padx=(0, 16))

        for var in self.konu_entry_vars.values():
            try:
                var.trace_add('write', lambda *_: self.update_total())
            except Exception:
                try:
                    var.trace('w', lambda *_: self.update_total())
                except Exception:
                    pass
        self.update_total()

        devam_btn = ctk.CTkButton(
            self, # DİKKAT: 'self.form_frame' yerine 'self'
            text="Devam Et",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            width=200,
            height=50,
            corner_radius=16,
            fg_color="#48bb78",
            hover_color="#38a169",
            text_color="#ffffff",
            command=self.devam_et # Bu sınıftaki 'devam_et'i çağır
        )
        devam_btn.pack(pady=(10, 10))

    def devam_et(self):
        """Seçimleri doğrula ve ana controller'a sinyal gönder"""
        self.logger.info("Devam et butonuna tıklandı (Form Sınıfı)")
        
        # Seçimleri al (Paylaşılan StringVars'lardan)
        soru_tipi = self.soru_tipi_var.get()
        zorluk = self.zorluk_var.get()
        cevap_anahtari = self.cevap_anahtari_var.get()
    
        self.logger.debug(f"Seçimler - Tip: {soru_tipi}, Zorluk: {zorluk}, Cevap Anahtarı: {cevap_anahtari}")
    
        # Validasyon (Dialog yöneticisi ana controller'dan alındı)
        if "seçin" in soru_tipi.lower() or "seçin" in zorluk.lower() or "eklensin" in cevap_anahtari.lower():
            self.logger.warning("Eksik seçim tespit edildi")
            self.dialog_yoneticisi.show_error("Lütfen tüm seçimleri yapın!\n- Soru tipi\n- Zorluk seviyesi\n- Cevap anahtarı")
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
                    self.dialog_yoneticisi.show_error(f"{konu_adi} için geçerli bir soru sayısı girin!")
                    return
            
            if toplam_soru == 0:
                self.dialog_yoneticisi.show_error("En az bir konu için soru sayısı belirtmelisiniz!")
                return
            
            # Bu formun kendi state'ine kaydet
            self.konu_soru_dagilimi = soru_dagilimi
            self.logger.info(f"Toplam {toplam_soru} soru seçildi")

        except Exception as e:
            self.logger.error(f"Soru dağılımı kontrolü hatası: {e}")
            self.dialog_yoneticisi.show_error("Soru sayıları kontrol edilirken hata oluştu!")
            return

        # Her konu için soru mevcudiyeti kontrolü
        bos_konular = []
        for konu_adi, istenen_sayi in soru_dagilimi.items():
            mevcut_sayi = self.get_available_questions(konu_adi, soru_tipi, zorluk)
            if mevcut_sayi == 0:
                bos_konular.append(konu_adi)

        if bos_konular:
            self.logger.warning("Boş klasörler tespit edildi")
            if len(bos_konular) == 1:
                uyari_mesaji = f"'{bos_konular[0]}' konusunda seçilen zorluk seviyesinde ({zorluk}) soru bulunamadı!\n\nFarklı bir zorluk seviyesi seçin veya bu konuyu atlayın."
            else:
                konu_listesi = "', '".join(bos_konular)
                uyari_mesaji = f"Şu konularda seçilen zorluk seviyesinde ({zorluk}) soru bulunamadı:\n\n'{konu_listesi}'\n\nFarklı bir zorluk seviyesi seçin veya bu konuları atlayın."

            self.dialog_yoneticisi.show_error(uyari_mesaji)
            return

        eksik_konular = []
        for konu_adi, istenen_sayi in soru_dagilimi.items():
            mevcut_sayi = self.get_available_questions(konu_adi, soru_tipi, zorluk)
            if 0 < mevcut_sayi < istenen_sayi:
                eksik_konular.append(f"{konu_adi}: {istenen_sayi} istendi, {mevcut_sayi} mevcut")

        if eksik_konular:
            self.logger.warning("Yetersiz soru bulunan konular var")
            hata_mesaji = "Bazı konularda yeterli soru yok:\n\n" + "\n".join(eksik_konular)
            self.dialog_yoneticisi.show_error(hata_mesaji)
            return

        # --- YENİ CALLBACK SİSTEMİ ---
        
        # Sayfa bilgilendirmesi (yazılı, oturum bazlı). Diyalog kapandıktan sonra devam et.
        if soru_tipi.lower() == "yazili" and toplam_soru > 2:
            global YAZILI_INFO_SHOWN
            if not YAZILI_INFO_SHOWN:
                self.logger.info("Yazılı için çoklu sayfa bilgilendirmesi (oturum bazlı) gösteriliyor")
                YAZILI_INFO_SHOWN = True
                
                # 'self' (bu form sınıfı) içindeki combobox bağlarını kaldır
                self._unbind_combobox_open_in(self)
                
                self.dialog_yoneticisi.show_multipage_info(
                    toplam_soru, 
                    on_close=lambda: self.on_devam_et_callback(self.konu_soru_dagilimi)
                )
                return

        # Bilgilendirme gerekmiyorsa callback'i doğrudan çağır
        self.on_devam_et_callback(self.konu_soru_dagilimi)

    def get_available_questions(self, konu_adi, soru_tipi, zorluk):
        """Bir konu için mevcut soru sayısını döndür"""
        try:
            # 'self.secilen_konular' ana controller'dan alındı
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