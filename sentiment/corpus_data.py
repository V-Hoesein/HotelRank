"""
corpus_data.py
──────────────
Kumpulan data latih (bootstrap) sederhana berisi ulasan dalam bahasa Indonesia dan Inggris.
Digunakan untuk men-training model Naive Bayes jika belum ada dataset yang lebih besar.
"""

POSITIVE_REVIEWS = [
    # Indonesian
    "kamar sangat bersih",
    "pelayanan ramah dan cepat",
    "kamar mandi harum dan bersih",
    "lokasi sangat strategis dekat dengan pusat perbelanjaan",
    "sarapan sangat enak dan bervariasi",
    "staf sangat membantu",
    "tempat tidur nyaman dan empuk",
    "suasana hotel tenang dan nyaman",
    "kolam renang bersih dan luas",
    "harga sangat sepadan dengan kualitas",
    "pasti akan kembali menginap di sini",
    "sangat direkomendasikan",
    "fasilitas lengkap dan berfungsi baik",
    "proses check-in sangat mudah dan cepat",
    "pemandangan dari kamar sangat indah",
    "hotel terbaik yang pernah saya kunjungi",
    "kebersihan sangat terjaga",
    "kamar luas dan terang",
    "internet wifi sangat cepat",
    "parkiran luas",
    "sangat puas menginap di sini",
    
    # English
    "room is very clean",
    "friendly and fast service",
    "bathroom is fragrant and clean",
    "great location near shopping center",
    "breakfast is delicious with many varieties",
    "staff is very helpful",
    "bed is comfortable and soft",
    "hotel atmosphere is quiet and cozy",
    "swimming pool is clean and spacious",
    "great value for money",
    "will definitely come back to stay here",
    "highly recommended",
    "complete facilities and working fine",
    "check-in process was easy and fast",
    "beautiful view from the room",
    "best hotel I have ever visited",
    "cleanliness is well maintained",
    "room is spacious and bright",
    "fast wifi internet",
    "spacious parking",
    "very satisfied staying here"
]

NEGATIVE_REVIEWS = [
    # Indonesian
    "kamar kotor dan bau",
    "pelayanan sangat buruk dan lambat",
    "kamar mandi kotor dan air tidak menyala",
    "lokasi sangat jauh dari mana-mana",
    "sarapan tidak enak dan hambar",
    "staf tidak ramah dan kasar",
    "tempat tidur keras dan gatal",
    "suasana hotel sangat berisik",
    "kolam renang kotor",
    "harga terlalu mahal untuk fasilitas seadanya",
    "tidak akan pernah kembali menginap di sini",
    "sangat tidak direkomendasikan",
    "fasilitas rusak dan tidak bisa digunakan",
    "proses check-in lambat dan berbelit-belit",
    "pemandangan dari kamar buruk",
    "hotel terburuk yang pernah saya kunjungi",
    "banyak kecoa dan semut di kamar",
    "kamar sempit dan pengap",
    "internet wifi sangat lambat bahkan mati",
    "parkiran susah didapat",
    "sangat kecewa menginap di sini",
    "ac tidak dingin",
    "air panas tidak berfungsi",

    # English
    "room is dirty and smelly",
    "very poor and slow service",
    "bathroom is dirty and water is not running",
    "location is far from everywhere",
    "breakfast is tasteless and bad",
    "staff is unfriendly and rude",
    "bed is hard and itchy",
    "hotel atmosphere is very noisy",
    "swimming pool is dirty",
    "overpriced for poor facilities",
    "will never come back to stay here",
    "not recommended at all",
    "broken facilities and unusable",
    "slow and complicated check-in process",
    "bad view from the room",
    "worst hotel I have ever visited",
    "many cockroaches and ants in the room",
    "room is cramped and stuffy",
    "very slow wifi internet even dead",
    "hard to find parking",
    "very disappointed staying here",
    "ac is not cold",
    "hot water is not working"
]

def get_training_data():
    """
    Mengembalikan data latih berupa tuple (corpus, labels).
    Label: 1 untuk positif, 0 untuk negatif.
    """
    corpus = POSITIVE_REVIEWS + NEGATIVE_REVIEWS
    labels = [1] * len(POSITIVE_REVIEWS) + [0] * len(NEGATIVE_REVIEWS)
    return corpus, labels
