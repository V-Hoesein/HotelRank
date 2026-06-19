def calculate_c1_score(favorite_features):
    """
    Hitung nilai mentah Fasilitas Hotel (C1) berdasarkan kategori.
    Max score: 0.45
    """
    if not favorite_features:
        return 0.0

    features = [f.lower() for f in favorite_features]
    
    score = 0.0
    
    # 1. Internet & Connectivity (0.10)
    if any('wifi' in f or 'wi-fi' in f or 'internet' in f for f in features):
        score += 0.10
        
    # 2. Food & Beverage (0.15)
    food_kws = ['breakfast', 'coffee shop', 'halal', 'restaurant', 'bar', 'vending machine', 'kitchen']
    if any(any(kw in f for kw in food_kws) for f in features):
        score += 0.15
        
    # 3. Room Service & Comfort (0.10)
    comfort_kws = ['room service', 'housekeeping', 'laundry', 'dry cleaning', 'air conditioning', 'blackout', 'linens', 'balcony', 'terrace']
    if any(any(kw in f for kw in comfort_kws) for f in features):
        score += 0.10
        
    # 4. Transportation (0.05)
    transport_kws = ['airport', 'car park', 'shuttle']
    if any(any(kw in f for kw in transport_kws) for f in features):
        score += 0.05
        
    # 5. Recreation (0.03)
    rec_kws = ['fitness', 'pool', 'sauna', 'hot tub', 'spring', 'massage', 'garden', 'beach', 'fishing', 'hiking', 'tours']
    if any(any(kw in f for kw in rec_kws) for f in features):
        score += 0.03
        
    # 6. Other Facilities (0.02)
    other_kws = ['elevator', 'shop', 'cash', 'safety', 'lounge', 'check-in', 'check-out', 'express', 'luggage', 'concierge', 'ticket', 'smoking', 'convenience']
    if any(any(kw in f for kw in other_kws) for f in features):
        score += 0.02
        
    return score

def calculate_average_rating(reviews):
    """
    Hitung rata-rata rating (C3) dari daftar ulasan.
    Max score: 10.0
    """
    if not reviews:
        return 0.0
        
    total_rating = 0.0
    count = 0
    for r in reviews:
        if r.get('rating') is not None:
            total_rating += r['rating']
            count += 1
            
    return total_rating / count if count > 0 else 0.0

def rank_hotels_with_saw(hotels_data):
    """
    Terapkan algoritma SAW untuk memeringkat hotel.
    """
    # 1. Ekstrak Matrix Keputusan (X)
    for hotel in hotels_data:
        # C1: Fasilitas
        hotel['c1_raw'] = calculate_c1_score(hotel.get('favoriteFeatures', []))
        
        # C2: Score Sentiment
        # Pastikan tidak None
        sentiment = hotel.get('averageSentimentScore')
        hotel['c2_raw'] = sentiment if sentiment is not None else 0.0
        
        # C3: Rating
        hotel['c3_raw'] = calculate_average_rating(hotel.get('reviews', []))
        
    # 2. Cari Nilai Max untuk setiap kriteria (semua kriteria adalah Benefit)
    max_c1 = max([h['c1_raw'] for h in hotels_data], default=0.0001)
    max_c2 = max([h['c2_raw'] for h in hotels_data], default=0.0001)
    max_c3 = max([h['c3_raw'] for h in hotels_data], default=0.0001)
    
    # Mencegah division by zero
    if max_c1 == 0: max_c1 = 1.0
    if max_c2 == 0: max_c2 = 1.0
    if max_c3 == 0: max_c3 = 1.0
    
    # Bobot
    w_c1 = 0.45
    w_c2 = 0.30
    w_c3 = 0.25
    
    # 3. Normalisasi (R) & Hitung SAW Score (V)
    for hotel in hotels_data:
        # Normalisasi
        r_c1 = hotel['c1_raw'] / max_c1
        r_c2 = hotel['c2_raw'] / max_c2
        r_c3 = hotel['c3_raw'] / max_c3
        
        # Simpan nilai normalisasi & weighted untuk ditampilkan
        hotel['c1_norm'] = r_c1
        hotel['c2_norm'] = r_c2
        hotel['c3_norm'] = r_c3
        
        hotel['c1_weighted'] = w_c1 * r_c1
        hotel['c2_weighted'] = w_c2 * r_c2
        hotel['c3_weighted'] = w_c3 * r_c3
        
        # Hitung Nilai Akhir SAW (V) - Skala maksimal 1.0
        v_score = (w_c1 * r_c1) + (w_c2 * r_c2) + (w_c3 * r_c3)
        hotel['saw_score'] = v_score  
        
    # 4. Urutkan berdasarkan saw_score secara descending
    hotels_data.sort(key=lambda x: x.get('saw_score', 0), reverse=True)
    
    # 5. Tambahkan rank index
    for index, hotel in enumerate(hotels_data):
        hotel['rank'] = index + 1
        
    return hotels_data
