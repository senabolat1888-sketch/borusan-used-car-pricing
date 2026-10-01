"""
Borusan portföy markaları (BMW, MINI, Jaguar, Land Rover) için ikinci el fiyat analizi.

Kullanım:
    python analysis.py used_cars.csv

Girdi : Kaggle "Used Car Price Prediction Dataset" (taeefnajib) -> used_cars.csv
Çıktı : outputs/ klasöründe grafikler, SQLite veritabanı ve model tahminleri
"""
import sys
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mt
import statsmodels.formula.api as smf
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

BRANDS = ["BMW", "MINI", "Jaguar", "Land Rover"]
COLORS = {"BMW": "#1c69d4", "MINI": "#2b2b2b", "Jaguar": "#7a1f2b", "Land Rover": "#1f4d2c"}
OUT = Path("outputs")
OUT.mkdir(exist_ok=True)


# ---------- 1) Temizleme ----------
def load_and_clean(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["brand"] = df["brand"].replace("Land", "Land Rover")  # veride "Land" + "Rover ..." olarak bölünmüş
    df["price"] = df["price"].str.replace("[$,]", "", regex=True).astype(float)
    df["mileage"] = (df["milage"].str.replace(" mi.", "", regex=False)
                     .str.replace(",", "", regex=False).astype(float))
    df = df.drop(columns=["milage"])  # orijinal kolon adı yazım hatalı ("milage")
    df["car_age"] = df["model_year"].max() - df["model_year"]  # en yeni model yılı = 0
    # Kaza bilgisi eksikse NaN kalır ("kaza yok" varsayılmaz)
    df["had_accident"] = df["accident"].map({
        "None reported": 0,
        "At least 1 accident or damage reported": 1,
    })
    df = df[(df.price > 500) & (df.price < 400_000) & (df.mileage < 300_000)].copy()
    return df


# ---------- 2) SQL ----------
def run_sql(df: pd.DataFrame) -> None:
    conn = sqlite3.connect(OUT / "borusan_analysis.db")
    df.to_sql("used_cars", conn, if_exists="replace", index=False)
    b = str(tuple(BRANDS))

    queries = {
        "Marka bazında özet": f"""
            SELECT brand, COUNT(*) AS adet, ROUND(AVG(price)) AS ort_fiyat,
                   ROUND(AVG(mileage)) AS ort_km, ROUND(AVG(car_age),1) AS ort_yas
            FROM used_cars WHERE brand IN {b} GROUP BY brand ORDER BY ort_fiyat DESC""",
        "Yaş grubuna göre ortalama fiyat": f"""
            SELECT CASE WHEN car_age <= 2 THEN '0-2 yıl' WHEN car_age <= 5 THEN '3-5 yıl'
                        WHEN car_age <= 9 THEN '6-9 yıl' ELSE '10+ yıl' END AS yas_grubu,
                   COUNT(*) AS adet, ROUND(AVG(price)) AS ort_fiyat
            FROM used_cars WHERE brand IN {b} GROUP BY yas_grubu ORDER BY MIN(car_age)""",
        "Kaza geçmişi (ham fark, yaş/km kontrolsüz)": f"""
            SELECT brand, had_accident, COUNT(*) AS adet, ROUND(AVG(price)) AS ort_fiyat
            FROM used_cars WHERE brand IN {b} AND had_accident IS NOT NULL
            GROUP BY brand, had_accident ORDER BY brand, had_accident""",
    }
    for title, q in queries.items():
        print(f"\n=== {title} ===")
        print(pd.read_sql(q, conn).to_string(index=False))
    conn.close()


# ---------- 3) OLS ----------
def fit_ols(df: pd.DataFrame):
    s = df[df.brand.isin(BRANDS)].dropna(subset=["had_accident"]).copy()
    s["km10k"] = s.mileage / 10_000
    s["log_price"] = np.log(s.price)
    m = smf.ols("log_price ~ car_age + km10k + had_accident + C(brand, Treatment('BMW'))",
                s).fit(cov_type="HC1")  # dayanıklı standart hatalar
    print(f"\n=== OLS (n={len(s)}, R²={m.rsquared:.3f}) ===")
    print(m.summary().tables[1])
    return m


def plot_effects(m) -> None:
    ci = m.conf_int()
    labels = {"car_age": "+1 yıl yaş", "km10k": "+10.000 mil", "had_accident": "Kaza/hasar kaydı"}
    pct = lambda x: (np.exp(x) - 1) * 100
    fig, ax = plt.subplots(figsize=(7, 3.3))
    for i, k in enumerate(labels):
        v, lo, hi = pct(m.params[k]), pct(ci.loc[k, 0]), pct(ci.loc[k, 1])
        ax.barh(i, v, color="#b3402a" if k == "had_accident" else "#1c69d4", height=0.5)
        ax.plot([lo, hi], [i, i], color="black", lw=1.5)
        ax.text(min(lo, v) - 0.4, i, f"{v:.1f}%", va="center", ha="right", fontsize=9)
    ax.set_yticks(range(3))
    ax.set_yticklabels(labels.values())
    ax.invert_yaxis()
    ax.axvline(0, color="gray", lw=0.8)
    ax.set_xlim(-22, 2)
    ax.set_xlabel("Fiyata etkisi (%, diğer değişkenler sabitken; çizgi = %95 güven aralığı)")
    ax.set_title("Fiyatı Ne Kadar Etkiliyor? (Log-lineer OLS, marka kontrollü)")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(OUT / "effects.png", dpi=150)
    plt.close()


# ---------- 4) Random Forest ----------
def fit_random_forest(df: pd.DataFrame) -> None:
    s = df[df.brand.isin(BRANDS)].dropna(subset=["had_accident", "fuel_type"]).copy()
    feats = ["brand", "car_age", "mileage", "had_accident", "fuel_type"]
    X_tr, X_te, y_tr, y_te = train_test_split(s[feats], s.price, test_size=0.2, random_state=42)
    pipe = Pipeline([
        ("prep", ColumnTransformer(
            [("cat", OneHotEncoder(handle_unknown="ignore"), ["brand", "fuel_type"])],
            remainder="passthrough")),
        ("rf", RandomForestRegressor(n_estimators=300, max_depth=8, random_state=42)),
    ])
    pipe.fit(X_tr, y_tr)
    pred = pipe.predict(X_te)
    mape = np.median(np.abs(pred - y_te) / y_te) * 100
    print(f"\n=== Random Forest (n={len(s)}, test={len(y_te)}) ===")
    print(f"R²={r2_score(y_te, pred):.3f}  MAE=${mean_absolute_error(y_te, pred):,.0f}  "
          f"medyan yüzdesel hata={mape:.0f}%")

    kfmt = mt.FuncFormatter(lambda x, p: f"${x/1000:.0f}k")
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    ax.scatter(y_te, pred, alpha=0.55, s=22, color="#1c69d4")
    lim = [0, max(y_te.max(), pred.max()) * 1.05]
    ax.plot(lim, lim, "k--", lw=1)
    ax.set_xlabel("Gerçek fiyat")
    ax.set_ylabel("Tahmin edilen fiyat")
    ax.set_title(f"Random Forest (test seti): R² = {r2_score(y_te, pred):.2f}")
    ax.xaxis.set_major_formatter(kfmt)
    ax.yaxis.set_major_formatter(kfmt)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(OUT / "model_performance.png", dpi=150)
    plt.close()


def plot_depreciation(df: pd.DataFrame) -> None:
    kfmt = mt.FuncFormatter(lambda x, p: f"${x/1000:.0f}k")
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for b in BRANDS:
        g = df[df.brand == b].groupby("car_age").price.agg(["mean", "count"])
        g = g[g["count"] >= 3]  # gürültüyü azaltmak için en az 3 ilan
        ax.plot(g.index, g["mean"], marker="o", ms=3, lw=2, label=b, color=COLORS[b])
    ax.set_xlabel("Araç yaşı (yıl, en yeni model yılı = 0)")
    ax.set_ylabel("Ortalama fiyat")
    ax.set_title("Yaşa Göre Ortalama İkinci El Fiyatı (her nokta ≥3 ilan)")
    ax.yaxis.set_major_formatter(kfmt)
    ax.legend(frameon=False)
    ax.set_xlim(0, 20)
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig(OUT / "depreciation_curve.png", dpi=150)
    plt.close()


if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "used_cars.csv"
    data = load_and_clean(csv_path)
    print(f"Temizlenmiş kayıt: {len(data)} | Borusan markaları: {data.brand.isin(BRANDS).sum()}")
    run_sql(data)
    model = fit_ols(data)
    plot_effects(model)
    fit_random_forest(data)
    plot_depreciation(data)
    print(f"\nGrafikler ve veritabanı '{OUT}/' klasörüne kaydedildi.")
