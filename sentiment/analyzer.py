"""
analyzer.py
───────────
Membaca file JSON dari results/cleaned_data/,
menganalisis sentimen pada tiap review ('originalComment') menggunakan Naive Bayes,
menghitung rata-rata skor sentimen hotel,
dan menyimpan hasil akhirnya ke results/analyzed_data/
"""

import json
import glob
import os
import sys

# Tambahkan direktori root ke path agar bisa mengimport module jika dieksekusi dari luar
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentiment.sentiment_model import SentimentAnalyzer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEANED_DIR = os.path.join(BASE_DIR, "data", "cleaned")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "analyzed")

def process_all_sentiments():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    files = sorted(glob.glob(os.path.join(CLEANED_DIR, "hotel_*.json")))
    if not files:
        print(f"[ERR] Tidak ada file di '{CLEANED_DIR}/'")
        return

    print(f"{'='*60}")
    print(f"[SENTIMENT] Memulai analisis untuk {len(files)} hotel...")
    print(f"{'='*60}\n")
    
    analyzer = SentimentAnalyzer()
    success = 0
    
    for fpath in files:
        fname = os.path.basename(fpath)
        try:
            with open(fpath, encoding="utf-8") as f:
                d = json.load(f)
        except Exception as e:
            print(f"  [ERR] {fname}: gagal baca - {e}")
            continue

        reviews = d.get("reviews", [])
        total_score = 0.0
        valid_reviews = 0
        
        for review in reviews:
            comment = review.get("originalComment", "")
            if comment and str(comment).strip():
                # Prediksi probabilitas positif (0.0 - 1.0)
                score = analyzer.predict_score(comment)
                
                # Mengubah probabilitas 0.0-1.0 menjadi skala 0-100 agar lebih mudah dibaca untuk SAW
                score_100 = round(score * 100, 2)
                
                review["sentimentScore"] = score_100
                review["sentimentLabel"] = "Positive" if score >= 0.5 else "Negative"
                
                total_score += score_100
                valid_reviews += 1
            else:
                review["sentimentScore"] = None
                review["sentimentLabel"] = "Neutral"
                
        # Hitung rata-rata
        average_sentiment = 0.0
        if valid_reviews > 0:
            average_sentiment = round(total_score / valid_reviews, 2)
            
        d["averageSentimentScore"] = average_sentiment
        d["totalAnalyzedReviews"] = valid_reviews
        
        out_path = os.path.join(OUTPUT_DIR, fname)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)

        print(f"  [OK] {fname} -> Rata-rata Sentimen: {average_sentiment}/100 ({valid_reviews} ulasan dianalisis)")
        success += 1

    print(f"\n{'='*60}")
    print(f"[DONE] Berhasil diproses : {success} file")
    print(f"       Output disimpan di: {OUTPUT_DIR}/")
    print(f"{'='*60}")

if __name__ == "__main__":
    process_all_sentiments()
