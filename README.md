# İkinci El Premium Araç Fiyatlandırma Analizi (BMW · MINI · Jaguar · Land Rover)

Borusan Otomotiv'in distribütörlüğünü yaptığı dört marka için ikinci el fiyatını belirleyen faktörleri (yaş, kilometre, kaza geçmişi) SQL ve istatistiksel modelleme ile inceleyen bir vaka çalışması.

> **Not:** Analiz, Borusan'ın kendi verisiyle değil, Kaggle'da halka açık paylaşılan **ABD pazarına ait** bir ilan verisiyle yapılmıştır. Amaç, aynı metodolojinin şirketin kendi verisine nasıl uygulanabileceğini göstermektir.

## Ana bulgular

- **Kilometre ve yaş güçlü etkiler:** Marka sabitken her ek 10.000 mil fiyatı yaklaşık **%8,5**, her ek yıl yaklaşık **%5** düşürüyor.
- **Kaza etkisi ham farktan çok daha küçük:** Ham ortalamalarda kazalı araçlar %18-48 daha ucuz görünüyor, ancak yaş ve km kontrol edildiğinde etki yaklaşık **%7** ve istatistiksel olarak sınırda (p = 0,08). Farkın büyük kısmı, kazalı araçların daha yaşlı ve yüksek km'li olmasından geliyor.
- **Tahmin performansı:** Log-lineer OLS R² = 0,75 (n = 571). Random Forest kıyası test setinde R² = 0,68 ortalama mutlak hata ≈ $11.900.

## İçerik

| Dosya | Açıklama |
|---|---|
| `analysis.py` | Temizleme, SQL sorguları, OLS ve Random Forest,|
| `borusan_analiz_sorgulari.sql` | Analizde kullanılan SQL sorguları |
| `requirements.txt` | Gerekli Python paketleri |

## Çalıştırma

1. Veri setini Kaggle'dan indir: [Used Car Price Prediction Dataset](https://www.kaggle.com/datasets/taeefnajib/used-car-price-prediction-dataset) (`used_cars.csv`). Veri, lisansı nedeniyle bu repoya eklenmemiştir.

2. Paketleri kur ve çalıştır:pip install -r requirements.txt
python analysis.py used_cars.csv
Grafikler ve SQLite veritabanı `outputs/` klasörüne yazılır.

## Yöntem

- **Temizleme:** Fiyat ve kilometre sayısal hale getirildi, aykırı değerler (fiyat < $500 veya > $400.000, km > 300.000) çıkarıldı. Kaza bilgisi eksik olan ilanlar "kaza yok" sayılmadı, analizden çıkarıldı.
- **SQL:** Marka, yaş grubu ve kaza durumuna göre özet sorguları (SQLite).
- **OLS:** `log(fiyat) ~ yaş + km + kaza + marka`, dayanıklı (HC1) standart hatalar.
- **Random Forest:** %80/%20 eğitim-test ayrımı, doğrusal olmayan kıyas olarak.

## Kısıtlar

- Veri ABD pazarına ve tek bir ilan platformuna ait; ilan fiyatı gerçekleşen satış fiyatı değildir.
- Model/versiyon ve donanım bilgisi kullanılmadı; yüksek fiyatlı araçlarda tahmin hatası büyüyor.
- Yaş etkisi kesit verisinden okunuyor (aynı araçların zaman içindeki değer kaybı değil).

## Hazırlayan

Sena Bolat
