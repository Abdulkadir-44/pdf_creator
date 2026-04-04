# logic/oturum_yoneticisi.py

import os
import logging
from logic.answer_utils import get_answer_for_image
from logic.pdf_generator import PDFCreator
from tkinter import filedialog
import random
# import sys

# PDFCreator import kontrolü için
try:
    # import reportlab
    PDF_CREATOR_MEVCUT = True
except ImportError:
    PDF_CREATOR_MEVCUT = False

# Fallback (basit) PDF için
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    FALLBACK_PDF_MEVCUT = True
except ImportError:
    FALLBACK_PDF_MEVCUT = False
    
"""
Soru Otomasyon Sistemi - Oturum Yöneticisi (Beyin)

Bu modül, SoruParametresiSecmePenceresi'nin (UI Controller)
TÜM İŞ MANTIĞINI (Business Logic) yönetir.

UI (Arayüz) bilmez. Sadece 'controller' referansı üzerinden
'state'i (durumu) yönetir, hesaplamaları yapar ve
UI'ın yenilenmesini tetikler.

Ana Sınıf:
- OturumYoneticisi: 
  'Controller'dan gelen sinyallerle (örn: gorseli_guncelle)
  tüm 'state'i (sayfa_haritasi, secilen_gorseller) yönetir.
"""

