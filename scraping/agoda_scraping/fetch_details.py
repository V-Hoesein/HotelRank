"""
fetch_details.py
────────────────
Membaca result_*.json dari folder results/search_results/,
mengunjungi setiap halaman hotel (propertyPage),
menangkap response dari:
  - POST https://www.agoda.com/graphql/property
  - POST https://www.agoda.com/api/cronos/property/review/HotelReviews
lalu menyimpannya ke results/raw_details/detail_<hotelId>.json
"""

import asyncio
import json
import glob
import os
import sys
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")

AGODA_BASE  = "https://www.agoda.com"
OUTPUT_DIR  = os.path.join(RESULTS_DIR, "raw_details")
RESULT_DIR  = os.path.join(RESULTS_DIR, "search_results")

# Jeda antar hotel (detik) — jangan terlalu cepat
DELAY_BETWEEN_HOTELS = 2

# Timeout menunggu kedua response muncul (detik)
CAPTURE_TIMEOUT = 20

# Jalankan browser secara tersembunyi
HEADLESS = False


# ─────────────────────────────────────────────────────────────
# Baca semua hotel dari result_*.json
# ─────────────────────────────────────────────────────────────
def load_hotels(result_file: str | None = None) -> list[dict]:
    if result_file:
        files = [result_file]
    else:
        files = sorted(glob.glob(os.path.join(RESULT_DIR, "result_*.json")))

    if not files:
        print(f"[ERR] Tidak ada file result_*.json di folder '{RESULT_DIR}/'")
        return []

    hotels = []
    for fpath in files:
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
        hotels.extend(data)
        print(f"[LOAD] {os.path.basename(fpath)}: {len(data)} hotel")

    return hotels


# ─────────────────────────────────────────────────────────────
# Ekstrak info dasar dari setiap hotel entry
# ─────────────────────────────────────────────────────────────
def extract_hotel_info(prop: dict) -> dict | None:
    property_id  = prop.get("propertyId")
    content      = prop.get("content", {})
    info         = content.get("informationSummary", {})
    property_page = (
        info.get("propertyLinks", {}).get("propertyPage")
    )

    if not property_id or not property_page:
        return None

    return {
        "propertyId":   property_id,
        "name":         info.get("displayName"),
        "propertyPage": property_page,
        "url":          AGODA_BASE + property_page,
    }


# ─────────────────────────────────────────────────────────────
# Kunjungi satu halaman hotel & tangkap kedua response
# ─────────────────────────────────────────────────────────────
async def capture_hotel_detail(context, hotel: dict) -> dict:
    url         = hotel["url"]
    property_id = hotel["propertyId"]

    captured = {
        "propertyId":    property_id,
        "name":          hotel["name"],
        "propertyPage":  hotel["propertyPage"],
        "graphql":       None,   # response dari graphql/property
        "reviews":       None,   # response dari HotelReviews
    }

    done_graphql = asyncio.Event()
    done_reviews = asyncio.Event()

    async def on_response(response):
        req = response.request
        if req.method != "POST":
            return

        # Tangkap graphql/property
        if "graphql/property" in response.url and captured["graphql"] is None:
            try:
                captured["graphql"] = await response.json()
                done_graphql.set()
            except Exception as e:
                print(f"    [WARN] graphql/property parse error: {e}")
                done_graphql.set()

        # Tangkap HotelReviews atau ReviewComments (keduanya bisa muncul tergantung flow)
        elif ("review/HotelReviews" in response.url or "review/ReviewComments" in response.url):
            try:
                review_data = await response.json()
                if captured["reviews"] is None:
                    captured["reviews"] = []
                captured["reviews"].append(review_data)
                done_reviews.set()
                print(f"    [VISUAL] Menangkap data review halaman ke-{len(captured['reviews'])}")
            except Exception as e:
                print(f"    [WARN] Reviews parse error: {e}")
                done_reviews.set()

    page = await context.new_page()
    page.on("response", on_response)

    try:
        print(f"    [VISUAL] Membuka {url}...")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Step 1: Tekan Escape 3x untuk menutup semua popup/kalender/backdrop
        print("    [VISUAL] Tekan Escape 3x untuk tutup popup...")
        for _ in range(3):
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)

        # Step 2: Scroll sedikit ke bawah agar navbar muncul, lalu klik tab "Reviews"
        print("    [VISUAL] Scroll agar navbar muncul...")
        await page.mouse.wheel(0, 600)
        await asyncio.sleep(2)  # Beri waktu lebih untuk render

        print("    [VISUAL] Klik tab Reviews di navbar...")
        clicked = False
        for attempt in range(3):  # Coba maksimal 3x
            try:
                reviews_tab = page.locator('button[data-element-name="customer-reviews-panel-navbar-menu"]').first
                await reviews_tab.wait_for(state="attached", timeout=8000)
                await reviews_tab.evaluate("node => node.click()")
                await asyncio.sleep(2)
                print(f"    [VISUAL] Tab Reviews berhasil diklik! (percobaan {attempt+1})")
                clicked = True
                break
            except Exception as e:
                print(f"    [WARN] Percobaan {attempt+1} gagal: {e}")
                await page.mouse.wheel(0, 200)
                await asyncio.sleep(1)

        if not clicked:
            print("    [WARN] Tombol Reviews tidak berhasil diklik setelah 3x percobaan.")

        # Step 3: Tunggu modal Reviews muncul (modal bisa tidak muncul di beberapa hotel)
        print("    [VISUAL] Menunggu modal Reviews terbuka...")
        try:
            modal = page.locator('[data-testid="property-info-modal-reviews"]')
            await modal.wait_for(state="visible", timeout=15000)
            print("    [VISUAL] Modal Reviews terbuka!")
        except Exception as e:
            print("    [INFO] Modal Reviews tidak muncul — mungkin Agoda langsung scroll ke section reviews.")

        # Tunggu hingga kedua response API tertangkap atau timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(done_graphql.wait(), done_reviews.wait()),
                timeout=CAPTURE_TIMEOUT
            )
            print("    [VISUAL] Data API tertangkap!")

            # Step 4: Loop klik Next Pagination sampai tidak ada tombol lagi
            await asyncio.sleep(1)
            page_num = 1
            while True:
                try:
                    # Scroll sedikit ke bawah untuk memicu lazy load/render pagination jika inline
                    await page.mouse.wheel(0, 800)
                    await asyncio.sleep(1)

                    # Cari di seluruh halaman (karena reviews bisa inline atau di dalam modal)
                    next_btn = page.locator(
                        'button[data-element-name="review-paginator-next"], '
                        'button[aria-label="Next reviews page"]'
                    )
                    count = await next_btn.count()
                    if count == 0:
                        print(f"    [VISUAL] Halaman {page_num}: Tombol Next tidak ada di DOM, selesai.")
                        break

                    # Cek apakah tombol disabled (sudah di halaman terakhir)
                    is_disabled = await next_btn.first.get_attribute("disabled")
                    if is_disabled is not None:
                        print(f"    [VISUAL] Halaman {page_num}: Tombol Next disabled, sudah halaman terakhir.")
                        break

                    print(f"    [VISUAL] Halaman {page_num} -> klik Next Pagination...")
                    await next_btn.first.scroll_into_view_if_needed()
                    await next_btn.first.evaluate("node => node.click()")
                    page_num += 1
                    await asyncio.sleep(2)  # Tunggu data halaman berikutnya dimuat

                except Exception as e:
                    print(f"    [VISUAL] Gagal klik Next Pagination: {e}")
                    break

        except asyncio.TimeoutError:
            missing = []
            if not done_graphql.is_set():
                missing.append("graphql/property")
            if not done_reviews.is_set():
                missing.append("HotelReviews")
            print(f"    [TIMEOUT] Tidak tertangkap: {', '.join(missing)}")

    except Exception as e:
        print(f"    [ERR] Gagal buka halaman: {e}")
    finally:
        await page.close()

    return captured


