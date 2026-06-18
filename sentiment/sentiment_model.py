"""
naive_bayes_model.py
────────────────────
Modul untuk memuat dan menggunakan model sentimen gabungan (Inggris & Indonesia).
Catatan: Nama file tetap naive_bayes_model untuk kompatibilitas, namun
model di baliknya sudah menggunakan Logistic Regression + TF-IDF (sentiment_model.joblib).
"""

import os
import joblib

# Path ke model gabungan di root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "sentiment_model.joblib")

def load_model():
    """
    Memuat model gabungan yang sudah di-training oleh train_sentiment.py
    """
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    else:
        raise FileNotFoundError(f"[MODEL] Model {MODEL_PATH} tidak ditemukan! Silakan jalankan 'python train_sentiment.py' di root folder terlebih dahulu.")

class SentimentAnalyzer:
    def __init__(self):
        self.model = load_model()
        
    def predict_score(self, text: str) -> float:
        """
        Memprediksi skor sentimen dari teks.
        Mengembalikan nilai probabilitas kelas positif (0.0 hingga 1.0).
        """
        if not text or not isinstance(text, str):
            return 0.5  # Sentimen netral jika kosong/invalid
            
        # preprocess_text seharusnya diaplikasikan, tapi pipeline tfidf lowercase=True
        # Kita pakai saja langsung karena pipeline menangani string dasar
        
        # predict_proba mengembalikan probabilitas [negatif, positif]
        probas = self.model.predict_proba([text])
        positive_prob = probas[0][1]
        
        return positive_prob
