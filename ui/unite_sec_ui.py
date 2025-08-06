import customtkinter as ctk
from tkinter import filedialog
import os

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

BG_COLOR = "#f2f2f2"
SCROLL_BG = "#e6e6e6"
BTN_BG = "#4a90e2"
BTN_FG = "#ffffff"

class UniteSecmePenceresi(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG_COLOR)
        self.controller = controller
        self.current_buttons = []
        self.setup_ui()

    def setup_ui(self):
        """UI elementlerini oluştur"""
        self.btn_font = ctk.CTkFont(family="Segoe UI", size=11, weight="bold")

        # Başlık
        title_label = ctk.CTkLabel(
            self,
            text="📂 Ünite Seçimi",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#2d3436"
        )
        title_label.pack(pady=20)

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

    def show_initial_message(self):
        """Başlangıç mesajını göster"""
        message_label = ctk.CTkLabel(
            self.scroll_frame,
            text="📁 Lütfen üstteki 'Ana Klasör Seç' butonuna tıklayarak\nsoru klasörünüzü seçin.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#6c757d",
            justify="center"
        )
        message_label.pack(pady=50)

    def ana_klasoru_sec(self):
        """Ana klasörü seç ve ünite butonlarını göster"""
        klasor_yolu = filedialog.askdirectory(title="Ana Soru Klasörünü Seçin")
        if klasor_yolu:
            self.goster_unite_butonlari(klasor_yolu)

    def goster_unite_butonlari(self, ana_klasor):
        """Ünite butonlarını göster"""
        # Scroll frame'i temizle
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.current_buttons.clear()

        try:
            # Klasörleri al
            klasorler = [d for d in os.listdir(ana_klasor) 
                        if os.path.isdir(os.path.join(ana_klasor, d))]
            
            if not klasorler:
                self.show_empty_folder_message()
                return

            # Her klasör için buton oluştur
            for klasor in klasorler:
                buton = ctk.CTkButton(
                    self.scroll_frame,
                    text=f"📚 {klasor}",
                    font=self.btn_font,
                    fg_color="#7bc96f",
                    text_color="#ffffff",
                    hover_color="#5aa75f",
                    width=250,
                    height=50,
                    command=lambda k=klasor: self.konu_secme_ekranini_ac(ana_klasor, k)
                )
                self.current_buttons.append(buton)

            self.relayout_buttons()

        except Exception as e:
            print("Ünite butonları gösterme hatası:", e)
            self.show_error_message(f"Hata: {str(e)}")

    def show_empty_folder_message(self):
        """Boş klasör mesajı göster"""
        message_label = ctk.CTkLabel(
            self.scroll_frame,
            text="📭 Seçilen klasörde alt klasör bulunamadı.\n\nLütfen soru klasörlerinizi içeren\nana klasörü seçtiğinizden emin olun.",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#e74c3c",
            justify="center"
        )
        message_label.pack(pady=50)

    def show_error_message(self, message):
        """Hata mesajı göster"""
        error_label = ctk.CTkLabel(
            self.scroll_frame,
            text=f"❌ {message}",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="#e74c3c",
            justify="center"
        )
        error_label.pack(pady=50)

    def konu_secme_ekranini_ac(self, ana_klasor, secilen_unite):
        """Konu seçme ekranını aç"""
        unite_klasor_yolu = os.path.join(ana_klasor, secilen_unite)
        self.controller.show_frame("KonuSecme", unite_klasor_yolu=unite_klasor_yolu)

    def ana_menuye_don(self):
        """Ana menüye dön"""
        self.controller.ana_menuye_don()

    def relayout_buttons(self):
        """Butonları yeniden düzenle"""
        if not self.current_buttons:
            return

        # Önceki grid ayarlarını temizle
        for widget in self.scroll_frame.winfo_children():
            widget.grid_forget()

        # Buton düzenleme parametreleri
        padding = 15
        margin = 30
        btn_width_px = 250

        # Pencere genişliğine göre kolon sayısını hesapla
        try:
            # Scroll frame genişliğini al (varsayılan değer 800)
            frame_width = self.scroll_frame.winfo_width()
            if frame_width <= 1:  # Henüz render olmamışsa
                frame_width = 800
        except:
            frame_width = 800

        usable_width = frame_width - 2 * margin
        max_columns = max(1, usable_width // (btn_width_px + padding))

        # Grid konfigürasyonu
        for col in range(max_columns):
            self.scroll_frame.grid_columnconfigure(col, weight=1)

        # Butonları yerleştir
        for idx, btn in enumerate(self.current_buttons):
            row = idx // max_columns
            col = idx % max_columns
            btn.grid(row=row, column=col, padx=padding//2, pady=10, sticky="ew")

        # Layout'u güncelle
        self.scroll_frame.update_idletasks()

if __name__ == "__main__":
    import tkinter as tk
    root = tk.Tk()
    root.state('zoomed')
    app = UniteSecmePenceresi(root, None)
    root.mainloop()