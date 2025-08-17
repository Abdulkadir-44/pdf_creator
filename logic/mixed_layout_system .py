from PIL import Image as PILImage
import os
import math

class MixedLayoutManager:
    def __init__(self, logger=None):
        self.logger = logger
        
        # 📏 Görsel kategorilendirme kriterleri
        self.UZUN_ASPECT_RATIO_MIN = 1.5   # Boy/en oranı 1.5'ten büyükse UZUN
        self.KISA_ASPECT_RATIO_MAX = 0.7   # Boy/en oranı 0.7'den küçükse KISA
        
        # ⚖️ Ağırlık sistemi (kapasite birimi olarak)
        self.KISA_SORU_AGIRLIK = 1
        self.UZUN_SORU_AGIRLIK = 2
        self.ORTA_SORU_AGIRLIK = 1.5
        self.MAKSIMUM_SAYFA_KAPASITESI = 8
        
        # 📐 Sayfa layout parametreleri
        self.page_width = 595  # A4 genişlik
        self.page_height = 842  # A4 yükseklik
        self.margin = 50
        self.usable_width = self.page_width - 2 * self.margin
        self.usable_height = self.page_height - 2 * self.margin
        
    def log(self, message):
        """Logger wrapper"""
        if self.logger:
            self.logger.info(message)
        else:
            print(message)
    
    def gorsel_kategori_belirle(self, gorsel_yolu):
        """Görseli analiz edip kategorisini belirle"""
        try:
            with PILImage.open(gorsel_yolu) as img:
                width = img.width
                height = img.height
                aspect_ratio = height / width  # Boy/En oranı
                
                # 📊 Kategori belirleme
                if aspect_ratio >= self.UZUN_ASPECT_RATIO_MIN:
                    kategori = "UZUN"
                    agirlik = self.UZUN_SORU_AGIRLIK
                    oncelik = 2  # Uzun sorular öncelik alır (yerleştirmesi zor)
                elif aspect_ratio <= self.KISA_ASPECT_RATIO_MAX:
                    kategori = "KISA"
                    agirlik = self.KISA_SORU_AGIRLIK
                    oncelik = 1
                else:
                    kategori = "ORTA"
                    agirlik = self.ORTA_SORU_AGIRLIK
                    oncelik = 1.5
                
                return {
                    'path': gorsel_yolu,
                    'width': width,
                    'height': height,
                    'aspect_ratio': aspect_ratio,
                    'kategori': kategori,
                    'agirlik': agirlik,
                    'oncelik': oncelik,
                    'filename': os.path.basename(gorsel_yolu)
                }
                
        except Exception as e:
            self.log(f"❌ Görsel analiz hatası {os.path.basename(gorsel_yolu)}: {e}")
            # Varsayılan değerler
            return {
                'path': gorsel_yolu,
                'width': 500,
                'height': 400,
                'aspect_ratio': 0.8,
                'kategori': "KISA",
                'agirlik': self.KISA_SORU_AGIRLIK,
                'oncelik': 1,
                'filename': os.path.basename(gorsel_yolu)
            }
    
    def toplu_analiz(self, gorsel_listesi):
        """Tüm görselleri analiz et ve istatistik çıkar"""
        self.log("🔍 Görsel analizi başlatılıyor...")
        
        analiz_sonuclari = []
        kategoriler = {'KISA': 0, 'ORTA': 0, 'UZUN': 0}
        
        for gorsel_yolu in gorsel_listesi:
            analiz = self.gorsel_kategori_belirle(gorsel_yolu)
            analiz_sonuclari.append(analiz)
            kategoriler[analiz['kategori']] += 1
        
        # 📊 Genel istatistikler
        toplam_agirlik = sum(g['agirlik'] for g in analiz_sonuclari)
        tahmini_sayfa = math.ceil(toplam_agirlik / self.MAKSIMUM_SAYFA_KAPASITESI)
        
        self.log(f"📊 ANALİZ RAPORU:")
        self.log(f"   📏 Kısa: {kategoriler['KISA']}, Orta: {kategoriler['ORTA']}, Uzun: {kategoriler['UZUN']}")
        self.log(f"   ⚖️ Toplam ağırlık: {toplam_agirlik}")
        self.log(f"   📄 Tahmini sayfa sayısı: {tahmini_sayfa}")
        
        return analiz_sonuclari
    
    def sayfa_icin_gorsel_sec(self, kalan_gorseller):
        """Bir sayfa için optimal görselleri seç - MIXED LAYOUT"""
        if not kalan_gorseller:
            return [], []
        
        secilen_gorseller = []
        kalan_kapasite = self.MAKSIMUM_SAYFA_KAPASITESI
        
        # 🎯 STRATEJİ: Önce uzun görselleri yerleştir (daha zor), sonra kısaları
        sirali_gorseller = sorted(kalan_gorseller, key=lambda x: x['oncelik'], reverse=True)
        
        self.log(f"🎯 Sayfa planlaması - Kalan görsel: {len(kalan_gorseller)}")
        
        for gorsel in sirali_gorseller:
            if gorsel['agirlik'] <= kalan_kapasite:
                secilen_gorseller.append(gorsel)
                kalan_kapasite -= gorsel['agirlik']
                
                self.log(f"   ✅ Seçildi: {gorsel['filename'][:25]} ({gorsel['kategori']}, Ağırlık: {gorsel['agirlik']})")
                
                # Kapasite doldu mu kontrolü
                if kalan_kapasite <= 0:
                    break
            else:
                self.log(f"   ❌ Sığmadı: {gorsel['filename'][:25]} (Gerekli: {gorsel['agirlik']}, Kalan: {kalan_kapasite})")
        
        # Seçilen görselleri kalan listesinden çıkar
        secilen_paths = [g['path'] for g in secilen_gorseller]
        yeni_kalan = [g for g in kalan_gorseller if g['path'] not in secilen_paths]
        
        # 📋 Sayfa özeti
        kullanilan_kapasite = self.MAKSIMUM_SAYFA_KAPASITESI - kalan_kapasite
        doluluk_orani = (kullanilan_kapasite / self.MAKSIMUM_SAYFA_KAPASITESI) * 100
        
        kategoriler = {}
        for kategori in ['KISA', 'ORTA', 'UZUN']:
            sayi = len([g for g in secilen_gorseller if g['kategori'] == kategori])
            if sayi > 0:
                kategoriler[kategori] = sayi
        
        self.log(f"📦 SAYFA ÖZETİ:")
        self.log(f"   🎯 Seçilen görseller: {len(secilen_gorseller)}")
        self.log(f"   ⚖️ Kullanılan kapasite: {kullanilan_kapasite}/{self.MAKSIMUM_SAYFA_KAPASITESI} (%{doluluk_orani:.1f})")
        self.log(f"   📊 Kategori dağılımı: {kategoriler}")
        self.log(f"   📄 Kalan görseller: {len(yeni_kalan)}")
        
        return secilen_gorseller, yeni_kalan
    
    def mixed_layout_hesapla(self, secilen_gorseller, page_width, page_height):
        """Mixed layout için pozisyonları hesapla"""
        if not secilen_gorseller:
            return []
        
        self.log(f"📐 Mixed layout hesaplanıyor...")
        
        # Basit grid sistemi - dinamik satır/sütun
        kisa_orta_sayisi = len([g for g in secilen_gorseller if g['kategori'] in ['KISA', 'ORTA']])
        uzun_sayisi = len([g for g in secilen_gorseller if g['kategori'] == 'UZUN'])
        
        layout_bilgileri = []
        
        # 📏 Layout stratejisi
        if uzun_sayisi == 0:
            # Sadece kısa/orta görseller - klasik 2x4 grid
            layout_bilgileri = self._klasik_grid_layout(secilen_gorseller, page_width, page_height)
        elif kisa_orta_sayisi == 0:
            # Sadece uzun görseller - tek sütun
            layout_bilgileri = self._tek_sutun_layout(secilen_gorseller, page_width, page_height)
        else:
            # Karışık layout - hybrid sistem
            layout_bilgileri = self._hybrid_layout(secilen_gorseller, page_width, page_height)
        
        return layout_bilgileri
    
    def _klasik_grid_layout(self, gorseller, page_width, page_height):
        """2x4 klasik grid layout"""
        self.log("   📐 Klasik grid layout kullanılıyor")
        
        cols = 2
        rows = 4
        margin = 50
        gap = 30
        
        usable_width = page_width - 2 * margin
        usable_height = page_height - 2 * margin
        
        box_width = (usable_width - gap) / cols
        box_height = (usable_height - (rows-1) * 20) / rows
        
        layout_bilgileri = []
        
        for i, gorsel in enumerate(gorseller[:8]):
            row = i % rows
            col = i // rows
            
            x = margin + col * (box_width + gap)
            y = page_height - margin - (row + 1) * box_height - row * 20
            
            layout_bilgileri.append({
                'gorsel': gorsel,
                'x': x,
                'y': y,
                'max_width': box_width * 0.95,
                'max_height': box_height * 0.85,
                'layout_type': 'grid'
            })
        
        return layout_bilgileri
    
    def _tek_sutun_layout(self, gorseller, page_width, page_height):
        """Tek sütun layout (uzun görseller için)"""
        self.log("   📐 Tek sütun layout kullanılıyor")
        
        margin = 50
        usable_width = page_width - 2 * margin
        usable_height = page_height - 2 * margin
        
        # Her görsel için eşit yükseklik
        gorsel_sayisi = len(gorseller)
        box_height = usable_height / gorsel_sayisi
        
        layout_bilgileri = []
        
        for i, gorsel in enumerate(gorseller):
            x = margin
            y = page_height - margin - (i + 1) * box_height
            
            layout_bilgileri.append({
                'gorsel': gorsel,
                'x': x,
                'y': y,
                'max_width': usable_width * 0.9,
                'max_height': box_height * 0.9,
                'layout_type': 'single_column'
            })
        
        return layout_bilgileri
    
    def _hybrid_layout(self, gorseller, page_width, page_height):
        """Hibrit layout (kısa + uzun karışık)"""
        self.log("   📐 Hibrit layout kullanılıyor")
        
        # Uzun görselleri üstte, kısa görselleri altta yerleştir
        uzun_gorseller = [g for g in gorseller if g['kategori'] == 'UZUN']
        kisa_orta_gorseller = [g for g in gorseller if g['kategori'] in ['KISA', 'ORTA']]
        
        margin = 50
        usable_width = page_width - 2 * margin
        usable_height = page_height - 2 * margin
        
        # Alan dağılımı: %60 uzun görseller, %40 kısa görseller
        uzun_alan_yuksekligi = usable_height * 0.6
        kisa_alan_yuksekligi = usable_height * 0.4
        
        layout_bilgileri = []
        
        # Uzun görseller (üst kısım)
        if uzun_gorseller:
            uzun_box_height = uzun_alan_yuksekligi / len(uzun_gorseller)
            
            for i, gorsel in enumerate(uzun_gorseller):
                x = margin
                y = page_height - margin - (i + 1) * uzun_box_height
                
                layout_bilgileri.append({
                    'gorsel': gorsel,
                    'x': x,
                    'y': y,
                    'max_width': usable_width * 0.9,
                    'max_height': uzun_box_height * 0.9,
                    'layout_type': 'hybrid_uzun'
                })
        
        # Kısa/orta görseller (alt kısım) - 2 sütun grid
        if kisa_orta_gorseller:
            cols = 2
            kisa_rows = math.ceil(len(kisa_orta_gorseller) / cols)
            
            if kisa_rows > 0:
                kisa_box_width = (usable_width - 30) / cols
                kisa_box_height = kisa_alan_yuksekligi / kisa_rows
                
                for i, gorsel in enumerate(kisa_orta_gorseller):
                    row = i // cols
                    col = i % cols
                    
                    x = margin + col * (kisa_box_width + 30)
                    y = margin + (kisa_rows - row - 1) * kisa_box_height
                    
                    layout_bilgileri.append({
                        'gorsel': gorsel,
                        'x': x,
                        'y': y,
                        'max_width': kisa_box_width * 0.95,
                        'max_height': kisa_box_height * 0.85,
                        'layout_type': 'hybrid_kisa'
                    })
        
        return layout_bilgileri

