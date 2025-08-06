from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
import os
import json

class PDFCreator:
    def __init__(self):
        self.story = []
        self.styles = getSampleStyleSheet()
    
    def baslik_ekle(self, baslik):
        """PDF'e başlık ekle"""
        p = Paragraph(baslik, self.styles["Title"])
        self.story.append(p)
        self.story.append(Spacer(1, 0.5*inch))
    
    def gorsel_ekle(self, gorsel_yolu, cevap=None):
        """PDF'e görsel ve cevap bilgisini ekle"""
        try:
            # Görsel boyutlarını ayarla
            img = Image(gorsel_yolu, width=6*inch, height=4*inch)
            self.story.append(img)
            
            # Cevap bilgisini ekle
            if cevap:
                cevap_stili = self.styles["Normal"]
                cevap_stili.alignment = 1  # Ortalama
                cevap_paragraf = Paragraph(f"Cevap: {cevap}", cevap_stili)
                self.story.append(cevap_paragraf)
                
            self.story.append(Spacer(1, 0.3*inch))
        except Exception as e:
            print(f"Görsel ekleme hatası: {e}")
    
    def cevap_anahtari_ekle(self, cevaplar):
        """PDF'in sonuna cevap anahtarı ekle"""
        self.story.append(Spacer(1, 0.5*inch))
        self.story.append(Paragraph("CEVAP ANAHTARI", self.styles["Heading1"]))
        self.story.append(Spacer(1, 0.2*inch))
        
        # Cevapları tablo formatında göster
        data = []
        for i, cevap in enumerate(cevaplar, 1):
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
        
        self.story.append(tablo)
    
    def kaydet(self, dosya_yolu):
        """PDF'i kaydet"""
        try:
            doc = SimpleDocTemplate(dosya_yolu, pagesize=letter)
            doc.build(self.story)
            return True
        except Exception as e:
            print(f"PDF kaydetme hatası: {e}")
            return False