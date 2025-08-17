import os
from PIL import Image, ImageDraw, ImageFont
import sys

def gorsel_buyut_test():
    """
    Template ve görsel alıp, görseli farklı boyutlarda test eden script
    """
    print("🔍 GÖRSEL BÜYÜTME TEST SCRİPTİ")
    print("=" * 50)
    
    # Dosya yollarını al
    template_path = "./templates/template.png"
    gorsel_path = "./17.png"
    
    # Dosyaları kontrol et
    if not os.path.exists(template_path):
        print(f"❌ Template bulunamadı: {template_path}")
        return
    
    if not os.path.exists(gorsel_path):
        print(f"❌ Görsel bulunamadı: {gorsel_path}")
        return
    
    try:
        # Template ve görseli aç
        template = Image.open(template_path).convert("RGB")
        gorsel = Image.open(gorsel_path).convert("RGB")
        
        print(f"✅ Template yüklendi: {template.size}")
        print(f"✅ Görsel yüklendi: {gorsel.size}")
        
        # Orijinal görsel bilgileri
        original_width, original_height = gorsel.size
        img_ratio = original_width / original_height
        aspect_ratio = original_height / original_width
        
        print(f"\n📊 GÖRSEL BİLGİLERİ:")
        print(f"   Orijinal boyut: {original_width}x{original_height}")
        print(f"   En/Boy oranı: {img_ratio:.3f}")
        print(f"   Boy/En oranı: {aspect_ratio:.3f}")
        
        # Soru tipi belirle
        if aspect_ratio >= 1.4:
            soru_tipi = "UZUN"
        elif aspect_ratio <= 0.8:
            soru_tipi = "KISA"
        else:
            soru_tipi = "ORTA"
        
        print(f"   Soru tipi: {soru_tipi}")
        
        # Kutucuk boyutları (template'e göre ayarla)
        template_width, template_height = template.size
        box_width = 258  # Sabit kutucuk genişliği
        box_height = 170  # Sabit kutucuk yüksekliği
        
        print(f"\n📦 KUTUCUK BİLGİLERİ:")
        print(f"   Kutucuk boyutu: {box_width}x{box_height}")
        print(f"   Kutucuk alanı: {box_width * box_height} px²")
        
        # Farklı büyütme yöntemlerini test et
        test_yontemleri = [
            ("Mevcut Yöntem", test_mevcut_yontem),
            ("Genişlik Odaklı", test_genislik_odakli),
            ("Zorla %90 Genişlik", test_zorla_90),
            ("Manuel Büyütme", test_manuel_buyutme)
        ]
        
        results = []
        
        for yontem_adi, yontem_func in test_yontemleri:
            print(f"\n🧪 TEST: {yontem_adi}")
            print("-" * 30)
            
            try:
                result = yontem_func(gorsel, box_width, box_height, img_ratio, aspect_ratio, soru_tipi)
                results.append((yontem_adi, result))
                
                final_width, final_height = result
                genislik_kaplama = (final_width / box_width) * 100
                yukseklik_kaplama = (final_height / box_height) * 100
                alan_kaplama = ((final_width * final_height) / (box_width * box_height)) * 100
                
                print(f"   📏 Sonuç boyut: {final_width:.0f}x{final_height:.0f}")
                print(f"   📊 Genişlik kaplama: %{genislik_kaplama:.1f}")
                print(f"   📊 Yükseklik kaplama: %{yukseklik_kaplama:.1f}")
                print(f"   📊 Alan kaplama: %{alan_kaplama:.1f}")
                
                if genislik_kaplama >= 80:
                    print("   ✅ GENİŞLİK BAŞARILI!")
                else:
                    print("   ❌ Genişlik yetersiz")
                    
            except Exception as e:
                print(f"   ❌ Hata: {e}")
                results.append((yontem_adi, None))
        
        # Özet rapor
        print(f"\n📋 ÖZET RAPOR:")
        print("=" * 50)
        for yontem_adi, result in results:
            if result:
                final_width, final_height = result
                genislik_kaplama = (final_width / box_width) * 100
                status = "✅ BAŞARILI" if genislik_kaplama >= 80 else "❌ Yetersiz"
                print(f"{yontem_adi:20}: {final_width:.0f}x{final_height:.0f} (%{genislik_kaplama:.1f}) {status}")
            else:
                print(f"{yontem_adi:20}: HATA")
        
        # En iyi sonucu template üzerinde göster
        en_iyi = max([r for r in results if r[1]], key=lambda x: (x[1][0] / box_width) * 100)
        print(f"\n🏆 EN İYİ SONUÇ: {en_iyi[0]}")
        
        # Test görselini oluştur
        test_gorseli_olustur(template, gorsel, results, box_width, box_height, soru_tipi)
        
    except Exception as e:
        print(f"❌ Genel hata: {e}")

