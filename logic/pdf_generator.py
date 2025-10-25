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
from logging.handlers import RotatingFileHandler

# Yeni loglama sistemi: Bu modülün kendi logger'ını al.
# Adı otomatik olarak 'logic.pdf_generator' olacaktır.
logger = logging.getLogger(__name__)

class PDFCreator:
    def __init__(self):
        self.gorsel_listesi = []
        self.baslik_metni = ""
        self.cevap_listesi = []
        self.soru_tipi = "test"
    
    def baslik_ekle(self, baslik):
        """PDF basligini ayarla"""
        self.baslik_metni = baslik
        logger.info(f"PDF basligi ayarlandi: {baslik}")
    
    def gorsel_ekle(self, gorsel_yolu, cevap=None):
        """Gorsel listesine ekle"""
        self.gorsel_listesi.append(gorsel_yolu)
        if cevap:
            self.cevap_listesi.append(cevap)
    
    def cevap_anahtari_ekle(self, cevaplar):
        """Cevap listesini ayarla"""
        self.cevap_listesi = cevaplar
        logger.info(f"Cevap anahtari eklendi ({len(cevaplar)} cevap)")

    def _create_yazili_layout(self, canvas_obj, gorseller, sayfa_no, page_width, page_height):
        """Yazili sablonu layout'u - Dinamik iyilestirilmis versiyon"""
        top_margin = page_height * 0.12
        left_margin = page_width * 0.05
        right_margin = page_width * 0.05
        bottom_margin = page_height * 0.08

        usable_width = page_width - left_margin - right_margin
        usable_height = page_height - top_margin - bottom_margin

        max_questions = min(len(gorseller), 2)

        gorsel_info = []
        cevap_area_height = 40
        
        for i, gorsel_path in enumerate(gorseller[:max_questions]):
            try:
                with PILImage.open(gorsel_path) as img:
                    img_ratio = img.width / img.height
                    original_width = img.width
                    original_height = img.height
                    
                    max_width = usable_width * 0.95
                    max_height = usable_height * 0.45
                    
                    if original_width <= max_width and original_height <= max_height:
                        final_width = original_width
                        final_height = original_height
                    else:
                        if original_width > max_width:
                            scale_factor = max_width / original_width
                            final_width = max_width
                            final_height = original_height * scale_factor
                        else:
                            final_width = original_width
                            final_height = original_height
                        
                        if final_height > max_height:
                            scale_factor = max_height / final_height
                            final_height = max_height
                            final_width = final_width * scale_factor
                    
                    gorsel_info.append({
                        'path': gorsel_path,
                        'optimal_height': final_height,
                        'width': final_width,
                        'ratio': img_ratio,
                        'is_small': original_width <= max_width and original_height <= max_height
                    })
                    
            except Exception as e:
                logger.error(f"Gorsel analiz hatasi: {gorsel_path}", exc_info=True)
                gorsel_info.append({
                    'path': gorsel_path,
                    'optimal_height': 250,
                    'width': usable_width * 0.95,
                    'ratio': 1.0,
                    'is_small': False
                })

        soru_area_height = usable_height / max_questions
        logger.info(f"Alan analizi - Her soru icin alan: {soru_area_height:.1f}, Toplam alan: {usable_height:.1f}")

        for i, info in enumerate(gorsel_info):
            try:
                soru_start_y = top_margin + i * soru_area_height
                
                final_width = info['width']
                final_height = info['optimal_height']
                available_height_for_image = soru_area_height - cevap_area_height - 20
                
                if final_height > available_height_for_image:
                    scale_factor = available_height_for_image / final_height
                    final_height = available_height_for_image
                    final_width = final_width * scale_factor

                y_start = page_height - soru_start_y - final_height - 10
                x_centered = left_margin + (usable_width - final_width) / 2

                canvas_obj.drawImage(
                    info['path'],
                    x_centered,
                    y_start,
                    width=final_width,
                    height=final_height
                )

                soru_no = (sayfa_no - 1) * max_questions + i + 1
                canvas_obj.setFont("Helvetica-Bold", 16)
                canvas_obj.setFillColor("#666666")
                canvas_obj.drawString(
                    left_margin - 10,
                    y_start + final_height - 25,
                    f"{soru_no}."
                )

                logger.info(f"Soru {soru_no} yerlestirildi - Boyut: {final_width:.0f}x{final_height:.0f}")

            except Exception as e:
                logger.error(f"Yazili soru {i+1} yerlestirme hatasi", exc_info=True)

    def create_template_page(self, canvas_obj, gorseller, sayfa_no, template_path):
        """Sablonu kullanarak bir sayfa olustur"""
        try:
            logger.info(f"Sayfa {sayfa_no} olusturuluyor ({len(gorseller)} soru)")
            page_width, page_height = A4

            if os.path.exists(template_path):
                canvas_obj.drawImage(template_path, 0, 0, width=page_width, height=page_height)
            else:
                logger.error(f"Sablon bulunamadi: {template_path}")
                return 0

            if self.soru_tipi.lower() == "yazili":
                self._create_yazili_layout(canvas_obj, gorseller, sayfa_no, page_width, page_height)
                yerlestirildi = len(gorseller)
                logger.info(f"Yazili sayfa {sayfa_no} - {yerlestirildi} soru yerlestirildi")
            else:
                yerlestirildi = self._create_working_test_layout(canvas_obj, gorseller, sayfa_no, page_width, page_height)
                logger.info(f"Test sayfa {sayfa_no} - {yerlestirildi} soru yerlestirildi")

            return yerlestirildi

        except Exception as e:
            logger.error(f"Sayfa {sayfa_no} olusturma hatasi", exc_info=True)
            return 0

    def _create_working_test_layout(self, canvas_obj, gorseller, sayfa_indices, sayfa_no, page_width, page_height, global_offset):
        """Calisan test layout sistemi"""
        top_margin = 35
        bottom_margin = 5
        left_margin = 20
        right_margin = 20
        col_gap = 40
        cols = 2
        soru_font_size = 10
        soru_spacing = 8
        image_spacing = 10

        usable_width = page_width - left_margin - right_margin
        col_width = (usable_width - col_gap) / cols
        usable_height = page_height - top_margin - bottom_margin

        current_x_positions = [left_margin + i * (col_width + col_gap) for i in range(cols)]
        current_y_positions = [page_height - top_margin for _ in range(cols)]

        soru_analizi = []
        for i, gorsel_path in enumerate(gorseller):
            try:
                with PILImage.open(gorsel_path) as img:
                    original_width = img.width
                    original_height = img.height
                    img_ratio = original_width / original_height

                    final_width = col_width * 0.98
                    final_height = final_width / img_ratio

                    total_height = final_height + soru_spacing + image_spacing

                    if total_height < 150:
                        kategori = 'KISA'
                    elif total_height < 300:
                        kategori = 'ORTA'
                    else:
                        kategori = 'UZUN'

                    soru_info = {
                        'index': i,
                        'path': gorsel_path,
                        'filename': os.path.basename(gorsel_path),
                        'final_size': (final_width, final_height),
                        'total_height': total_height,
                        'kategori': kategori
                    }
                    soru_analizi.append(soru_info)
            except Exception as e:
                logger.error(f"Soru {i+1} analiz hatasi: {gorsel_path}", exc_info=True)
                soru_info = {
                    'index': i,
                    'path': gorsel_path,
                    'filename': os.path.basename(gorsel_path),
                    'final_size': (col_width * 0.98, 250),
                    'total_height': 300,
                    'kategori': 'ORTA'
                }
                soru_analizi.append(soru_info)

        yerlestirildi_sayisi = 0
        kullanilan_indices = set()

        for sutun_index in range(cols):
            while True:
                kalan_bosluk = current_y_positions[sutun_index] - bottom_margin
                if kalan_bosluk < 50:
                    break

                uygun_sorular = []
                for soru in soru_analizi:
                    if soru['index'] in kullanilan_indices:
                        continue
                    if soru['total_height'] <= kalan_bosluk:
                        uygun_sorular.append(soru)

                if not uygun_sorular:
                    break

                secilen_soru = min(uygun_sorular, key=lambda s: (kalan_bosluk - s['total_height']))
                img_x = current_x_positions[sutun_index]
                soru_y = current_y_positions[sutun_index] - soru_font_size
                img_y = soru_y - soru_spacing - secilen_soru['final_size'][1]

                try:
                    canvas_obj.drawImage(
                        secilen_soru['path'],
                        img_x, img_y,
                        width=secilen_soru['final_size'][0],
                        height=secilen_soru['final_size'][1]
                    )
                    canvas_obj.setFont("Helvetica-Bold", soru_font_size)
                    canvas_obj.setFillColor("#333333")
                    toplam_soru_no = global_offset + yerlestirildi_sayisi + 1
                    cift_haneli_offset = -2 if toplam_soru_no >= 10 else 0
                    numara_x = img_x - 10 + cift_haneli_offset
                    numara_y = img_y + secilen_soru['final_size'][1] - 10
                    canvas_obj.drawString(numara_x, numara_y, f"{toplam_soru_no}.")
                except Exception as e:
                    logger.error(f"Gorsel cizim hatasi: {secilen_soru['path']}", exc_info=True)
                    continue

                current_y_positions[sutun_index] = img_y - image_spacing
                kullanilan_indices.add(secilen_soru['index'])
                yerlestirildi_sayisi += 1

        logger.info(f"Test layout tamamlandi - {yerlestirildi_sayisi} soru yerlestirildi")
        kullanilan_global_indices = set(sayfa_indices[i] for i in kullanilan_indices if i < len(sayfa_indices))
        return yerlestirildi_sayisi, kullanilan_global_indices

    def kaydet(self, dosya_yolu):
        """Düzeltilmiş PDF kaydetme fonksiyonu"""
        try:
            print(f"🚀 PDF OLUŞTURMA BAŞLIYOR - {self.soru_tipi} tipi")
            logger.info(f"PDF oluşturma başlıyor: Tip={self.soru_tipi}, Dosya={os.path.basename(dosya_yolu)}")
            self.global_soru_sayaci = 0

            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            template_name = "template2.png" if self.soru_tipi.lower() == "yazili" else "template3.png"
            template_path = os.path.join(current_dir, "templates", template_name)

            if not os.path.exists(template_path):
                logger.warning("Şablon bulunamadı, basit PDF oluşturuluyor")
                return self._basit_pdf_olustur(dosya_yolu)

            c = canvas.Canvas(dosya_yolu, pagesize=A4)
            kalan_sorular = list(range(len(self.gorsel_listesi)))
            sayfa_no = 1
            max_sayfa = 50

            sayfa_basi_soru = 2 if self.soru_tipi.lower() == "yazili" else 8

            while kalan_sorular and sayfa_no <= max_sayfa:
                c.drawImage(template_path, 0, 0, width=A4[0], height=A4[1])

                bu_sayfa_soru_sayisi = min(len(kalan_sorular), sayfa_basi_soru)
                sayfa_gorselleri = [self.gorsel_listesi[i] for i in kalan_sorular[:bu_sayfa_soru_sayisi]]
                sayfa_indices = kalan_sorular[:bu_sayfa_soru_sayisi]

                if self.soru_tipi.lower() == "yazili":
                    yerlestirildi = self._create_yazili_layout_simple(
                        c, sayfa_gorselleri, sayfa_no, A4[0], A4[1], self.global_soru_sayaci
                    )
                    kullanilan_set = set(sayfa_indices[:yerlestirildi])
                else:
                    yerlestirildi, kullanilan_set = self._create_working_test_layout(
                        c, sayfa_gorselleri, sayfa_indices, sayfa_no, A4[0], A4[1], self.global_soru_sayaci
                    )

                self.global_soru_sayaci += yerlestirildi
                if yerlestirildi == 0:
                    logger.warning("Hiç soru yerleştirilemedi - Döngü sonlandırılıyor")
                    break
                
                kalan_sorular = [i for i in kalan_sorular if i not in kullanilan_set]
                if kalan_sorular:
                    c.showPage()
                    sayfa_no += 1
            
            if self.cevap_listesi and len(self.cevap_listesi) > 0:
                c.showPage()
                self.create_answer_key_page(c)
                logger.info("Cevap anahtarı sayfası eklendi")
            else:
                logger.info("Cevap anahtarı eklenmedi - liste boş veya istenmiyor")

            c.save()
            logger.info(f"PDF başarıyla kaydedildi: {dosya_yolu}")
            return True

        except Exception as e:
            print(f"❌ PDF KAYDETME HATASI: {e}")
            logger.error(f"PDF kaydetme işleminde kritik hata", exc_info=True)
            return False

    def _create_yazili_layout_simple(self, canvas_obj, gorseller, sayfa_no, page_width, page_height, global_offset):
        """Yazılı için basit layout - sayfa başına maksimum 2 soru"""
        logger.info(f"Yazılı basit layout - Sayfa {sayfa_no}, {len(gorseller)} soru")
        max_soru_sayisi = min(len(gorseller), 2)

        top_margin = page_height * 0.12
        left_margin = page_width * 0.05
        right_margin = page_width * 0.05
        bottom_margin = page_height * 0.08

        usable_width = page_width - left_margin - right_margin
        usable_height = page_height - top_margin - bottom_margin

        soru_area_height = usable_height / max_soru_sayisi
        yerlestirildi_sayisi = 0

        for i in range(max_soru_sayisi):
            if i >= len(gorseller):
                break
            try:
                gorsel_path = gorseller[i]
                soru_start_y = top_margin + i * soru_area_height
                with PILImage.open(gorsel_path) as img:
                    original_width, original_height = img.width, img.height
                    img_ratio = original_width / original_height
                    max_img_width = usable_width * 0.95
                    max_img_height = soru_area_height * 0.8

                    if img_ratio > (max_img_width / max_img_height):
                        final_width = max_img_width
                        final_height = max_img_width / img_ratio
                    else:
                        final_height = max_img_height
                        final_width = max_img_height * img_ratio

                    img_x = left_margin + (usable_width - final_width) / 2
                    img_y = page_height - soru_start_y - final_height - 20
                    canvas_obj.drawImage(gorsel_path, img_x, img_y, width=final_width, height=final_height)

                    soru_no = global_offset + i + 1
                    canvas_obj.setFont("Helvetica-Bold", 16)
                    canvas_obj.setFillColor("#666666")
                    canvas_obj.drawString(left_margin - 10, img_y + final_height - 25, f"{soru_no}.")
                    yerlestirildi_sayisi += 1
                    logger.info(f"✅ Yazılı soru {soru_no} yerleştirildi")
            except Exception as e:
                logger.error(f"❌ Yazılı soru {i+1} yerleştirme hatası", exc_info=True)
        return yerlestirildi_sayisi

    def create_answer_key_page(self, canvas_obj):
        """Cevap anahtari sayfasi olustur - Soru tipine göre farklı düzenler"""
        try:
            logger.info(f"Cevap anahtari sayfasi olusturuluyor ({len(self.cevap_listesi)} cevap) - Tip: {self.soru_tipi}")
            
            if self.soru_tipi.lower() == "yazili":
                self._create_yazili_answer_key(canvas_obj)
            else:
                self._create_test_answer_key(canvas_obj)
                
        except Exception as e:
            logger.error(f"Cevap anahtari olusturma hatasi", exc_info=True)

    def _create_test_answer_key(self, canvas_obj):
        """Test şablonu için 2 sütunlu cevap anahtarı"""
        page_width, page_height = A4
        title_text = "CEVAP ANAHTARI (TEST)"
        row_height = 25
        col1_x_soru, col1_x_cevap = 80, 150
        col2_x_soru, col2_x_cevap = 320, 390
        max_rows_per_col = 22
        per_page = max_rows_per_col * 2
        total_answers = len(self.cevap_listesi)

        for page_start in range(0, total_answers, per_page):
            canvas_obj.setFont("Helvetica-Bold", 18)
            text_width = canvas_obj.stringWidth(title_text, "Helvetica-Bold", 18)
            canvas_obj.drawString((page_width - text_width) / 2, page_height - 100, title_text)
            
            start_y = page_height - 150
            canvas_obj.setFont("Helvetica-Bold", 12)
            canvas_obj.drawString(col1_x_soru, start_y, "Soru No")
            canvas_obj.drawString(col1_x_cevap, start_y, "Cevap")
            canvas_obj.line(col1_x_soru, start_y - 5, col1_x_cevap + 50, start_y - 5)
            canvas_obj.drawString(col2_x_soru, start_y, "Soru No")
            canvas_obj.drawString(col2_x_cevap, start_y, "Cevap")
            canvas_obj.line(col2_x_soru, start_y - 5, col2_x_cevap + 50, start_y - 5)
            canvas_obj.setFont("Helvetica", 10)

            for row in range(max_rows_per_col):
                left_idx = page_start + row
                if left_idx < total_answers:
                    y_pos = start_y - (row + 2) * row_height
                    canvas_obj.drawString(col1_x_soru, y_pos, f"{left_idx + 1}")
                    canvas_obj.drawString(col1_x_cevap, y_pos, str(self.cevap_listesi[left_idx]))
                
                right_idx = page_start + max_rows_per_col + row
                if right_idx < total_answers:
                    y_pos = start_y - (row + 2) * row_height
                    canvas_obj.drawString(col2_x_soru, y_pos, f"{right_idx + 1}")
                    canvas_obj.drawString(col2_x_cevap, y_pos, str(self.cevap_listesi[right_idx]))

            if page_start + per_page < total_answers:
                canvas_obj.showPage()
        logger.info("Test cevap anahtari sayfasi tamamlandi")

    def _create_yazili_answer_key(self, canvas_obj):
        """Yazılı şablonu için tek sütunlu, geniş cevap alanlı cevap anahtarı"""
        page_width, page_height = A4
        title_text = "CEVAP ANAHTARI (YAZILI)"
        row_height = 35  # Yazılı için daha yüksek satır
        soru_x = 80
        cevap_x = 200
        cevap_width = 400  # Geniş cevap alanı
        max_rows_per_page = 20  # Yazılı için daha az satır
        total_answers = len(self.cevap_listesi)

        for page_start in range(0, total_answers, max_rows_per_page):
            canvas_obj.setFont("Helvetica-Bold", 18)
            text_width = canvas_obj.stringWidth(title_text, "Helvetica-Bold", 18)
            canvas_obj.drawString((page_width - text_width) / 2, page_height - 100, title_text)
            
            start_y = page_height - 150
            canvas_obj.setFont("Helvetica-Bold", 12)
            canvas_obj.drawString(soru_x, start_y, "Soru No")
            canvas_obj.drawString(cevap_x, start_y, "Cevap")
            canvas_obj.line(soru_x, start_y - 5, cevap_x + cevap_width, start_y - 5)
            canvas_obj.setFont("Helvetica", 10)

            for row in range(max_rows_per_page):
                idx = page_start + row
                if idx < total_answers:
                    y_pos = start_y - (row + 2) * row_height
                    canvas_obj.drawString(soru_x, y_pos, f"{idx + 1}.")
                    
                    # Cevabı geniş alanda göster, uzun cevaplar için satır kaydırma
                    cevap_text = str(self.cevap_listesi[idx])
                    if len(cevap_text) > 50:  # Uzun cevap kontrolü
                        # Uzun cevapları satırlara böl
                        words = cevap_text.split()
                        lines = []
                        current_line = ""
                        for word in words:
                            if len(current_line + " " + word) <= 50:
                                current_line += (" " + word) if current_line else word
                            else:
                                if current_line:
                                    lines.append(current_line)
                                current_line = word
                        if current_line:
                            lines.append(current_line)
                        
                        # İlk satırı çiz
                        canvas_obj.drawString(cevap_x, y_pos, lines[0])
                        # Diğer satırları alt alta çiz
                        for i, line in enumerate(lines[1:], 1):
                            if y_pos - (i * 12) > 50:  # Sayfa altına taşmaması için
                                canvas_obj.drawString(cevap_x, y_pos - (i * 12), line)
                    else:
                        canvas_obj.drawString(cevap_x, y_pos, cevap_text)

            if page_start + max_rows_per_page < total_answers:
                canvas_obj.showPage()
        logger.info("Yazılı cevap anahtari sayfasi tamamlandi")

    def _basit_pdf_olustur(self, dosya_yolu):
        """Sablon bulunamazsa basit PDF olustur"""
        try:
            logger.info("Basit PDF olusturma moduna gecildi")
            story, styles = [], getSampleStyleSheet()
            
            if self.baslik_metni:
                story.append(Paragraph(self.baslik_metni, styles["Title"]))
                story.append(Spacer(1, 0.5*inch))
            
            for i, gorsel_yolu in enumerate(self.gorsel_listesi):
                try:
                    story.append(Image(gorsel_yolu, width=6*inch, height=4*inch))
                    if i < len(self.cevap_listesi):
                        story.append(Paragraph(f"Cevap: {self.cevap_listesi[i]}", styles["Normal"]))
                    story.append(Spacer(1, 0.3*inch))
                except Exception as e:
                    logger.error(f"Basit PDF - Gorsel {i+1} ekleme hatasi: {gorsel_yolu}", exc_info=True)
            
            if self.cevap_listesi:
                story.append(Spacer(1, 0.5*inch))
                story.append(Paragraph("CEVAP ANAHTARI", styles["Heading1"]))
                story.append(Spacer(1, 0.2*inch))
                
                data = [[f"{i}. Soru", cevap] for i, cevap in enumerate(self.cevap_listesi, 1)]
                
                tablo = Table(data, colWidths=[1*inch, 1*inch])
                tablo.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white), ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12), ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(tablo)
            
            doc = SimpleDocTemplate(dosya_yolu, pagesize=A4)
            doc.build(story)
            logger.info("Basit PDF basariyla olusturuldu")
            return True
        except Exception as e:
            logger.error(f"Basit PDF olusturma hatasi", exc_info=True)
            return False