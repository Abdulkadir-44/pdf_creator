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

class PDFCreator:
    def __init__(self):
        self.gorsel_listesi = []
        self.baslik_metni = ""
        self.cevap_listesi = []
    
    def baslik_ekle(self, baslik):
        """PDF başlığını ayarla"""
        self.baslik_metni = baslik
    
    def gorsel_ekle(self, gorsel_yolu, cevap=None):
        """Görsel listesine ekle"""
        self.gorsel_listesi.append(gorsel_yolu)
        if cevap:
            self.cevap_listesi.append(cevap)
    
    def cevap_anahtari_ekle(self, cevaplar):
        """Cevap listesini ayarla"""
        self.cevap_listesi = cevaplar
    
    def create_template_page(self, canvas_obj, gorseller, sayfa_no, template_path):
        """Şablonu kullanarak bir sayfa oluştur"""
        try:
            # Şablon boyutları (1414x2000 -> A4'e dönüştür)
            page_width, page_height = A4
            
            # Şablonu arka plan olarak ekle
            if os.path.exists(template_path):
                canvas_obj.drawImage(template_path, 0, 0, width=page_width, height=page_height)
            
            # 2x4 grid koordinatları (A4 boyutuna göre ayarlanmış)
            top_margin = page_height * 0.1  # %15 üst margin
            left_margin = page_width * 0.05   # %5 sol margin
            right_margin = page_width * 0.01  # %5 sağ margin
            bottom_margin = page_height * 0.1 # %10 alt margin
            
            # Kullanılabilir alan
            usable_width = page_width - left_margin - right_margin
            usable_height = page_height - top_margin - bottom_margin
            
            # Her soru için alan
            soru_width = usable_width / 2 - 10  # 10pt gap
            soru_height = usable_height / 4 - 40 # 15pt gap
            
            # Görselleri yerleştir
            for i, gorsel_path in enumerate(gorseller):
                if i >= 8:  # Sayfa başına maksimum 8 soru
                    break
                
                try:
                    # Grid pozisyonu
                    row = i % 4
                    col = i // 4
                    
                    # Koordinatları hesapla (Y koordinatı ters çevrilmeli - PDF koordinat sistemi)
                    x = left_margin + col * (soru_width + 10)
                    y = page_height - top_margin - (row + 1) * (soru_height + 15)
                    
                    # PIL ile görseli yükle ve boyutlandır
                    with PILImage.open(gorsel_path) as img:
                        # Aspect ratio koruyarak boyutlandır
                        img_ratio = img.width / img.height
                        target_ratio = soru_width / soru_height
                        
                        if img_ratio > target_ratio:
                            # Görsel daha geniş, genişliğe göre boyutlandır
                            new_width = soru_width
                            new_height = soru_width / img_ratio
                        else:
                            # Görsel daha uzun, yüksekliğe göre boyutlandır
                            new_height = soru_height
                            new_width = soru_height * img_ratio
                        
                        # Görseli ortalamak için offset hesapla
                        x_offset = (soru_width - new_width) / 2
                        y_offset = (soru_height - new_height) / 2
                        
                        # Görseli çiz
                        canvas_obj.drawImage(
                            gorsel_path,
                            x + x_offset,
                            y + y_offset,
                            width=new_width,
                            height=new_height
                        )
                        
                        # Soru numarası ekle
                        soru_no = (sayfa_no - 1) * 8 + i + 1
                        # Arka plan daire çiz (sarı/turuncu)
                        # canvas_obj.setFillColor(colors.orange)
                        # canvas_obj.circle(x - 5, y + soru_height - 5, 6, fill=1)

                        # Numarayı beyaz renkle dairenin içine yaz
                        canvas_obj.setFillColor(colors.black)
                        canvas_obj.setFont("Helvetica-Bold", 10)
                        num_text = str(soru_no)
                        text_width = canvas_obj.stringWidth(num_text, "Helvetica-Bold", 10)
                        canvas_obj.drawString(x - 5 - text_width/2, y + soru_height - 10, num_text)

                        # Rengi geri siyaha çevir
                        canvas_obj.setFillColor(colors.black)
                
                except Exception as e:
                    print(f"Soru {i+1} ekleme hatası: {e}")
                    
        except Exception as e:
            print(f"Sayfa oluşturma hatası: {e}")
    
    def create_answer_key_page(self, canvas_obj):
        """Cevap anahtarı sayfası oluştur"""
        try:
            page_width, page_height = A4
            
            # Başlık
            canvas_obj.setFont("Helvetica-Bold", 18)
            title_text = "CEVAP ANAHTARI"
            text_width = canvas_obj.stringWidth(title_text, "Helvetica-Bold", 18)
            canvas_obj.drawString((page_width - text_width) / 2, page_height - 100, title_text)
            
            # Cevapları tabloda göster
            start_y = page_height - 150
            col_width = 120
            row_height = 25
            
            # Başlık satırı
            canvas_obj.setFont("Helvetica-Bold", 12)
            canvas_obj.drawString(100, start_y, "Soru No")
            canvas_obj.drawString(200, start_y, "Cevap")
            
            # Çizgi çek (başlık altı)
            canvas_obj.line(100, start_y - 5, 300, start_y - 5)
            
            # Cevapları yazdır
            canvas_obj.setFont("Helvetica", 10)
            for i, cevap in enumerate(self.cevap_listesi):
                y_pos = start_y - (i + 2) * row_height  # +2 çünkü başlık satırı var
                if y_pos < 100:  # Sayfa sonu kontrolü
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
                
        except Exception as e:
            print(f"Cevap anahtarı oluşturma hatası: {e}")
    
    def kaydet(self, dosya_yolu):
        """Şablonu kullanarak PDF kaydet"""
        try:
            # Şablon yolunu belirle
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            template_path = os.path.join(current_dir, "templates", "template.png")
            
            if not os.path.exists(template_path):
                print("Şablon bulunamadı, basit PDF oluşturuluyor...")
                return self._basit_pdf_olustur(dosya_yolu)
            
            # Canvas oluştur
            c = canvas.Canvas(dosya_yolu, pagesize=A4)
            
            # Sayfa başına 8 soru
            sorular_per_sayfa = 8
            toplam_sayfa = math.ceil(len(self.gorsel_listesi) / sorular_per_sayfa)
            
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
            return True
            
        except Exception as e:
            print(f"PDF kaydetme hatası: {e}")
            return False
    
    def _basit_pdf_olustur(self, dosya_yolu):
        """Şablon bulunamazsa basit PDF oluştur"""
        try:
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
                    print(f"Görsel {i+1} ekleme hatası: {e}")
            
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
            return True
            
        except Exception as e:
            print(f"Basit PDF oluşturma hatası: {e}")
            return False