-- Borusan portföy markaları: ikinci el fiyat analizi (SQLite)
-- Tablo: used_cars (Kaggle cars.com verisi, temizlenmiş; car_age = 2024 - model_year)
-- had_accident: 1 = kaza/hasar kaydı var, 0 = yok, NULL = bilinmiyor

-- 1) Marka bazında ortalama fiyat, km ve yaş
SELECT brand, COUNT(*) AS adet, ROUND(AVG(price)) AS ort_fiyat,
       ROUND(AVG(mileage)) AS ort_km, ROUND(AVG(car_age),1) AS ort_yas
FROM used_cars
WHERE brand IN ('BMW','MINI','Jaguar','Land Rover')
GROUP BY brand ORDER BY ort_fiyat DESC;

-- 2) Yaş grubuna göre ortalama fiyat
SELECT CASE WHEN car_age <= 2 THEN '0-2 yıl' WHEN car_age <= 5 THEN '3-5 yıl'
            WHEN car_age <= 9 THEN '6-9 yıl' ELSE '10+ yıl' END AS yas_grubu,
       COUNT(*) AS adet, ROUND(AVG(price)) AS ort_fiyat
FROM used_cars
WHERE brand IN ('BMW','MINI','Jaguar','Land Rover')
GROUP BY yas_grubu ORDER BY MIN(car_age);

-- 3) Kaza geçmişi: ham fiyat farkı (yaş/km kontrolsüz; rapordaki OLS ile birlikte okunmalı)
SELECT brand, had_accident, COUNT(*) AS adet, ROUND(AVG(price)) AS ort_fiyat
FROM used_cars
WHERE brand IN ('BMW','MINI','Jaguar','Land Rover') AND had_accident IS NOT NULL
GROUP BY brand, had_accident ORDER BY brand, had_accident;

-- 4) Kilometre grubuna göre ortalama fiyat
SELECT brand,
       CASE WHEN mileage < 50000 THEN '<50k' WHEN mileage < 100000 THEN '50-100k' ELSE '100k+' END AS km_grubu,
       COUNT(*) AS adet, ROUND(AVG(price)) AS ort_fiyat
FROM used_cars
WHERE brand IN ('BMW','MINI','Jaguar','Land Rover')
GROUP BY brand, km_grubu ORDER BY brand, ort_fiyat DESC;

-- 5) Borusan portföyü vs genel pazar
SELECT CASE WHEN brand IN ('BMW','MINI','Jaguar','Land Rover') THEN 'Borusan portföyü' ELSE 'Diğer markalar' END AS grup,
       COUNT(*) AS adet, ROUND(AVG(price)) AS ort_fiyat, ROUND(AVG(mileage)) AS ort_km,
       ROUND(100.0*SUM(had_accident)/COUNT(had_accident),1) AS kaza_orani_yuzde
FROM used_cars GROUP BY grup;
