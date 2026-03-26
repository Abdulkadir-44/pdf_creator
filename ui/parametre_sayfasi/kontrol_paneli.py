# ui/parametre_sayfasi/kontrol_paneli.py

import customtkinter as ctk
import logging

# ToolTip'i bu dosyada da kullanacağımız için import ediyoruz
from ui.widgets.tooltip import ToolTip

"""
Soru Otomasyon Sistemi - Kontrol Paneli Bileşeni

Bu modül, SoruParametresiSecmePenceresi'nin "Ekran 2"sinin (Önizleme)
SAĞ TARAFINI yönetir.

Ana Sınıf:
- KontrolPaneli: 
  Tüm sağ panel widget'larını (Başlık Entry'si, Soru Kartları
  ScrollableFrame'i, 'PDF Oluştur' ve 'Geri' butonları) oluşturur.
  
  Kullanıcı etkileşimlerini (Sil, Güncelle, PDF, Geri)
  doğrudan KENDİSİ İŞLEMEZ. Bunun yerine 'callbacks'
  sözlüğü aracılığıyla ana 'controller'a sinyal gönderir.
"""

class KontrolPaneli(ctk.CTkFrame):
    """
    Ekran 2'nin (Önizleme) sağ panelini (Başlık, Soru Listesi, Butonlar)
    oluşturan CTkFrame bileşeni.
    
    Metodlar:
    - __init__(self, parent, controller, callbacks, ...):
        Sınıfı başlatır ve 'create_controls_panel'den taşınan tüm
        widget oluşturma mantığını çalıştırır.
        
    - (İç yardımcı metodlar):
        Tüm buton komutları (lambda), 'callbacks' sözlüğündeki
        ana controller fonksiyonlarını (örn: on_kaldir) çağırır.
    """
    
    def __init__(self, parent, controller, callbacks, bu_sayfanin_sutunlari, global_offset):
        """
        Sağ kontrol panelini oluşturur.
        (Bu __init__ metodu, 'create_controls_panel' fonksiyonunun
         tamamının yerini alır)
        
        Args:
            parent (ctk.CTkFrame): Bu panelin içine yerleşeceği 
                                  'controls_container'.
            controller (SoruParametresiSecmePenceresi): Ana UI sınıfı.
            callbacks (dict): Ana controller'daki fonksiyonlara
                              sinyal göndermek için {'on_kaldir': ..., ...}
            bu_sayfanin_sutunlari (list): Gösterilecek soru verisi.
            global_offset (int): Soru numaralandırması için başlangıç sayısı.
        """
        
        # Bu sınıfın kendisi 'controls_container'ın İÇİNDEKİ
        # ana frame'dir. 'parent'tan (controls_container)
        # fg_color'ını miras alır.
        super().__init__(parent, fg_color="transparent")
        
        self.controller = controller
        self.logger = controller.logger
        self.callbacks = callbacks
        
        # --- 'create_controls_panel'den KOPYALANAN KOD ---
        
        # ÜST: Başlık Girişi (Entry)
        title_bar = ctk.CTkFrame(self, fg_color="transparent")
        title_bar.pack(fill="x", padx=15, pady=(15, 10))
        
        title_entry = ctk.CTkEntry(
            title_bar,
            # DİKKAT: 'self.baslik_text_var' yerine 'self.controller.baslik_text_var'
            textvariable=self.controller.baslik_text_var,
            placeholder_text="Lütfen başlık girin",
            height=36
        )
        title_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        # DİKKAT: 'trace' ve 'bind' ana controller'daki metodları çağırmalı
        if not getattr(self.controller, "_title_trace_id", None):
            self.controller._title_trace_id = self.controller.baslik_text_var.trace_add(
                "write",
                # DİKKAT: 'self._refresh_preview_debounced' yerine 'self.controller._...'
                lambda *args: self.controller._refresh_preview_debounced(450)
            )
        def _on_destroy(_):
            try:
                if getattr(self.controller, "_title_trace_id", None):
                    self.controller.baslik_text_var.trace_remove("write", self.controller._title_trace_id)
                    self.controller._title_trace_id = None
            except Exception:
                pass
        title_entry.bind("<Destroy>", _on_destroy)

        # --- Scrollable frame ---
        scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#f8f9fa",
            corner_radius=8
        )
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))
        
        # Sütunları düzleştir (Aynı mantık)
        bu_sayfanin_soru_bilgileri_duz = []
        for sutun in bu_sayfanin_sutunlari:
            bu_sayfanin_soru_bilgileri_duz.extend(sutun)
        
        # --- Her soru için kontrol kartı ---
        for i, soru_info in enumerate(bu_sayfanin_soru_bilgileri_duz):
            
            gorsel_path = soru_info['path']
            gercek_global_index = soru_info['index'] 
            card = ctk.CTkFrame(
                scroll_frame,
                fg_color="#ffffff",
                corner_radius=10,
            )
            card.pack(fill="x", padx=10, pady=(8, 8))
    
            soru_no = global_offset + i + 1
            
            try:
                cevap = self.controller.oturum_yoneticisi.get_answer_for_image(gorsel_path)
            except Exception:
                cevap = "?"
    
            try:
                # DİKKAT: 'self.find_topic_from_path' -> 'self.controller.find_topic_from_path'
                konu_adi_tam = self.controller.find_topic_from_path(gorsel_path) or "Bilinmeyen"
            except Exception:
                konu_adi_tam = "Bilinmeyen"
    
            # Üst satır (soru no & cevap)
            top_frame = ctk.CTkFrame(card, fg_color="transparent")
            top_frame.pack(fill="x", padx=15, pady=(15, 5))
    
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
    
            # Orta satır
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
            
            ToolTip(info_icon, konu_adi_tam)
                
            MAX_LEN = 25
            konu_kisa = konu_adi_tam if len(konu_adi_tam) <= MAX_LEN else (konu_adi_tam[:MAX_LEN] + "…")
            ctk.CTkLabel(
                header, text=konu_kisa,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#1e293b"
            ).grid(row=0, column=1, sticky="w")
                
            btn_row = ctk.CTkFrame(header, fg_color="transparent")
            btn_row.grid(row=0, column=2, sticky="e")
    
            # --- DİKKAT: CALLBACK SİSTEMİ ---
            
            # GÜNCELLE Butonu
            ctk.CTkButton(
                btn_row, text="🔄", width=34, height=30,
                fg_color="#e2e8f0", text_color="#1f2937",
                hover_color="#cbd5e1",
                # ESKİ: command=lambda idx=gercek_global_index: self.gorseli_guncelle_new(idx)
                command=lambda idx=gercek_global_index: self.callbacks['on_guncelle'](idx)
            ).pack(side="left", padx=(0, 6))
    
            # SİL Butonu
            ctk.CTkButton(
                btn_row, text="🗑", width=34, height=30,
                fg_color="#fee2e2", text_color="#991b1b",
                hover_color="#fecaca",
                # ESKİ: command=lambda idx=gercek_global_index: self.gorseli_kaldir_new(idx)
                command=lambda idx=gercek_global_index: self.callbacks['on_kaldir'](idx)
            ).pack(side="left")
    
        # --- Alt butonlar ---
        buttons_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        buttons_frame.pack(fill="x", padx=15, pady=(0, 15))
        buttons_frame.pack_propagate(False)
    
        button_container = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        button_container.pack(expand=True)
        
        # PDF OLUŞTUR Butonu — soru yoksa devre dışı
        has_questions = len(self.controller.secilen_gorseller) > 0
        ctk.CTkButton(
            button_container, text="PDF Oluştur",
            command=self.callbacks['on_pdf_olustur'],
            font=ctk.CTkFont(size=14, weight="bold"),
            width=160, height=40, corner_radius=10,
            fg_color="#28a745" if has_questions else "#adb5bd",
            hover_color="#218838" if has_questions else "#adb5bd",
            state="normal" if has_questions else "disabled"
        ).pack(side="left", padx=(0, 10))
        
        # GERİ Butonu
        ctk.CTkButton(
            button_container, text="Geri",
            # ESKİ: command=self.geri_don
            command=self.callbacks['on_geri_don'],
            font=ctk.CTkFont(size=14, weight="bold"),
            width=100, height=40, corner_radius=10,
            fg_color="#6c757d", hover_color="#5a6268"
        ).pack(side="left")