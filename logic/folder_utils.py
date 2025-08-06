import os
import random

# Soru havuzu ana klasörü (uygulama klasörüne göre değiştirilebilir)
SORU_HAVUZU_YOLU = os.path.join(os.getcwd(), "soru_havuzu")
print(f"DEBUG - SORU_HAVUZU_YOLU: {SORU_HAVUZU_YOLU}")

# Klasör varlığını kontrol et ve kullanıcıya bilgi ver
if not os.path.exists(SORU_HAVUZU_YOLU):
    print(f"UYARI: {SORU_HAVUZU_YOLU} klasörü bulunamadı. Lütfen soru_havuzu klasörünün varlığını kontrol edin.")
else:
    print(f"Bilgi: {SORU_HAVUZU_YOLU} klasörü bulundu.")


def get_topics():
    """Ana dizindeki konu klasörlerini döndürür."""
    try:
        return [d for d in os.listdir(SORU_HAVUZU_YOLU) if os.path.isdir(os.path.join(SORU_HAVUZU_YOLU, d))]
    except FileNotFoundError:
        return []


def get_levels(konu):
    """Belirli bir konu klasörü içindeki zorluk seviyelerini döndürür."""
    konu_path = os.path.join(SORU_HAVUZU_YOLU, konu)
    try:
        return [d for d in os.listdir(konu_path) if os.path.isdir(os.path.join(konu_path, d))]
    except FileNotFoundError:
        return []


def get_random_image(konu, seviye):
    """Belirtilen konu ve seviyedeki klasörden rastgele bir görsel döndürür."""
    seviye_path = os.path.join(SORU_HAVUZU_YOLU, konu, seviye)
    if not os.path.exists(seviye_path):
        raise FileNotFoundError(f"Seçilen klasör bulunamadı: {seviye_path}")

    tum_gorseller = [f for f in os.listdir(seviye_path)
                     if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    if not tum_gorseller:
        raise FileNotFoundError(f"{konu}/{seviye} klasöründe hiç görsel bulunamadı.")

    secilen = random.choice(tum_gorseller)
    return os.path.join(seviye_path, secilen)
