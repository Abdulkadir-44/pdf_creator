import os
import logging
from datetime import datetime

# Geçerli görsel dosya uzantıları
GEÇERLİ_UZANTILAR = (".jpg", ".jpeg", ".png", ".gif", ".bmp")

# Logger kurulumu
def _setup_logger():
    """Folder utils için logger kurulumu"""
    logger = logging.getLogger('FolderUtils')
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

# Global logger instance
_logger = _setup_logger()

def klasor_yapisi_oku(ana_klasor):
    """
    Ana soru havuzu klasörünü tarar ve şu yapıyı döner:
    {
        "Karbonhidrat": {
            "test": {
                "kolay": [dosya1, dosya2, ...],
                "orta": [...],
                "zor": [...]
            },
            "yazili": {
                "kolay": [...],
                "orta": [...],
                "zor": [...]
            }
        },
        ...
    }
    """
    _logger.info(f"Klasör yapısı taranıyor: {os.path.basename(ana_klasor)}")
    
    try:
        yapı = {}
        
        if not os.path.exists(ana_klasor):
            _logger.error(f"Ana klasör bulunamadı: {ana_klasor}")
            raise FileNotFoundError(f"Belirtilen klasör bulunamadı: {ana_klasor}")

        # Ana klasördeki konu klasörlerini tara
        konu_sayisi = 0
        toplam_gorsel = 0
        
        for konu in os.listdir(ana_klasor):
            konu_yolu = os.path.join(ana_klasor, konu)
            
            if os.path.isdir(konu_yolu):
                _logger.debug(f"Konu klasörü işleniyor: {konu}")
                konu_sayisi += 1
                yapı[konu] = {}
                
                # Konu klasöründeki soru tipi klasörlerini tara (test/yazili)
                for soru_tipi in os.listdir(konu_yolu):
                    soru_tipi_yolu = os.path.join(konu_yolu, soru_tipi)
                    
                    if os.path.isdir(soru_tipi_yolu):
                        _logger.debug(f"Soru tipi klasörü işleniyor: {konu}/{soru_tipi}")
                        yapı[konu][soru_tipi] = {}
                        
                        # Zorluk seviyesi klasörlerini tara
                        for zorluk in os.listdir(soru_tipi_yolu):
                            zorluk_yolu = os.path.join(soru_tipi_yolu, zorluk)
                            
                            if os.path.isdir(zorluk_yolu):
                                _logger.debug(f"Zorluk klasörü işleniyor: {konu}/{soru_tipi}/{zorluk}")
                                
                                # Görselleri bul
                                görseller = []
                                try:
                                    for dosya in os.listdir(zorluk_yolu):
                                        if dosya.lower().endswith(GEÇERLİ_UZANTILAR):
                                            görsel_yolu = os.path.join(zorluk_yolu, dosya)
                                            görseller.append(görsel_yolu)
                                            toplam_gorsel += 1
                                    
                                    yapı[konu][soru_tipi][zorluk] = görseller
                                    
                                    if görseller:
                                        _logger.debug(f"{len(görseller)} görsel bulundu: {konu}/{soru_tipi}/{zorluk}")
                                    else:
                                        _logger.warning(f"Hiç görsel bulunamadı: {konu}/{soru_tipi}/{zorluk}")
                                        
                                except PermissionError as e:
                                    _logger.error(f"Klasör okuma izni yok: {zorluk_yolu}")
                                    yapı[konu][soru_tipi][zorluk] = []
                                except Exception as e:
                                    _logger.error(f"Klasör okuma hatası ({zorluk_yolu}): {e}")
                                    yapı[konu][soru_tipi][zorluk] = []
        
        _logger.info(f"Klasör taraması tamamlandı - {konu_sayisi} konu, {toplam_gorsel} görsel")
        return yapı
        
    except FileNotFoundError:
        raise  # Bu hatayı tekrar fırlat
    except Exception as e:
        _logger.error(f"Klasör yapısı okuma genel hatası: {e}")
        raise Exception(f"Klasör yapısı okunamadı: {str(e)}")

