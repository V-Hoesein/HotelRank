import asyncio
import json
import os
from playwright.async_api import async_playwright

REVIEW_URL   = "https://www.agoda.com/api/cronos/property/review/ReviewComments"
AGODA_HOME   = "https://www.agoda.com/"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")

OUTPUT_DIR   = os.path.join(RESULTS_DIR, "raw_reviews")

# ─── Konfigurasi review ────────────────────────────────────
HOTEL_ID          = 86738595
HOTEL_PROVIDER_ID = 332
PAGE_SIZE         = 50      # review per halaman
MAX_PAGES         = None    # None = ambil semua halaman, isi angka untuk batasi

BASE_PAYLOAD = {
    "hotelId":          HOTEL_ID,
    "providerId":       HOTEL_PROVIDER_ID,
    "demographicId":    0,
    "pageSize":         PAGE_SIZE,
    "sorting":          7,
    "providerIds":      [332],
    "isReviewPage":     False,
    "isCrawlablePage":  True,
    "filters": {
        "language": [],
        "room": []
    },
    "searchKeyword": "",
    "searchFilters": []
}
# ──────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────
# Step 1: Buka Agoda di browser untuk dapatkan headers/cookies
# ─────────────────────────────────────────────────────────────
async def get_agoda_context(playwright):
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        locale="en-US",
        viewport={"width": 1440, "height": 900},
    )
    page = await context.new_page()

    captured_headers: dict = {}

    # Intercept request apapun ke agoda untuk mendapatkan headers asli
    async def intercept(request):
        nonlocal captured_headers
        if not captured_headers and "agoda.com" in request.url:
            captured_headers = dict(request.headers)

    page.on("request", intercept)

    print("[INIT] Membuka Agoda untuk mendapatkan headers & cookies...")
    await page.goto(AGODA_HOME, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(2000)
    await page.close()

    # Bersihkan header yang berpotensi konflik
    for key in ["content-length", "accept-encoding", "content-type", "accept"]:
        captured_headers.pop(key, None)

    captured_headers["content-type"] = "application/json"
    captured_headers["accept"]       = "application/json, text/plain, */*"
    captured_headers["origin"]       = "https://www.agoda.com"
    captured_headers["referer"]      = f"https://www.agoda.com/hotel/{HOTEL_ID}"

    print(f"[INIT] Headers siap. ({len(captured_headers)} header ditangkap)")
    return browser, context, captured_headers


# ─────────────────────────────────────────────────────────────
# Step 2: Fetch satu halaman review
# ─────────────────────────────────────────────────────────────
async def fetch_review_page(context, headers: dict, page_no: int) -> dict | None:
    payload = {**BASE_PAYLOAD, "page": page_no}

    response = await context.request.post(
        REVIEW_URL,
        data=json.dumps(payload),
        headers=headers,
    )

    if response.status != 200:
        text = await response.text()
        print(f"  [ERR] Halaman {page_no}: status {response.status} - {text[:200]}")
        return None

    try:
        return await response.json()
    except Exception as e:
        print(f"  [ERR] Halaman {page_no}: gagal parse JSON - {e}")
        return None


# ─────────────────────────────────────────────────────────────
# Step 3: Ambil semua halaman review
# ─────────────────────────────────────────────────────────────
async def fetch_all_reviews():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_reviews   = []
    total_reviews = None
    page_no       = 1

    async with async_playwright() as p:
        browser, context, headers = await get_agoda_context(p)

        print(f"\n[FETCH] Mulai mengambil review hotel ID {HOTEL_ID}...")
        print(f"{'='*60}")

        while True:
            # Batasi halaman jika MAX_PAGES diset
            if MAX_PAGES is not None and page_no > MAX_PAGES:
                print(f"[STOP] Batas MAX_PAGES={MAX_PAGES} tercapai.")
                break

            print(f"[Hal. {page_no}] Mengambil {PAGE_SIZE} review...", end=" ", flush=True)
            data = await fetch_review_page(context, headers, page_no)

            if data is None:
                print("Gagal, berhenti.")
                break

            # Simpan raw response per halaman
            raw_path = os.path.join(OUTPUT_DIR, f"hotel_{HOTEL_ID}_page_{page_no:03d}.json")
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Coba ambil total review jika ada
            if total_reviews is None:
                total_reviews = (
                    data.get("totalReviewCount")
                    or data.get("data", {}).get("totalReviewCount")
                )
                if total_reviews:
                    total_pages = (total_reviews + PAGE_SIZE - 1) // PAGE_SIZE
                    print(f"\n[INFO] Total review: {total_reviews} (~{total_pages} halaman)", end="\n")
                else:
                    print(f"\n[INFO] Total review tidak diketahui dari response ini, akan terus fetch sampai habis.", end="\n")

            # Ekstrak daftar review dari response
            reviews = (
                data.get("comments")
                or data.get("data", {}).get("comments")
                or data.get("reviews")
                or data.get("data", {}).get("reviews")
                or []
            )

            if not reviews:
                print(f"  [STOP] Tidak ada review di halaman {page_no}, selesai.")
                break

            all_reviews.extend(reviews)
            print(f"  [OK] +{len(reviews)} review (total: {len(all_reviews)})")

            # Cek apakah sudah halaman terakhir
            if len(reviews) < PAGE_SIZE:
                print(f"  [DONE] Halaman terakhir tercapai.")
                break

            page_no += 1
            await asyncio.sleep(1)  # jeda antar request

        await browser.close()

    return all_reviews, total_reviews


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────
async def main():
    all_reviews, total_reviews = await fetch_all_reviews()

    print(f"\n{'='*60}")
    print(f"[STAT] Total review diambil : {len(all_reviews)}")
    print(f"[STAT] Total review di server: {total_reviews if total_reviews else 'Tidak diketahui'}")
    print(f"{'='*60}")

    if not all_reviews:
        print("[WARN] Tidak ada review yang berhasil diambil.")
        print(f"       Cek raw file di '{OUTPUT_DIR}/' untuk debug.")
        return

    # Simpan gabungan semua review
    out_path = os.path.join(OUTPUT_DIR, f"hotel_{HOTEL_ID}_all_reviews.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, indent=2, ensure_ascii=False)
    print(f"[SAVE] Semua review -> {out_path}")

    # Preview
    print("\n=== PREVIEW (3 pertama) ===")
    for r in all_reviews[:3]:
        print(json.dumps(r, ensure_ascii=False, indent=2)[:300])
        print("...")


if __name__ == "__main__":
    asyncio.run(main())
