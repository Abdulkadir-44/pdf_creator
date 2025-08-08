import os

# Soru havuzu ana klasörü (uygulama klasörüne göre değiştirilebilir)
SORU_HAVUZU_YOLU = os.path.join(os.getcwd(), "soru_havuzu")


def get_unite_klasorleri(ana_klasor=SORU_HAVUZU_YOLU):
    """Ana klasördeki ünite klasörlerini döndürür."""
    return [d for d in os.listdir(ana_klasor) if os.path.isdir(os.path.join(ana_klasor, d))]


def get_konu_basliklari(unite_klasor_yolu):
    """Ünite klasörü altındaki konu başlıklarını döndürür."""
    return [d for d in os.listdir(unite_klasor_yolu) if os.path.isdir(os.path.join(unite_klasor_yolu, d))]


def get_soru_tipleri(konu_klasor_yolu):
    """Konu başlığı klasörü altındaki soru tiplerini (test/yazılı) döndürür."""
    return [d for d in os.listdir(konu_klasor_yolu) if os.path.isdir(os.path.join(konu_klasor_yolu, d))]


def get_zorluk_seviyeleri(soru_tipi_klasor_yolu):
    """Soru tipi klasörü (test/yazılı) altındaki zorluk seviyelerini döndürür."""
    return [d for d in os.listdir(soru_tipi_klasor_yolu) if os.path.isdir(os.path.join(soru_tipi_klasor_yolu, d))]


def get_gorseller(zorluk_klasor_yolu):
    """Zorluk klasörü altındaki görselleri döndürür."""
    return [os.path.join(zorluk_klasor_yolu, f) for f in os.listdir(zorluk_klasor_yolu)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp"))]


def get_template_path(soru_tipi):
    """Soru tipine göre uygun şablon dosyasının yolunu döndürür."""
    if soru_tipi.lower() == "test":
        return os.path.join("templates", "template_test.png")
    elif soru_tipi.lower() == "yazılı":
        return os.path.join("templates", "template_yazili.png")
    else:
        return os.path.join("templates", "template_default.png")