def klasor_istatistikleri(ana_klasor):
    """
    Klasör yapısı hakkında detaylı istatistikler döner.
    
    Args:
        ana_klasor (str): Ana klasör yolu
        
    Returns:
        dict: İstatistik bilgileri
    """
    _logger.info(f"İstatistikler hesaplanıyor: {os.path.basename(ana_klasor)}")
    
    try:
        yapı = klasor_yapisi_oku(ana_klasor)
        
        istatistikler = {
            "toplam_konu": len(yapı),
            "konular": {},
            "toplam_gorsel": 0,
            "soru_tipi_dagilimi": {"test": 0, "yazili": 0},
            "zorluk_dagilimi": {"kolay": 0, "orta": 0, "zor": 0}
        }
        
        for konu, soru_tipleri in yapı.items():
            konu_toplam = 0
            konu_detay = {"test": {}, "yazili": {}}
            
            for soru_tipi, zorluklar in soru_tipleri.items():
                for zorluk, görseller in zorluklar.items():
                    görsel_sayisi = len(görseller)
                    konu_toplam += görsel_sayisi
                    istatistikler["toplam_gorsel"] += görsel_sayisi
                    
                    # Soru tipi dağılımı
                    if soru_tipi in istatistikler["soru_tipi_dagilimi"]:
                        istatistikler["soru_tipi_dagilimi"][soru_tipi] += görsel_sayisi
                    
                    # Zorluk dağılımı
                    if zorluk in istatistikler["zorluk_dagilimi"]:
                        istatistikler["zorluk_dagilimi"][zorluk] += görsel_sayisi
                    
                    konu_detay[soru_tipi][zorluk] = görsel_sayisi
            
            istatistikler["konular"][konu] = {
                "toplam": konu_toplam,
                "detay": konu_detay
            }
        
        _logger.info(f"İstatistik hesaplandı - {istatistikler['toplam_konu']} konu, {istatistikler['toplam_gorsel']} görsel")
        return istatistikler
        
    except Exception as e:
        _logger.error(f"İstatistik hesaplama hatası: {e}")
        return {"error": f"İstatistik hesaplanamadı: {str(e)}"}

def klasor_dogrulama(ana_klasor):
    """
    Klasör yapısını doğrular ve eksiklikleri/sorunları raporlar.
    
    Args:
        ana_klasor (str): Ana klasör yolu
        
    Returns:
        dict: Doğrulama sonuçları
    """
    _logger.info(f"Klasör doğrulaması başlatılıyor: {os.path.basename(ana_klasor)}")
    
    try:
        if not os.path.exists(ana_klasor):
            return {
                "status": "error",
                "message": "Ana klasör bulunamadı",
                "errors": [f"Klasör mevcut değil: {ana_klasor}"]
            }
        
        yapı = klasor_yapisi_oku(ana_klasor)
        errors = []
        warnings = []
        
        expected_soru_tipleri = ["test", "yazili"]
        expected_zorluklar = ["kolay", "orta", "zor"]
        
        for konu, soru_tipleri in yapı.items():
            # Soru tipi eksikliklerini kontrol et
            for expected_tip in expected_soru_tipleri:
                if expected_tip not in soru_tipleri:
                    warnings.append(f"Eksik soru tipi: {konu}/{expected_tip}")
                    continue
                
                # Zorluk seviyesi eksikliklerini kontrol et
                for expected_zorluk in expected_zorluklar:
                    if expected_zorluk not in soru_tipleri[expected_tip]:
                        warnings.append(f"Eksik zorluk seviyesi: {konu}/{expected_tip}/{expected_zorluk}")
                    elif len(soru_tipleri[expected_tip][expected_zorluk]) == 0:
                        warnings.append(f"Boş klasör: {konu}/{expected_tip}/{expected_zorluk}")
        
        # Genel durumu değerlendir
        if errors:
            status = "error"
            _logger.error(f"Doğrulama başarısız - {len(errors)} hata")
        elif warnings:
            status = "warning"
            _logger.warning(f"Doğrulama uyarılarla tamamlandı - {len(warnings)} uyarı")
        else:
            status = "success"
            _logger.info("Klasör yapısı doğrulaması başarılı")
        
        return {
            "status": status,
            "errors": errors,
            "warnings": warnings,
            "total_errors": len(errors),
            "total_warnings": len(warnings)
        }
        
    except Exception as e:
        _logger.error(f"Doğrulama hatası: {e}")
        return {
            "status": "error",
            "message": f"Doğrulama sırasında hata: {str(e)}",
            "errors": [str(e)]
        }

