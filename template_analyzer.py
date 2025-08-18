import os
from PIL import Image as PILImage
import numpy as np
from reportlab.lib.pagesizes import A4

# PDF'i PNG'ye çevirmek için PyMuPDF kullanacağız
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("⚠️ PyMuPDF yüklü değil. Yüklemek için: pip install PyMuPDF")

def pdf_to_png_and_analyze(pdf_path, page_number=0):
    """PDF'den belirtilen sayfayı PNG'ye çevir ve analiz et"""
    
    if not PYMUPDF_AVAILABLE:
        print("❌ PyMuPDF gerekli. Yüklemek için: pip install PyMuPDF")
        return False
    
    debug_file = "pdf_analiz_debug.txt"
    
    with open(debug_file, 'w', encoding='utf-8') as f:
        f.write("=== PDF ANALİZ DEBUG ===\n\n")
    
    def log_pdf(msg):
        print(msg)
        with open(debug_file, 'a', encoding='utf-8') as f:
            f.write(msg + '\n')
    
    try:
        log_pdf(f"🔍 PDF analizi: {os.path.basename(pdf_path)}")
        log_pdf(f"📄 Sayfa: {page_number + 1}")
        
        # PDF'i aç
        doc = fitz.open(pdf_path)
        
        if page_number >= len(doc):
            log_pdf(f"❌ Sayfa {page_number + 1} bulunamadı. Toplam sayfa: {len(doc)}")
            return False
        
        log_pdf(f"📚 Toplam sayfa sayısı: {len(doc)}")
        
        # Belirtilen sayfayı al
        page = doc[page_number]
        
        # Sayfa boyutları
        rect = page.rect
        log_pdf(f"📏 PDF sayfa boyutu: {rect.width:.1f} x {rect.height:.1f} points")
        
        # PNG'ye çevir - yüksek çözünürlük
        zoom = 2  # 2x zoom = daha net görüntü
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        # PNG olarak kaydet
        png_path = pdf_path.replace('.pdf', f'_sayfa_{page_number + 1}.png')
        pix.save(png_path)
        
        log_pdf(f"✅ PNG kaydedildi: {os.path.basename(png_path)}")
        log_pdf(f"🖼️ PNG boyutu: {pix.width} x {pix.height} pixels")
        
        doc.close()
        
        # Şimdi PNG'yi analiz et
        log_pdf(f"\n🔍 PNG ANALİZİ BAŞLIYOR...")
        analyze_png_margins(png_path, log_pdf)
        
        return png_path
        
    except Exception as e:
        log_pdf(f"❌ PDF analiz hatası: {e}")
        import traceback
        log_pdf(f"Detay: {traceback.format_exc()}")
        return False

