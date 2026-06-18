# HotelRank 🏨

HotelRank adalah sistem cerdas yang dirancang untuk mengumpulkan, membersihkan, dan menganalisis ulasan hotel secara otomatis. Sistem ini menggabungkan web scraping (*Playwright*) dengan Machine Learning (*Logistic Regression + TF-IDF*) untuk menganalisis sentimen ulasan pengunjung dan memberikan peringkat (ranking) hotel dari yang terbaik hingga terburuk.

---

## 📂 Struktur Direktori

Project ini dibagi menjadi tiga bagian utama agar rapi dan mudah dikelola:

```text
HotelRank/
├── app/                # (Tahap Pengembangan) Kode website antarmuka menggunakan Flask
├── data/               # Tempat penyimpanan semua file data
│   ├── analyzed/       # Hasil akhir sentimen dari tiap hotel
│   ├── cleaned/        # Data mentah hotel yang sudah dibersihkan
│   └── raw/            # Data JSON mentah hasil scraping dari Agoda
├── scraping/           # Kumpulan script Playwright untuk menyedot data dari web
├── sentiment/          # Logika kecerdasan buatan & Machine Learning
└── tests/              # Kumpulan file untuk pengujian (Unit Test)
```

---

## 🛠️ Persiapan (Environment Setup)

Sebelum menjalankan sistem ini, pastikan Anda telah menginstal dependensi yang dibutuhkan:

1. **Install library Python:**
   Pastikan Anda berada di direktori utama `HotelRank`, lalu jalankan:
   ```bash
   pip install playwright flask pytest pandas scikit-learn joblib kagglehub
   ```

2. **Install Browser Playwright:**
   Digunakan oleh bot untuk membuka browser secara otomatis:
   ```bash
   playwright install chromium
   ```

---

## 🚀 Cara Menjalankan Pipeline (Step-by-Step)

Ikuti urutan langkah di bawah ini untuk menjalankan keseluruhan sistem dari awal hingga akhir.

### Tahap 1: Melatih Model AI (Training)
Sebelum menganalisis ulasan, kita perlu membuat "otak" AI terlebih dahulu. Model ini dilatih menggunakan dataset dari Kaggle (Inggris) dan corpus lokal (Indonesia).
```bash
python -m sentiment.train_model
```
> **Output:** Akan menghasilkan file `sentiment_model.joblib` di direktori utama.

### Tahap 2: Mengambil Data (Scraping)
*Catatan: Sistem keamanan Agoda mungkin memblokir akses otomatis. Jika terjadi error, Anda mungkin harus menggunakan proxy atau mematikan mode headless.*

1. **Mencari Hotel:**
   ```bash
   python scraping/fetch_search.py
   ```
2. **Menggabungkan Hasil Pencarian:**
   Jika ada banyak *response*, gabungkan menjadi satu daftar utuh:
   ```bash
   python scraping/merge_responses.py
   ```
3. **Mendapatkan Detail & Ulasan Hotel:**
   Script ini akan membaca hasil pencarian dan mengunjungi setiap halaman hotel untuk menarik datanya secara spesifik.
   ```bash
   python scraping/fetch_details.py
   ```
> **Output:** File hasil scraping mentah dan kotor akan disimpan di `data/raw/raw_details/`.

### Tahap 3: Pembersihan Data (Cleaning)
Membersihkan ribuan baris JSON kotor dari Agoda agar tersisa informasi pentingnya saja (Nama Hotel, Fasilitas, dan Teks Review).
```bash
python scraping/clean_details.py
```
> **Output:** Data JSON hotel yang sudah bersih akan disimpan di `data/cleaned/`.

### Tahap 4: Analisis Sentimen (Sentiment Analyzer)
Menganalisis teks ulasan yang sudah bersih menggunakan model yang telah kita latih di Tahap 1 untuk mendapatkan skor sentimen.
```bash
python sentiment/analyzer.py
```
> **Output:** Hasil kalkulasi sentimen per hotel (dari skala 0-100) akan disimpan di `data/analyzed/`. File ini siap digunakan untuk membuat urutan peringkat (ranking)!

### Tahap 5: Menjalankan Web App
Jika Anda ingin melihat hasilnya di browser melalui antarmuka website:
```bash
python run.py
```
> *Pastikan file di dalam `app/` sudah dikonfigurasi untuk membaca dari folder `data/analyzed/`.*

---

## 💡 Troubleshooting
Jika Anda menemui pesan *Error* seperti `UnicodeEncodeError` di terminal Windows saat melakukan scraping, Anda bisa memaksakan terminal untuk menggunakan format `UTF-8` dengan perintah berikut:

**PowerShell:**
```powershell
$env:PYTHONIOENCODING="utf-8"
python scraping/fetch_search.py
```
