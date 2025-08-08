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
    
    def create_template_page(self, canvas_obj, gorseller, sayfa_no, template_path):
        """Şablonu kullanarak bir sayfa oluştur"""
        try:
            self.logger.info(f"Sayfa {sayfa_no} oluşturuluyor ({len(gorseller)} soru)")
            page_width, page_height = A4

            # Şablonu arka plan olarak ekle
            if os.path.exists(template_path):
                canvas_obj.drawImage(template_path, 0, 0, width=page_width, height=page_height)
                self.logger.debug(f"Şablon yüklendi: {os.path.basename(template_path)}")
            else:
                self.logger.error(f"Şablon bulunamadı: {template_path}")
                return

            # Soru tipine göre layout
            if self.soru_tipi.lower() == "yazili":
                self._create_yazili_layout(canvas_obj, gorseller, sayfa_no, page_width, page_height)
            else:
                self._create_test_layout(canvas_obj, gorseller, sayfa_no, page_width, page_height)
            
            self.logger.info(f"Sayfa {sayfa_no} başarıyla tamamlandı")

        except Exception as e:
            self.logger.error(f"Sayfa {sayfa_no} oluşturma hatası: {e}")
    
    def _create_yazili_layout(self, canvas_obj, gorseller, sayfa_no, page_width, page_height):
        """Yazılı şablonu layout'u"""
        self.logger.debug("Yazılı layout uygulanıyor")
        
        # Layout hesaplamaları
        top_margin = page_height * 0.1
        left_margin = page_width * 0.05
        right_margin = page_width * 0.05
        bottom_margin = page_width * 0.05
        
        usable_width = page_width - left_margin - right_margin
        usable_height = page_height - top_margin - bottom_margin
        
        soru_ve_cevap_yuksekligi = usable_height / 3
        soru_height = soru_ve_cevap_yuksekligi * 0.6
        soru_width = usable_width
        
        self.logger.debug(f"Yazılı layout boyutları - Genişlik: {soru_width:.1f}, Yükseklik: {soru_height:.1f}")

        # Görselleri yerleştir
        for i, gorsel_path in enumerate(gorseller):
            if i >= 3:  # Yazılı için maksimum 3 soru
                self.logger.warning(f"Yazılı sayfada maksimum 3 soru gösterilebilir, {len(gorseller)} soru var")
                break

            try:
                # Pozisyon hesaplama
                x = left_margin
                y = page_height - top_margin - (i + 1) * soru_ve_cevap_yuksekligi + (soru_ve_cevap_yuksekligi - soru_height)

                # Görsel yerleştirme
                with PILImage.open(gorsel_path) as img:
                    img_ratio = img.width / img.height
                    new_width = soru_width
                    new_height = min(soru_height, soru_width / img_ratio)

                    canvas_obj.drawImage(gorsel_path, x, y, width=new_width, height=new_height)

                    # Soru numarası
                    soru_no = (sayfa_no - 1) * 3 + i + 1
                    canvas_obj.setFont("Helvetica-Bold", 12)
                    canvas_obj.drawString(x + 10, y + new_height - 20, f"{soru_no}.")
                    
                    self.logger.debug(f"Yazılı soru {soru_no} yerleştirildi (Boyut: {new_width:.0f}x{new_height:.0f})")

            except Exception as e:
                self.logger.error(f"Yazılı soru {i+1} yerleştirme hatası: {e}")
    
    def _create_test_layout(self, canvas_obj, gorseller, sayfa_no, page_width, page_height):
        """Test şablonu layout'u"""
        self.logger.debug("Test layout uygulanıyor")
        
        # Layout hesaplamaları
        top_margin = page_height * 0.1
        left_margin = page_width * 0.05
        right_margin = page_width * 0.01
        bottom_margin = page_height * 0.1

        usable_width = page_width - left_margin - right_margin
        usable_height = page_height - top_margin - bottom_margin

        soru_width = usable_width / 2 - 10
        soru_height = usable_height / 4 - 40
        
        self.logger.debug(f"Test layout boyutları - Genişlik: {soru_width:.1f}, Yükseklik: {soru_height:.1f}")

        for i, gorsel_path in enumerate(gorseller):
            if i >= 8:  # Test için maksimum 8 soru
                self.logger.warning(f"Test sayfada maksimum 8 soru gösterilebilir, {len(gorseller)} soru var")
                break

            try:
                # Grid pozisyonu
                row = i % 4
                col = i // 4

                x = left_margin + col * (soru_width + 10)
                y = page_height - top_margin - (row + 1) * (soru_height + 15)

                # Görsel yerleştirme
                with PILImage.open(gorsel_path) as img:
                    img_ratio = img.width / img.height
                    target_ratio = soru_width / soru_height

                    if img_ratio > target_ratio:
                        new_width = soru_width
                        new_height = soru_width / img_ratio
                    else:
                        new_height = soru_height
                        new_width = soru_height * img_ratio

                    x_offset = (soru_width - new_width) / 2
                    y_offset = (soru_height - new_height) / 2

                    canvas_obj.drawImage(gorsel_path, x + x_offset, y + y_offset, width=new_width, height=new_height)

                    # Soru numarası
                    soru_no = (sayfa_no - 1) * 8 + i + 1
                    canvas_obj.setFont("Helvetica-Bold", 10)
                    canvas_obj.drawString(x - 5, y + soru_height - 10, str(soru_no))
                    
                    self.logger.debug(f"Test soru {soru_no} yerleştirildi (Konum: {row+1},{col+1})")

            except Exception as e:
                self.logger.error(f"Test soru {i+1} yerleştirme hatası: {e}")

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
        """Şablonu kullanarak PDF kaydet"""
        try:
            self.logger.info(f"PDF oluşturma başlatıldı - Soru Tipi: {self.soru_tipi}")
            self.logger.info(f"Toplam görsel sayısı: {len(self.gorsel_listesi)}")
            
            # Şablon seçimi
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            if self.soru_tipi.lower() == "yazili":
                template_name = "template2.png"
                sorular_per_sayfa = 3
                self.logger.info("Yazılı şablonu seçildi")
            else:
                template_name = "template.png"
                sorular_per_sayfa = 8
                self.logger.info("Test şablonu seçildi")

            template_path = os.path.join(current_dir, "templates", template_name)
            self.logger.debug(f"Şablon yolu: {template_path}")

            if not os.path.exists(template_path):
                self.logger.warning("Şablon bulunamadı, basit PDF oluşturuluyor")
                return self._basit_pdf_olustur(dosya_yolu)
            
            # Canvas oluştur
            c = canvas.Canvas(dosya_yolu, pagesize=A4)
            toplam_sayfa = math.ceil(len(self.gorsel_listesi) / sorular_per_sayfa)
            self.logger.info(f"Toplam {toplam_sayfa} sayfa oluşturulacak")
            
            # Her sayfa için
            for sayfa_no in range(1, toplam_sayfa + 1):
                start_idx = (sayfa_no - 1) * sorular_per_sayfa
                end_idx = min(start_idx + sorular_per_sayfa, len(self.gorsel_listesi))
                sayfa_gorselleri = self.gorsel_listesi[start_idx:end_idx]
                
                # Şablonlu sayfa oluştur
                self.create_template_page(c, sayfa_gorselleri, sayfa_no, template_path)
                
                if sayfa_no < toplam_sayfa:
                    c.showPage()
            
            # Cevap anahtarı sayfası ekle
            if self.cevap_listesi:
                c.showPage()
                self.create_answer_key_page(c)
            
            c.save()
            self.logger.info(f"PDF başarıyla kaydedildi: {os.path.basename(dosya_yolu)}")
            return True
            
        except Exception as e:
            self.logger.error(f"PDF kaydetme hatası: {e}")
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