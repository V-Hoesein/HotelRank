import os
import sys
import kagglehub
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score
import joblib
import re

# Tambahkan path ke modul scraping untuk mengambil data corpus bahasa Indonesia
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'scraping', 'agoda_scraping')))
from sentiment.corpus_data import get_training_data

def preprocess_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def main():
    print("Mengunduh dataset dari Kaggle (Bahasa Inggris)...")
    path = kagglehub.dataset_download("abhi8923shriv/sentiment-analysis-dataset")
    csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
    csv_file_path = os.path.join(path, csv_files[0])
    
    try:
        df = pd.read_csv(csv_file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(csv_file_path, encoding='latin-1')
        
    df.columns = df.columns.str.strip().str.lower()
    
    text_col = 'text'
    sentiment_col = 'sentiment'
    if text_col not in df.columns or sentiment_col not in df.columns:
        text_cols = [c for c in df.columns if 'text' in c or 'tweet' in c or 'review' in c]
        sentiment_cols = [c for c in df.columns if 'sentiment' in c or 'label' in c or 'target' in c]
        if text_cols: text_col = text_cols[0]
        if sentiment_cols: sentiment_col = sentiment_cols[0]
            
    df = df.dropna(subset=[text_col, sentiment_col])
    
    # Konversi label Kaggle menjadi 1 (Positive) dan 0 (Negative)
    # Asumsi dataset kaggle sentimentnya string seperti 'positive', 'negative' atau 1, 0
    if df[sentiment_col].dtype == object:
        df['target'] = df[sentiment_col].astype(str).str.lower().apply(lambda x: 1 if 'pos' in x or x == '1' else 0)
    else:
        df['target'] = df[sentiment_col]
        
    df['cleaned_text'] = df[text_col].apply(preprocess_text)
    df = df[df['cleaned_text'].str.len() > 0]
    
    # Mengambil data corpus bahasa Indonesia
    print("Memuat data latih Bahasa Indonesia dari corpus_data.py...")
    indo_corpus, indo_labels = get_training_data()
    df_indo = pd.DataFrame({
        'cleaned_text': [preprocess_text(text) for text in indo_corpus],
        'target': indo_labels
    })
    
    # Menggabungkan dataset Inggris (Kaggle) dan Indonesia (Corpus)
    print("Menggabungkan dataset...")
    df_combined = pd.concat([df[['cleaned_text', 'target']], df_indo], ignore_index=True)
    
    # Acak dataset
    df_combined = df_combined.sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"Total dataset setelah digabung: {len(df_combined)} baris")

    print("Membagi dataset untuk training dan testing...")
    X_train, X_test, y_train, y_test = train_test_split(
        df_combined['cleaned_text'], 
        df_combined['target'], 
        test_size=0.2, 
        random_state=42, 
        stratify=df_combined['target']
    )
    
    print("Membangun dan melatih model Hybrid (Inggris + Indonesia)...")
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=10000, ngram_range=(1, 2))),
        ('clf', LogisticRegression(random_state=42, max_iter=1000, n_jobs=-1))
    ])
    
    pipeline.fit(X_train, y_train)
    
    y_pred = pipeline.predict(X_test)
    print(f"Akurasi: {accuracy_score(y_test, y_pred):.4f}")
    
    # Menyimpan model gabungan ke root direktori
    model_filename = 'sentiment_model.joblib'
    joblib.dump(pipeline, model_filename)
    print(f"Selesai! Model gabungan disimpan ke '{model_filename}'")

if __name__ == "__main__":
    main()
