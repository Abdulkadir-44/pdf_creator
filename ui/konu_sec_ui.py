import customtkinter as ctk
import tkinter as tk
import os
from PIL import Image, ImageTk
import math
from tkinter import filedialog

# Modern tema ayarları
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

class KonuSecmePenceresi(ctk.CTkFrame):
    def __init__(self, parent, controller, unite_klasor_yolu):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.unite_klasor_yolu = unite_klasor_yolu
        self.secilen_gorseller = []
        
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

        # Soru Sayısı Seçimi
        soru_label = ctk.CTkLabel(
            self.form_frame, 
            text="🔢 Soru Sayısı:",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#495057"
        )
        soru_label.pack(pady=(10, 10), anchor="w", padx=40)

        self.soru_sayisi_var = tk.StringVar()
        self.soru_menu = ctk.CTkComboBox(
            self.form_frame,
            variable=self.soru_sayisi_var,
            values=["1 Soru", "2 Soru", "3 Soru", "5 Soru", "10 Soru"],
            font=ctk.CTkFont(family="Segoe UI", size=14),
            width=400,
            height=40,
            corner_radius=10,
            state="readonly"
        )
        self.soru_menu.set("Soru sayısı seçin...")
        self.soru_menu.pack(pady=(0, 30), padx=40)

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
        soru_sayisi_text = self.soru_sayisi_var.get()
        
        # Validasyon
        if any("seçin" in var.get().lower() for var in [self.konu_var, self.zorluk_var, self.soru_sayisi_var]):
            self.show_error("Lütfen tüm alanları seçin!")
            return
        
        # Seçilen klasör yolunu oluştur
        secilen_konu_path = os.path.join(self.unite_klasor_yolu, secilen_konu, zorluk.lower())
        
        # Soru sayısını al
        soru_sayisi = int(soru_sayisi_text.split()[0])
        
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
                        "Tüm görseller kaldırıldı!\nYeni seçim yapmak için 'Geri' butonuna tıklayın."
                    )
                    return

                # Önizlemeyi güncelle
                # Önce mevcut içeriği temizle
                for widget in parent_frame.winfo_children():
                    widget.destroy()

                # Görselleri yeniden göster
                self.display_images(parent_frame)

                # Bilgi etiketini güncelle (soru sayısı değişti)
                self.guncelle_bilgi_etiketi()

        except Exception as e:
            print(f"Görsel kaldırma hatası: {e}")
            self.show_error("Görsel kaldırılırken bir hata oluştu!")

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
        """Görselleri göster"""
        for i, gorsel_path in enumerate(self.secilen_gorseller):
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

                # Görsel adı etiketi
                name_label = ctk.CTkLabel(
                    img_container,
                    text=f"📸 {os.path.basename(gorsel_path)}",
                    font=ctk.CTkFont(family="Segoe UI", size=12),
                    text_color="#495057"
                )
                name_label.pack(pady=(0, 5))

                # Zorluk ve cevap bilgisi frame'i
                info_frame = ctk.CTkFrame(img_container, fg_color="transparent")
                info_frame.pack(pady=(0, 10))

                # Zorluk seviyesini klasör yolundan al
                zorluk_seviyesi = self.zorluk_var.get()

                # Bilgi etiketi
                info_label = ctk.CTkLabel(
                    info_frame,
                    text=f"Zorluk: {zorluk_seviyesi}      Cevap: A",
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                    text_color="#495057"
                )
                info_label.pack(side="left", padx=(0, 20))

                # Kaldır butonu
                kaldir_btn = ctk.CTkButton(
                    info_frame,
                    text="🗑️ Kaldır",
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                    width=80,
                    height=30,
                    corner_radius=8,
                    fg_color="#e74c3c",
                    hover_color="#c0392b",
                    text_color="#ffffff",
                    command=lambda idx=i: self.gorseli_kaldir(idx, parent_frame)
                )
                kaldir_btn.pack(side="right")

            except Exception as e:
                print(f"Görsel yükleme hatası: {e}")
                # Hata durumunda placeholder göster
                error_container = ctk.CTkFrame(parent_frame, fg_color="#f8f9fa", corner_radius=10)
                error_container.pack(pady=10, padx=10, fill="x")

                error_label = ctk.CTkLabel(
                    error_container,
                    text=f"❌ Görsel yüklenemedi:\n{os.path.basename(gorsel_path)}",
                    font=ctk.CTkFont(family="Segoe UI", size=12),
                    text_color="#e74c3c"
                )
                error_label.pack(pady=20)
   
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
                import sys
                import os
                
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
    
            # PDF oluştur
            pdf = PDFCreator()
            pdf.baslik_ekle(f"{konu} - {zorluk} Seviyesi")
    
            # Tüm görselleri ekle
            for idx, gorsel in enumerate(self.secilen_gorseller, 1):
                pdf.gorsel_ekle(gorsel)
    
            # Kaydetme konumu sor
            cikti_dosya = filedialog.asksaveasfilename(
                title="PDF'i Nereye Kaydetmek İstersiniz?",
                defaultextension=".pdf",
                filetypes=[("PDF Dosyası", "*.pdf")],
                initialfile=f"{konu}_{zorluk}_{len(self.secilen_gorseller)}_soru.pdf"
            )
    
            if cikti_dosya:
                if pdf.kaydet(cikti_dosya):
                    # Başarılı bildirimi
                    self.show_notification(
                        "✅ PDF Başarıyla Oluşturuldu!",
                        f"📁 Kayıt Yeri: {os.path.basename(cikti_dosya)}\n\n"
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
            from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch

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

            # Görselleri ekle
            for gorsel_yolu in self.secilen_gorseller:
                try:
                    img = Image(gorsel_yolu, width=6*inch, height=4*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.3*inch))
                except Exception as e:
                    print(f"Görsel ekleme hatası: {e}")

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

    def show_notification(self, title, message):
        """Kullanıcıya bildirim göster"""
        color = "#27ae60" if "✅" in title else "#e74c3c"
        self._show_dialog(title, message, color)

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
    import tkinter as tk
    root = tk.Tk()
    root.state('zoomed')
    app = KonuSecmePenceresi(root, None, ".")
    root.mainloop()