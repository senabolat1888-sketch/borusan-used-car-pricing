# İkinci El Premium Araç Fiyatlandırma Analizi (BMW · MINI · Jaguar · Land Rover)

Borusan Otomotiv'in distribütörlüğünü yaptığı dört marka için ikinci el fiyatını belirleyen faktörleri (yaş, kilometre, kaza geçmişi) SQL ve istatistiksel modelleme ile inceleyen bir vaka çalışması.

> **Not:** Analiz, Borusan'ın kendi verisiyle değil, Kaggle'da halka açık paylaşılan **ABD pazarına ait** bir ilan verisiyle yapılmıştır. Amaç, aynı metodolojinin şirketin kendi verisine nasıl uygulanabileceğini göstermektir.

## Ana bulgular

- **Kilometre ve yaş güçlü etkiler:** Marka sabitken her ek 10.000 mil fiyatı yaklaşık **%8,5**, her ek yıl yaklaşık **%5** düşürüyor.
- **Kaza etkisi ham farktan çok daha küçük:** Ham ortalamalarda kazalı araçlar %18-48 daha ucuz görünüyor, ancak yaş ve km kontrol edildiğinde etki yaklaşık **%7** ve istatistiksel olarak sınırda (p = 0,08). Farkın büyük kısmı, kazalı araçların daha yaşlı ve yüksek km'li olmasından geliyor.
- **Tahmin performansı:** Log-lineer OLS R² = 0,75 (n = 571). Random Forest kıyası test setinde R² = 0,68, ortalama mutlak hata ≈ $11.900.

## İçerik

| Dosya | Açıklama |
|---|---|
| `analysis.py` | Temizleme, SQL sorguları, OLS ve Random Forest, grafikler (tek script) |
| `borusan_analiz_sorgulari.sql` | Analizde kullanılan SQL sorguları |
| `requirements.txt` | Gerekli Python paketleri |

## Çalıştırma

1. Veri setini Kaggle'dan indir: [Used Car Price Prediction Dataset](https://www.kaggle.com/datasets/taeefnajib/used-car-price-prediction-dataset) (`used_cars.csv`). Veri, lisansı nedeniyle bu repoya eklenmemiştir.
2. Paketleri kur ve çalıştır:

```bash
pip install -r requirements.txt
python analysis.py used_cars.csv
Hazırlayan
Sena Bolat
