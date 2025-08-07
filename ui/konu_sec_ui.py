import customtkinter as ctk
import tkinter as tk
import os
import sys
from PIL import Image, ImageTk
import math
from tkinter import filedialog
from PIL import Image, ImageDraw, ImageFont
import tempfile

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
        self.selected_questions = []  # Store selected question paths
        
        # UI'ı oluştur
        self.setup_ui()

    def setup_ui(self):
        """Ana UI'ı oluştur"""
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

    def create_selection_widgets(self):
        """Seçim widget'larını oluştur"""
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
                command=lambda n=num: self.soru_sayisi_var.set(str(n))
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

    def get_konu_klasorleri(self):
        """Konu klasörlerini al"""
        try:
            klasorler = [d for d in os.listdir(self.unite_klasor_yolu) 
                        if os.path.isdir(os.path.join(self.unite_klasor_yolu, d))]
            return klasorler if klasorler else ["(Klasör boş)"]
        except Exception as e:
            print("Konu klasörleri alma hatası:", e)
            return ["(Hata oluştu)"]

    def ana_menuye_don(self):
        """Ana menüye dön"""
        self.controller.ana_menuye_don()

    def unite_sec_sayfasina_don(self):
        """Ünite seçim sayfasına dön"""
        self.controller.show_frame("UniteSecme")

    def devam_et(self):
        """Seçimleri doğrula ve önizleme ekranını göster"""
        # Seçimleri al
        secilen_konu = self.konu_var.get()
        zorluk = self.zorluk_var.get()

        # Validasyon
        if any("seçin" in var.get().lower() for var in [self.konu_var, self.zorluk_var]):
            self.show_error("Lütfen konu ve zorluk seviyesini seçin!")
            return

        # Soru sayısı validasyonu
        try:
            soru_sayisi = int(self.soru_sayisi_var.get())
            if soru_sayisi <= 0:
                raise ValueError
        except (ValueError, AttributeError):
            self.show_error("Lütfen geçerli bir soru sayısı girin!")
            return

        # Seçilen klasör yolunu oluştur
        secilen_konu_path = os.path.join(self.unite_klasor_yolu, secilen_konu, zorluk.lower())

        # Klasördeki maksimum soru sayısını kontrol et
        try:
            gorseller = [f for f in os.listdir(secilen_konu_path) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            max_soru = len(gorseller)

            if soru_sayisi > max_soru:
                self.show_error(f"Seçtiğiniz zorluk seviyesinde sadece {max_soru} soru bulunuyor!")
                return
        except Exception as e:
            print("Klasör okuma hatası:", e)
            self.show_error("Seçilen klasörde görsel bulunamadı!")
            return

        # Rastgele görselleri seç
        self.secilen_gorseller = self.rastgele_gorseller_sec(secilen_konu_path, soru_sayisi)

        if self.secilen_gorseller:
            # Önizleme ekranını göster
            self.gorsel_onizleme_alani_olustur()
        else:
            self.show_error("Seçilen klasörde görsel bulunamadı!")
  
    def rastgele_gorseller_sec(self, klasor_yolu, adet):
        """Belirtilen klasörden rastgele görsel seç"""
        try:
            if not os.path.exists(klasor_yolu):
                return []
                
            gorseller = [f for f in os.listdir(klasor_yolu) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
            
            if not gorseller:
                return []

            import random
            if len(gorseller) <= adet:
                return [os.path.join(klasor_yolu, f) for f in gorseller]
            else:
                return [os.path.join(klasor_yolu, f) 
                       for f in random.sample(gorseller, adet)]
        except Exception as e:
            print("Görsel seçme hatası:", e)
            return []

    def gorsel_onizleme_alani_olustur(self):
        """Görsel önizleme alanını oluştur"""
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
            text=f"📚 {secilen_konu} | ⚡ {zorluk} | 🔢 {len(self.secilen_gorseller)} soru",
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
            command=lambda: self.pdf_olustur(secilen_konu, zorluk),
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
                print(f"Görsel kaldırıldı: {os.path.basename(kaldirilan_gorsel)}")

                # Eğer hiç görsel kalmadıysa uyarı göster
                if not self.secilen_gorseller:
                    self.show_notification(
                        "⚠️ Uyarı",
                        "Tüm görseller kaldırıldı!\nYeni seçim yapmak için 'Geri' butonuna tıklayın.",
                        geri_don=False 
                    )
                    return

                # Önizlemeyi güncelle
                # Önce mevcut içeriği temizle
                for widget in parent_frame.winfo_children():
                    widget.destroy()

                # Sayfa kontrolü yap
                sorular_per_sayfa = 8
                toplam_sayfa = math.ceil(len(self.secilen_gorseller) / sorular_per_sayfa)
                if hasattr(self, 'current_page') and self.current_page >= toplam_sayfa:
                    self.current_page = max(0, toplam_sayfa - 1)

                self.display_images(parent_frame)

                # Bilgi etiketini güncelle (soru sayısı değişti)
                self.guncelle_bilgi_etiketi()

        except Exception as e:
            print(f"Görsel kaldırma hatası: {e}")
            self.show_error("Görsel kaldırılırken bir hata oluştu!")

    def gorseli_guncelle(self, index, parent_frame):
        """Seçilen görseli güncelle"""
        try:
            if 0 <= index < len(self.secilen_gorseller):
                # Mevcut klasör yolunu al
                secilen_konu = self.konu_var.get()
                zorluk = self.zorluk_var.get()
                klasor_yolu = os.path.join(self.unite_klasor_yolu, secilen_konu, zorluk.lower())

                # Klasördeki tüm görselleri al
                tum_gorseller = [f for f in os.listdir(klasor_yolu) 
                               if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]

                if not tum_gorseller:
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
                    self.show_error("Güncellenecek başka görsel kalmadı!")
                    return

                # Rastgele yeni bir görsel seç
                import random
                yeni_gorsel = random.choice(kullanilabilir_gorseller)

                # Görseli güncelle
                self.secilen_gorseller[index] = yeni_gorsel

                # Önizlemeyi yenile
                for widget in parent_frame.winfo_children():
                    widget.destroy()

                self.display_images(parent_frame)

        except Exception as e:
            print(f"Görsel güncelleme hatası: {e}")
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
                    zorluk = self.zorluk_var.get()
                    info_widget.configure(
                        text=f"📚 {secilen_konu} | ⚡ {zorluk} | 🔢 {len(self.secilen_gorseller)} soru"
                    )
        except Exception as e:
            print(f"Bilgi etiketi güncelleme hatası: {e}")

    def display_images(self, parent_frame):
        """Görselleri sayfa sayfa PDF şablonunda göster"""
        # Sayfa başına 8 soru (2x4)
        sorular_per_sayfa = 8
        toplam_sayfa = math.ceil(len(self.secilen_gorseller) / sorular_per_sayfa)

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

        # PDF sayfası önizlemesi oluştur
        pdf_preview = self.create_page_preview(sayfa_gorselleri, start_idx)

        if pdf_preview:
            # Ana container - PDF ve butonları yan yana yerleştirmek için
            main_container = ctk.CTkFrame(parent_frame, fg_color="transparent")
            main_container.pack(pady=20, padx=10, fill="both", expand=True)

            # PDF önizleme container (sol taraf)
            preview_container = ctk.CTkFrame(main_container, fg_color="#ffffff", corner_radius=10)
            preview_container.pack(side="left", fill="both", expand=True, padx=(0, 10))

            # PDF görselini göster
            pdf_label = tk.Label(
                preview_container,
                image=pdf_preview,
                bg="#ffffff"
            )
            pdf_label.image = pdf_preview  # Referansı koru
            pdf_label.pack(pady=20)

            # Butonlar container (sağ taraf)
            buttons_container = ctk.CTkFrame(main_container, fg_color="#f8f9fa", corner_radius=10, width=250)
            buttons_container.pack(side="right", fill="y", padx=(10, 0))
            buttons_container.pack_propagate(False)  # Sabit genişlik için

            # Her soru için butonlar
            self.create_question_buttons_vertical(buttons_container, sayfa_gorselleri, start_idx, parent_frame)
    
    def change_page(self, parent_frame, direction):
        """Sayfa değiştir"""
        sorular_per_sayfa = 8
        toplam_sayfa = math.ceil(len(self.secilen_gorseller) / sorular_per_sayfa)

        new_page = self.current_page + direction
        if 0 <= new_page < toplam_sayfa:
            self.current_page = new_page

            # Sayfayı yenile
            for widget in parent_frame.winfo_children():
                widget.destroy()

            self.display_images(parent_frame)

    def create_question_buttons_vertical(self, parent_container, sayfa_gorselleri, start_idx, main_parent_frame):
        """Soruların yanında dikey olarak butonlar oluştur"""
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
                from logic.answer_utils import get_answer_for_image
                cevap = get_answer_for_image(gorsel_path)
            except ImportError:
                cevap = "?"

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
        try:
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            template_path = os.path.join(current_dir, "templates", "template.png")

            if not os.path.exists(template_path):
                print(f"Şablon bulunamadı: {template_path}")
                return None

            # Şablonu aç
            template = Image.open(template_path).convert("RGB")
            template_copy = template.copy()

            # 2x4 grid koordinatları hesapla
            template_width, template_height = 1414, 2000

            # Margin'ler
            top_margin = 150
            left_margin = 50
            right_margin = 50
            bottom_margin = 100

            # Kullanılabilir alan
            usable_width = template_width - left_margin - right_margin
            usable_height = template_height - top_margin - bottom_margin

            # Her soru için alan
            soru_width = usable_width // 2 - 20  # 20px gap
            soru_height = usable_height // 4 - 40  # 20px gap

            # Görselleri yerleştir
            for i, gorsel_path in enumerate(sayfa_gorselleri):
                try:
                    # Grid pozisyonu hesapla
                    row = i % 4  # 0, 0, 1, 1, 2, 2, 3, 3
                    col = i // 4   # 0, 1, 0, 1, 0, 1, 0, 1

                    # Koordinatları hesapla
                    x = left_margin + col * (soru_width + 20)
                    y = top_margin + row * (soru_height + 40)

                    # Soruyu aç ve boyutlandır
                    soru_img = Image.open(gorsel_path)
                    soru_img.thumbnail((soru_width, soru_height), Image.Resampling.LANCZOS)

                    # Görseli yerleştir (ortalayarak)
                    img_w, img_h = soru_img.size
                    paste_x = x + (soru_width - img_w) // 2
                    paste_y = y + (soru_height - img_h) // 2

                    template_copy.paste(soru_img, (paste_x, paste_y))

                    # Soru numarası ekle
                    draw = ImageDraw.Draw(template_copy)
                    try:
                        font = ImageFont.truetype("arial.ttf", 20)
                    except:
                        font = ImageFont.load_default()

                    soru_no = start_idx + i + 1
                    draw.text((x + 15, y + 30), f"{soru_no}.", fill="black", font=font)

                except Exception as e:
                    print(f"Soru {i+1} yerleştirme hatası: {e}")

            # Önizleme için boyutlandır (oranı koru)
            preview_width = 600
            preview_height = int(2000 * preview_width / 1414)
            template_copy = template_copy.resize((preview_width, preview_height), Image.Resampling.LANCZOS)

            return ImageTk.PhotoImage(template_copy)

        except Exception as e:
            print(f"Sayfa önizleme hatası: {e}")
            return None

    def create_question_buttons(self, parent_container, sayfa_gorselleri, start_idx, main_parent_frame):
        """Her soru için düzenle/sil butonları oluştur"""
        buttons_frame = ctk.CTkFrame(parent_container, fg_color="transparent")
        buttons_frame.pack(pady=20)

        # 2 sütunluk grid oluştur
        for i, gorsel_path in enumerate(sayfa_gorselleri):
            row = i // 2
            col = i % 2

            # Her soru için buton grubu
            question_frame = ctk.CTkFrame(buttons_frame, fg_color="#f8f9fa", corner_radius=8)
            question_frame.grid(row=row, column=col, padx=10, pady=5, sticky="ew")

            # Soru numarası ve bilgisi
            soru_no = start_idx + i + 1
            try:
                from logic.answer_utils import get_answer_for_image
                cevap = get_answer_for_image(gorsel_path)
            except ImportError:
                cevap = "?"

            info_label = ctk.CTkLabel(
                question_frame,
                text=f"Soru {soru_no} | Cevap: {cevap}",
                font=ctk.CTkFont(size=11, weight="bold")
            )
            info_label.pack(pady=5)

            # Butonlar
            btn_frame = ctk.CTkFrame(question_frame, fg_color="transparent")
            btn_frame.pack(pady=5)

            # Güncelle butonu
            update_btn = ctk.CTkButton(
                btn_frame,
                text="🔄",
                width=30, height=25,
                command=lambda idx=start_idx+i: self.gorseli_guncelle(idx, main_parent_frame)
            )
            update_btn.pack(side="left", padx=2)

            # Sil butonu
            remove_btn = ctk.CTkButton(
                btn_frame,
                text="🗑️",
                width=30, height=25,
                fg_color="#e74c3c",
                hover_color="#c0392b",
                command=lambda idx=start_idx+i: self.gorseli_kaldir(idx, main_parent_frame)
            )
            remove_btn.pack(side="left", padx=2)

        # Grid sütunlarını eşit genişlikte yap
        buttons_frame.grid_columnconfigure(0, weight=1)
        buttons_frame.grid_columnconfigure(1, weight=1)

    def create_pdf_preview(self, gorsel_path, soru_no):
        """Görseli PDF şablonuna yerleştirerek önizleme oluştur"""
        try:
            # Şablon yolunu belirle
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # ui klasöründen çıkıp ana dizine git
            template_path = os.path.join(current_dir, "templates", "template.png")

            if not os.path.exists(template_path):
                print(f"Şablon bulunamadı: {template_path}")
                return None

            # Şablonu aç
            template = Image.open(template_path).convert("RGB")
            template_copy = template.copy()

            # Soruyu aç ve boyutlandır
            soru_image = Image.open(gorsel_path)

            # Şablondaki soru alanının boyutlarını hesapla (şablonunuza göre ayarlayın)
            template_width, template_height = template_copy.size

            # Soru alanı koordinatları (şablonunuza göre ayarlayın)
            # Örnek: şablonun %20'si margin, %60'ı soru alanı
            margin_x = int(template_width * 0.1)
            margin_y = int(template_height * 0.15)
            soru_width = int(template_width * 0.8)
            soru_height = int(template_height * 0.7)

            # Soruyu boyutlandır (aspect ratio'yu koru)
            soru_image.thumbnail((soru_width, soru_height), Image.Resampling.LANCZOS)

            # Soruyu şablona yerleştir (ortalayarak)
            soru_w, soru_h = soru_image.size
            paste_x = margin_x + (soru_width - soru_w) // 2
            paste_y = margin_y + (soru_height - soru_h) // 2

            template_copy.paste(soru_image, (paste_x, paste_y))

            # Soru numarasını ekle
            draw = ImageDraw.Draw(template_copy)
            try:
                # Daha büyük font kullan
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()

            draw.text((margin_x, margin_y - 40), f"Soru {soru_no}", fill="black", font=font)

            # Önizleme için boyutlandır
            preview_size = (400, 500)  # Önizleme boyutu
            template_copy.thumbnail(preview_size, Image.Resampling.LANCZOS)

            # PhotoImage'e çevir
            preview_photo = ImageTk.PhotoImage(template_copy)

            return preview_photo

        except Exception as e:
            print(f"PDF önizleme oluşturma hatası: {e}")
            return None

    def display_simple_image(self, parent_frame, gorsel_path, index):
        """Basit görsel gösterimi (şablon bulunamadığında)"""
        try:
            # Görsel container
            img_container = ctk.CTkFrame(parent_frame, fg_color="#f8f9fa", corner_radius=10)
            img_container.pack(pady=10, padx=10, fill="x")

            # Görsel yükle ve boyutlandır
            img = Image.open(gorsel_path)
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            # Görsel etiketi
            img_label = tk.Label(
                img_container, 
                image=photo, 
                bg="#f8f9fa", 
                bd=2, 
                relief="solid",
                borderwidth=1
            )
            img_label.image = photo  # Referansı koru
            img_label.pack(pady=10)

            # Şablon bulunamadı uyarısı
            warning_label = ctk.CTkLabel(
                img_container,
                text="⚠️ PDF şablonu bulunamadı, basit görsel gösteriliyor",
                font=ctk.CTkFont(family="Segoe UI", size=10),
                text_color="#dc3545"
            )
            warning_label.pack(pady=(0, 5))

            # Zorluk ve cevap bilgisi (önceki kodunuzla aynı)
            info_frame = ctk.CTkFrame(img_container, fg_color="transparent")
            info_frame.pack(pady=(0, 10))

            zorluk_seviyesi = self.zorluk_var.get()

            try:
                from logic.answer_utils import get_answer_for_image
                cevap = get_answer_for_image(gorsel_path)
            except ImportError:
                cevap = "?"

            info_label = ctk.CTkLabel(
                info_frame,
                text=f"Soru {index+1} | Zorluk: {zorluk_seviyesi} | Cevap: {cevap}",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color="#495057"
            )
            info_label.pack(side="left", padx=(0, 20))

            # Butonlar (önceki kodunuzla aynı)
            button_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            button_frame.pack(side="right")

            update_btn = ctk.CTkButton(
                button_frame,
                text="🔄",
                font=ctk.CTkFont(size=14),
                width=30,
                height=30,
                corner_radius=8,
                fg_color="#3498db",
                hover_color="#2980b9",
                command=lambda idx=index: self.gorseli_guncelle(idx, parent_frame)
            )
            update_btn.pack(side="left", padx=(0, 10))

            remove_btn = ctk.CTkButton(
                button_frame,
                text="🗑️",
                font=ctk.CTkFont(size=14),
                width=30,
                height=30,
                corner_radius=8,
                fg_color="#e74c3c",
                hover_color="#c0392b",
                command=lambda idx=index: self.gorseli_kaldir(idx, parent_frame)
            )
            remove_btn.pack(side="left")

        except Exception as e:
            print(f"Basit görsel gösterim hatası: {e}")

    def geri_don(self):
        """Konu seçim ekranına geri dön"""
        try:
            # Form içeriğini temizle ve seçim widget'larını yeniden oluştur
            for widget in self.form_frame.winfo_children():
                widget.destroy()

            self.create_selection_widgets()

        except Exception as e:
            print("Geri dönüş hatası:", e)
            # Hata durumunda ünite seçimine dön
            self.unite_sec_sayfasina_don()

    def pdf_olustur(self, konu, zorluk):
        """PDF oluştur ve kullanıcıya bildir"""
       
        try:
            # Önce reportlab modülünü kontrol et
            try:
                import reportlab
                print("✅ Reportlab modülü mevcut")
            except ImportError:
                self.show_notification(
                    "❌ Eksik Modül",
                    "📦 PDF oluşturmak için 'reportlab' modülü gerekli.\n\n"
                    "💡 Çözüm: Terminal'e şunu yazın:\n"
                    "pip install reportlab"
                )
                return
    
            # PDF generator'ı import etmeyi dene
            try:
                from logic.pdf_generator import PDFCreator
                print("✅ PDFCreator başarıyla import edildi")
            except ImportError as e:
                print(f"❌ PDFCreator import hatası: {e}")
                
                # Alternatif import yollarını dene
                
                
                # Mevcut dosyanın bulunduğu klasörü al
                current_dir = os.path.dirname(os.path.abspath(__file__))
                logic_path = os.path.join(current_dir, 'logic')
                
                # logic klasörünü sys.path'e ekle
                if logic_path not in sys.path:
                    sys.path.append(logic_path)
                
                try:
                    from logic.pdf_generator import PDFCreator
                    print("✅ PDFCreator alternatif yolla import edildi")
                except ImportError as e2:
                    print(f"❌ Alternatif import de başarısız: {e2}")
                    
                    # Son çare: Dosyayı doğrudan çalıştır
                    self.basit_pdf_olustur(konu, zorluk)
                    return
    
            # Cevap bilgisini almak için modülü import et
            try:
                from logic.answer_utils import get_answer_for_image
                cevap_bilgisi_mevcut = True
            except ImportError:
                cevap_bilgisi_mevcut = False
                print("⚠️ Cevap bilgisi modülü bulunamadı, cevaplar gösterilmeyecek.")
            
            # PDF oluştur
            pdf = PDFCreator()
            pdf.baslik_ekle(f"{konu} - {zorluk} Seviyesi")
    
            # Tüm görselleri ve cevapları ekle
            cevaplar = []
            for idx, gorsel in enumerate(self.secilen_gorseller, 1):
                # Cevap bilgisini al
                if cevap_bilgisi_mevcut:
                    cevap = get_answer_for_image(gorsel)
                    cevaplar.append(cevap)
                    pdf.gorsel_ekle(gorsel)
                else:
                    pdf.gorsel_ekle(gorsel)
            
            # Cevap anahtarını ekle
            if cevap_bilgisi_mevcut and cevaplar:
                pdf.cevap_anahtari_ekle(cevaplar)
    
            # Kaydetme konumu sor
            cikti_dosya = filedialog.asksaveasfilename(
                title="PDF'i Nereye Kaydetmek İstersiniz?",
                defaultextension=".pdf",
                filetypes=[("PDF Dosyası", "*.pdf")],
                initialfile=f"{konu}_{zorluk}_{len(self.secilen_gorseller)}_soru.pdf"
            )
    
            if cikti_dosya:
                if pdf.kaydet(cikti_dosya):
                    kayit_yeri = f"{os.path.basename(os.path.dirname(cikti_dosya))}/{os.path.basename(cikti_dosya)}"

                    # Başarılı bildirimi
                    self.show_notification(
                        "✅ PDF Başarıyla Oluşturuldu!",
                        f"📁 Kayıt Yeri: {kayit_yeri}\n\n"
                        f"✨ {len(self.secilen_gorseller)} soru PDF formatında kaydedildi"
                    )
                else:
                    self.show_notification(
                        "❌ PDF Oluşturulamadı",
                        "📄 PDF oluşturulurken bir hata oluştu.\n"
                        "Lütfen tekrar deneyin."
                    )
    
        except Exception as e:
            print(f"❌ Genel PDF oluşturma hatası: {e}")
            self.show_notification(
                "❌ Hata",
                f"Beklenmeyen bir hata oluştu:\n{str(e)}\n\nLütfen konsolu kontrol edin."
            )

    def basit_pdf_olustur(self, konu, zorluk):
        """Basit PDF oluşturma - PDFCreator sınıfı import edilemediğinde"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            # Cevap bilgisini almak için modülü import et
            try:
                from logic.answer_utils import get_answer_for_image
                cevap_bilgisi_mevcut = True
            except ImportError:
                cevap_bilgisi_mevcut = False
                print("⚠️ Cevap bilgisi modülü bulunamadı, cevaplar gösterilmeyecek.")

            # Kaydetme konumu sor
            cikti_dosya = filedialog.asksaveasfilename(
                title="PDF'i Nereye Kaydetmek İstersiniz?",
                defaultextension=".pdf",
                filetypes=[("PDF Dosyası", "*.pdf")],
                initialfile=f"{konu}_{zorluk}_{len(self.secilen_gorseller)}_soru.pdf"
            )

            if not cikti_dosya:
                return

            # PDF oluştur
            story = []
            styles = getSampleStyleSheet()

            # Başlık ekle
            baslik = Paragraph(f"{konu} - {zorluk} Seviyesi", styles["Title"])
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
                        cevap = get_answer_for_image(gorsel_yolu)
                        cevaplar.append(cevap)
                        cevap_stili = styles["Normal"]
                        cevap_stili.alignment = 1  # Ortalama
                        cevap_paragraf = Paragraph(f"Cevap: {cevap}", cevap_stili)
                        story.append(cevap_paragraf)
                    
                    story.append(Spacer(1, 0.3*inch))
                except Exception as e:
                    print(f"Görsel ekleme hatası: {e}")
                    
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

            self.show_notification(
                "✅ PDF Başarıyla Oluşturuldu!",
                f"📁 Kayıt Yeri: {os.path.basename(cikti_dosya)}\n\n"
                f"✨ {len(self.secilen_gorseller)} soru PDF formatında kaydedildi"
            )

        except Exception as e:
            print(f"Basit PDF oluşturma hatası: {e}")
            self.show_notification(
                "❌ Hata",
                f"PDF oluşturulurken hata: {str(e)}"
            )
   
    def show_error(self, message):
        """Hata mesajını göster"""
        self._show_dialog("⚠️ Uyarı", message, "#dc3545")

    def show_notification(self, title, message,geri_don=False):
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

if __name__ == "__main__":
    # import tkinter as tk
    # root = tk.Tk()
    root = ctk.CTk()
    root.state('zoomed')
    app = KonuSecmePenceresi(root, None, ".")
    root.mainloop()