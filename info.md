# Soru Otomasyon Sistemi — Proje Detaylı Teknik Dokümantasyon

> **Son Güncelleme:** 2026-04-05
> **Dil:** Python 3
> **Framework:** CustomTkinter (UI) + ReportLab (PDF) + Pillow (Görsel İşleme)
> **Mimari:** MVC benzeri (Controller → Beyin → UI)

---

## 1. Proje Genel Yapısı

```
pdf_creator/
├── main.py                          # Giriş noktası
├── logger_config.py                 # Merkezi loglama (RotatingFileHandler)
├── logic/                           # İş mantığı katmanı (Beyin)
│   ├── __init__.py                  # Boş
│   ├── oturum_yoneticisi.py         # Soru seçim, güncelleme, PDF oluşturma beyni
│   ├── pdf_generator.py             # ReportLab ile PDF çizim motoru
│   ├── onizleme_cizici.py           # PIL ile PDF önizleme çizici
│   ├── resim_yonetimi_beyni.py      # Klasör/resim yönetimi iş mantığı
│   ├── answer_utils.py              # Cevap okuma (test: dosya adı, yazılı: JSON)
│   └── file_manager.py              # ÖLÜ DOSYA — hiçbir yerden import edilmiyor
├── ui/                              # Arayüz katmanı
│   ├── __init__.py                  # Boş
│   ├── main_ui.py                   # Ana pencere + ana menü
│   ├── ders_sec_ui.py               # Ders seçme ekranı
│   ├── konu_baslik_sec_ui.py        # Konu ve başlık seçme ekranı
│   ├── soru_parametresi_sec_ui.py   # Soru parametresi + önizleme (Controller)
│   ├── dialog_yoneticisi.py         # Tüm pop-up/dialog pencereleri
│   ├── resim_yonetimi_ui.py         # Resim yükleme/klasör yönetimi arayüzü
│   ├── parametre_sayfasi/           # Parametre sayfası alt bileşenleri
│   │   ├── sayfa_basligi.py         # Header bileşeni
│   │   ├── parametre_secim_formu.py # Form bileşeni (Ekran 1)
│   │   ├── onizleme_ekrani.py       # Önizleme iskeleti (Ekran 2)
│   │   └── kontrol_paneli.py        # Sağ panel (soru listesi + butonlar)
│   └── widgets/
│       └── tooltip.py               # Hover tooltip bileşeni
├── templates/                       # PDF şablon görselleri (PNG)
│   ├── template.png                 # Test - Sayfa 1 (başlıklı)
│   ├── template2.png                # Yazılı - Sayfa 1 (başlıklı)
│   ├── template3.png                # Test - Sayfa 2+ (başlıksız)
│   └── template4.png                # Yazılı - Sayfa 2+ (başlıksız)
└── resources/fonts/                 # Arial + Calibri fontları
```

---

## 2. Uygulama Başlatma Akışı

```
main.py
  ├── setup_logging()                → logger_config.py (RotatingFileHandler kurulumu)
  └── AnaPencere()                   → ui/main_ui.py
        ├── init_frames()
        │     ├── AnaMenu(container, self)         # Ana menü butonları
        │     ├── DersSecmePenceresi(container, self)  # Ders seçme
        │     └── ResimYonetimiPenceresi(container, self)  # Klasör yönetimi
        └── show_frame("AnaMenu")    # İlk ekranı göster
```

**Loglar:** `%APPDATA%/SoruOtomasyonSistemi/logs/` altında:
- `general.log` — INFO+ (5MB, 5 backup)
- `errors.log` — ERROR+ (2MB, 3 backup)

---

## 3. Sayfa Navigasyon Akışı

```
AnaMenu
  ├── [Soru Seç ve PDF Oluştur] → DersSecmePenceresi
  │     └── [Ders Butonları] → KonuBaslikSecmePenceresi (dinamik oluşturulur)
  │           └── [Devam Et] → SoruParametresiSecmePenceresi (dinamik oluşturulur)
  │                 ├── Ekran 1: ParametreSecimFormu (soru tipi, zorluk, adet seçimi)
  │                 └── Ekran 2: OnizlemeEkrani (PDF önizleme + kontrol paneli)
  └── [Klasör Yönetimi] → ResimYonetimiPenceresi
```

