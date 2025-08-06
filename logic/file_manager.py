import os

GEÇERLİ_UZANTILAR = (".jpg", ".jpeg", ".png")

def klasor_yapisi_oku(ana_klasor):
    """
    Ana soru havuzu klasörünü tarar ve şu yapıyı döner:
    {
        "Karbonhidrat": {
            "Kolay": [dosya1, dosya2, ...],
            "Orta": [...],
            "Zor": [...]
        },
        ...
    }
    """
    yapı = {}

    if not os.path.exists(ana_klasor):
        raise FileNotFoundError("Belirtilen klasör bulunamadı.")

    for konu in os.listdir(ana_klasor):
        konu_yolu = os.path.join(ana_klasor, konu)
        if os.path.isdir(konu_yolu):
            yapı[konu] = {}
            for zorluk in os.listdir(konu_yolu):
                zorluk_yolu = os.path.join(konu_yolu, zorluk)
                if os.path.isdir(zorluk_yolu):
                    görseller = [
                        os.path.join(zorluk_yolu, dosya)
                        for dosya in os.listdir(zorluk_yolu)
                        if dosya.lower().endswith(GEÇERLİ_UZANTILAR)
                    ]
                    yapı[konu][zorluk] = görseller
    return yapı
