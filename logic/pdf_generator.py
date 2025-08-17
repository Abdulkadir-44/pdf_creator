from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image as PILImage
import os
import json
import math
import logging
from datetime import datetime

class PDFCreator:
    def __init__(self):
        self.gorsel_listesi = []
        self.baslik_metni = ""
        self.cevap_listesi = []
        self.soru_tipi = "test"
        
        # Logger oluştur
        self.logger = self._setup_logger()
    
    def _setup_logger(self):
        """Logger kurulumu"""
        logger = logging.getLogger('PDFCreator')
        logger.setLevel(logging.INFO)
        
        # Eğer handler yoksa ekle (tekrar eklenmesini önler)
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # Formatter - dosya ve satır bilgisi ile
            formatter = logging.Formatter(
                '%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        return logger

    def baslik_ekle(self, baslik):
        """PDF başlığını ayarla"""
        self.baslik_metni = baslik
        self.logger.info(f"PDF başlığı ayarlandı: {baslik}")
    
    def gorsel_ekle(self, gorsel_yolu, cevap=None):
        """Görsel listesine ekle"""
        self.gorsel_listesi.append(gorsel_yolu)
        if cevap:
            self.cevap_listesi.append(cevap)
        self.logger.debug(f"Görsel eklendi: {os.path.basename(gorsel_yolu)} (Cevap: {cevap or 'Yok'})")
    
    def cevap_anahtari_ekle(self, cevaplar):
        """Cevap listesini ayarla"""
        self.cevap_listesi = cevaplar
        self.logger.info(f"Cevap anahtarı eklendi ({len(cevaplar)} cevap)")
    
    def _create_yazili_layout(self, canvas_obj, gorseller, sayfa_no, page_width, page_height):
        """Yazılı şablonu layout'u - Dinamik iyileştirilmiş versiyon"""
        self.logger.debug("Dinamik yazılı layout uygulanıyor")

        # DEBUG: Gelen görselleri logla
        self.logger.info(f"YAZILI DEBUG - Sayfa {sayfa_no}")
        self.logger.info(f"Gelen görsel sayısı: {len(gorseller)}")
        for idx, gorsel in enumerate(gorseller):
            self.logger.info(f"  {idx}: {os.path.basename(gorsel)}")

        # Şablon uyumlu margin hesaplaması
        top_margin = page_height * 0.12      # %12 - şablon başlığı için alan bırak
        left_margin = page_width * 0.05      # %5 sol margin
        right_margin = page_width * 0.05     # %5 sağ margin  
        bottom_margin = page_height * 0.08   # %8 alt margin

        usable_width = page_width - left_margin - right_margin
        usable_height = page_height - top_margin - bottom_margin

        # Maksimum 2 soru için alan hesapla
        max_questions = min(len(gorseller), 2)

        # ÖNCE GÖRSELLERİN BOYUTLARINI ANALİZ ET - DOĞAL BOYUT KORUMA
        gorsel_info = []
        cevap_area_height = 40  # Sabit cevap alanı
        
        for i, gorsel_path in enumerate(gorseller[:max_questions]):
            try:
                with PILImage.open(gorsel_path) as img:
                    img_ratio = img.width / img.height
                    original_width = img.width
                    original_height = img.height
                    
                    # Sayfa genişliğine göre maksimum genişlik
                    max_width = usable_width * 0.95
                    max_height = usable_height * 0.45  # Maksimum %45 sayfa
                    
                    # DOĞAL BOYUT KORUMA YAKLAŞIMI
                    # Eğer orijinal görsel sayfa genişliğinden küçükse, orijinalinde bırak
                    if original_width <= max_width and original_height <= max_height:
                        # Küçük görsel - orijinal boyutunda bırak
                        final_width = original_width
                        final_height = original_height
                        self.logger.debug(f"Görsel {i+1} - Küçük, orijinal boyutunda: {final_width}x{final_height}")
                    else:
                        # Büyük görsel - sığacak şekilde küçült
                        if original_width > max_width:
                            # Genişlik sınırına göre küçült
                            scale_factor = max_width / original_width
                            final_width = max_width
                            final_height = original_height * scale_factor
                        else:
                            final_width = original_width
                            final_height = original_height
                        
                        # Yükseklik kontrolü
                        if final_height > max_height:
                            scale_factor = max_height / final_height
                            final_height = max_height
                            final_width = final_width * scale_factor
                        
                        self.logger.debug(f"Görsel {i+1} - Büyük, küçültüldü: {final_width:.0f}x{final_height:.0f}")
                    
                    gorsel_info.append({
                        'path': gorsel_path,
                        'optimal_height': final_height,
                        'width': final_width,
                        'ratio': img_ratio,
                        'is_small': original_width <= max_width and original_height <= max_height
                    })
                    
                    self.logger.debug(f"Görsel {i+1} analizi - Final boyut: {final_width:.0f}x{final_height:.0f}")
                    
            except Exception as e:
                self.logger.error(f"Görsel analiz hatası: {e}")
                # Fallback değerler
                gorsel_info.append({
                    'path': gorsel_path,
                    'optimal_height': 250,
                    'width': usable_width * 0.95,
                    'ratio': 1.0,
                    'is_small': False
                })

        # ALAN DAĞITIMI - SABİT YARIM YARIM BÖLME
        # Her soru için sayfanın yarısını kullan
        soru_area_height = usable_height / max_questions  # Her soru için eşit alan
        
        self.logger.info(f"Alan analizi - Her soru için alan: {soru_area_height:.1f}, Toplam alan: {usable_height:.1f}")

        # GÖRSELLERİ YERLEŞTİR - SABİT BÖLME SİSTEMİ
        for i, info in enumerate(gorsel_info):
            try:
                # Her soru için sabit alan - yarı yarıya
                soru_start_y = top_margin + i * soru_area_height
                
                # Görsel boyutları (doğal boyutlarda)
                final_width = info['width']
                final_height = info['optimal_height']

                # Görselin soru alanı içinde merkezlenmesi
                available_height_for_image = soru_area_height - cevap_area_height - 20  # 20px buffer
                
                # Eğer görsel çok büyükse, alan sınırına sığdır
                if final_height > available_height_for_image:
                    scale_factor = available_height_for_image / final_height
                    final_height = available_height_for_image
                    final_width = final_width * scale_factor
                    self.logger.debug(f"Soru {i+1} alan sınırına sığdırıldı: {final_width:.0f}x{final_height:.0f}")

                # Y pozisyonu - soru alanının üst kısmından başla
                y_start = page_height - soru_start_y - final_height - 10  # 10px üst padding

                # X pozisyonu - merkezle
                x_centered = left_margin + (usable_width - final_width) / 2

                # Görseli çiz
                canvas_obj.drawImage(
                    info['path'],
                    x_centered,
                    y_start,
                    width=final_width,
                    height=final_height
                )

                # Soru numarası - daha açık renk
                soru_no = (sayfa_no - 1) * max_questions + i + 1
                canvas_obj.setFont("Helvetica-Bold", 16)
                canvas_obj.setFillColor("#666666")  # Koyu gri renk (siyah yerine)

                # Numara pozisyonu - sol margin dışına
                canvas_obj.drawString(
                    left_margin - 10,
                    y_start + final_height - 25,
                    f"{soru_no}."
                )

                # DEBUG bilgisi
                self.logger.info(f"YAZILI DEBUG - Soru {soru_no} işleniyor:")
                self.logger.info(f"  Liste index: {i}")
                self.logger.info(f"  Dosya: {os.path.basename(info['path'])}")
                self.logger.info(f"  Soru alanı Y: {soru_start_y:.1f} - {soru_start_y + soru_area_height:.1f}")
                self.logger.info(f"  Görsel Y pozisyonu: {y_start:.1f}")
                self.logger.info(f"  Görsel X pozisyonu: {x_centered:.1f}")
                self.logger.info(f"  Boyut: {final_width:.0f}x{final_height:.0f}")

            except Exception as e:
                self.logger.error(f"Yazılı soru {i+1} yerleştirme hatası: {e}")

    def create_template_page(self, canvas_obj, gorseller, sayfa_no, template_path):
        """Şablonu kullanarak bir sayfa oluştur - GERİ DÖNÜŞ DEĞERİ İLE"""
        try:
            self.logger.info(f"Sayfa {sayfa_no} oluşturuluyor ({len(gorseller)} soru)")
            page_width, page_height = A4

            # Şablonu arka plan olarak ekle
            if os.path.exists(template_path):
                canvas_obj.drawImage(template_path, 0, 0, width=page_width, height=page_height)
                self.logger.debug(f"Şablon yüklendi: {os.path.basename(template_path)}")
            else:
                self.logger.error(f"Şablon bulunamadı: {template_path}")
                return 0

            # Soru tipine göre layout ve geri dönüş değeri
            if self.soru_tipi.lower() == "yazili":
                self._create_yazili_layout(canvas_obj, gorseller, sayfa_no, page_width, page_height)
                yerlestirildi = len(gorseller)  # Yazılı için tüm görseller yerleştirilir
                self.logger.info(f"Yazılı sayfa {sayfa_no} - {yerlestirildi} soru yerleştirildi")
            else:
                # Test için düzeltilmiş sistem
                yerlestirildi = self._create_working_test_layout(canvas_obj, gorseller, sayfa_no, page_width, page_height)
                self.logger.info(f"Test sayfa {sayfa_no} - {yerlestirildi} soru yerleştirildi")

            self.logger.info(f"Sayfa {sayfa_no} başarıyla tamamlandı")
            return yerlestirildi

        except Exception as e:
            self.logger.error(f"Sayfa {sayfa_no} oluşturma hatası: {e}")
            return 0

    def _create_working_test_layout(self, canvas_obj, gorseller, sayfa_no, page_width, page_height):
        """Dinamik layout ile soruları sayfaya yerleştirir (flow layout mantığı)"""

        # Sayfa margin ve sütun ayarları
        top_margin = 50
        bottom_margin = 50
        left_margin = 25
        right_margin = 25
        col_gap = 30

        usable_width = page_width - left_margin - right_margin
        usable_height = page_height - top_margin - bottom_margin

        # 2 sütun genişliği
        cols = 2
        col_width = (usable_width - col_gap) / cols

        # Başlangıç konumları
        current_x_positions = [left_margin, left_margin + col_width + col_gap]  # 2 sütunun x pozisyonu
        current_y_positions = [page_height - top_margin, page_height - top_margin]  # her sütun için y başlangıcı

        yerlestirilen = 0
        soru_no = (sayfa_no - 1) * 8 + 1  # soru numarası başlangıcı

        for i, gorsel_path in enumerate(gorseller):
            try:
                # Görsel boyut bilgisi al
                with PILImage.open(gorsel_path) as img:
                    original_width = img.width
                    original_height = img.height
                    img_ratio = original_width / original_height

                # Görseli sütun genişliğine göre orantılı küçült
                final_width = col_width * 0.95
                final_height = final_width / img_ratio

                # Hangi sütuna yerleşecek? -> daha yüksek olan değil, daha fazla boşluğu olan
                column_index = 0 if current_y_positions[0] > current_y_positions[1] else 1

                # Mevcut sütunun Y pozisyonu
                new_y = current_y_positions[column_index] - final_height - 20  # altına biraz boşluk

                # Eğer bu görsel sığmazsa, yeni sayfa aç
                if new_y < bottom_margin:
                    # Yeni sayfa
                    canvas_obj.showPage()
                    sayfa_no += 1
                    self.logger.info(f"📄 Yeni sayfa oluşturuldu: {sayfa_no}")

                    # Pozisyonları resetle
                    current_y_positions = [page_height - top_margin, page_height - top_margin]
                    column_index = 0
                    new_y = current_y_positions[column_index] - final_height - 20

                # Pozisyon X
                img_x = current_x_positions[column_index]
                img_y = new_y

                # Görseli çiz
                canvas_obj.drawImage(gorsel_path, img_x, img_y, width=final_width, height=final_height)

                # Soru numarasını yaz
                canvas_obj.setFont("Helvetica-Bold", 12)
                canvas_obj.setFillColor("#333333")
                canvas_obj.drawString(img_x - 15, img_y + final_height + 5, f"{soru_no}.")

                # Y pozisyonunu güncelle
                current_y_positions[column_index] = img_y - 10  # yeni görselin altına boşluk bırak

                self.logger.info(f"✅ Soru {soru_no} yerleştirildi (Sütun {column_index+1})")
                soru_no += 1
                yerlestirilen += 1

            except Exception as e:
                self.logger.error(f"❌ Görsel yerleştirme hatası: {e}")
                continue

        return yerlestirilen

    def create_answer_key_page(self, canvas_obj):
        """Cevap anahtarı sayfası oluştur"""
        try:
            self.logger.info(f"Cevap anahtarı sayfası oluşturuluyor ({len(self.cevap_listesi)} cevap)")
            page_width, page_height = A4
            
            # Başlık
            canvas_obj.setFont("Helvetica-Bold", 18)
            title_text = "CEVAP ANAHTARI"
            text_width = canvas_obj.stringWidth(title_text, "Helvetica-Bold", 18)
            canvas_obj.drawString((page_width - text_width) / 2, page_height - 100, title_text)
            
            # Cevapları tabloda göster
            start_y = page_height - 150
            row_height = 25
            
            # Başlık satırı
            canvas_obj.setFont("Helvetica-Bold", 12)
            canvas_obj.drawString(100, start_y, "Soru No")
            canvas_obj.drawString(200, start_y, "Cevap")
            canvas_obj.line(100, start_y - 5, 300, start_y - 5)
            
            # Cevapları yazdır
            canvas_obj.setFont("Helvetica", 10)
            for i, cevap in enumerate(self.cevap_listesi):
                y_pos = start_y - (i + 2) * row_height
                if y_pos < 100:  # Sayfa sonu kontrolü
                    self.logger.debug("Cevap anahtarı yeni sayfaya geçiyor")
                    canvas_obj.showPage()
                    # Yeni sayfada başlık tekrarla
                    canvas_obj.setFont("Helvetica-Bold", 18)
                    text_width = canvas_obj.stringWidth(title_text, "Helvetica-Bold", 18)
                    canvas_obj.drawString((page_width - text_width) / 2, page_height - 100, title_text)
                    
                    canvas_obj.setFont("Helvetica-Bold", 12)
                    canvas_obj.drawString(100, page_height - 150, "Soru No")
                    canvas_obj.drawString(200, page_height - 150, "Cevap")
                    canvas_obj.line(100, page_height - 155, 300, page_height - 155)
                    
                    start_y = page_height - 150
                    y_pos = start_y - 2 * row_height
                    canvas_obj.setFont("Helvetica", 10)
                
                canvas_obj.drawString(100, y_pos, f"{i + 1}")
                canvas_obj.drawString(200, y_pos, str(cevap))
            
            self.logger.info("Cevap anahtarı sayfası tamamlandı")
                
        except Exception as e:
            self.logger.error(f"Cevap anahtarı oluşturma hatası: {e}")
    
    def kaydet(self, dosya_yolu):
        """ÇALIŞAN PDF kaydet sistemi - Import'sız"""
        try:
            self.logger.info(f"PDF oluşturma başlatıldı - Soru Tipi: {self.soru_tipi}")
            self.logger.info(f"PDF OLUŞTURMA DEBUG:")
            self.logger.info(f"Toplam görsel sayısı: {len(self.gorsel_listesi)}")
            for idx, gorsel in enumerate(self.gorsel_listesi):
                self.logger.info(f"  {idx}: {os.path.basename(gorsel)}")

            # Şablon seçimi
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            if self.soru_tipi.lower() == "yazili":
                template_name = "template2.png"
                self.logger.info("Yazılı şablonu seçildi")
            else:
                template_name = "template.png"
                self.logger.info("Test şablonu seçildi")

            template_path = os.path.join(current_dir, "templates", template_name)
            self.logger.debug(f"Şablon yolu: {template_path}")

            if not os.path.exists(template_path):
                self.logger.warning("Şablon bulunamadı, basit PDF oluşturuluyor")
                return self._basit_pdf_olustur(dosya_yolu)

            # Canvas oluştur
            c = canvas.Canvas(dosya_yolu, pagesize=A4)

            # 📄 BASIT ÇALIŞAN SİSTEM - İmport yok
            self.logger.info("📄 Basit çalışan sistem aktif")
            
            kalan_gorseller = self.gorsel_listesi.copy()
            sayfa_no = 1
            max_sayfa = 50  # Güvenlik limiti

            self.logger.info("🔄 Dinamik sayfa sistemi başlatılıyor...")

            while kalan_gorseller and sayfa_no <= max_sayfa:
                if self.soru_tipi.lower() == "yazili":
                    # Yazılı için sabit 2 soru
                    sayfa_gorselleri = kalan_gorseller[:2]
                    kalan_gorseller = kalan_gorseller[2:]
                    yerlestirildi = len(sayfa_gorselleri)
                    self.logger.info(f"📄 YAZILI SAYFA {sayfa_no} - {len(sayfa_gorselleri)} soru işlenecek")
                    self.create_template_page(c, sayfa_gorselleri, sayfa_no, template_path)
                else:
                    # Test için maksimum 8 soru dene
                    max_soru_bu_sayfa = min(len(kalan_gorseller), 8)
                    sayfa_gorselleri = kalan_gorseller[:max_soru_bu_sayfa]

                    self.logger.info(f"📄 SAYFA {sayfa_no} - {len(sayfa_gorselleri)} soru test ediliyor")

                    # Şablonlu sayfa oluştur ve gerçekte kaç soru yerleştirildiğini öğren
                    yerlestirildi = self.create_template_page(c, sayfa_gorselleri, sayfa_no, template_path)

                    # Yerleştirilen soruları kalan_gorseller'den çıkar
                    kalan_gorseller = kalan_gorseller[yerlestirildi:]

                self.logger.info(f"✅ Sayfa {sayfa_no}: {yerlestirildi} soru yerleştirildi, kalan: {len(kalan_gorseller)}")

                # Sonraki sayfa için hazırlık
                if kalan_gorseller:
                    c.showPage()
                    sayfa_no += 1
                
                # EMNİYET KONTROLÜ
                if yerlestirildi == 0:
                    self.logger.error("🚨 Hiç soru yerleştirilemedi - DÖNGÜ SONLANDIRILIYOR")
                    break

            if sayfa_no > max_sayfa:
                self.logger.error(f"🚨 Maksimum sayfa sınırı ({max_sayfa}) aşıldı!")

            self.logger.info(f"📊 Toplam {sayfa_no} sayfa oluşturuldu")

            # Cevap anahtarı sayfası ekle
            if self.cevap_listesi:
                c.showPage()
                self.create_answer_key_page(c)
                self.logger.info("📋 Cevap anahtarı sayfası eklendi")

            c.save()
            self.logger.info(f"🎉 PDF başarıyla kaydedildi: {os.path.basename(dosya_yolu)}")
            return True

        except Exception as e:
            self.logger.error(f"❌ PDF kaydetme hatası: {e}")
            import traceback
            self.logger.error(f"Detaylı hata: {traceback.format_exc()}")
            return False
    
    def _basit_pdf_olustur(self, dosya_yolu):
        """Şablon bulunamazsa basit PDF oluştur"""
        try:
            self.logger.info("Basit PDF oluşturma moduna geçildi")
            story = []
            styles = getSampleStyleSheet()
            
            # Başlık
            if self.baslik_metni:
                p = Paragraph(self.baslik_metni, styles["Title"])
                story.append(p)
                story.append(Spacer(1, 0.5*inch))
            
            # Görseller
            for i, gorsel_yolu in enumerate(self.gorsel_listesi):
                try:
                    img = Image(gorsel_yolu, width=6*inch, height=4*inch)
                    story.append(img)
                    
                    if i < len(self.cevap_listesi):
                        cevap_paragraf = Paragraph(f"Cevap: {self.cevap_listesi[i]}", styles["Normal"])
                        story.append(cevap_paragraf)
                    
                    story.append(Spacer(1, 0.3*inch))
                except Exception as e:
                    self.logger.error(f"Basit PDF - Görsel {i+1} ekleme hatası: {e}")
            
            # Cevap anahtarı
            if self.cevap_listesi:
                story.append(Spacer(1, 0.5*inch))
                story.append(Paragraph("CEVAP ANAHTARI", styles["Heading1"]))
                story.append(Spacer(1, 0.2*inch))
                
                data = []
                for i, cevap in enumerate(self.cevap_listesi, 1):
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
            
            doc = SimpleDocTemplate(dosya_yolu, pagesize=A4)
            doc.build(story)
            self.logger.info("Basit PDF başarıyla oluşturuldu")
            return True
            
        except Exception as e:
            self.logger.error(f"Basit PDF oluşturma hatası: {e}")
            return False



"""
def _create_test_layout(self, canvas_obj, gorseller, sayfa_no, page_width, page_height):
        # Layout parametreleri
        top_margin = 50
        left_margin = 25
        right_margin = 25
        bottom_margin = 50
        
        usable_width = page_width - left_margin - right_margin
        usable_height = page_height - top_margin - bottom_margin
        
        cols = 2
        rows = 4
        col_gap = 30
        row_gap = 20
        
        box_width = (usable_width - col_gap) / cols
        box_height = (usable_height - (rows-1) * row_gap) / rows
        
        self.logger.info("✨ Temiz final layout - Akıllı sığdırma aktif")
        self.logger.info(f"📦 Kutucuk boyutu: {box_width:.0f} x {box_height:.0f}")
        
        # Grid pozisyonları hesapla
        grid_positions = []
        for i in range(8):
            row = i % rows
            col = i // rows
            
            x = left_margin + col * (box_width + col_gap)
            y = page_height - top_margin - (row + 1) * box_height - row * row_gap
            
            grid_positions.append({
                'index': i,
                'row': row,
                'col': col,
                'x': x,
                'y': y,
                'box_width': box_width,
                'box_height': box_height
            })
        
        # ✅ DAHA ESNEK MINIMUM BOYUT KRİTERLERİ
        MIN_ACCEPTABLE_WIDTH = box_width * 0.25   # %35 → %25 (daha esnek)
        MIN_ACCEPTABLE_HEIGHT = box_height * 0.15  # %25 → %15 (daha esnek)
        MIN_SCALE_FACTOR = 0.08                    # 0.12 → 0.08 (daha esnek)
        
        self.logger.debug(f"🎯 Sığma kriterleri: Min boyut {MIN_ACCEPTABLE_WIDTH:.0f}x{MIN_ACCEPTABLE_HEIGHT:.0f}, Min ölçek %{MIN_SCALE_FACTOR*100:.0f}")
        
        # Görselleri yerleştir
        yerlestirildi_sayisi = 0
        
        for i in range(min(len(gorseller), 8)):
            try:
                pos = grid_positions[i]
                gorsel_path = gorseller[i]
                
                self.logger.debug(f"🖼️ Soru {i+1} test ediliyor: {os.path.basename(gorsel_path)}")
                
                with PILImage.open(gorsel_path) as img:
                    original_width = img.width
                    original_height = img.height
                    img_ratio = original_width / original_height
                    
                    # Boyutlandırma
                    max_img_width = pos['box_width'] * 0.95
                    max_img_height = pos['box_height'] * 0.85
                    
                    if img_ratio > (max_img_width / max_img_height):
                        final_width = max_img_width
                        final_height = max_img_width / img_ratio
                    else:
                        final_height = max_img_height
                        final_width = max_img_height * img_ratio
                    
                    # Sığma kontrolü
                    scale_factor = min(final_width / original_width, final_height / original_height)
                    
                    is_too_small = (
                        final_width < MIN_ACCEPTABLE_WIDTH or 
                        final_height < MIN_ACCEPTABLE_HEIGHT or 
                        scale_factor < MIN_SCALE_FACTOR
                    )
                    
                    if is_too_small:
                        self.logger.warning(f"   ❌ Soru {i+1} çok küçülüyor")
                        # ❌ YANLIŞ: break ile tüm döngüyü kırma
                        # ✅ DOĞRU: Bu soruyu atla, diğerlerini dene
                        continue
                    
                    # Yerleştir - üst hizalama
                    self.logger.debug(f"   ✅ Soru {i+1} yerleştiriliyor")
                    
                    img_x = pos['x'] + (pos['box_width'] - final_width) / 2
                    img_y = pos['y'] + pos['box_height'] - final_height - 15
                    
                    # Görseli çiz
                    canvas_obj.drawImage(gorsel_path, img_x, img_y, width=final_width, height=final_height)
                    
                    # Soru numarası
                    soru_no = (sayfa_no - 1) * 8 + yerlestirildi_sayisi + 1
                    canvas_obj.setFont("Helvetica-Bold", 12)
                    canvas_obj.setFillColor("#666666")
                    
                    numara_x = pos['x'] - 5
                    numara_y = pos['y'] + pos['box_height'] - 27
                    
                    canvas_obj.drawString(numara_x, numara_y, f"{soru_no}.")
                    
                    yerlestirildi_sayisi += 1
                    
            except Exception as e:
                self.logger.error(f"❌ Soru {i+1} hatası: {e}")
                # Hata durumunda da devam et
                continue
        
        # ✅ EMNİYET KONTROLÜ - En az 1 soru yerleştir
        if yerlestirildi_sayisi == 0 and len(gorseller) > 0:
            self.logger.warning("🚨 HİÇ SORU YERLEŞTİRİLEMEDİ - ZORLA YERLEŞTİRME AKTIF")
            
            # İlk görseli zorla yerleştir (çok küçük olsa bile)
            try:
                pos = grid_positions[0]
                gorsel_path = gorseller[0]
                
                with PILImage.open(gorsel_path) as img:
                    # Minimum boyutlarda yerleştir
                    final_width = MIN_ACCEPTABLE_WIDTH
                    final_height = MIN_ACCEPTABLE_HEIGHT
                    
                    img_x = pos['x'] + (pos['box_width'] - final_width) / 2
                    img_y = pos['y'] + pos['box_height'] - final_height - 15
                    
                    canvas_obj.drawImage(gorsel_path, img_x, img_y, width=final_width, height=final_height)
                    
                    # Soru numarası
                    soru_no = (sayfa_no - 1) * 8 + 1
                    canvas_obj.setFont("Helvetica-Bold", 12)
                    canvas_obj.setFillColor("#666666")
                    canvas_obj.drawString(pos['x'] - 5, pos['y'] + pos['box_height'] - 27, f"{soru_no}.")
                    
                    yerlestirildi_sayisi = 1
                    self.logger.warning("🔧 1 soru zorla yerleştirildi")
                    
            except Exception as e:
                self.logger.error(f"🚨 Zorla yerleştirme bile başarısız: {e}")
                # Son çare: 1 döndür ki sonsuz döngü olmasın
                yerlestirildi_sayisi = 1
        
        # Sonuç raporu
        kalan_soru = len(gorseller) - yerlestirildi_sayisi
        self.logger.info(f"📄 Sayfa {sayfa_no}: {yerlestirildi_sayisi} soru yerleştirildi")
        if kalan_soru > 0:
            self.logger.info(f"📄 Sonraki sayfaya giden: {kalan_soru} soru")
        
        return yerlestirildi_sayisi



----------------------------------------------------------

 def _create_test_layout(self, canvas_obj, gorseller, sayfa_no, page_width, page_height):
        

        # Layout parametreleri - AYNI
        top_margin = 50
        left_margin = 25
        right_margin = 25
        bottom_margin = 50

        usable_width = page_width - left_margin - right_margin
        usable_height = page_height - top_margin - bottom_margin

        # 10'lu grid
        cols = 2
        rows = 5
        col_gap = 30
        row_gap = 15

        box_width = (usable_width - col_gap) / cols
        box_height = (usable_height - (rows-1) * row_gap) / rows

        self.logger.info("🔍 DEBUG 10'LU SİSTEM - Çerçevelerle analiz")
        self.logger.info(f"📦 Kutucuk boyutu: {box_width:.0f} x {box_height:.0f}")
        self.logger.info(f"📏 8'li sistemde kutucuk: 283x180 idi")
        self.logger.info(f"📏 10'lu sistemde kutucuk: {box_width:.0f}x{box_height:.0f}")
        self.logger.info(f"📉 Boyut farkı: Genişlik: {box_width-283:.0f}, Yükseklik: {box_height-180:.0f}")

        # Grid pozisyonları hesapla
        grid_positions = []
        for i in range(10):
            row = i % rows
            col = i // rows

            x = left_margin + col * (box_width + col_gap)
            y = page_height - top_margin - (row + 1) * box_height - row * row_gap

            grid_positions.append({
                'index': i,
                'row': row,
                'col': col,
                'x': x,
                'y': y,
                'box_width': box_width,
                'box_height': box_height
            })

        # 🎨 DEBUG ÇERÇEVELERİ BAŞLANGICI
        self.logger.info("🎨 Debug çerçeveleri çiziliyor...")

        # 1. MARGIN ALANLARI - AÇIK GRİ
        canvas_obj.setFillColor("#F5F5F5")  # Çok açık gri
        canvas_obj.setStrokeColor("#CCCCCC")
        canvas_obj.setLineWidth(1)

        # Sol margin
        canvas_obj.rect(0, 0, left_margin, page_height, fill=1, stroke=1)
        # Sağ margin
        canvas_obj.rect(page_width - right_margin, 0, right_margin, page_height, fill=1, stroke=1)
        # Üst margin
        canvas_obj.rect(left_margin, page_height - top_margin, usable_width, top_margin, fill=1, stroke=1)
        # Alt margin
        canvas_obj.rect(left_margin, 0, usable_width, bottom_margin, fill=1, stroke=1)

        # 2. KUTUCUK ÇERÇEVELERİ - MAVİ
        canvas_obj.setStrokeColor("#0066CC")
        canvas_obj.setLineWidth(2)

        for pos in grid_positions:
            canvas_obj.rect(pos['x'], pos['y'], pos['box_width'], pos['box_height'], fill=0, stroke=1)

            # Kutucuk bilgisi
            canvas_obj.setFont("Helvetica-Bold", 8)
            canvas_obj.setFillColor("#0066CC")
            canvas_obj.drawString(pos['x'] + 5, pos['y'] + pos['box_height'] - 15, 
                                f"Kutu {pos['index']+1}")
            canvas_obj.drawString(pos['x'] + 5, pos['y'] + pos['box_height'] - 25, 
                                f"{pos['box_width']:.0f}x{pos['box_height']:.0f}")

        # 3. BOYUT KARŞILAŞTIRMA BİLGİLERİ
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.setFillColor("#FF6600")
        canvas_obj.drawString(10, page_height - 20, f"10'lu sistem: {box_width:.0f}x{box_height:.0f} kutucuklar")
        canvas_obj.drawString(10, page_height - 35, f"8'li sistem: 283x180 kutucuklar")
        canvas_obj.drawString(10, page_height - 50, f"Fark: {box_width-283:.0f}x{box_height-180:.0f}")

        # Minimum kabul edilebilir boyutlar
        MIN_ACCEPTABLE_WIDTH = box_width * 0.30
        MIN_ACCEPTABLE_HEIGHT = box_height * 0.20
        MIN_SCALE_FACTOR = 0.10

        # Görselleri yerleştir
        yerlestirildi_sayisi = 0

        for i in range(min(len(gorseller), 10)):
            try:
                pos = grid_positions[i]
                gorsel_path = gorseller[i]

                self.logger.info(f"🖼️ DEBUG Soru {i+1}: {os.path.basename(gorsel_path)}")

                with PILImage.open(gorsel_path) as img:
                    original_width = img.width
                    original_height = img.height
                    img_ratio = original_width / original_height

                    # ORANTILI + TUTARLI BOYUTLANDIRMA 
                    # Hedef: Tüm görseller daha tutarlı boyutlarda ama oranları korunmuş
                    target_width = pos['box_width'] * 0.80   # 0.95 → 0.80 (daha küçük)
                    target_height = pos['box_height'] * 0.75  # 0.85 → 0.75 (daha küçük)
                    
                    # Orantılı boyutlandırma (AYNI LOJİK)
                    if img_ratio > (target_width / target_height):
                        # Genişlik sınırlayıcı
                        final_width = target_width
                        final_height = target_width / img_ratio
                    else:
                        # Yükseklik sınırlayıcı
                        final_height = target_height
                        final_width = target_height * img_ratio
                    
                    # TUTARLILIK İÇİN MİNİMUM BOYUT GARANTİSİ
                    min_area_ratio = 0.65  # Kutucuğun en az %65'ini kaplar
                    kutucuk_alani = pos['box_width'] * pos['box_height']
                    gorsel_alani = final_width * final_height
                    alan_orani = gorsel_alani / kutucuk_alani
                    
                    if alan_orani < min_area_ratio:
                        # Alanı büyütmek için ölçekle (oran korunur)
                        scale_factor = (min_area_ratio / alan_orani) ** 0.5
                        final_width = final_width * scale_factor
                        final_height = final_height * scale_factor

                    # DEBUG: BOYUT BİLGİLERİ
                    scale_factor = min(final_width / original_width, final_height / original_height)
                    self.logger.info(f"   📏 Orijinal: {original_width}x{original_height}")
                    self.logger.info(f"   📏 Final: {final_width:.0f}x{final_height:.0f}")
                    self.logger.info(f"   📏 Ölçek: %{scale_factor*100:.1f}")

                    # Sığma kontrolü
                    is_too_small = (
                        final_width < MIN_ACCEPTABLE_WIDTH or 
                        final_height < MIN_ACCEPTABLE_HEIGHT or 
                        scale_factor < MIN_SCALE_FACTOR
                    )

                    if is_too_small:
                        self.logger.warning(f"   ❌ SIĞMIYOR - Çok küçük!")
                        self.logger.info(f"   📄 Kalan {len(gorseller) - i} soru sonraki sayfaya")
                        break

                    # Yerleştir
                    img_x = pos['x'] + (pos['box_width'] - final_width) / 2
                    img_y = pos['y'] + pos['box_height'] - final_height - 15

                    # Görseli çiz
                    canvas_obj.drawImage(gorsel_path, img_x, img_y, width=final_width, height=final_height)

                    # 4. GÖRSEL ÇERÇEVESİ - YEŞİL
                    canvas_obj.setStrokeColor("#00AA00")
                    canvas_obj.setLineWidth(1)
                    canvas_obj.rect(img_x, img_y, final_width, final_height, fill=0, stroke=1)

                    # Görsel boyut bilgisi
                    canvas_obj.setFont("Helvetica", 7)
                    canvas_obj.setFillColor("#00AA00")
                    canvas_obj.drawString(img_x, img_y - 10, f"{final_width:.0f}x{final_height:.0f}")
                    canvas_obj.drawString(img_x, img_y - 20, f"%{scale_factor*100:.0f}")

                    # Soru numarası
                    soru_no = (sayfa_no - 1) * 10 + yerlestirildi_sayisi + 1
                    canvas_obj.setFont("Helvetica-Bold", 12)
                    canvas_obj.setFillColor("#666666")

                    numara_x = pos['x'] - 5
                    numara_y = pos['y'] + pos['box_height'] - 27

                    canvas_obj.drawString(numara_x, numara_y, f"{soru_no}.")

                    yerlestirildi_sayisi += 1
                    self.logger.info(f"   ✅ Yerleştirildi!")

            except Exception as e:
                self.logger.error(f"❌ Soru {i+1} hatası: {e}")

        # 5. SONUÇ BİLGİLERİ
        kalan_soru = len(gorseller) - yerlestirildi_sayisi

        # Sayfanın altına sonuç yaz
        canvas_obj.setFont("Helvetica-Bold", 12)
        canvas_obj.setFillColor("#FF0000")
        canvas_obj.drawString(10, 40, f"SONUÇ: {yerlestirildi_sayisi}/10 soru yerleşti")
        canvas_obj.drawString(10, 25, f"Sonraki sayfaya: {kalan_soru} soru")

        self.logger.info("=" * 60)
        self.logger.info(f"🎯 DEBUG SONUÇLARI:")
        self.logger.info(f"📦 Kutucuk boyutu: {box_width:.0f}x{box_height:.0f}")
        self.logger.info(f"✅ Yerleştirilen: {yerlestirildi_sayisi} soru")
        self.logger.info(f"❌ Sonraki sayfaya: {kalan_soru} soru")
        self.logger.info("=" * 60)

        return yerlestirildi_sayisi

-----------------------------------------------------------
def _create_working_test_layout(self, canvas_obj, gorseller, sayfa_no, page_width, page_height):
        

        # Sayfa margin ve sütun ayarları
        top_margin = 50
        bottom_margin = 50
        left_margin = 25
        right_margin = 25
        col_gap = 30

        usable_width = page_width - left_margin - right_margin
        usable_height = page_height - top_margin - bottom_margin

        # 2 sütun genişliği
        cols = 2
        col_width = (usable_width - col_gap) / cols

        # Başlangıç konumları
        current_x_positions = [left_margin, left_margin + col_width + col_gap]  # 2 sütunun x pozisyonu
        current_y_positions = [page_height - top_margin, page_height - top_margin]  # her sütun için y başlangıcı

        yerlestirilen = 0
        soru_no = (sayfa_no - 1) * 8 + 1  # soru numarası başlangıcı

        for i, gorsel_path in enumerate(gorseller):
            try:
                # Görsel boyut bilgisi al
                with PILImage.open(gorsel_path) as img:
                    original_width = img.width
                    original_height = img.height
                    img_ratio = original_width / original_height

                # Görseli sütun genişliğine göre orantılı küçült
                final_width = col_width * 0.95
                final_height = final_width / img_ratio

                # Hangi sütuna yerleşecek? -> daha yüksek olan değil, daha fazla boşluğu olan
                column_index = 0 if current_y_positions[0] > current_y_positions[1] else 1

                # Mevcut sütunun Y pozisyonu
                new_y = current_y_positions[column_index] - final_height - 20  # altına biraz boşluk

                # Eğer bu görsel sığmazsa, yeni sayfa aç
                if new_y < bottom_margin:
                    # Yeni sayfa
                    canvas_obj.showPage()
                    sayfa_no += 1
                    self.logger.info(f"📄 Yeni sayfa oluşturuldu: {sayfa_no}")

                    # Pozisyonları resetle
                    current_y_positions = [page_height - top_margin, page_height - top_margin]
                    column_index = 0
                    new_y = current_y_positions[column_index] - final_height - 20

                # Pozisyon X
                img_x = current_x_positions[column_index]
                img_y = new_y

                # Görseli çiz
                canvas_obj.drawImage(gorsel_path, img_x, img_y, width=final_width, height=final_height)

                # Soru numarasını yaz
                canvas_obj.setFont("Helvetica-Bold", 12)
                canvas_obj.setFillColor("#333333")
                canvas_obj.drawString(img_x - 15, img_y + final_height + 5, f"{soru_no}.")

                # Y pozisyonunu güncelle
                current_y_positions[column_index] = img_y - 10  # yeni görselin altına boşluk bırak

                self.logger.info(f"✅ Soru {soru_no} yerleştirildi (Sütun {column_index+1})")
                soru_no += 1
                yerlestirilen += 1

            except Exception as e:
                self.logger.error(f"❌ Görsel yerleştirme hatası: {e}")
                continue

        return yerlestirilen


"""