# ui/parametre_sayfasi/sayfa_basligi.py

import customtkinter as ctk

"""
Soru Otomasyon Sistemi - Sayfa Başlığı (Header) Bileşeni

Bu modül, SoruParametresiSecmePenceresi'nin en üstünde yer alan
başlık çubuğunu (Header) yönetir.

Ana Sınıf:
- SayfaBasligi: 
  'Ana Menü' ve 'Konu Seçimi' butonlarını, ders adını
  ve sayfa alt başlığını çizer.
  
  Butonlara tıklandığında, 'callbacks' aracılığıyla
  ana 'controller'a sinyal gönderir.
"""

class SayfaBasligi(ctk.CTkFrame):
    """
    Sayfanın en üstündeki başlık çubuğunu (Header) oluşturan
    CTkFrame bileşeni.
    
    Metodlar:
    - __init__(self, parent, controller, ders_adi, callbacks):
        Sınıfı başlatır ve 'create_header'dan taşınan tüm
        widget oluşturma mantığını çalıştırır.
    """
    
    def __init__(self, parent, controller, ders_adi, callbacks):
        """
        Başlık çubuğunu başlatır.
        (Bu __init__ metodu, 'create_header' fonksiyonunun
         tamamının yerini alır)
        
        Args:
            parent (ctk.CTkFrame): Bu başlığın içine yerleşeceği 
                                  'main_container'.
            controller (SoruParametresiSecmePenceresi): Ana UI sınıfı.
            ders_adi (str): Başlıkta gösterilecek dersin adı.
            callbacks (dict): Ana controller'daki fonksiyonlara
                              sinyal göndermek için {'on_ana_menu': ..., ...}
        """
        
        # DİKKAT: Ana controller'dan 'colors' sözlüğünü al
        self.colors = controller.colors
        
        # Bu sınıfın kendisi 'header_frame'dir
        super().__init__(
            parent,
            height=100,
            corner_radius=0,
            fg_color=self.colors['primary']
        )
        
        self.controller = controller
        self.ders_adi = ders_adi
        self.callbacks = callbacks
        
        # --- 'create_header'dan KOPYALANAN KOD ---
        
        self.pack(fill="x")
        self.pack_propagate(False)

        # Header içeriği
        header_content = ctk.CTkFrame(self, fg_color="transparent")
        header_content.pack(expand=True, fill="both", padx=40, pady=15)

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
            # DİKKAT: Callback (sinyal) kullanımı
            command=self.callbacks['on_ana_menu']
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
            # DİKKAT: Callback (sinyal) kullanımı
            command=self.callbacks['on_konu_secimi']
        )
        back_btn.pack(side="left")

        # Sağ taraf - Başlık
        right_frame = ctk.CTkFrame(header_content, fg_color="transparent")
        right_frame.pack(side="right", fill="y")

        title_label = ctk.CTkLabel(
            right_frame,
            text=f"{self.ders_adi}",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.colors['light']
        )
        title_label.pack(anchor="e")

        subtitle_label = ctk.CTkLabel(
            right_frame,
            text="Soru Parametre Seçimi",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#e0e0e0"
        )
        subtitle_label.pack(anchor="e", pady=(3, 0))