def test_mevcut_yontem(gorsel, box_width, box_height, img_ratio, aspect_ratio, soru_tipi):
    """Mevcut proje algoritması"""
    if soru_tipi == "UZUN":
        max_img_width = box_width * 0.98
        max_img_height = box_height * 0.95
        buyutme_carpani = 1.10
    else:
        max_img_width = box_width * 0.95
        max_img_height = box_height * 0.85
        buyutme_carpani = 1.0
    
    # Boyutlandırma
    if img_ratio > (max_img_width / max_img_height):
        final_width = max_img_width
        final_height = max_img_width / img_ratio
    else:
        final_height = max_img_height
        final_width = max_img_height * img_ratio
    
    # Büyütme
    if buyutme_carpani > 1.0:
        final_width *= buyutme_carpani
        final_height *= buyutme_carpani
        
        # Sınır kontrolü
        if final_width > box_width:
            final_width = box_width
            final_height = box_width / img_ratio
        if final_height > box_height:
            final_height = box_height
            final_width = box_height * img_ratio
    
    return final_width, final_height

def test_genislik_odakli(gorsel, box_width, box_height, img_ratio, aspect_ratio, soru_tipi):
    """Genişlik odaklı yaklaşım"""
    if soru_tipi == "UZUN":
        # Önce genişliği maksimuma getir
        final_width = box_width * 0.90  # %90 genişlik
        final_height = final_width / img_ratio
        
        # Yükseklik kontrolü
        if final_height > box_height * 0.95:
            final_height = box_height * 0.95
            final_width = final_height * img_ratio
    else:
        # Kısa sorular için normal
        final_width = box_width * 0.95
        final_height = final_width / img_ratio
        if final_height > box_height * 0.85:
            final_height = box_height * 0.85
            final_width = final_height * img_ratio
    
    return final_width, final_height

def test_zorla_90(gorsel, box_width, box_height, img_ratio, aspect_ratio, soru_tipi):
    """Zorla %90 genişlik"""
    if soru_tipi == "UZUN":
        final_width = box_width * 0.90  # Zorla %90
        final_height = final_width * aspect_ratio  # Doğru oran kullan
        
        # Yükseklik taşarsa küçült
        if final_height > box_height * 0.95:
            final_height = box_height * 0.95
            final_width = final_height / aspect_ratio
    else:
        return test_genislik_odakli(gorsel, box_width, box_height, img_ratio, aspect_ratio, soru_tipi)
    
    return final_width, final_height

def test_manuel_buyutme(gorsel, box_width, box_height, img_ratio, aspect_ratio, soru_tipi):
    """Manuel büyütme - En agresif"""
    if soru_tipi == "UZUN":
        # Direkt %95 genişlik ver
        final_width = box_width * 0.95
        final_height = box_height * 0.95
        
        # En-boy oranını kontrol et, gerekirse küçült
        if final_height / final_width > aspect_ratio:
            final_height = final_width * aspect_ratio
        else:
            final_width = final_height / aspect_ratio
    else:
        final_width = box_width * 0.95
        final_height = final_width / img_ratio
        if final_height > box_height * 0.85:
            final_height = box_height * 0.85
            final_width = final_height * img_ratio
    
    return final_width, final_height

def test_gorseli_olustur(template, gorsel, results, box_width, box_height, soru_tipi):
    """Test sonuçlarını gösteren görsel oluştur"""
    try:
        # Template kopyala
        test_template = template.copy()
        draw = ImageDraw.Draw(test_template)
        
        # Font yükle
        try:
            font = ImageFont.truetype("arial.ttf", 16)
            small_font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Test alanları - 2x2 grid
        positions = [
            (50, 100),    # Sol üst
            (350, 100),   # Sağ üst  
            (50, 400),    # Sol alt
            (350, 400)    # Sağ alt
        ]
        
        # Her test sonucunu göster
        for i, (yontem_adi, result) in enumerate(results[:4]):
            if result is None:
                continue
                
            x, y = positions[i]
            final_width, final_height = result
            
            # Kutucuk çerçevesi çiz
            draw.rectangle([x, y, x + box_width, y + box_height], outline="red", width=2)
            
            # Görseli boyutlandır ve yerleştir
            test_gorsel = gorsel.copy()
            test_gorsel = test_gorsel.resize((int(final_width), int(final_height)), Image.Resampling.LANCZOS)
            
            # Görseli ortala
            paste_x = x + (box_width - final_width) // 2
            paste_y = y + (box_height - final_height) // 2
            test_template.paste(test_gorsel, (int(paste_x), int(paste_y)))
            
            # Bilgileri yaz
            genislik_kaplama = (final_width / box_width) * 100
            draw.text((x, y - 40), yontem_adi, fill="black", font=font)
            draw.text((x, y - 20), f"{final_width:.0f}x{final_height:.0f} (%{genislik_kaplama:.1f})", 
                     fill="blue", font=small_font)
        
        # Başlık ekle
        draw.text((50, 20), f"GÖRSEL BÜYÜTME TESTİ - {soru_tipi} SORU", fill="black", font=font)
        draw.text((50, 45), f"Kutucuk: {box_width}x{box_height}", fill="gray", font=small_font)
        
        # Kaydet
        output_path = "gorsel_buyutme_test.png"
        test_template.save(output_path)
        print(f"\n💾 Test görseli kaydedildi: {output_path}")
        
    except Exception as e:
        print(f"❌ Test görseli oluşturma hatası: {e}")

if __name__ == "__main__":
    gorsel_buyut_test()