def analyze_png_margins(png_path, log_func):
    """PNG dosyasından margin'leri analiz et"""
    
    try:
        with PILImage.open(png_path) as img:
            width, height = img.size
            log_func(f"📏 PNG boyutu: {width}x{height} pixels")
            
            # RGB'ye çevir
            rgb_img = img.convert('RGB')
            img_array = np.array(rgb_img)
            
            # En yaygın renk (arka plan)
            pixels = img_array.reshape(-1, 3)
            from collections import Counter
            color_counts = Counter([tuple(pixel) for pixel in pixels])
            top_colors = color_counts.most_common(3)
            
            log_func(f"🎨 En yaygın renkler:")
            for i, (color, count) in enumerate(top_colors):
                percentage = (count / len(pixels)) * 100
                log_func(f"   {i+1}. RGB{color} - %{percentage:.1f}")
            
            # Arka plan rengi (en yaygın)
            bg_color = top_colors[0][0]
            
            # MARGIN ANALİZİ - GERÇEK KULLANILABILIR ALANI BULMA
            log_func(f"\n📐 MARGIN ANALİZİ:")
            
            # ÜST MARGIN - içerik başladığı yeri bul
            ust_margin_pixel = 0
            for y in range(height):
                row = img_array[y]
                # Bu satırda çok fazla farklı renk var mı? (içerik başladı)
                unique_colors = len(set(tuple(pixel) for pixel in row))
                
                if unique_colors > 10:  # İçerik başladı
                    ust_margin_pixel = y
                    log_func(f"   🔍 İçerik başlangıcı: {y}. satır ({unique_colors} farklı renk)")
                    break
                elif y < 50:  # İlk 50 satırı detayını göster
                    log_func(f"   Satır {y}: {unique_colors} farklı renk")
            
            # ALT MARGIN - aşağıdan yukarı tara
            alt_margin_pixel = 0
            for y in range(height-1, -1, -1):
                row = img_array[y]
                unique_colors = len(set(tuple(pixel) for pixel in row))
                
                if unique_colors > 10:  # İçerik var
                    alt_margin_pixel = height - y
                    log_func(f"   🔍 İçerik sonu: {y}. satır")
                    break
            
            # SOL MARGIN
            sol_margin_pixel = 0
            for x in range(width):
                column = img_array[:, x]
                unique_colors = len(set(tuple(pixel) for pixel in column))
                
                if unique_colors > 10:
                    sol_margin_pixel = x
                    break
            
            # SAĞ MARGIN
            sag_margin_pixel = 0
            for x in range(width-1, -1, -1):
                column = img_array[:, x]
                unique_colors = len(set(tuple(pixel) for pixel in column))
                
                if unique_colors > 10:
                    sag_margin_pixel = width - x
                    break
            
            log_func(f"📏 PIXEL CİNSİNDEN MARGİNLER:")
            log_func(f"   Üst: {ust_margin_pixel} px")
            log_func(f"   Alt: {alt_margin_pixel} px")
            log_func(f"   Sol: {sol_margin_pixel} px")
            log_func(f"   Sağ: {sag_margin_pixel} px")
            
            # KULLANILABILIR ALAN
            kullanilabilir_width_px = width - sol_margin_pixel - sag_margin_pixel
            kullanilabilir_height_px = height - ust_margin_pixel - alt_margin_pixel
            
            log_func(f"📊 KULLANILABILIR ALAN (PIXEL):")
            log_func(f"   Genişlik: {kullanilabilir_width_px} px")
            log_func(f"   Yükseklik: {kullanilabilir_height_px} px")
            
            # POINT'E ÇEVİRME (A4 referansı)
            a4_width, a4_height = A4
            
            # PNG'nin zoom faktörünü hesapla (2x zoom kullanmıştık)
            zoom_factor = 2
            actual_pdf_width = width / zoom_factor
            actual_pdf_height = height / zoom_factor
            
            pixel_to_point_x = a4_width / actual_pdf_width
            pixel_to_point_y = a4_height / actual_pdf_height
            
            ust_margin_point = (ust_margin_pixel / zoom_factor) * pixel_to_point_y
            alt_margin_point = (alt_margin_pixel / zoom_factor) * pixel_to_point_y
            sol_margin_point = (sol_margin_pixel / zoom_factor) * pixel_to_point_x
            sag_margin_point = (sag_margin_pixel / zoom_factor) * pixel_to_point_x
            
            kullanilabilir_width_point = (kullanilabilir_width_px / zoom_factor) * pixel_to_point_x
            kullanilabilir_height_point = (kullanilabilir_height_px / zoom_factor) * pixel_to_point_y
            
            log_func(f"\n📐 POINT CİNSİNDEN MARGİNLER:")
            log_func(f"   Üst: {ust_margin_point:.1f} points")
            log_func(f"   Alt: {alt_margin_point:.1f} points")
            log_func(f"   Sol: {sol_margin_point:.1f} points")
            log_func(f"   Sağ: {sag_margin_point:.1f} points")
            
            log_func(f"📊 KULLANILABILIR ALAN (POINT):")
            log_func(f"   Genişlik: {kullanilabilir_width_point:.1f} points")
            log_func(f"   Yükseklik: {kullanilabilir_height_point:.1f} points")
            
            # MEVCUT KOD İLE KARŞILAŞTIRMA
            log_func(f"\n⚖️ MEVCUT KOD İLE KARŞILAŞTIRMA:")
            
            mevcut_config = {
                'top_margin': 50,
                'bottom_margin': 5,
                'left_margin': 25,
                'right_margin': 25
            }
            
            mevcut_usable_height = a4_height - mevcut_config['top_margin'] - mevcut_config['bottom_margin']
            
            log_func(f"🔴 Mevcut kod kullanılabilir yükseklik: {mevcut_usable_height:.1f} points")
            log_func(f"🔵 Gerçek kullanılabilir yükseklik: {kullanilabilir_height_point:.1f} points")
            log_func(f"📊 Fark: {kullanilabilir_height_point - mevcut_usable_height:+.1f} points")
            
            # ÖNERİLEN YENİ CONFIG
            log_func(f"\n🎯 ÖNERİLEN GERÇEK CONFIG:")
            log_func(f"template_config = {{")
            log_func(f"    'top_margin': {int(ust_margin_point)},")
            log_func(f"    'bottom_margin': {int(alt_margin_point)},")
            log_func(f"    'left_margin': {int(sol_margin_point)},")
            log_func(f"    'right_margin': {int(sag_margin_point)},")
            log_func(f"    'col_gap': 30,")
            log_func(f"    'cols': 2")
            log_func(f"}}")
            
            return {
                'margins_point': {
                    'top': int(ust_margin_point),
                    'bottom': int(alt_margin_point),
                    'left': int(sol_margin_point),
                    'right': int(sag_margin_point)
                },
                'usable_area_point': {
                    'width': kullanilabilir_width_point,
                    'height': kullanilabilir_height_point
                }
            }
            
    except Exception as e:
        log_func(f"❌ PNG analiz hatası: {e}")
        return None

# KULLANIM
def analyze_completed_pdf(pdf_path, page_number=0):
    """Tamamlanmış PDF'i analiz et"""
    print(f"🚀 PDF analizi başlıyor: {os.path.basename(pdf_path)}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF bulunamadı: {pdf_path}")
        return None
    
    result = pdf_to_png_and_analyze(pdf_path, page_number)
    
    if result:
        print(f"✅ Analiz tamamlandı! Sonuçlar: pdf_analiz_debug.txt")
        print(f"🖼️ PNG dosyası: {result}")
    else:
        print("❌ Analiz başarısız")
    
    return result

# ÇALIŞTI RMAK İÇIN
if __name__ == "__main__":
    # Senin PDF'in
    pdf_path = "./test_results/test_test_10___ekstrem_uzun.pdf"
    analyze_completed_pdf(pdf_path, page_number=0)  # İlk sayfa