# Ana entegrasyon fonksiyonu
def create_smart_mixed_layout(canvas_obj, gorseller, sayfa_no, page_width, page_height, logger=None):
    """Ana mixed layout fonksiyonu - PDF Creator'a entegre edilecek"""
    
    layout_manager = MixedLayoutManager(logger)
    
    # 1. Görselleri analiz et
    analiz_sonuclari = []
    for gorsel_path in gorseller:
        analiz = layout_manager.gorsel_kategori_belirle(gorsel_path)
        analiz_sonuclari.append(analiz)
    
    # 2. Layout hesapla
    layout_bilgileri = layout_manager.mixed_layout_hesapla(analiz_sonuclari, page_width, page_height)
    
    # 3. Görselleri yerleştir
    yerlestirildi_sayisi = 0
    
    for layout_info in layout_bilgileri:
        try:
            gorsel = layout_info['gorsel']
            
            # Görsel boyutlandırma
            with PILImage.open(gorsel['path']) as img:
                original_width = img.width
                original_height = img.height
                img_ratio = original_width / original_height
                
                max_width = layout_info['max_width']
                max_height = layout_info['max_height']
                
                # Orantılı boyutlandırma - BÜYÜTME İZNİ VAR
                if img_ratio > (max_width / max_height):
                    final_width = max_width
                    final_height = max_width / img_ratio
                else:
                    final_height = max_height
                    final_width = max_height * img_ratio
                
                # Görseli çiz
                img_x = layout_info['x'] + (layout_info['max_width'] - final_width) / 2
                img_y = layout_info['y']
                
                canvas_obj.drawImage(gorsel['path'], img_x, img_y, width=final_width, height=final_height)
                
                # Soru numarası
                soru_no = (sayfa_no - 1) * 8 + yerlestirildi_sayisi + 1
                canvas_obj.setFont("Helvetica-Bold", 12)
                canvas_obj.setFillColor("#666666")
                canvas_obj.drawString(layout_info['x'] - 5, layout_info['y'] + layout_info['max_height'] - 15, f"{soru_no}.")
                
                yerlestirildi_sayisi += 1
                
                if logger:
                    logger.info(f"✅ {gorsel['kategori']} görsel yerleştirildi: {gorsel['filename']}")
                
        except Exception as e:
            if logger:
                logger.error(f"❌ Görsel yerleştirme hatası: {e}")
    
    return yerlestirildi_sayisi