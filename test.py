import random
import os
import time
from datetime import datetime

class PDFTestSuite:
    def __init__(self, pdf_creator, soru_klasoru):
        self.pdf_creator = pdf_creator
        self.soru_klasoru = soru_klasoru
        self.tum_sorular = self._load_all_sorular()
        self.test_results = []
        
    def _load_all_sorular(self):
        """Klasörden tüm soruları yükle"""
        try:
            dosyalar = [f for f in os.listdir(self.soru_klasoru) 
                       if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            soru_paths = [os.path.join(self.soru_klasoru, f) for f in dosyalar]
            print(f"📁 {len(soru_paths)} soru yüklendi")
            return soru_paths
        except Exception as e:
            print(f"❌ Soru yükleme hatası: {e}")
            return []
    
    def _analyze_soru_sizes(self):
        """Soruları boyutlarına göre kategorize et"""
        from PIL import Image as PILImage
        
        uzun_sorular = []
        orta_sorular = []
        kisa_sorular = []
        
        for soru_path in self.tum_sorular:
            try:
                with PILImage.open(soru_path) as img:
                    ratio = img.width / img.height
                    # Tahmini yükseklik (sütun genişliği 283px varsayımı)
                    tahmini_height = 283 * 0.98 / ratio
                    
                    if tahmini_height > 300:
                        uzun_sorular.append(soru_path)
                    elif tahmini_height > 180:
                        orta_sorular.append(soru_path)
                    else:
                        kisa_sorular.append(soru_path)
            except Exception as e:
                print(f"⚠️ {os.path.basename(soru_path)} analiz edilemedi: {e}")
                orta_sorular.append(soru_path)  # Fallback
        
        print(f"📊 Soru analizi: {len(uzun_sorular)} uzun, {len(orta_sorular)} orta, {len(kisa_sorular)} kısa")
        return uzun_sorular, orta_sorular, kisa_sorular
    
    def _create_test_pdf(self, test_name, sorular, soru_tipi="test"):
        """Test PDF'i oluştur - DETAYLI LOG İLE"""
        try:
            print(f"\n🔧 {test_name} başlatılıyor...")
            
            # PDF creator'ı temizle
            self.pdf_creator.gorsel_listesi = []
            self.pdf_creator.cevap_listesi = []
            self.pdf_creator.soru_tipi = soru_tipi
            
            # Başlık ekle
            self.pdf_creator.baslik_ekle(f"Test: {test_name}")
            
            # Soruları ekle
            for i, soru_path in enumerate(sorular):
                self.pdf_creator.gorsel_ekle(soru_path)
                print(f"  📎 Soru {i+1}: {os.path.basename(soru_path)}")
            
            # PDF'i kaydet
            output_path = f"test_results/test_{test_name.lower().replace(' ', '_').replace('-', '_')}.pdf"
            os.makedirs("test_results", exist_ok=True)
            
            print(f"  💾 PDF kaydediliyor: {output_path}")
            
            start_time = time.time()
            success = self.pdf_creator.kaydet(output_path)
            end_time = time.time()
            
            if success:
                print(f"  ✅ BAŞARILI - {end_time - start_time:.2f}s")
            else:
                print(f"  ❌ BAŞARISIZ")
            
            return {
                'success': success,
                'output_path': output_path,
                'duration': end_time - start_time,
                'soru_count': len(sorular)
            }
            
        except Exception as e:
            print(f"❌ Test {test_name} hatası: {e}")
            return {
                'success': False,
                'error': str(e),
                'soru_count': len(sorular)
            }
    
    def run_all_tests(self):
        """Sadece kritik testleri çalıştır - PROBLEM TESPİTİ İÇİN"""
        print("🎯 KRİTİK TEST SETİ - PROBLEM TESPİTİ")
        print("=" * 50)
        
        # Soruları analiz et
        uzun_sorular, orta_sorular, kisa_sorular = self._analyze_soru_sizes()
        
        # Kritik test senaryoları
        critical_tests = test_cases = [
            {
                "name": "Test 1 - Az Soru",
                "description": "5 rastgele soru ile temel test",
                "sorular": random.sample(self.tum_sorular, min(5, len(self.tum_sorular))),
                "soru_tipi": "test"
            },
            {
                "name": "Test 2 - Tam Sayfa",
                "description": "8 soru ile tek sayfa doldurma",
                "sorular": random.sample(self.tum_sorular, min(8, len(self.tum_sorular))),
                "soru_tipi": "test"
            },
            {
                "name": "Test 3 - Çok Soru",
                "description": "15 soru ile çoklu sayfa testi",
                "sorular": random.sample(self.tum_sorular, min(15, len(self.tum_sorular))),
                "soru_tipi": "test"
            },
            {
                "name": "Test 4 - Maksimum",
                "description": "Tüm sorular (18 soru)",
                "sorular": self.tum_sorular.copy(),
                "soru_tipi": "test"
            },
            {
                "name": "Test 5 - Sadece Uzun",
                "description": "Sadece uzun sorular",
                "sorular": uzun_sorular[:min(8, len(uzun_sorular))],
                "soru_tipi": "test"
            },
            {
                "name": "Test 6 - Sadece Kısa",
                "description": "Sadece kısa sorular",
                "sorular": kisa_sorular[:min(10, len(kisa_sorular))],
                "soru_tipi": "test"
            },
            {
                "name": "Test 7 - Uzun Ağırlıklı",
                "description": "6 uzun + 2 kısa soru karışımı",
                "sorular": uzun_sorular[:min(6, len(uzun_sorular))] + kisa_sorular[:min(2, len(kisa_sorular))],
                "soru_tipi": "test"
            },
            {
                "name": "Test 8 - Kısa Ağırlıklı",
                "description": "6 kısa + 2 uzun soru karışımı",
                "sorular": kisa_sorular[:min(6, len(kisa_sorular))] + uzun_sorular[:min(2, len(uzun_sorular))],
                "soru_tipi": "test"
            },
            {
                "name": "Test 10 - Ekstrem Uzun",
                "description": "En uzun 3 soru ile zorlama testi",
                "sorular": uzun_sorular[:min(3, len(uzun_sorular))],
                "soru_tipi": "test"
            },
        ]
        
        # Testleri çalıştır
        for i, test_case in enumerate(critical_tests, 1):
            print(f"\n🧪 {i}/5: {test_case['name']}")
            print(f"📝 {test_case['description']}")
            
            # Test çalıştır
            result = self._create_test_pdf(
                test_case['name'], 
                test_case['sorular'],
                test_case['soru_tipi']
            )
            
            # Sonuçları kaydet
            result['test_name'] = test_case['name']
            result['description'] = test_case['description']
            self.test_results.append(result)
            
            print("-" * 30)
        
        # Özet rapor
        self._print_critical_summary()
    
    def _print_critical_summary(self):
        """Kritik test sonuçlarının özet raporu"""
        print("\n" + "=" * 50)
        print("📊 KRİTİK TEST SONUÇLARI")
        print("=" * 50)
        
        basarili = sum(1 for r in self.test_results if r['success'])
        toplam = len(self.test_results)
        
        print(f"🎯 Toplam: {toplam} | ✅ Başarılı: {basarili} | ❌ Başarısız: {toplam - basarili}")
        print(f"📈 Başarı Oranı: %{(basarili/toplam)*100:.1f}")
        
        print(f"\n📋 Test Detayları:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            soru_count = result['soru_count']
            duration = result.get('duration', 0)
            print(f"  {status} {result['test_name']}: {soru_count} soru - {duration:.1f}s")
        
        print("=" * 50)

# Ana çalıştırma fonksiyonu
def run_critical_tests():
    """Kritik testleri çalıştır"""
    from logic.pdf_generator import PDFCreator
    
    pdf_creator = PDFCreator()
    soru_klasoru = "C:\\Users\\abdul\\Desktop\\Soru-Havuzu\\Unite-1\\Karbonhidrat\\Test\\Kolay"
    
    test_suite = PDFTestSuite(pdf_creator, soru_klasoru)
    test_suite.run_critical_tests_only()

if __name__ == "__main__":
    run_critical_tests()