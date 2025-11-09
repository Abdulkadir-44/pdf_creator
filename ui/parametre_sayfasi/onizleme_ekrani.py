# ui/parametre_sayfasi/onizleme_ekrani.py

import customtkinter as ctk
import logging

"""
Soru Otomasyon Sistemi - Önizleme Ekranı İskeleti

Bu modül, SoruParametresiSecmePenceresi'nin "Ekran 2"sinin (Önizleme)
ana iskeletini oluşturur.

Ana Sınıf:
- OnizlemeEkrani: 
  Tüm önizleme ekranının ana 'holder' (tutucu) frame'idir.
  Görevi, ekranı "Sol Panel (PDF Önizleme)" ve "Sağ Panel (Kontroller)"
  olarak ikiye ayıran iki ana frame'i (pdf_container, controls_container)
  oluşturmak ve tutmaktır.
  
  İçeriğin doldurulması (display_images_new vb.) ana controller
  tarafından yönetilir.
"""

class OnizlemeEkrani(ctk.CTkFrame):
    """
    Ekran 2'nin (Önizleme) ana iskeletini (sol/sağ paneller) oluşturan
    CTkFrame bileşeni.
    
    Özellikler:
    - self.pdf_container (CTkFrame): Sol panel (Önizleme alanı)
    - self.controls_container (CTkFrame): Sağ panel (Kontrol alanı)
    
    Metodlar:
    - __init__(self, parent, controller):
        Frame'i başlatır ve _setup_layout() metodunu çağırır.
        
    - _setup_layout(self):
        Ana dosyadan (gorsel_onizleme_alani_olustur) taşınan 
        iskelet kodunu çalıştırır, sol ve sağ panelleri oluşturur.
    """
    
    def __init__(self, parent_frame, controller):
        """
        Önizleme Ekranı iskeletini başlatır.
        
        Args:
            parent_frame (ctk.CTkFrame): Bu formun içine yerleşeceği 
                                        ana 'icerik_cercevesi'.
            controller (SoruParametresiSecmePenceresi): Ana UI sınıfı.
        """
        
        # Bu sınıfın kendisi 'main_container'dır
        super().__init__(parent_frame, fg_color="transparent")
        
        self.controller = controller
        self.logger = controller.logger
        
        self._setup_layout()

    def _setup_layout(self):
        """
        'gorsel_onizleme_alani_olustur'dan taşınan iskelet kodunu oluşturur.
        """
        self.logger.debug("OnizlemeEkrani iskeleti oluşturuluyor (sol/sağ paneller)")
        
        # Ana içerik alanı - yan yana düzen
        # (Ana 'main_container' zaten 'self' olduğu için 'content_frame' ile başlıyoruz)
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        # Sol taraf - PDF önizleme
        self.pdf_container = ctk.CTkFrame(content_frame, fg_color="#f8f9fa", corner_radius=10)
        self.pdf_container.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # Sağ taraf - Kontroller (sabit 400px)
        self.controls_container = ctk.CTkFrame(content_frame, fg_color="#ffffff", corner_radius=10, width=400)
        self.controls_container.pack(side="right", fill="y", padx=(5, 0))
        self.controls_container.pack_propagate(False)