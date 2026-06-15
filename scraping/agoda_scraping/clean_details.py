"""
clean_details.py
────────────────
Membaca semua file results/raw_details/detail_*.json,
mengekstrak per hotel:
  - name
  - favoriteFeatures
  - reviews (originalComment + rating)
Menyimpan 1 file per hotel ke:
  results/cleaned_data/hotel_<propertyId>.json
"""

import json
import glob
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")

DETAIL_DIR = os.path.join(RESULTS_DIR, "raw_details")
OUTPUT_DIR = os.path.join(RESULTS_DIR, "cleaned_data")


def extract_favorite_features(graphql: dict) -> list[str]:
    try:
        prop_details = (
            graphql.get("data", {})
                   .get("propertyDetailsSearch", {})
                   .get("propertyDetails", [])
        )
        if not prop_details:
            return []
        features = (
            prop_details[0]
            .get("contentDetail", {})
            .get("contentHighlights", {})
            .get("favoriteFeatures", [])
        )
        return [f.get("name", "") for f in features if f.get("name")]
    except Exception:
        return []


def extract_reviews(reviews_data: dict) -> list[dict]:
    result = []
    try:
        comments = (
            reviews_data.get("commentList", {})
                        .get("comments", [])
        )
    except Exception:
        return result

    for c in comments:
        reviewer = c.get("reviewerInfo") or {}
        result.append({
            "hotelReviewId":   c.get("hotelReviewId"),
            "rating":          c.get("rating"),
            "ratingText":      c.get("ratingText"),
            "reviewDate":      c.get("reviewDate"),
            "reviewTitle":     c.get("reviewTitle"),
            "originalTitle":   c.get("originalTitle"),
            "originalComment": c.get("originalComment"),
            "reviewComments":  c.get("reviewComments"),
            "reviewPositives": c.get("reviewPositives"),
            "reviewNegatives": c.get("reviewNegatives"),
            "reviewerCountry": reviewer.get("countryName"),
            "reviewGroupName": reviewer.get("reviewGroupName"),
            "roomTypeName":    reviewer.get("roomTypeName"),
            "lengthOfStay":    reviewer.get("lengthOfStay"),
        })

    return result


def process_all():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(glob.glob(os.path.join(DETAIL_DIR, "detail_*.json")))
    if not files:
        print(f"[ERR] Tidak ada file di '{DETAIL_DIR}/'")
        return

    print(f"{'='*60}")
    print(f"[CLEAN] Memproses {len(files)} file detail hotel...")
    print(f"{'='*60}\n")

    success = 0
    skipped = 0

    for fpath in files:
        fname = os.path.basename(fpath)
        try:
            with open(fpath, encoding="utf-8") as f:
                d = json.load(f)
        except Exception as e:
            print(f"  [ERR] {fname}: gagal baca - {e}")
            skipped += 1
            continue

        property_id  = d.get("propertyId")
        hotel_name   = d.get("name") or f"Hotel {property_id}"
        graphql      = d.get("graphql") or {}
        reviews_data = d.get("reviews") or {}

        fav_features = extract_favorite_features(graphql)
        reviews      = extract_reviews(reviews_data)

        # Struktur output 1 hotel
        cleaned = {
            "propertyId":       property_id,
            "name":             hotel_name,
            "favoriteFeatures": fav_features,
            "reviews":          reviews,
        }

        out_path = os.path.join(OUTPUT_DIR, f"hotel_{property_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2, ensure_ascii=False)

        print(f"  [OK] {fname} -> hotel_{property_id}.json "
              f"({len(fav_features)} fitur, {len(reviews)} review)")
        success += 1

    print(f"\n{'='*60}")
    print(f"[DONE] Berhasil : {success} file")
    print(f"       Gagal    : {skipped} file")
    print(f"       Output   : {OUTPUT_DIR}/hotel_<id>.json")
    print(f"{'='*60}")


if __name__ == "__main__":
    process_all()
