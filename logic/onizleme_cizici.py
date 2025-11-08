# logic/onizleme_cizici.py

import os
import logging
from PIL import Image, ImageDraw, ImageFont, ImageTk

"""
Soru Otomasyon Sistemi - Önizleme Çizim Yardımcısı

Bu modül, SoruParametresiSecmePenceresi için PDF önizleme
görsellerini oluşturan tüm 'PIL' (Pillow) çizim mantığını
merkezileştirir.

Bu sınıf UI (Arayüz) bilmez, sadece kendisine verilen verilere
dayanarak bir 'ImageTk.PhotoImage' nesnesi üretir.

Ana Sınıf:
- OnizlemeCizici: 
  Gerekli verileri ('soru_tipi', 'baslik_text' vb.) alır
  ve 'generate_preview_image' metodu aracılığıyla
  hazır bir önizleme resmi döndürür.
"""

class OnizlemeCizici:
    """
    Tüm PDF önizleme çizim (PIL) işlemlerini yönetir.
    
    Metodlar:
    - __init__(self, soru_tipi, baslik_text, logger, constants):
        Çizim için gerekli olan tüm verileri ve ayarları alır.
        
    - generate_preview_image(self, bu_sayfanin_sutunlari, ...):
        Ana giriş noktası. Şablonu yükler, başlığı çizer ve
        doğru layout fonksiyonunu (_create_test_preview...) çağırır.
        
    - _draw_title_on_image(self, image):
        Başlığı PIL kullanarak resmin üzerine çizer.
        
    - _create_yazili_preview(self, template_copy, ...):
        Yazılı sınav layout'unu çizer.
        
    - _create_test_preview_BestFit(self, template_copy, ...):
        Test sınavı layout'unu (BestFit) çizer.
    """
    
    def __init__(self, soru_tipi, baslik_text, logger, constants_dict):
        """
        Çiziciyi başlatır.
        
        Args:
            soru_tipi (str): "Test" veya "Yazili".
            baslik_text (str): Kullanıcının girdiği başlık metni.
            logger (logging.Logger): Ana controller'dan gelen logger.
            constants_dict (dict): Ana controller'dan gelen sabitler
                                   (örn: 'BASLIK_PT_MAX').
        """
        self.soru_tipi = soru_tipi
        self.baslik_text = baslik_text
        self.logger = logger
        self.constants = constants_dict
        
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        font_dir = os.path.join(self.base_dir, "resources", "fonts")
        
        # Ana Fontlar (Arial)
        self.font_path_regular = os.path.join(font_dir, "arial.ttf")
        self.font_path_bold = os.path.join(font_dir, "arialbd.ttf")
        
        # Yedek Fontlar (Calibri)
        self.font_path_regular_fallback = os.path.join(font_dir, "calibri.ttf")
        self.font_path_bold_fallback = os.path.join(font_dir, "calibrib.ttf")

        # Kontrol (Eğer arial.ttf bulunamazsa Calibri'yi kullan)
        if not os.path.exists(self.font_path_regular):
            self.logger.warning(f"Arial font not found at {self.font_path_regular}. Using Calibri fallback.")
            self.font_path_regular = self.font_path_regular_fallback
            
        if not os.path.exists(self.font_path_bold):
            self.logger.warning(f"Arial Bold font not found at {self.font_path_bold}. Using Calibri Bold fallback.")
            self.font_path_bold = self.font_path_bold_fallback
        


    def generate_preview_image(self, bu_sayfanin_sutunlari, global_offset, page_index):
        """
        Bir sayfa için PDF önizlemesi oluşturur.
        Bu, 'create_page_preview' fonksiyonunun yeni yeridir.
        """
        self.logger.debug(f"Sayfa önizlemesi oluşturuluyor - Sayfa İndeksi: {page_index}, Offset: {global_offset}")

        try:
            # Soru tipine göre şablon seç
            templates_dir = os.path.join(self.base_dir, "templates")
            soru_tipi = self.soru_tipi.lower()
            sayfa_no = page_index + 1 # 1'den başlayan sayfa no
            
            self.logger.debug(f"Şablon seçimi - Soru tipi: {soru_tipi}, Sayfa No: {sayfa_no}")

            if sayfa_no == 1:
                template_name = "template2.png" if soru_tipi == "yazili" else "template.png"
                template_name_fallback = template_name
            else:
                template_name = "template4.png" if soru_tipi == "yazili" else "template3.png"
                template_name_fallback = "template2.png" if soru_tipi == "yazili" else "template.png"
            
            template_path = os.path.join(templates_dir, template_name)
            
            if not os.path.exists(template_path):
                self.logger.warning(f"Onizleme: Dinamik şablon '{template_name}' bulunamadı. Fallback '{template_name_fallback}' kullanılıyor.")
                template_path = os.path.join(templates_dir, template_name_fallback)
                
                if not os.path.exists(template_path):
                     self.logger.error(f"Fallback şablon '{template_name_fallback}' dahi bulunamadı!")
                     return None

            template = Image.open(template_path).convert("RGB")
            template_copy = template.copy()
            
            if page_index == 0:
                self._draw_title_on_image(template_copy)
            
            self.logger.debug(f"Şablon yüklendi - Boyut: {template_copy.size}")

            template_width, template_height = template_copy.size
            
            if soru_tipi == "yazili":
                sayfa_gorselleri_bilgileri_duz = []
                for sutun in bu_sayfanin_sutunlari:
                    sayfa_gorselleri_bilgileri_duz.extend(sutun)
                self._create_yazili_preview(template_copy, sayfa_gorselleri_bilgileri_duz, template_width, template_height, global_offset, page_index)
            else:
                self._create_test_preview_BestFit(template_copy, bu_sayfanin_sutunlari, template_width, template_height, global_offset, page_index)

            # Önizleme için boyutlandır (oranı koru)
            preview_width = 600
            preview_height = int(2000 * preview_width / 1414) # A4 Oranı
            
            resampling_filter = Image.Resampling.LANCZOS if hasattr(Image.Resampling, "LANCZOS") else Image.ANTIALIAS
            template_copy = template_copy.resize((preview_width, preview_height), resampling_filter)

            self.logger.debug("Sayfa önizlemesi başarıyla oluşturuldu")
            return ImageTk.PhotoImage(template_copy)

        except Exception as e:
            self.logger.error(f"Sayfa önizleme hatası: {e}", exc_info=True)
            return None

    def _draw_title_on_image(self, image):
        """Şablon imajının üst-ortasına başlığı çizer (tek font, tek marjin)."""
        if image is None:
            return
        
        # DİKKAT: 'self.baslik_text_var.get()' yerine 'self.baslik_text'
        text_raw = (self.baslik_text or "").strip()
        text = text_raw.replace('i', 'İ').upper() or "QUIZ"
        TOP_MARGIN = 50
        W, H = image.size
        
        # DİKKAT: Sabitleri 'self.constants' dict'inden al
        max_w = int(W * self.constants['TITLE_MAX_W_RATIO'])

        draw = ImageDraw.Draw(image)

        def try_font(pt):
            try:
                # Ana fontu (Arial) yükle
                return ImageFont.truetype(self.font_path_regular, pt)
            except Exception:
                try:
                    # Başarısız olursa yedek fontu (Calibri) yükle
                    return ImageFont.truetype(self.font_path_regular_fallback, pt)
                except Exception:
                    self.logger.error("Hem Arial hem de Calibri fontları yüklenemedi. Varsayılan font kullanılıyor.")
                    return ImageFont.load_default()
                

        # DİKKAT: Sabitleri 'self.constants' dict'inden al
        pt = self.constants['BASLIK_PT_MAX']
        font = try_font(pt)
        w = draw.textbbox((0, 0), text, font=font)[2]
        
        # DİKKAT: Sabitleri 'self.constants' dict'inden al
        while pt > self.constants['BASLIK_PT_MIN'] and w > max_w:
            pt -= 1
            font = try_font(pt)
            w = draw.textbbox((0, 0), text, font=font)[2]

        if w > max_w and len(text) > 5:
            t = text
            while len(t) > 5:
                t = t[:-2] + "…"
                w = draw.textbbox((0, 0), t, font=font)[2]
                if w <= max_w:
                    text = t
                    break

        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (W - tw) // 2
        y = TOP_MARGIN

        draw.text((x + 1, y + 1), text, font=font, fill=(0, 0, 0))
        draw.text((x, y), text, font=font, fill="darkred")

    def _create_yazili_preview(self, template_copy, sayfa_gorselleri_bilgileri_duz, template_width, template_height, global_offset, page_index):
        """Yazılı şablonu önizleme layout'u (Hiçbir değişiklik gerekmedi)"""
        self.logger.debug("Yazılı önizleme layout'u uygulanıyor")
        
        A4_H = 841.89
        scale_factor = template_height / A4_H
        
        if page_index == 0:
            top_margin_pixel = 50 * scale_factor
        else:
            top_margin_pixel = 35 * scale_factor
        
        left_margin = int(template_width * 0.05)
        right_margin = int(template_width * 0.05)
        bottom_margin = int(template_height * 0.05)
        
        usable_width = template_width - left_margin - right_margin
        usable_height = template_height - top_margin_pixel - bottom_margin
        
        max_soru = 2
        soru_ve_cevap_yuksekligi = usable_height // max_soru 
        yazili_soru_height = int(soru_ve_cevap_yuksekligi * 0.7) 
        yazili_soru_width = usable_width

        self.logger.debug(f"Yazılı layout boyutları - Genişlik: {yazili_soru_width}, Yükseklik: {yazili_soru_height}")

        for i, soru_info in enumerate(sayfa_gorselleri_bilgileri_duz):
            if i >= max_soru:
                self.logger.warning(f"Yazılı önizlemede maksimum {max_soru} soru gösterilebilir.")
                break
                
            try:
                gorsel_path = soru_info['path']
                soru_no = global_offset + i + 1
                
                x_sol_kenar = left_margin 
                y_tavan = top_margin_pixel + i * soru_ve_cevap_yuksekligi

                soru_img = Image.open(gorsel_path)
                
                img_ratio = soru_img.width / soru_img.height
                final_width = yazili_soru_width
                final_height = int(final_width / img_ratio)

                if final_height > yazili_soru_height:
                    final_height = yazili_soru_height
                    final_width = int(final_height * img_ratio)
                
                paste_x = x_sol_kenar + (yazili_soru_width - final_width) // 2
                
                resampling_filter = Image.Resampling.LANCZOS if hasattr(Image.Resampling, "LANCZOS") else Image.ANTIALIAS
                soru_img = soru_img.resize((final_width, final_height), resampling_filter)
                template_copy.paste(soru_img, (int(paste_x), int(y_tavan)))

                draw = ImageDraw.Draw(template_copy)
                
                try:
                    # Ana BOLD fontu (Arial Bold) yükle
                    font = ImageFont.truetype(self.font_path_bold, 24) 
                except Exception:
                    try:
                        # Yedek BOLD fontu (Calibri Bold) yükle
                        font = ImageFont.truetype(self.font_path_bold_fallback, 24)
                    except:
                        font = ImageFont.load_default()
                
                numara_x = x_sol_kenar
                if soru_no >= 10:
                    numara_x -= (10 * scale_factor) 
                
                draw.text((numara_x - 20, y_tavan), f"{soru_no}.", fill="#000000", font=font)
                
                self.logger.debug(f"Yazılı soru {soru_no} yerleştirildi - Boyut: {final_width}x{final_height}")

            except Exception as e:
                self.logger.error(f"Yazılı soru {i+1} yerleştirme hatası: {e}", exc_info=True)
                            
    def _create_test_preview_BestFit(self, template_copy, bu_sayfanin_sutunlari, template_width, template_height, global_offset, page_index):
        """Test şablonu önizleme layout'u (Hiçbir değişiklik gerekmedi)"""
        self.logger.debug(f"Test önizleme (BestFit NİZAMİ) layout'u uygulanıyor - {sum(len(s) for s in bu_sayfanin_sutunlari)} soru")

        A4_W, A4_H = 595.27, 841.89
        template_W, template_H = template_width, template_height
        
        scale_factor = template_H / A4_H 
        
        if page_index == 0:
            top_margin = 50 * scale_factor
        else:
            top_margin = 35 * scale_factor

        bottom_margin = 5 * scale_factor
        left_margin = 20 * scale_factor
        right_margin = 20 * scale_factor
        col_gap = 40 * scale_factor
        cols = 2
        
        soru_numara_font_size = int(12 * scale_factor)
        
        soru_spacing = 8 * scale_factor
        image_spacing = 10 * scale_factor

        col_width = (template_W - left_margin - right_margin - col_gap) / cols
        
        current_x_positions = [left_margin + i * (col_width + col_gap) for i in range(cols)]
        
        current_y_positions_tepe = [top_margin for _ in range(cols)] 

        yerlestirildi_sayaci = 0 
        
        draw = ImageDraw.Draw(template_copy)
        try:
            # Ana BOLD fontu (Arial Bold) yükle
            numara_font = ImageFont.truetype(self.font_path_bold, soru_numara_font_size)
        except Exception:
            try:
                # Yedek BOLD fontu (Calibri Bold) yükle
                numara_font = ImageFont.truetype(self.font_path_bold_fallback, soru_numara_font_size)
            except:
                numara_font = ImageFont.load_default()

        for sutun_index in range(cols):
            sutun_sorulari = bu_sayfanin_sutunlari[sutun_index]
            img_x = current_x_positions[sutun_index]
            
            for soru_info in sutun_sorulari:
                
                scaled_width = soru_info['final_size'][0] * scale_factor
                scaled_height = soru_info['final_size'][1] * scale_factor
                
                pil_y_top = current_y_positions_tepe[sutun_index] + soru_spacing
                
                try:
                    soru_img = Image.open(soru_info['path'])
                    resampling_filter = Image.Resampling.LANCZOS if hasattr(Image.Resampling, "LANCZOS") else Image.ANTIALIAS
                    soru_img = soru_img.resize((int(scaled_width), int(scaled_height)), resampling_filter)
                    
                    template_copy.paste(soru_img, (int(img_x), int(pil_y_top)))
                    
                    soru_no = global_offset + yerlestirildi_sayaci + 1
                    
                    numara_x = img_x - (15 * scale_factor)
                    numara_y = pil_y_top 
                    if soru_no >= 10:
                        numara_x -= (5 * scale_factor) 
                        
                    draw.text((numara_x + 10, numara_y), f"{soru_no}.", fill="#333333", font=numara_font)

                except Exception as e:
                    self.logger.error(f"PIL Gorsel cizim hatasi: {soru_info['path']}", exc_info=True)
                    continue

                current_y_positions_tepe[sutun_index] = pil_y_top + scaled_height + image_spacing
                yerlestirildi_sayaci += 1
                
        self.logger.info(f"Test önizleme (BestFit NİZAMİ) tamamlandi - {yerlestirildi_sayaci} soru yerlestirildi")