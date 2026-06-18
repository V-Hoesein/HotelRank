# HotelRank 🏨

HotelRank adalah sistem cerdas yang dirancang untuk mengumpulkan, membersihkan, dan menganalisis ulasan hotel secara otomatis. Sistem ini menggabungkan web scraping (*Playwright*), Machine Learning (*Logistic Regression + TF-IDF*) untuk mendeteksi sentimen, dan Sistem Pendukung Keputusan (SPK) menggunakan metode **SAW (Simple Additive Weighting)** untuk memberikan peringkat (ranking) hotel yang paling akurat dari yang terbaik hingga terburuk.

---

## 🏗️ Technical App Flow & Logic

Alur kerja aplikasi dirancang secara otomatis (pipeline) dengan skema berikut:

1. **Scraping Engine**: Mengambil data kotor dari website Agoda (Informasi Hotel, Fasilitas, dan Ulasan Pengunjung).
2. **Data Cleaning**: Membersihkan file JSON kotor, membuang key yang tidak relevan, dan hanya menyisakan atribut penting.
3. **Machine Learning Model**: Model AI dilatih (Training) dengan Dataset Bahasa Inggris dan Bahasa Indonesia untuk mempelajari pola kalimat positif, netral, dan negatif.
4. **Sentiment Analyzer**: Menganalisis ulasan hotel yang sudah dibersihkan ke dalam model Machine Learning untuk mendapatkan `averageSentimentScore` (0-100).
5. **Decision Support System (SAW)**: Menerapkan algoritma cerdas untuk menggabungkan skor Fasilitas, skor Sentimen, dan Rating asli menggunakan pembobotan tertentu.
6. **Web Dashboard (Flask)**: Menampilkan data akhir hasil algoritma SAW ke dalam antarmuka visual yang modern dan premium (Dark Glassmorphism).

---

## 🧮 Logika Algoritma SAW (Simple Additive Weighting)

Untuk menentukan *ranking* suatu hotel, sistem ini tidak hanya mengandalkan sentimen. Kami mengkombinasikan tiga kriteria (*Benefit*) dengan bobot masing-masing:

- **C1 (Fasilitas Hotel)** - Bobot: 45% (0.45)
- **C2 (Score Sentiment)** - Bobot: 30% (0.30)
- **C3 (Rata-rata Rating)** - Bobot: 25% (0.25)

### 1. Perhitungan Kriteria Fasilitas (C1)
Sistem akan membaca list `favoriteFeatures` dari setiap JSON hotel, kemudian mencocokkannya ke dalam 6 kategori. Jika suatu hotel memiliki setidaknya 1 fitur di kategori tersebut, hotel mendapat bobot kategori secara utuh:
- *Internet & Connectivity* (0.10) - contoh: Free Wi-Fi
- *Food & Beverage* (0.15) - contoh: Breakfast, Restaurant
- *Room Service & Comfort* (0.10) - contoh: Room service, AC
- *Transportation* (0.05) - contoh: Airport transfer
- *Recreation* (0.03) - contoh: Pool, Fitness, Sauna
- *Other Facilities* (0.02) - contoh: Elevator, Smoking area

*Nilai mentah maksimal C1 adalah 0.45.*

### 2. Rumus Normalisasi Matrix (R)
Nilai mentah dari masing-masing kriteria (*X*) dibagi dengan nilai mentah maksimum (*Max*) dari kriteria yang sama di seluruh daftar hotel. Karena semuanya bersifat *Benefit* (semakin tinggi semakin baik), rumusnya adalah:

`R_ij = X_ij / Max_j`

### 3. Perhitungan Skor Akhir (V)
Nilai Normalisasi (R) dikalikan dengan bobot kriteria aslinya (W), lalu dijumlahkan untuk mendapatkan Skor SAW akhir:

`V_i = (W_C1 * R_C1) + (W_C2 * R_C2) + (W_C3 * R_C3)`

Hasil `V_i` kemudian dikalikan 100 untuk menjadikannya rentang persentase (0-100) dan ditampilkan di UI Web Dashboard.

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

### Tahap 5: Menjalankan Web App (Dashboard)
Setelah semua data diproses dan algoritma SAW siap, Anda bisa melihat hasilnya dalam bentuk web antarmuka yang sangat modern:
```bash
python run.py
```
> *Buka `http://127.0.0.1:5000` di browser. Sistem secara otomatis akan mengeksekusi algoritma SAW di latar belakang (backend) dan menampilkan daftar hotel dengan peringkat terbaik di urutan teratas.*

---

## 💡 Troubleshooting
Jika Anda menemui pesan *Error* seperti `UnicodeEncodeError` di terminal Windows saat melakukan scraping, Anda bisa memaksakan terminal untuk menggunakan format `UTF-8` dengan perintah berikut:

**PowerShell:**
```powershell
$env:PYTHONIOENCODING="utf-8"
python scraping/fetch_search.py
```
