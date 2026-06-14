"""
merge_responses.py
──────────────────
Membaca semua file response_*.json di folder agoda_responses/,
mengekstrak array dari data.citySearch.properties,
menggabungkan semuanya menjadi 1 array unik berdasarkan propertyId,
lalu menyimpan ke agoda/result_<keyword>.json
"""

import json
import glob
import os
import sys

RESPONSES_DIR = "agoda_responses"
OUTPUT_DIR    = "agoda"
KEYWORD       = "yogyakarta"   # ← ganti sesuai kota/keyword pencarian Anda


def extract_properties(filepath: str) -> list[dict]:
    """Ekstrak data.citySearch.properties dari satu file response."""
    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ⚠️  Gagal baca {os.path.basename(filepath)}: {e}")
        return []

    props = (
        data.get("data", {})
            .get("citySearch", {})
            .get("properties", [])
    )

    if not isinstance(props, list):
        return []

    return props


def merge_unique(all_props: list[dict]) -> list[dict]:
    """Gabungkan properties, deduplikasi berdasarkan propertyId."""
    seen     = {}
    skipped  = 0

    for prop in all_props:
        pid = prop.get("propertyId")
        if pid is None:
            skipped += 1
            continue
        if pid not in seen:
            seen[pid] = prop       # simpan pertama kali ditemukan

    if skipped:
        print(f"  ℹ️  {skipped} item dilewati (tidak punya propertyId)")

    return list(seen.values())


def main(keyword: str = KEYWORD):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(glob.glob(os.path.join(RESPONSES_DIR, "response_*.json")))
    if not files:
        print(f"❌ Tidak ada file di '{RESPONSES_DIR}/'")
        return

    print(f"{'='*55}")
    print(f"[MERGE] Response -> agoda/result_{keyword}.json")
    print(f"{'='*55}")
    print(f"[INFO] Ditemukan {len(files)} file response.\n")

    all_props = []
    for fpath in files:
        props = extract_properties(fpath)
        if props:
            all_props.extend(props)
            print(f"  [OK] {os.path.basename(fpath)}: {len(props)} properties")
        else:
            print(f"  [--] {os.path.basename(fpath)}: (tidak ada properties)")

    print(f"\n[STAT] Total mentah sebelum deduplikasi : {len(all_props)}")

    unique_props = merge_unique(all_props)
    print(f"[STAT] Total unik setelah deduplikasi   : {len(unique_props)}")

    out_path = os.path.join(OUTPUT_DIR, f"result_{keyword}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(unique_props, f, indent=2, ensure_ascii=False)

    print(f"\n[SAVE] Tersimpan ke -> {out_path}")
    print(f"{'='*55}")


if __name__ == "__main__":
    kw = sys.argv[1] if len(sys.argv) > 1 else KEYWORD
    main(kw)
