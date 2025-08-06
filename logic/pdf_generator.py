from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import os

class PDFCreator:
    def __init__(self):
        self.story = []
        self.styles = getSampleStyleSheet()
    
    def baslik_ekle(self, baslik):
        """PDF'e başlık ekle"""
        p = Paragraph(baslik, self.styles["Title"])
        self.story.append(p)
        self.story.append(Spacer(1, 0.5*inch))
    
    def gorsel_ekle(self, gorsel_yolu):
        """PDF'e görsel ekle"""
        try:
            # Görsel boyutlarını ayarla
            img = Image(gorsel_yolu, width=6*inch, height=4*inch)
            self.story.append(img)
            self.story.append(Spacer(1, 0.3*inch))
        except Exception as e:
            print(f"Görsel ekleme hatası: {e}")
    
    def kaydet(self, dosya_yolu):
        """PDF'i kaydet"""
        try:
            doc = SimpleDocTemplate(dosya_yolu, pagesize=letter)
            doc.build(self.story)
            return True
        except Exception as e:
            print(f"PDF kaydetme hatası: {e}")
            return False