class OturumYoneticisi:
    """
    Tüm 'state' (durum) ve 'iş mantığı'nı yöneten "Beyin" sınıfı.
    
    Metodlar:
    - __init__(self, controller):
        Ana UI Controller'a bağlanır. 'logger' ve 'dialog_yoneticisi'
        gibi yardımcıları 'controller' üzerinden alır.
        
    - (Tüm iş mantığı fonksiyonları):
        gorseli_guncelle_new, pdf_olustur, _proceed_to_preview,
        _replan_and_refresh_ui, vb.
        
    - (Yardımcı metodlar):
        find_topic_from_path, _havuzu_sifirla, vb.
    """
    
    def __init__(self, controller):
        """
        Oturum Yöneticisini başlatır.
        
        Args:
            controller (SoruParametresiSecmePenceresi): 
                Ana UI sınıfı (Yönetici). Tüm 'state'e ve 
                yardımcılara (logger, dialog) erişim için kullanılır.
        """
        self.controller = controller
        # Gerekli yardımcıları 'controller'dan al
        self.logger = self.controller.logger
        self.dialog_yoneticisi = self.controller.dialog_yoneticisi
        
    
    def _havuzu_sifirla(self):
        """Kullanılan sorular havuzunu sıfırla"""
        try:
            # DİKKAT: 'self.controller' üzerindeki state'i yönetir
            self.controller.kullanilan_sorular = {
                konu_adi: set() for konu_adi in self.controller.secilen_konular.keys()
            }
            self.logger.debug("Kullanılan sorular havuzu sıfırlandı")
        except Exception as e:
            self.logger.error(f"Havuz sıfırlama hatası: {e}")

    def secili_gorselleri_al(self, soru_tipi, zorluk, on_complete=None):
        """
        Çift Havuz Sistemi:
        - kullanilan_sorular: Önizleme havuzu (her PDF'te sıfırlanır)
        - kalici_kullanilan: Oturum havuzu (sadece PDF'e basılanlar, sıfırlanmaz)
        """
        try:
            # 1. OTURUM HAVUZU (kalici) — oturum boyunca sıfırlanmaz
            if not hasattr(self.controller, 'kalici_kullanilan'):
                self.controller.kalici_kullanilan = {}
            kalici_ref = self.controller.kalici_kullanilan

            # 2. ÖNİZLEME HAVUZUNU SIFIRLA — her yeni PDF için taze başlangıç
            self._havuzu_sifirla()
            kullanilan_ref = self.controller.kullanilan_sorular

            konu_dagilimi = self.controller.konu_soru_dagilimi
            secilen_konular = self.controller.secilen_konular

            # 3. HAVUZ YETERLİLİK KONTROLÜ
            tukenen_konular = []
            for konu_adi, sayi in konu_dagilimi.items():
                konu_path = secilen_konular[konu_adi]
                klasor_yolu = os.path.join(konu_path, soru_tipi.lower(), zorluk.lower())
                if not os.path.exists(klasor_yolu):
                    continue
                tum_disk = [f for f in os.listdir(klasor_yolu)
                            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
                kalici_set = kalici_ref.get(konu_adi, set())
                kalan = [f for f in tum_disk if f not in kalici_set]
                if len(kalan) < sayi:
                    tukenen_konular.append((konu_adi, len(kalan), sayi))

            # 4. HAVUZ TÜKENDİYSE DIALOG GÖSTER
            if tukenen_konular:
                def _sifirla_ve_devam():
                    # Tükenen konuların kalıcı havuzunu sıfırla
                    for konu_adi, _, _ in tukenen_konular:
                        kalici_ref[konu_adi] = set()
                        self.logger.info(f"'{konu_adi}' kalıcı havuzu sıfırlandı.")
                    self._secim_yap_ve_devam(soru_tipi, zorluk, kalici_ref,
                                             kullanilan_ref, on_complete)

                def _mevcut_kadar_devam():
                    self.logger.info("Havuz yetersiz — mevcut soruyla devam ediliyor.")
                    self._secim_yap_ve_devam(soru_tipi, zorluk, kalici_ref,
                                             kullanilan_ref, on_complete)

                self.dialog_yoneticisi.show_kalici_havuz_bitti_dialog(
                    tukenen_konular, _sifirla_ve_devam, _mevcut_kadar_devam
                )
                return  # Dialog callback'i devam ettirecek
            else:
                # Havuz yeterli, direkt devam
                self._secim_yap_ve_devam(soru_tipi, zorluk, kalici_ref,
                                         kullanilan_ref, on_complete)

        except Exception as e:
            self.logger.error(f"Görsel seçme hazırlık hatası: {e}", exc_info=True)
            self.controller.secilen_gorseller = []
            if callable(on_complete):
                on_complete()

    def _secim_yap_ve_devam(self, soru_tipi, zorluk, kalici_ref, kullanilan_ref, on_complete=None):
        """Havuz kontrolü sonrası gerçek soru seçimini yapar."""
        try:
            tum_gorseller = []
            konu_dagilimi = self.controller.konu_soru_dagilimi
            secilen_konular = self.controller.secilen_konular

            for konu_adi, sayi in konu_dagilimi.items():
                konu_path = secilen_konular[konu_adi]
                klasor_yolu = os.path.join(konu_path, soru_tipi.lower(), zorluk.lower())

                if not os.path.exists(klasor_yolu):
                    self.logger.warning(f"Klasör bulunamadı: {klasor_yolu}")
                    continue

                tum_disk = [f for f in os.listdir(klasor_yolu)
                            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]

                if not tum_disk:
                    self.logger.warning(f"'{konu_adi}' klasöründe görsel yok: {klasor_yolu}")
                    continue

                # Kalıcı havuzdan çıkar (oturum geneli)
                kalici_set = kalici_ref.get(konu_adi, set())
                kalan = [f for f in tum_disk if f not in kalici_set]

                # Seç
                if len(kalan) >= sayi:
                    secilen = random.sample(kalan, sayi)
                else:
                    secilen = kalan  # Mevcut kadar al
                    if kalan:
                        self.logger.info(f"'{konu_adi}': {sayi} istendi, {len(kalan)} seçildi.")

                # Önizleme havuzuna ekle (kullanilan_sorular)
                if konu_adi not in kullanilan_ref:
                    kullanilan_ref[konu_adi] = set()
                for gorsel in secilen:
                    kullanilan_ref[konu_adi].add(gorsel)
                    tum_gorseller.append(os.path.join(klasor_yolu, gorsel))

                self.logger.debug(
                    f"'{konu_adi}': {len(secilen)} seçildi | "
                    f"Önizleme havuzu: {len(kullanilan_ref[konu_adi])} | "
                    f"Kalıcı havuz: {len(kalici_set)}"
                )

            if not tum_gorseller:
                self.logger.error("Hiç görsel seçilemedi!")
                self.dialog_yoneticisi.show_error(
                    "Seçilen konularda görsel bulunamadı!\n"
                    "Klasör yapısını kontrol edin."
                )
                self.controller.secilen_gorseller = []
                return

            random.shuffle(tum_gorseller)
            self.logger.info(f"Toplam {len(tum_gorseller)} görsel seçildi ve karıştırıldı.")
            self.controller.secilen_gorseller = tum_gorseller

            if callable(on_complete):
                on_complete()

        except Exception as e:
            self.logger.error(f"Görsel seçim hatası: {e}", exc_info=True)
            self.controller.secilen_gorseller = []
            self.dialog_yoneticisi.show_error(f"Görsel seçilirken hata oluştu: {e}")


            
    def _proceed_to_preview(self, soru_tipi, zorluk):
        """Bilgilendirme sonrası güvenle önizleme akışına geç."""
        try:
            # GÖRSELLERİ AL — callback ile devam (dialog olabilir)
            def _sonraki_adim():
                secilen_gorseller = self.controller.secilen_gorseller
                if not secilen_gorseller:
                    return  # _secim_yap_ve_devam zaten hata gösterdi
                self._planlama_ve_ui(soru_tipi, secilen_gorseller)

            self.secili_gorselleri_al(soru_tipi, zorluk, on_complete=_sonraki_adim)

        except Exception as e:
            self.logger.error(f"Önizleme akışında hata: {e}", exc_info=True)
            self.dialog_yoneticisi.show_error(f"Önizleme başlatılırken hata oluştu: {e}")

    def _planlama_ve_ui(self, soru_tipi, secilen_gorseller):
        """Seçilen görsellerle planlama yapar ve önizleme UI'ını açar."""
        try:
            self.logger.info("Planlama başlatılıyor...")
            pdf_planner = PDFCreator()
            pdf_planner.gorsel_listesi = secilen_gorseller

            if soru_tipi.lower() == "test":
                sayfa_haritasi = pdf_planner.planla_test_duzeni()
            else:
                self.logger.info("Yazılı (basit) planlaması başlatılıyor...")
                soru_listesi = []
                for i, path in enumerate(secilen_gorseller):
                    soru_listesi.append({
                        'index': i, 'path': path, 'total_height': 500,
                        'final_size': (500, 400)
                    })
                sayfa_listesi = []
                for i in range(0, len(soru_listesi), 2):
                    sayfa_sorulari = soru_listesi[i:i+2]
                    sayfa_listesi.append([sayfa_sorulari, []])
                sayfa_haritasi = sayfa_listesi

            self.controller.sayfa_haritasi = sayfa_haritasi

            if sayfa_haritasi:
                self.logger.info(f"{len(secilen_gorseller)} görsel {len(sayfa_haritasi)} sayfaya planlandı.")
                self.controller.current_page = 0
                self.controller.gorsel_onizleme_alani_olustur()
            else:
                self.logger.error("Planlama sonucu boş")
                self.dialog_yoneticisi.show_error("Seçilen konularda görsel bulunamadı!")

        except Exception as e:
            self.logger.error(f"Planlama hatası: {e}", exc_info=True)
            self.dialog_yoneticisi.show_error(f"Önizleme oluşturulurken hata oluştu: {e}")

    def _replan_and_refresh_ui(self):
        """
        'secilen_gorseller' değiştiğinde çağrılır.
        'sayfa_haritasi'nı yeniden hesaplar ve UI'ın yenilenmesini tetikler.
       
        """
        try:
            self.logger.info("'secilen_gorseller' değişti, plan yeniden hesaplanıyor...")
            
            # 1. GÜNCEL STATE'İ AL
            secilen_gorseller = self.controller.secilen_gorseller
            soru_tipi = self.controller.soru_tipi_var.get().lower()

            # 2. YENİDEN PLANLA
            pdf_planner = PDFCreator()
            pdf_planner.gorsel_listesi = secilen_gorseller
            
            if soru_tipi == "test":
                yeni_harita = pdf_planner.planla_test_duzeni() 
            else:
                soru_listesi = []
                for i, path in enumerate(secilen_gorseller):
                    soru_listesi.append({
                        'index': i, 'path': path, 'total_height': 500, 
                        'final_size': (500, 400) # Tahmini boyut
                    })
                sayfa_listesi = []
                for i in range(0, len(soru_listesi), 2):
                    sayfa_sorulari = soru_listesi[i:i+2]
                    sayfa_listesi.append([ sayfa_sorulari, [] ]) 
                yeni_harita = sayfa_listesi
            
            # 3. STATE'İ GÜNCELLE
            self.controller.sayfa_haritasi = yeni_harita

            # 4. Sayfa taşmasını engelle (STATE'İ GÜNCELLE)
            toplam_sayfa = len(yeni_harita)
            if not yeni_harita: # Eğer son soru da silindiyse
                self.controller.sayfa_haritasi = [ [ [], [] ] ] # Boş bir sayfa
                toplam_sayfa = 1
            
            if self.controller.current_page >= toplam_sayfa:
                self.controller.current_page = max(0, toplam_sayfa - 1)
            
            # 5. UI'I TETİKLE
            # DİKKAT: 'self.controller' üzerinden UI fonksiyonunu çağır
            if hasattr(self.controller, 'onizleme_ekrani') and self.controller.onizleme_ekrani and self.controller.onizleme_ekrani.winfo_exists():
                self.controller.display_images_new(
                    self.controller.onizleme_ekrani.pdf_container, 
                    self.controller.onizleme_ekrani.controls_container
                )
                self.logger.info("Plan ve UI başarıyla yenilendi.")
            else:
                self.logger.warning("_replan_and_refresh_ui: UI referansları bulunamadı, yenilenemedi.")
        
        except Exception as e:
            self.logger.error(f"Yeniden planlama ve UI yenileme hatası: {e}", exc_info=True)

    def gorseli_guncelle_new(self, index):
        """Görseli havuzdan yeni bir taneyle değiştirir."""
        try:
            # STATE'İ OKU
            secilen_gorseller = self.controller.secilen_gorseller
            
            if 0 <= index < len(secilen_gorseller):
                mevcut_gorsel_path = secilen_gorseller[index]
                mevcut_konu = self.find_topic_from_path(mevcut_gorsel_path)
                
                if not mevcut_konu:
                    self.dialog_yoneticisi.show_error("Görselin hangi konudan geldiği bulunamadı!")
                    return
    
                # STATE'İ OKU
                soru_tipi = self.controller.soru_tipi_var.get()
                zorluk = self.controller.zorluk_var.get()
                konu_path = self.controller.secilen_konular[mevcut_konu]
                klasor_yolu = os.path.join(konu_path, soru_tipi.lower(), zorluk.lower())
    
                tum_gorseller = [f for f in os.listdir(klasor_yolu) 
                               if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
    
                if not tum_gorseller:
                    self.dialog_yoneticisi.show_error("Güncellenecek görsel bulunamadı!")
                    return
    
                # ÖNCEDEN KULLANILAN SORULAR
                kullanilan_sorular = self.controller.kullanilan_sorular
                if mevcut_konu not in kullanilan_sorular:
                    kullanilan_sorular[mevcut_konu] = set()

                # ŞU AN EKRANDA OLAN SORULAR — secilen_gorseller'den kesin olarak al
                # os.path.normcase: Windows'ta slash+büyük/küçük harf normalize eder
                klasor_abs = os.path.normcase(os.path.abspath(klasor_yolu))
                gosterilenler_bu_klasorde = set(
                    os.path.basename(g)
                    for g in secilen_gorseller
                    if os.path.normcase(os.path.abspath(os.path.dirname(g))) == klasor_abs
                )

                # İKİ KAYNAĞI BİRLEŞTİR: geçmiş kullanılan + şu an ekrandakiler
                kullanilmis = kullanilan_sorular[mevcut_konu] | gosterilenler_bu_klasorde

                kullanilmamis_gorseller = [
                    f for f in tum_gorseller if f not in kullanilmis
                ]

                self.logger.debug(
                    f"GÜNCELLE [{mevcut_konu}]: "
                    f"Ekranda={gosterilenler_bu_klasorde} | "
                    f"Kullanıldı={kullanilan_sorular[mevcut_konu]} | "
                    f"Uygun={len(kullanilmamis_gorseller)}/{len(tum_gorseller)}"
                )

                if not kullanilmamis_gorseller:
                    secili_konu_gorselleri_sayisi = len(gosterilenler_bu_klasorde)
                    toplam_soru_sayisi = len(tum_gorseller)

                    if secili_konu_gorselleri_sayisi >= toplam_soru_sayisi:
                        self.logger.warning(f"'{mevcut_konu}' için güncelleme başarısız. Tüm sorular ({toplam_soru_sayisi}) zaten seçili.")
                        self.dialog_yoneticisi.show_error(
                            f"'{mevcut_konu}' konusundaki tüm sorular ({toplam_soru_sayisi} adet) zaten seçilmiş.\n\n"
                            "Güncellemek için havuzda başka soru kalmadı."
                        )
                        return
                    else:
                        self.logger.info(f"'{mevcut_konu}' için havuz tükendi. Reset dialogu gösteriliyor.")

                        def _sifirla_ve_guncelle():
                            # State değişikliği BEYINDE yapılır, dialog'da değil
                            kullanilan_sorular[mevcut_konu] = set()
                            self.logger.info(f"'{mevcut_konu}' önizleme havuzu sıfırlandı.")
                            self.gorseli_guncelle_new(index)

                        self.dialog_yoneticisi.show_havuz_tukendi_dialog(
                            mevcut_konu, on_sifirla=_sifirla_ve_guncelle
                        )
                        return
    
                yeni_gorsel_dosya = random.choice(kullanilmamis_gorseller)
                yeni_gorsel_path = os.path.join(klasor_yolu, yeni_gorsel_dosya)
                eski_gorsel_dosya = os.path.basename(mevcut_gorsel_path)
                
                # STATE'İ GÜNCELLE
                kullanilan_sorular[mevcut_konu].add(yeni_gorsel_dosya)
                secilen_gorseller[index] = yeni_gorsel_path
                
                self.logger.info(f"Görsel güncellendi: {eski_gorsel_dosya} -> {yeni_gorsel_dosya}")
    
                # UI'I TETİKLE
                self._replan_and_refresh_ui()
    
        except Exception as e:
            self.logger.error(f"Görsel güncelleme hatası: {e}")
            self.dialog_yoneticisi.show_error("Görsel güncellerken bir hata oluştu!")

    def gorseli_kaldir_new(self, index):
        """Görseli kaldırır ve planı/UI'ı günceller."""
        try:
            # STATE'İ OKU
            secilen_gorseller = self.controller.secilen_gorseller
            
            if 0 <= index < len(secilen_gorseller):
                # STATE'İ GÜNCELLE
                kaldirilan_gorsel_path = secilen_gorseller.pop(index)

                kaldirilan_konu = self.find_topic_from_path(kaldirilan_gorsel_path)
                if kaldirilan_konu:
                    kaldirilan_dosya = os.path.basename(kaldirilan_gorsel_path)
                    self.logger.info(f"Silinen görsel kullanılan listesinde tutuldu: {kaldirilan_dosya}")

                self.logger.info(f"Görsel kaldırıldı: {os.path.basename(kaldirilan_gorsel_path)}")

                if not secilen_gorseller:
                    self.dialog_yoneticisi.show_notification(
                        "Uyarı",
                        "Tüm görseller kaldırıldı!\nYeni seçim yapmak için 'Geri' butonuna tıklayın.",
                        geri_don=False 
                    )
                
                # UI'I TETİKLE
                self._replan_and_refresh_ui()

        except Exception as e:
            self.logger.error(f"Görsel kaldırma hatası: {e}")
            self.dialog_yoneticisi.show_error("Görsel kaldırılırken bir hata oluştu!")
               
    def find_topic_from_path(self, gorsel_path):
        """Görsel yolundan hangi konudan geldiğini bul"""
        try:
            # STATE'İ OKU
            secilen_konular = self.controller.secilen_konular
            for konu_adi, konu_path in secilen_konular.items():
                if konu_path in gorsel_path:
                    return konu_adi
            return None
        except Exception as e:
            self.logger.error(f"Konu bulma hatası: {e}")
            return None
    
    def get_answer_for_image(self, image_path):
        return get_answer_for_image(image_path)
    
    def _get_sorular_per_sayfa(self):
        """Soru tipine göre sayfa başı soru sayısını döndür"""
        # STATE'İ OKU
        soru_tipi = self.controller.soru_tipi_var.get().lower()
        return 2 if soru_tipi == "yazili" else 8
                                   
    def pdf_olustur(self):
        """PDF oluşturma işleminin tüm mantığı."""
        self.logger.info(f"PDF oluşturma başlatıldı - {self.controller.ders_adi}")
        
        try:
            # 1. KONTROLLER
            if not PDF_CREATOR_MEVCUT:
                self.logger.error("Reportlab modülü bulunamadı (PDFCreator)")
                self.dialog_yoneticisi.show_notification(
                    "Eksik Modül",
                    "PDF oluşturmak için 'reportlab' modülü gerekli.\n\nÇözüm: Terminal'e şunu yazın:\npip install reportlab"
                )
                return
            
            # 2. HAZIRLIK (STATE'İ OKU)
            pdf = PDFCreator()
            pdf.soru_tipi = self.controller.soru_tipi_var.get()
            baslik = (self.controller.baslik_text_var.get() or "").strip() or "QUIZ"
            pdf.baslik_ekle(baslik)
            
            # STATE'İ OKU
            pdf.gorsel_listesi = self.controller.secilen_gorseller[:]
            sayfa_haritasi = self.controller.sayfa_haritasi
            
            self.logger.info("PDF Cevap Anahtarı için 'sayfa_haritasi' okunuyor...")
            cevaplar = []
            for sayfa_sutunlari in sayfa_haritasi:
                for sutun in sayfa_sutunlari:
                    for soru_info in sutun:
                        cevap = get_answer_for_image(soru_info['path'])
                        cevaplar.append(cevap)
            self.logger.info(f"PDF Cevap Anahtarı {len(cevaplar)} cevap ile oluşturuldu (Planlanmış Sıra).")
            
            cevap_anahtari_isteniyor = self.controller.cevap_anahtari_var.get() == "Evet"
            
            if cevap_anahtari_isteniyor and cevaplar:
                pdf.cevap_anahtari_ekle(cevaplar)
            
            # 3. KAYDETME FONKSİYONU (İÇ FONKSİYON)
            def _proceed_to_save():
                try:
                    cikti_dosya = filedialog.asksaveasfilename(
                        title="PDF'i Nereye Kaydetmek İstersiniz?",
                        defaultextension=".pdf",
                        filetypes=[("PDF Dosyası", "*.pdf")],
                        initialfile=f"{self.controller.ders_adi}_{self.controller.soru_tipi_var.get()}_{self.controller.zorluk_var.get()}_{len(self.controller.secilen_gorseller)}_soru.pdf"
                    )

                    if cikti_dosya:
                        self.logger.info(f"PDF kaydediliyor: {cikti_dosya}")
                        
                        # STATE'İ GÖNDER
                        if pdf.kaydet(cikti_dosya, self.controller.sayfa_haritasi):
                            kayit_yeri = f"{os.path.basename(os.path.dirname(cikti_dosya))}/{os.path.basename(cikti_dosya)}"
                            self.logger.info(f"PDF başarıyla oluşturuldu: {os.path.basename(cikti_dosya)}")
                            
                            # KALICI HAVUZA COMMIT — sadece PDF'e basılan sorular
                            if not hasattr(self.controller, 'kalici_kullanilan'):
                                self.controller.kalici_kullanilan = {}
                            for gorsel_path in self.controller.secilen_gorseller:
                                konu = self.find_topic_from_path(gorsel_path)
                                if konu:
                                    dosya_adi = os.path.basename(gorsel_path)
                                    if konu not in self.controller.kalici_kullanilan:
                                        self.controller.kalici_kullanilan[konu] = set()
                                    self.controller.kalici_kullanilan[konu].add(dosya_adi)
                            self.logger.info(
                                f"Kalıcı havuz güncellendi: "
                                f"{sum(len(v) for v in self.controller.kalici_kullanilan.values())} "
                                f"soru toplam olarak işaretlendi."
                            )
                            
                            # Gerçek konu dağılımını secilen_gorseller'den hesapla
                            gercek_dagilim = {}
                            for gorsel_path in self.controller.secilen_gorseller:
                                konu = self.find_topic_from_path(gorsel_path)
                                if konu:
                                    gercek_dagilim[konu] = gercek_dagilim.get(konu, 0) + 1
                            toplam_soru = len(self.controller.secilen_gorseller)
                            mesaj = (
                                f"Kayıt Yeri: {kayit_yeri}\n\n"
                                f"{toplam_soru} soru PDF formatında kaydedildi\n\n"
                                "Konu Dağılımı:\n" +
                                "\n".join([f"• {konu}: {sayi} soru" for konu, sayi in gercek_dagilim.items()])
                            )
                            if self.controller.soru_tipi_var.get().lower() == "test" and toplam_soru > 60:
                                mesaj += (
                                    f"\n\n⚠️ Optik cevap anahtarı şablonu 60 soru kapasitesine sahiptir.\n"
                                    f"61. sorudan itibaren ({toplam_soru - 60} soru) cevap anahtarında yer almayacak."
                                )
                            self.dialog_yoneticisi.show_notification(
                                "PDF Başarıyla Oluşturuldu!",
                                mesaj
                            )
                        else:
                            self.logger.error("PDF kaydedilemedi")
                            self.dialog_yoneticisi.show_notification("PDF Oluşturulamadı", "PDF oluşturulurken bir hata oluştu.")
                    else:
                        self.logger.info("Kullanıcı PDF kaydetmeyi iptal etti")
                except Exception as e:
                    self.logger.error(f"PDF kaydetme (_proceed_to_save) hatası: {e}", exc_info=True)
                    self.dialog_yoneticisi.show_error(f"PDF kaydedilirken hata oluştu: {e}")
            
            # 4. ONAY AŞAMASI (KARAR)
            bilinmeyen = 0
            if cevap_anahtari_isteniyor and cevaplar:
                bilinmeyen = sum(1 for c in cevaplar if str(c).strip() == "?")
            
            if bilinmeyen > 0:
                info = f"{len(cevaplar)} sorudan {bilinmeyen} tanesi için cevap bulunamadı (%{int(100 * bilinmeyen / len(cevaplar))})."
                self.logger.warning(info + " Kullanıcı onayı bekleniyor.")
                self.dialog_yoneticisi._show_cevap_onay_dialog(message=info, on_confirm_callback=_proceed_to_save)
            else:
                self.logger.info("Cevaplarda sorun yok, kaydetme başlatılıyor.")
                _proceed_to_save()

        except Exception as e:
            self.logger.error(f"PDF oluşturma genel hatası: {e}", exc_info=True)
            self.dialog_yoneticisi.show_notification(
                "Hata",
                f"Beklenmeyen bir hata oluştu:\n{str(e)}\nLütfen konsolu kontrol edin."
            )
                         
    def basit_pdf_olustur(self):
        """Basit PDF oluşturma - PDFCreator sınıfı import edilemediğinde."""
        self.logger.warning("Basit PDF oluşturma moduna geçildi")
        
        if not FALLBACK_PDF_MEVCUT:
             self.logger.error("Fallback PDF için 'reportlab' modülü bulunamadı")
             self.dialog_yoneticisi.show_error("PDF oluşturulamadı. 'reportlab' modülü eksik.")
             return
             
        try:
            # STATE'İ OKU
            secilen_gorseller = self.controller.secilen_gorseller
            
            cikti_dosya = filedialog.asksaveasfilename(
                title="PDF'i Nereye Kaydetmek İstersiniz?",
                defaultextension=".pdf",
                filetypes=[("PDF Dosyası", "*.pdf")],
                initialfile=f"{self.controller.ders_adi}_{self.controller.soru_tipi_var.get()}_{self.controller.zorluk_var.get()}_{len(secilen_gorseller)}_soru.pdf"
            )

            if not cikti_dosya:
                self.logger.info("Basit PDF kaydetme iptal edildi")
                return

            story = []
            styles = getSampleStyleSheet()

            # STATE'İ OKU
            konu_dagilimi = self.controller.konu_soru_dagilimi
            konu_listesi = ", ".join(list(konu_dagilimi.keys())[:2])
            if len(konu_dagilimi) > 2:
                konu_listesi += f" ve diğerleri"
            
            baslik_text = f"{self.controller.ders_adi} - {konu_listesi} - {self.controller.soru_tipi_var.get()} - {self.controller.zorluk_var.get()}"
            baslik = Paragraph(baslik_text, styles["Title"])
            story.append(baslik)
            story.append(Spacer(1, 0.5*inch))

            for gorsel_yolu in secilen_gorseller:
                try:
                    img = Image(gorsel_yolu, width=6*inch, height=4*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.3*inch))
                except Exception as e:
                    self.logger.error(f"Basit PDF görsel ekleme hatası: {e}")

            doc = SimpleDocTemplate(cikti_dosya, pagesize=letter)
            doc.build(story)
            self.logger.info(f"Basit PDF başarıyla oluşturuldu: {os.path.basename(cikti_dosya)}")

            self.dialog_yoneticisi.show_notification(
                "PDF Başarıyla Oluşturuldu!",
                f"Kayıt Yeri: {os.path.basename(cikti_dosya)}\n\n{len(secilen_gorseller)} soru PDF formatında kaydedildi"
            )

        except Exception as e:
            self.logger.error(f"Basit PDF oluşturma hatası: {e}")
            self.dialog_yoneticisi.show_notification(
                "Hata",
                f"PDF oluşturulurken hata: {str(e)}"
            )