def dosya_uzanti_analizi(ana_klasor):
    """
    Klasördeki dosya uzantılarını analiz eder.
    
    Args:
        ana_klasor (str): Ana klasör yolu
        
    Returns:
        dict: Uzantı analiz sonuçları
    """
    _logger.debug(f"Dosya uzantı analizi başlatılıyor: {os.path.basename(ana_klasor)}")
    
    try:
        uzanti_sayilari = {}
        gecersiz_dosyalar = []
        toplam_dosya = 0
        
        for root, dirs, files in os.walk(ana_klasor):
            for file in files:
                toplam_dosya += 1
                file_lower = file.lower()
                
                # Uzantıyı al
                _, uzanti = os.path.splitext(file_lower)
                
                if uzanti:
                    uzanti_sayilari[uzanti] = uzanti_sayilari.get(uzanti, 0) + 1
                    
                    # Geçersiz uzantıları kontrol et
                    if uzanti not in [ext.lower() for ext in GEÇERLİ_UZANTILAR]:
                        if not file.endswith('.json'):  # cevaplar.json dosyasını hariç tut
                            gecersiz_dosyalar.append(os.path.join(root, file))
                
        gecerli_gorsel_sayisi = sum(
            count for ext, count in uzanti_sayilari.items()
            if ext in [e.lower() for e in GEÇERLİ_UZANTILAR]
        )
        
        _logger.debug(f"Uzantı analizi tamamlandı - {toplam_dosya} dosya, {len(gecersiz_dosyalar)} geçersiz")
        
        return {
            "toplam_dosya": toplam_dosya,
            "gecerli_gorsel_sayisi": gecerli_gorsel_sayisi,
            "uzanti_sayilari": uzanti_sayilari,
            "gecersiz_dosyalar": gecersiz_dosyalar,
            "gecerli_uzantilar": list(GEÇERLİ_UZANTILAR)
        }
        
    except Exception as e:
        _logger.error(f"Uzantı analizi hatası: {e}")
        return {"error": f"Uzantı analizi hatası: {str(e)}"}

def temizlik_onerisi(ana_klasor):
    """
    Klasör temizliği için öneriler sunar.
    
    Args:
        ana_klasor (str): Ana klasör yolu
        
    Returns:
        dict: Temizlik önerileri
    """
    _logger.info(f"Temizlik analizi yapılıyor: {os.path.basename(ana_klasor)}")
    
    try:
        uzanti_analizi = dosya_uzanti_analizi(ana_klasor)
        dogrulama = klasor_dogrulama(ana_klasor)
        
        oneriler = []
        
        # Geçersiz dosyalar için öneri
        if uzanti_analizi.get("gecersiz_dosyalar"):
            oneriler.append({
                "tip": "gecersiz_dosyalar",
                "mesaj": f"{len(uzanti_analizi['gecersiz_dosyalar'])} geçersiz dosya bulundu",
                "dosyalar": uzanti_analizi["gecersiz_dosyalar"][:10],  # İlk 10 dosyayı göster
                "toplam": len(uzanti_analizi["gecersiz_dosyalar"])
            })
        
        # Boş klasörler için öneri
        if dogrulama.get("warnings"):
            bos_klasorler = [w for w in dogrulama["warnings"] if "Boş klasör" in w]
            if bos_klasorler:
                oneriler.append({
                    "tip": "bos_klasorler",
                    "mesaj": f"{len(bos_klasorler)} boş klasör bulundu",
                    "klasorler": bos_klasorler
                })
        
        # Eksik yapılar için öneri
        eksik_yapilar = [w for w in dogrulama.get("warnings", []) if "Eksik" in w]
        if eksik_yapilar:
            oneriler.append({
                "tip": "eksik_yapilar",
                "mesaj": f"{len(eksik_yapilar)} eksik yapı bulundu",
                "eksikler": eksik_yapilar
            })
        
        _logger.info(f"Temizlik analizi tamamlandı - {len(oneriler)} öneri")
        
        return {
            "oneriler": oneriler,
            "toplam_oneri": len(oneriler),
            "analiz_tarihi": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        _logger.error(f"Temizlik analizi hatası: {e}")
        return {"error": f"Temizlik analizi hatası: {str(e)}"}

# Logger seviyesini değiştirmek için yardımcı fonksiyon
def set_log_level(level):
    """
    Logger seviyesini değiştirir.
    
    Args:
        level (str): 'DEBUG', 'INFO', 'WARNING', 'ERROR'
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR
    }
    
    if level.upper() in level_map:
        _logger.setLevel(level_map[level.upper()])
        _logger.info(f"Log seviyesi {level.upper()} olarak ayarlandı")
    else:
        _logger.warning(f"Geçersiz log seviyesi: {level}")