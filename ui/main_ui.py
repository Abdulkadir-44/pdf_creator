import customtkinter as ctk
from ui.ders_sec_ui import DersSecmePenceresi
from ui.konu_baslik_sec_ui import KonuBaslikSecmePenceresi
from ui.soru_parametresi_sec_ui import SoruParametresiSecmePenceresi 
import logging


logger = logging.getLogger(__name__)

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

BG_COLOR = "#f2f2f2"
BTN_BG = "#4a90e2"
BTN_FG = "#ffffff"

class AnaPencere(ctk.CTk):
    def __init__(self):
        super().__init__()
        logger.info("AnaPencere (controller) başlatılıyor.")

        self.title("Soru Otomasyon Sistemi")
        self.configure(bg=BG_COLOR)

        # Tüm sayfaları tutacak bir ana container frame
        self.container = ctk.CTkFrame(self, fg_color=BG_COLOR)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Sayfaları depolayacağımız bir dictionary
        self.frames = {}
        
        # Sabit sayfaları oluştur
        self.init_frames()

        # Başlangıç sayfasını göster
        self.show_frame("AnaMenu")
        
        # Pencere hazır olduktan sonra maximize yap
        self.after(50, lambda: self.state('zoomed'))

    def init_frames(self):
        logger.debug("Sabit frame'ler oluşturuluyor: AnaMenu, UniteSecme")
        """Sabit frame'leri başlangıçta oluştur"""
        # Ana Menü
        self.frames["AnaMenu"] = AnaMenu(self.container, self)
        self.frames["AnaMenu"].grid(row=0, column=0, sticky="nsew")
        
        # Ders Seçme (eski UniteSecme)
        self.frames["UniteSecme"] = DersSecmePenceresi(self.container, self)
        self.frames["UniteSecme"].grid(row=0, column=0, sticky="nsew")

    def show_frame(self, frame_name, **kwargs):
        """Frame'i göster"""
        logger.info(f"'{frame_name}' sayfası gösterilmek üzere çağrıldı.")
        
        # Dinamik frame oluşturma
        if frame_name == "KonuBaslikSecme":
            ders_klasor_yolu = kwargs.get('ders_klasor_yolu')
            ders_adi = kwargs.get('ders_adi')
            logger.debug(f"KonuBaslikSecme sayfası '{ders_adi}' dersi için dinamik olarak oluşturuluyor/güncelleniyor.")
            if ders_klasor_yolu and ders_adi:
                # Eğer frame varsa güncelle, yoksa oluştur
                if "KonuBaslikSecme" in self.frames:
                    self.frames["KonuBaslikSecme"].destroy()
                
                self.frames["KonuBaslikSecme"] = KonuBaslikSecmePenceresi(
                    self.container, self, ders_klasor_yolu, ders_adi
                )
                self.frames["KonuBaslikSecme"].grid(row=0, column=0, sticky="nsew")
        
        elif frame_name == "SoruParametre":
            ders_adi = kwargs.get('ders_adi')
            secilen_konular = kwargs.get('secilen_konular')
            logger.debug(f"SoruParametre sayfası '{ders_adi}' dersinin  konusu için oluşturuluyor.")
            if ders_adi and secilen_konular:
                # Eğer frame varsa güncelle, yoksa oluştur
                if "SoruParametre" in self.frames:
                    self.frames["SoruParametre"].destroy()
                
                self.frames["SoruParametre"] = SoruParametresiSecmePenceresi(
                    self.container, self, None, ders_adi, secilen_konular
                )
                self.frames["SoruParametre"].grid(row=0, column=0, sticky="nsew")
        
        # Frame'i en üste getir
        if frame_name in self.frames:
            self.frames[frame_name].tkraise()

    def ana_menuye_don(self):
        """Ana menüye dön"""
        logger.info("Ana menüye dönülüyor.")
        self.show_frame("AnaMenu")

class AnaMenu(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color=BG_COLOR)
        logger.info("AnaMenu frame'i oluşturuldu.")
        
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        btn_font = ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        
        # Ana frame
        ana_frame = ctk.CTkFrame(self, fg_color=BG_COLOR)
        ana_frame.pack(expand=True)

        # Başlık
        title_label = ctk.CTkLabel(
            ana_frame,
            text="🎯 Soru Otomasyon Sistemi",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color="#2d3436"
        )
        title_label.pack(pady=15)

        # Soru seç butonu
        soru_sec_btn = ctk.CTkButton(
            ana_frame,
            text="✔ Soru Seç ve PDF Oluştur",
            font=btn_font,
            fg_color=BTN_BG,
            text_color=BTN_FG,
            hover_color="#357ABD",
            width=300,
            height=50,
            command=self.soru_sec_ekranini_ac
        )
        soru_sec_btn.pack(pady=20)

        # Klasör yönetim butonu
        klasor_yonet_btn = ctk.CTkButton(
            ana_frame,
            text="🗂 Soru Yükle / Klasör Yönetimi",
            font=btn_font,
            fg_color=BTN_BG,
            text_color=BTN_FG,
            hover_color="#357ABD",
            width=300,
            height=50,
            command=self.klasor_yonetimi_ekranini_ac
        )
        klasor_yonet_btn.pack(pady=10)

    def soru_sec_ekranini_ac(self):
        """Ders seçme ekranını göster"""
        logger.info("'Soru Seç ve PDF Oluştur' butonuna tıklandı.")
        self.controller.show_frame("UniteSecme")

    def klasor_yonetimi_ekranini_ac(self):
        """Klasör yönetimi ekranını göster (gelecekte implement edilecek)"""
        logger.warning("'Klasör Yönetimi' butonuna tıklandı (henüz implement edilmedi).")
        # Geçici mesaj göster
        temp_window = ctk.CTkToplevel(self.controller)
        temp_window.title("Bilgi")
        temp_window.geometry("300x150")
        temp_window.resizable(False, False)
        
        label = ctk.CTkLabel(
            temp_window,
            text="Klasör Yönetimi\n(Yapım Aşamasında)",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            text_color="black"
        )
        label.pack(pady=40)
        
        ok_btn = ctk.CTkButton(
            temp_window,
            text="Tamam",
            command=temp_window.destroy
        )
        ok_btn.pack(pady=10)

# if __name__ == "__main__":
#     app = AnaPencere()
#     app.mainloop()