# ui/dialog_yoneticisi.py

import customtkinter as ctk
import logging

"""
Soru Otomasyon Sistemi - Dialog Yöneticisi

Bu modül, uygulama genelinde kullanılacak tüm pop-up (CTkToplevel)
pencerelerin oluşturulmasını ve yönetilmesini merkezileştirir.

Ana Sınıf:
- DialogYoneticisi: 
  Ana UI penceresine (parent_ui) bağlanarak, onun adına
  hata, bildirim, onay ve bilgilendirme pencereleri açar.
"""

class DialogYoneticisi:
    """
    Tüm pop-up pencereleri (Hata, Bildirim, Onay) yönetir.
    
    Metodlar:
    - __init__(self, parent_ui): 
        Ana UI sınıfına (SoruParametresiSecmePenceresi) bağlanır.
        Logger, master ve controller referanslarını alır.
    
    - show_error(self, message): 
        Genel bir hata/uyarı mesajı gösterir.
    
    - show_notification(self, title, message, geri_don=False): 
        Başarı veya bilgi mesajı gösterir.
    
    - _show_dialog(self, title, message, color): 
        Tüm dialoglar için kullanılan ana şablon.
    
    - show_multipage_info(self, istenen_sayi, on_close=None): 
        Yazılı sınavlar için çoklu sayfa bilgilendirmesi yapar.
        
    - _show_cevap_onay_dialog(self, message, on_confirm_callback): 
        Cevap anahtarında '?' varsa kullanıcıdan onay ister.
        
    - show_havuz_tukendi_dialog(self, konu_adi, index): 
        Soru güncellemede havuz biterse sıfırlama onayı ister.
        
    - _darken_color(self, hex_color): 
        Dialog butonları için renk koyulaştırma yardımcısı.
    """
    
    def __init__(self, parent_ui):
        """
        Dialog yöneticisini başlatır.
        
        Args:
            parent_ui: Bu sınıfı çağıran ana UI sınıfı 
                         (SoruParametresiSecmePenceresi instance'ı).
                         'self.parent_ui.master', 'self.parent_ui.controller',
                         'self.parent_ui.logger' gibi referanslara erişmek için kullanılır.
        """
        self.parent_ui = parent_ui
        self.master = parent_ui.master
        self.controller = parent_ui.controller
        self.logger = parent_ui.logger 
        
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
                # DİKKAT: Ana sınıfın metodunu çağırıyoruz
                self.parent_ui.geri_don() 

        ok_btn = ctk.CTkButton(
            notify_window,
            text="Tamam",
            command=geri_don_ve_kapat
        )
        ok_btn.pack(pady=20)

    def _show_dialog(self, title, message, color):
        """Genel dialog gösterme metodu"""
        self.logger.debug(f"Dialog gösteriliyor: {title}")
        
        # DİKKAT: self.controller referansını kullanıyoruz
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
            # DİKKAT: self.controller referansını kullanıyoruz
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

    def _show_cevap_onay_dialog(self, message, on_confirm_callback):
        """
        Kullanıcıya cevapların '?' olacağını bildiren ve ONAY/REDDET soran
        yeni bir dialog gösterir.
        """
        try:
            dialog_window = ctk.CTkToplevel(self.master)
            dialog_window.title("Cevap Uyarısı")
            dialog_window.geometry("450x300")
            dialog_window.resizable(False, False)
            dialog_window.transient(self.master)
            dialog_window.grab_set()

            # Merkeze yerleştir
            self.master.update_idletasks()
            x = self.master.winfo_x() + self.master.winfo_width()//2 - 225
            y = self.master.winfo_y() + self.master.winfo_height()//2 - 150
            dialog_window.geometry(f"+{x}+{y}")

            icon_label = ctk.CTkLabel(
                dialog_window, text="⚠️",
                font=ctk.CTkFont(size=48), text_color="#ffc107"
            )
            icon_label.pack(pady=20)

            message_label = ctk.CTkLabel(
                dialog_window,
                text=message + "\n\nCevap anahtarı '?' olarak oluşturulacak.\nYine de devam etmek istiyor musunuz?",
                font=ctk.CTkFont(size=14), justify="center", wraplength=400
            )
            message_label.pack(pady=20, padx=20)

            button_frame = ctk.CTkFrame(dialog_window, fg_color="transparent")
            button_frame.pack(pady=20)

            def on_confirm():
                dialog_window.destroy()
                if callable(on_confirm_callback):
                    on_confirm_callback()

            def on_reject():
                dialog_window.destroy()

            evet_btn = ctk.CTkButton(
                button_frame, text="Evet, Devam Et", command=on_confirm,
                font=ctk.CTkFont(size=14, weight="bold"), width=140, height=40,
                fg_color="#28a745", hover_color="#218838"
            )
            evet_btn.pack(side="left", padx=10)

            hayir_btn = ctk.CTkButton(
                button_frame, text="Hayır, İptal", command=on_reject,
                font=ctk.CTkFont(size=14, weight="bold"), width=100, height=40,
                fg_color="#6c757d", hover_color="#5a6268"
            )
            hayir_btn.pack(side="left", padx=10)
            
        except Exception as e:
            self.logger.error(f"Onay dialogu gösterilirken hata: {e}", exc_info=True)
            if callable(on_confirm_callback):
                on_confirm_callback()
                
    def show_havuz_tukendi_dialog(self, konu_adi, index):
        """Havuz tükendiğinde kullanıcıya sor"""

        dialog_window = ctk.CTkToplevel(self.master)
        dialog_window.title("Soru Havuzu Tükendi")
        dialog_window.geometry("450x300")
        dialog_window.resizable(False, False)
        dialog_window.transient(self.master)
        dialog_window.grab_set()

        self.master.update_idletasks()
        x = self.master.winfo_x() + self.master.winfo_width()//2 - 225
        y = self.master.winfo_y() + self.master.winfo_height()//2 - 150
        dialog_window.geometry(f"+{x}+{y}")

        icon_label = ctk.CTkLabel(
            dialog_window, text="🔄", font=ctk.CTkFont(size=48)
        )
        icon_label.pack(pady=20)

        message = f"'{konu_adi}' konusundaki tüm sorular kullanıldı.\n\nSoru havuzunu sıfırlayarak baştan başlamak ister misiniz?"
        message_label = ctk.CTkLabel(
            dialog_window, text=message,
            font=ctk.CTkFont(size=14), justify="center", wraplength=400
        )
        message_label.pack(pady=20, padx=20)

        button_frame = ctk.CTkFrame(dialog_window, fg_color="transparent")
        button_frame.pack(pady=20)

        def sifirla_ve_guncelle():
            # Havuzu sıfırla
            # DİKKAT: Ana sınıfın 'kullanilan_sorular' özelliğini değiştiriyoruz
            self.parent_ui.kullanilan_sorular[konu_adi] = set() 
            dialog_window.destroy()
            # DİKKAT: Ana sınıfın metodunu çağırıyoruz
            self.parent_ui.gorseli_guncelle_new(index) 

        def iptal():
            dialog_window.destroy()

        evet_btn = ctk.CTkButton(
            button_frame, text="Evet, Sıfırla", command=sifirla_ve_guncelle,
            font=ctk.CTkFont(size=14, weight="bold"), width=120, height=40,
            fg_color="#28a745", hover_color="#218838"
        )
        evet_btn.pack(side="left", padx=10)

        hayir_btn = ctk.CTkButton(
            button_frame, text="Hayır", command=iptal,
            font=ctk.CTkFont(size=14, weight="bold"), width=80, height=40,
            fg_color="#6c757d", hover_color="#5a6268"
        )
        hayir_btn.pack(side="left", padx=10)

    def show_kalici_havuz_bitti_dialog(self, tukenen_konular, on_sifirla, on_devam):
        """
        Oturum havuzu tükenince kullanıcıya seçenek sunar:
        - Havuzu sıfırla (her zaman)
        - Mevcut kadarıyla devam et (yalnızca kalan soru > 0 ise)
        """
        try:
            toplam_kalan = sum(mevcut for _, mevcut, _ in tukenen_konular)
            hic_kalmadi = toplam_kalan == 0

            konu_listesi = "\n".join([
                f"• {konu}: {mevcut}/{istened} soru mevcut"
                for konu, mevcut, istened in tukenen_konular
            ])

            if hic_kalmadi:
                mesaj = (
                    f"Aşağıdaki konu(lar)daki tüm sorular bu oturumda kullanıldı:\n\n"
                    f"{konu_listesi}\n\n"
                    f"Devam etmek için havuzu sıfırlamanız gerekiyor.\n"
                    f"(Önceki PDF'lerdeki sorular tekrar gelebilir)"
                )
            else:
                mesaj = (
                    f"Aşağıdaki konu(lar)daki oturum soru havuzu tükendi:\n\n"
                    f"{konu_listesi}\n\n"
                    f"Ne yapmak istersiniz?"
                )

            yukseklik = "300" if hic_kalmadi else "340"
            dialog_window = ctk.CTkToplevel(self.controller)
            dialog_window.title("Oturum Havuzu Tükendi")
            dialog_window.geometry(f"520x{yukseklik}")
            dialog_window.resizable(False, False)
            dialog_window.transient(self.controller)
            dialog_window.grab_set()

            try:
                x = int(self.controller.winfo_x() + self.controller.winfo_width()/2 - 260)
                y = int(self.controller.winfo_y() + self.controller.winfo_height()/2 - 170)
                dialog_window.geometry(f"+{x}+{y}")
            except Exception:
                pass

            ctk.CTkLabel(dialog_window, text="🔁", font=ctk.CTkFont(size=44),
                         text_color="#f39c12").pack(pady=(20, 5))

            ctk.CTkLabel(dialog_window, text=mesaj,
                         font=ctk.CTkFont(size=13), justify="center",
                         wraplength=460).pack(padx=20, pady=5)

            btn_frame = ctk.CTkFrame(dialog_window, fg_color="transparent")
            btn_frame.pack(pady=20)

            def _sifirla():
                dialog_window.destroy()
                if callable(on_sifirla):
                    on_sifirla()

            def _devam():
                dialog_window.destroy()
                if callable(on_devam):
                    on_devam()

            ctk.CTkButton(
                btn_frame, text="🔄 Havuzu Sıfırla", command=_sifirla,
                font=ctk.CTkFont(size=13, weight="bold"), width=160, height=38,
                fg_color="#e67e22", hover_color="#ca6f1e"
            ).pack(side="left", padx=8)

            # Kalan soru varsa "Devam Et" butonu göster
            if not hic_kalmadi:
                ctk.CTkButton(
                    btn_frame, text="▶ Mevcut Kadarıyla Devam", command=_devam,
                    font=ctk.CTkFont(size=13, weight="bold"), width=190, height=38,
                    fg_color="#2980b9", hover_color="#2471a3"
                ).pack(side="left", padx=8)

        except Exception as e:
            self.logger.error(f"Kalıcı havuz dialog hatası: {e}", exc_info=True)
            if callable(on_devam):
                on_devam()