Tüm sayfalar `AnaPencere.frames` dict'inde tutulur. `show_frame(name)` ile `tkraise()` yapılır.
Dinamik sayfalar (`KonuBaslikSecme`, `SoruParametre`) her seferinde `destroy()` + yeniden oluşturulur.

---

## 4. İş Mantığı Katmanı (logic/)

### 4.1. oturum_yoneticisi.py — OturumYoneticisi

**Rolü:** Tüm soru seçim, güncelleme ve PDF oluşturma state'ini yönetir. "Beyin" sınıfı.

**State (Durum) Değişkenleri:**
- `self.controller` — SoruParametresiSecmePenceresi referansı
- `self.controller.secilen_gorseller` — Seçilen soru dosya yolları listesi
- `self.controller.sayfa_haritasi` — BestFit algoritmasının ürettiği plan
- `self.controller.kullanilan_sorular` — Önizleme havuzu (dict: konu→set)
- `self.controller.kalici_kullanilan` — Oturum havuzu (dict: konu→set, PDF'e basılanlar)

**Çift Havuz Sistemi:**
```
kullanilan_sorular (Önizleme Havuzu)
  → Her yeni PDF seçiminde sıfırlanır
  → Güncelle/kaldır işlemlerinde güncellenir
  → Amaç: Aynı önizleme içinde tekrar gelmesini engelle

kalici_kullanilan (Oturum Havuzu)
  → ASLA otomatik sıfırlanmaz (kullanıcı isterse dialog ile sıfırlar)
  → PDF başarıyla kaydedildiğinde commit edilir
  → Amaç: Farklı PDF'lerde aynı soru tekrar gelmesin
```

#### Fonksiyonlar:

**`__init__(self, controller)`**
- Controller referansını alır, logger ve dialog_yoneticisi'ne erişim sağlar.

**`_havuzu_sifirla(self)`**
- `self.controller.kullanilan_sorular` dict'ini resetler.
- Her yeni PDF oluşturmada çağrılır.

**`secili_gorselleri_al(self, soru_tipi, zorluk, on_complete=None)`**
- Çift havuz sistemiyle soru seçimi yapar.
- `kalici_kullanilan` havuzunu kontrol eder.
- Havuz biterse `show_kalici_havuz_bitti_dialog` gösterir.
- İç fonksiyonlar:
  - `_sifirla_ve_devam()` — Kalıcı havuzu sıfırlar ve seçime devam eder.
  - `_mevcut_kadar_devam()` — Kalan sorularla devam eder.
- **Çağıran:** `SoruParametresiSecmePenceresi._form_onaylandi_callback()`

**`_secim_yap_ve_devam(self, soru_tipi, zorluk, kalici_ref, kullanilan_ref, on_complete)`**
- Gerçek soru seçimini yapar: `random.sample()` ile rastgele seçer.
- Her konu için ayrı klasörden okur.
- Kullanılan soruları hem `kullanilan_sorular` hem `kalici_kullanilan`'a ekler.
- Sonunda `_proceed_to_preview()` çağırır.

**`_proceed_to_preview(self, soru_tipi, zorluk)`**
- `_planlama_ve_ui()` çağırır.
- Yazılı modda fazla soru varsa bilgilendirme dialogu gösterir.

**`_planlama_ve_ui(self, soru_tipi, secilen_gorseller)`**
- `secilen_gorseller`'i controller'a atar.
- Test → `PDFCreator.planla_test_duzeni()` çağırır (BestFit).
- Yazılı → Sahte `(500, 400)` boyutlarla basit plan oluşturur.
- Sonunda `gorsel_onizleme_alani_olustur()` ve `display_images_new()` çağırır.

**`_replan_and_refresh_ui(self)`**
- Soru güncellendiğinde/kaldırıldığında yeniden planlar.
- `planla_test_duzeni()` tekrar çağırır → BestFit yeniden çalışır.
- UI'ı yeniler: `refresh_pdf_preview_only()`, `display_images_new()`.
- **Çağıran:** `gorseli_guncelle_new()`, `gorseli_kaldir_new()`

**`gorseli_guncelle_new(self, index)`**
- Verilen global indeksteki soruyu yenisiyle değiştirir.
- Aynı konudan yeni soru seçer (kullanılmamış havuzdan).
- `secilen_gorseller` listesinden ekranda olan soruları çıkartarak "kullanılmamış" soruları hesaplar.
- Path karşılaştırmasında `os.path.normcase + os.path.abspath` kullanır.
- Havuz biterse → callback pattern ile `show_havuz_tukendi_dialog` gösterir.
- Sonunda `_replan_and_refresh_ui()` çağırır.
- **Çağıran:** `SoruParametresiSecmePenceresi.gorseli_guncelle_new()` → `KontrolPaneli` buton callback'i

**`gorseli_kaldir_new(self, index)`**
- Soruyu `secilen_gorseller`'den siler.
- `kullanilan_sorular`'dan da kaldırır.
- `_replan_and_refresh_ui()` çağırır.

**`find_topic_from_path(self, gorsel_path)`**
- Görsel yolundan konu adını çıkarır (path parsing).

**`get_answer_for_image(self, image_path)`**
- `answer_utils.get_answer_for_image()` wrapper'ı.

**`_get_sorular_per_sayfa(self)`**
- Test → `None` (BestFit belirler), Yazılı → `2`.

**`pdf_olustur(self)`**
- PDFCreator nesnesi oluşturur, görselleri ve cevapları ekler.
- Cevaplarda "?" varsa `_show_cevap_onay_dialog` gösterir.
- PDF kaydı başarılıysa `kalici_kullanilan`'a commit eder.
- İç fonksiyon `_proceed_to_save()` asıl kaydetme işlemini yapar.

**`basit_pdf_olustur(self)`**
- PDFCreator import edilemezse fallback olarak basit PDF oluşturur.

---

### 4.2. pdf_generator.py — PDFCreator

**Rolü:** ReportLab ile PDF dosyasını oluşturur. Şablon üzerine çizer.

**Font Sistemi (modül seviyesinde):**
- `resources/fonts/` altından Arial → Calibri → Helvetica sırasıyla yüklenir.
- `DEFAULT_FONT_REGULAR`, `DEFAULT_FONT_BOLD` global sabitleri atanır.

#### Fonksiyonlar:

**`__init__(self)`**
- `gorsel_listesi`, `baslik_metni`, `cevap_listesi`, `soru_tipi` başlatır.

**`baslik_ekle(self, baslik)`**
- Başlık metnini atar.

**`gorsel_ekle(self, gorsel_yolu, cevap=None)`**
- Görsel ve cevabı listelere ekler.

**`planla_test_duzeni(self)` ⭐ BestFit Algoritması**
- Tüm soruları PIL ile açar, boyutlarını hesaplar.
- `col_width * 0.98` genişliğe sığdırır, oranı korur.
- **BestFit:** Sayfa başına 2 sütun. Her sütuna boşluğa EN İYİ SIĞAN soruyu yerleştirir.
- `min(uygun_sorular, key=lambda s: (kalan_bosluk - s['total_height']))` — boşluk israfını minimize eder.
- **ÖNEMLİ:** Sıra (index) önemli DEĞİL, boyut önemli. Bu yüzden güncelleme yapılınca sıra değişebilir.
- Sayfa 1 → `top_margin=50`, Sayfa 2+ → `top_margin=35`.
- Çıktı: `sayfa_haritasi = [[sutun0_soruları, sutun1_soruları], ...]`

**`cevap_anahtari_ekle(self, cevaplar)`**
- Cevap listesini atar.

**`_draw_title_on_canvas(self, canvas_obj)`**
- ReportLab canvas üzerine başlık çizer.
- Font boyutunu otomatik küçültür (max_width'e sığana kadar).

**`_create_yazili_layout(self, ...)` ⚠️ ÖLÜ FONKSİYON**
- Eski yazılı layout'u. `kaydet()` bunu çağırmıyor.

**`create_template_page(self, ...)` ⚠️ ÖLÜ FONKSİYON**
- Eski şablon sayfası. `kaydet()` bunu çağırmıyor.

**`_create_working_test_layout(self, canvas_obj, bu_sayfanin_sutunlari, ...)`**
- BestFit'ten gelen hazır planı alır ve çizer. Kendi hesaplama YAPMAZ.
- ReportLab koordinat sistemi (dipten yukarı) kullanır.
- Her soru için `drawImage()` + soru numarası yazar.
- Return: `(yerlestirildi_sayaci, global_offset)`

**`kaydet(self, dosya_yolu, sayfa_haritasi=None)`**
- Ana kaydetme fonksiyonu.
- Her sayfa için şablon seçer (sayfa 1: başlıklı, sayfa 2+: başlıksız).
- Yazılı → `_create_yazili_layout_simple()`, Test → `_create_working_test_layout()`.
- Son sayfaya cevap anahtarı ekler.

**`_create_yazili_layout_simple(self, canvas_obj, gorseller, ...)`**
- Sayfa başına max 2 soru. Resmi oranını koruyarak sığdırır.

**`create_answer_key_page(self, canvas_obj)`**
- Soru tipine göre doğru cevap anahtarı fonksiyonunu çağırır.

**`_create_test_answer_key(self, canvas_obj)`**
- 2 sütunlu test cevap anahtarı: "1. A", "2. B" formatında.

**`_create_yazili_answer_key(self, canvas_obj)`**
- Tek sütunlu yazılı cevap anahtarı: her cevap için geniş alan.

**`_create_optik_cevap_anahtari(self, canvas_obj)`**
- "BOŞ OPTİK.pdf" şablonu üzerine cevapları karalar.
- 12'şerli blok yapısı: 1-12, 13-24, 25-36, 37-48.

**`_basit_pdf_olustur(self, dosya_yolu)`**
- Şablon bulunamazsa en basit PDF.

---

### 4.3. onizleme_cizici.py — OnizlemeCizici

**Rolü:** PIL (Pillow) ile PDF önizleme görseli oluşturur. ImageTk.PhotoImage döner.

#### Fonksiyonlar:

**`__init__(self, soru_tipi, baslik_text, logger, constants_dict)`**
- Font yollarını belirler (Arial → Calibri fallback).

**`_get_font(self, is_bold=False, size=24)`**
- Merkezi font yükleme. Ana → yedek → default sırasıyla dener.

**`generate_preview_image(self, bu_sayfanin_sutunlari, global_offset, page_index)`**
- Ana giriş noktası.
- Şablon PNG'yi yükler, başlığı çizer, layout fonksiyonunu çağırır.
- 600px genişliğe resize eder.
- Return: `ImageTk.PhotoImage`

**`_draw_title_on_image(self, image)`**
- PIL ile başlığı çizer. Font boyutunu otomatik küçültür.

**`_create_yazili_preview(self, template_copy, ...)`**
- Yazılı mod önizlemesi. Sayfa başına max 2 soru.

**`_create_test_preview_BestFit(self, template_copy, bu_sayfanin_sutunlari, ...)`**
- Test mod önizlemesi. BestFit planını alır ve çizer.
- Resim açılamazsa kırmızı çerçeve + hata mesajı gösterir (continue bug düzeltildi).
- Y koordinatı ve sayaç HER DURUMDA güncellenir.

---

### 4.4. resim_yonetimi_beyni.py — ResimYonetimiBeyni

**Rolü:** Klasör yapısı, resim sayma, thumbnail cache, dosya kopyalama/silme.

**State:**
- `self._count_cache` — Klasör→resim sayısı
- `self._size_cache` — Klasör→boyut (byte)
- `self._thumb_cache` — OrderedDict LRU Cache (max 50 PIL.Image)
- `self.ana_klasor_yolu` — Seçilen ana klasör

**NOT:** `_has_subfolders()` fonksiyonu satır 235 ve 391'de İKİ KERE tanımlı. Python son tanımı kullanır.

#### Önemli Fonksiyonlar:

**`set_ana_klasor(self, path)`**
- Ana klasörü ayarlar ve tüm cache'leri temizler.

**`get_folder_level(self, folder_path)`**
- Klasörün hiyerarşideki seviyesini döner: ROOT/DERS/KONU/TUR/ZORLUK.

**`_find_folder_insensitive(self, parent_path, target_name)`**
- Case-insensitive klasör arama. "yazılı"/"YAZILI"/"Yazılı" hepsini bulur.
- Türkçe karakter desteği: `ı` → `i` dönüşümü.

**`get_pil_thumbnail(self, path, max_size=(180,180))`**
- LRU Cache ile thumbnail üretir.
- Cache doluysa (50) en eski PIL Image silinir + `img.close()`.
- Cache'te varsa `move_to_end()` ile sona taşır (LRU).

**`get_ders_details_data(self, folder_path)`**
- Thread'de çalışır. Ders istatistiklerini toplar.

**`get_konu_details_data(self, folder_path)`**
- Thread'de çalışır. Konu istatistiklerini toplar (Test/Yazılı alt klasörleri dahil).

**`search_folders_and_parents(self, search_text)`**
- `os.walk` ile arama. Ebeveyn klasörleri de sonuçlara ekler.
- Derinlik sınırı: max `depth=2` (DERS+KONU).

**`get_sadece_alt_klasorler(self, folder_path)`**
- Bir seviye alt klasörleri getirir. `(isim, yol, alt_klasoru_var_mi)` tuple.

---

### 4.5. answer_utils.py — Cevap Okuyucu

**Tek fonksiyon: `get_answer_for_image(image_path)`**

```
Yolda '/test/' varsa → Dosya adından oku: "1-A.png" → rsplit('-', 1) → "A"
Yolda '/yazili/' varsa → cevaplar.json'dan oku: {"dosya.png": "cevap"}
İkisi de yoksa → "?" döner
```

---

### 4.6. file_manager.py ⚠️ ÖLÜ DOSYA

Sadece `GECERLI_UZANTILAR` sabiti ve logger tanımı var. Hiçbir yerden import edilmiyor.

---

## 5. UI Katmanı (ui/)

### 5.1. main_ui.py — AnaPencere + AnaMenu

**AnaPencere (CTk)** — Uygulamanın ana penceresi (controller).
- `init_frames()` — AnaMenu, DersSecme, ResimYonetimi oluşturur.
- `show_frame(name, **kwargs)` — Frame gösterir. Dinamik frame'leri destroy+recreate eder.
- `ana_menuye_don()` — Ana menüye döner.

**AnaMenu (CTkFrame)** — İki butonlu giriş ekranı.
- `soru_sec_ekranini_ac()` → `show_frame("UniteSecme")`
- `klasor_yonetimi_ekranini_ac()` → `show_frame("ResimYonetimi")`

---

### 5.2. ders_sec_ui.py — DersSecmePenceresi

- Kullanıcı ana klasörü seçer (`filedialog.askdirectory`).
- Alt klasörleri (dersler) buton olarak gösterir.
- Responsive grid layout (`relayout_buttons()` pencere boyutuna göre).
- **Çağrı:** Ders butonuna tıkla → `konu_baslik_ekranini_ac(ana_klasor, secilen_ders)` → `AnaPencere.show_frame("KonuBaslikSecme", ...)`

---

### 5.3. konu_baslik_sec_ui.py — KonuBaslikSecmePenceresi

- Sol panel: Konuları checkbox'larla listeler + arama + filtre (Tümü/Test/Yazılı).
- Sağ panel: Seçilen konuları gösterir.
- Her konu için detaylı soru dağılımı: Test(K/O/Z), Yazılı(K/O/Z) sayıları.
- Sayfalama: İlk 20 konu gösterir, "Daha Fazla Yükle" butonu.
- **Çağrı:** Devam Et → `AnaPencere.show_frame("SoruParametre", ders_adi=..., secilen_konular=...)`

---

### 5.4. soru_parametresi_sec_ui.py — SoruParametresiSecmePenceresi

**Bu sınıf hem UI Controller'dır hem de OturumYoneticisi'ni barındırır.**

**State:**
```python
self.secilen_gorseller = []         # Seçilen soru dosya yolları
self.sayfa_haritasi = []            # BestFit planı
self.current_page = 0               # Aktif sayfa indeksi
self.kullanilan_sorular = {}        # Önizleme havuzu (konu→set)
self.kalici_kullanilan = {}         # Oturum havuzu (konu→set)
self.baslik_text_var                # StringVar — başlık metni
self.soru_tipi_var                  # StringVar — "Test"/"Yazılı"
self.zorluk_var                     # StringVar — "Kolay"/"Orta"/"Zor"/"Karışık"
```

**Alt Bileşenler (Composition):**
- `OturumYoneticisi(self)` — Beyin
- `DialogYoneticisi(self)` — Dialoglar
- `OnizlemeCizici(...)` — Önizleme çizici
- `SayfaBasligi(...)` — Header
- `ParametreSecimFormu(...)` — Form (Ekran 1)
- `OnizlemeEkrani(...)` — Önizleme iskeleti (Ekran 2)
- `KontrolPaneli(...)` — Sağ panel

**Ekran 1 → Ekran 2 Geçişi:**
```
ParametreSecimFormu.devam_et()
  → on_devam_et_callback = self._form_onaylandi_callback
    → OturumYoneticisi.secili_gorselleri_al(soru_tipi, zorluk)
      → _secim_yap_ve_devam(...)
        → _proceed_to_preview(...)
          → _planlama_ve_ui(...)
            → gorsel_onizleme_alani_olustur()
            → display_images_new(pdf_container, controls_container)
```

**Soru Güncelleme Akışı:**
```
KontrolPaneli "Güncelle" butonu
  → SoruParametresiSecmePenceresi.gorseli_guncelle_new(index)
    → OturumYoneticisi.gorseli_guncelle_new(index)
      → Yeni soru seç (aynı konudan)
      → secilen_gorseller[index] = yeni_yol
      → _replan_and_refresh_ui()
        → planla_test_duzeni() veya yazılı plan
        → refresh_pdf_preview_only()
        → display_images_new()
```

**Soru Kaldırma Akışı:**
```
KontrolPaneli "Sil" butonu
  → SoruParametresiSecmePenceresi.gorseli_kaldir_new(index)
    → OturumYoneticisi.gorseli_kaldir_new(index)
      → secilen_gorseller.pop(index)
      → kullanilan_sorular'dan kaldır
      → _replan_and_refresh_ui()
```

**PDF Oluşturma Akışı:**
```
KontrolPaneli "PDF Oluştur" butonu
  → SoruParametresiSecmePenceresi.pdf_olustur()
    → OturumYoneticisi.pdf_olustur()
      → PDFCreator oluştur
      → gorsel_ekle(yol, cevap)  (her soru için)
      → cevap_anahtari_ekle(cevaplar)
      → Cevaplarda "?" varsa → _show_cevap_onay_dialog
      → _proceed_to_save()
        → kaydet(dosya_yolu, sayfa_haritasi)
        → Başarılıysa → kalici_kullanilan'a commit
```

**Sayfa Değiştirme:**
```
change_page_new(pdf_container, controls_container, direction)
  → current_page += direction
  → refresh_pdf_preview_only()    # Sol panel
  → display_images_new(...)       # Sağ panel
```

#### Fonksiyonlar:

- `setup_ui()` — Ana layout: header + içerik çerçevesi.
- `goster_parametre_formu()` — Ekran 1'i gösterir.
- `_form_onaylandi_callback(konu_soru_dagilimi)` — Form onayı → Beyne yönlendir.
- `gorsel_onizleme_alani_olustur()` — Ekran 2 iskeletini oluşturur (OnizlemeEkrani).
- `refresh_pdf_preview_only()` — Sol panel PDF önizlemesini yeniler (OnizlemeCizici ile).
- `display_images_new(pdf_container, controls_container)` — Sağ paneli (KontrolPaneli) oluşturur.
- `change_page_pdf_only(direction)` — Sayfa değiştir (sadece sol panel).
- `_refresh_preview_debounced(delay_ms=500)` — Başlık değişiminde gecikme ile yenile.
- `geri_don()` — Ekran 2 → Ekran 1'e döner.

---

### 5.5. dialog_yoneticisi.py — DialogYoneticisi

**Rolü:** Tüm pop-up pencereler. State'e dokunmaz, callback pattern kullanır.

- `show_error(message)` — Kırmızı hata dialogu.
- `show_notification(title, message, geri_don=False)` — Yeşil bildirim. `geri_don=True` ise ana menüye döner.
- `_show_dialog(title, message, color)` — Genel dialog oluşturucu.
- `show_multipage_info(istenen_sayi, on_close)` — Yazılı çoklu sayfa bilgilendirmesi.
- `_darken_color(hex_color)` — Rengi koyulaştırır (hover efekti için).
- `_show_cevap_onay_dialog(message, on_confirm_callback)` — "?" cevaplar için onay/reddet.
- `show_havuz_tukendi_dialog(konu_adi, on_sifirla, on_iptal)` — Önizleme havuzu bittiğinde.
- `show_kalici_havuz_bitti_dialog(tukenen_konular, on_sifirla, on_devam)` — Oturum havuzu bittiğinde. Kalan soru yoksa "Devam" butonu gizlenir.

---

### 5.6. parametre_sayfasi/ — Alt Bileşenler

**SayfaBasligi** — Header çubuğu. Callbacks: `on_ana_menu`, `on_konu_secimi`.

**ParametreSecimFormu** — Ekran 1 formu.
- Soru tipi (Test/Yazılı), zorluk (Kolay/Orta/Zor/Karışık), başlık, soru sayısı (konu başına).
- `devam_et()` — Doğrulama yapar (min 1 soru, havuzda yeterli var mı?) → callback çağırır.
- `get_available_questions(konu, tip, zorluk)` — Havuzdaki mevcut soru sayısını döner.
- `update_total()` — Toplam soru sayısını canlı günceller.

**OnizlemeEkrani** — İskelet frame. Sol (pdf_container) ve sağ (controls_container) panelleri oluşturur.

**KontrolPaneli** — Sağ panel.
- Soru listesi: her soru için numara, konu, cevap, güncelle/sil butonları.
- PDF Oluştur ve Geri Dön butonları.
- Callbacks: `on_sil`, `on_guncelle`, `on_pdf_olustur`, `on_geri_don`, `on_sayfa_degistir`.

---

### 5.7. resim_yonetimi_ui.py — ResimYonetimiPenceresi

- Sol panel: TreeView klasör ağacı (tembel yükleme — expand'de alt klasörler yüklenir).
- Sağ panel: Seçilen klasörün detayları + resim yükleme/silme.
- `ResimYonetimiBeyni` instance'ı kullanır.
- Thread'lerle ağır I/O işleri arka planda yapılır.
- Arama: debounced (300ms), arka plan thread'inde.

---

## 6. Klasör Hiyerarşisi (Beklenen Yapı)

```
Ana Klasör/
├── Matematik/                    # DERS (depth=1)
│   ├── Türev/                    # KONU (depth=2)
│   │   ├── Test/                 # TÜR (depth=3)
│   │   │   ├── Kolay/            # ZORLUK (depth=4)
│   │   │   │   ├── 1-A.png       # Soru görseli (cevap: A)
│   │   │   │   ├── 2-B.png
│   │   │   │   └── ...
│   │   │   ├── Orta/
│   │   │   └── Zor/
│   │   └── Yazılı/
│   │       ├── Kolay/
│   │       │   ├── soru1.png
│   │       │   └── cevaplar.json  # {"soru1.png": "x²+2x+1", ...}
│   │       ├── Orta/
│   │       └── Zor/
│   └── İntegral/
└── Fizik/
```

---

## 7. Bilinen Sorunlar ve Teknik Borçlar

| # | Sorun | Dosya | Durum |
|---|---|---|---|
| 1 | `_has_subfolders` 2 kere tanımlı | `resim_yonetimi_beyni.py:235,391` | Düzeltilmedi |
| 2 | ÖLÜ: `_create_yazili_layout` | `pdf_generator.py:265` | Silinmedi |
| 3 | ÖLÜ: `create_template_page` | `pdf_generator.py:366` | Silinmedi |
| 4 | ÖLÜ: `file_manager.py` dosyası | `logic/file_manager.py` | Silinmedi |
| 5 | Yazılı modu sahte `(500,400)` boyutu | `oturum_yoneticisi.py` | Düzeltilmedi |
| 6 | BestFit güncelleme sonrası sıra değiştiriyor | `pdf_generator.py:181` | Düzeltilmedi |

---

## 8. Bağımlılıklar

```
customtkinter     — UI framework
Pillow (PIL)      — Görsel işleme, thumbnail, önizleme çizim
reportlab         — PDF oluşturma
tkinter           — Temel UI (filedialog, ttk.Treeview)
```

Standart kütüphaneler: `os, logging, json, math, random, shutil, datetime, collections, sys, threading`
