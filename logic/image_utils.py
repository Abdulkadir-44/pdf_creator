import os
import random

def rastgele_gorsel_sec(konular_dict, konu, zorluk):
    try:
        gorsel_yolu = konular_dict[konu][zorluk]
        dosyalar = [f for f in os.listdir(gorsel_yolu) if f.lower().endswith(('.jpg', '.png'))]
        if not dosyalar:
            raise FileNotFoundError("Hiç görsel bulunamadı.")
        secilen = random.choice(dosyalar)
        return os.path.join(gorsel_yolu, secilen)
    except KeyError:
        raise ValueError("Seçilen konu veya zorluk geçersiz.")