# ─────────────────────────────────────────────────────────────
# Simpan detail ke file JSON
# ─────────────────────────────────────────────────────────────
def save_detail(detail: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"detail_{detail['propertyId']}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(detail, f, indent=2, ensure_ascii=False)
    return out_path


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────
async def main(result_file: str | None = None):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load semua hotel
    raw_hotels = load_hotels(result_file)
    if not raw_hotels:
        return

    hotels = [h for h in (extract_hotel_info(p) for p in raw_hotels) if h]
    print(f"\n[INFO] {len(hotels)} hotel siap diproses dari {len(raw_hotels)} total.\n")

    # 2. Cek hotel yang sudah selesai (skip jika sudah ada file detail-nya)
    already_done = {
        int(os.path.basename(f).replace("detail_", "").replace(".json", ""))
        for f in glob.glob(os.path.join(OUTPUT_DIR, "detail_*.json"))
    }
    todo = [h for h in hotels if h["propertyId"] not in already_done]
    skipped = len(hotels) - len(todo)
    if skipped:
        print(f"[SKIP] {skipped} hotel sudah punya file detail, dilanjutkan dari yang belum.\n")

    if not todo:
        print("[OK] Semua hotel sudah selesai diproses.")
        return

    print(f"{'='*60}")
    print(f"Agoda Detail Scraper — {len(todo)} hotel akan diproses")
    print(f"{'='*60}\n")

    # 3. Buka browser sekali untuk semua hotel
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1440, "height": 900},
        )

        success = 0
        partial = 0
        failed  = 0

        for idx, hotel in enumerate(todo, 1):
            pid  = hotel["propertyId"]
            name = hotel.get("name") or f"Hotel {pid}"
            print(f"[{idx:>3}/{len(todo)}] {name} (ID: {pid})")
            print(f"         URL: {hotel['url']}")

            detail = await capture_hotel_detail(context, hotel)

            has_graphql = detail["graphql"] is not None
            has_reviews = detail["reviews"] is not None

            status_parts = []
            if has_graphql:
                status_parts.append("graphql OK")
            else:
                status_parts.append("graphql MISS")
            if has_reviews:
                status_parts.append("reviews OK")
            else:
                status_parts.append("reviews MISS")

            out_path = save_detail(detail)

            if has_graphql and has_reviews:
                success += 1
                tag = "[OK]"
            elif has_graphql or has_reviews:
                partial += 1
                tag = "[PARTIAL]"
            else:
                failed += 1
                tag = "[FAILED]"

            print(f"         {tag} {' | '.join(status_parts)} -> {out_path}\n")

            # Jeda antar hotel
            if idx < len(todo):
                await asyncio.sleep(DELAY_BETWEEN_HOTELS)

        await browser.close()

    print(f"{'='*60}")
    print(f"[DONE] Selesai memproses {len(todo)} hotel.")
    print(f"       OK      : {success}")
    print(f"       Partial : {partial}")
    print(f"       Failed  : {failed}")
    print(f"       Output  : {OUTPUT_DIR}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    # Bisa dijalankan dengan argumen file spesifik:
    #   python fetch_details.py agoda/result_19806.json
    # Atau tanpa argumen untuk baca semua result_*.json:
    #   python fetch_details.py
    target_file = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(target_file))
