import asyncio
import json
import glob
import os
from urllib.parse import urlparse, parse_qs
from playwright.async_api import async_playwright

import fetch_details
import clean_details

SEARCH_URL = "https://www.agoda.com/search?city=19806&checkIn=2026-06-21&los=1&adults=2&rooms=1"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")

# Folder menyimpan setiap response GraphQL mentah
RESPONSES_DIR = os.path.join(RESULTS_DIR, "raw_graphql")

# Folder output hasil merge
OUTPUT_DIR = os.path.join(RESULTS_DIR, "search_results")

# Delay setelah scroll habis (detik)
SCROLL_DELAY = 3

# Batas maksimum klik tombol Next
MAX_PAGES = 20


# ─────────────────────────────────────────────
# Helper: Ambil keyword dari URL (nilai city=)
# ─────────────────────────────────────────────
def get_keyword_from_url(url: str) -> str:
    qs = parse_qs(urlparse(url).query)
    return qs.get("city", ["unknown"])[0]


# ─────────────────────────────────────────────
# Helper: Scroll perlahan dari atas ke bawah
# ─────────────────────────────────────────────
async def slow_scroll_to_bottom(page):
    await page.evaluate("""
        async () => {
            await new Promise((resolve) => {
                const distance = 120;
                const delay    = 80;
                const timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    const bottom = document.body.scrollHeight - window.innerHeight;
                    if (window.scrollY >= bottom) {
                        clearInterval(timer);
                        resolve();
                    }
                }, delay);
            });
        }
    """)


# ─────────────────────────────────────────────
# Helper: Cek apakah tombol "Next" ada
# ─────────────────────────────────────────────
async def find_next_button(page):
    btn = page.locator("#paginationNext")
    try:
        await btn.wait_for(state="visible", timeout=3000)
        return btn
    except Exception:
        return None


# ─────────────────────────────────────────────
# Merge: Baca semua response_*.json, gabung
# unik berdasarkan propertyId, simpan ke
# agoda/result_<keyword>.json
# ─────────────────────────────────────────────
def merge_and_save(keyword: str) -> list[dict]:
    files = sorted(glob.glob(os.path.join(RESPONSES_DIR, "response_*.json")))
    seen  = {}

    for fpath in files:
        try:
            with open(fpath, encoding="utf-8") as f:
                body = json.load(f)
        except Exception:
            continue

        props = (
            body.get("data", {})
                .get("citySearch", {})
                .get("properties", [])
        )

        for prop in props:
            pid = prop.get("propertyId")
            if pid is not None and pid not in seen:
                seen[pid] = prop

    unique = list(seen.values())

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, f"result_{keyword}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)

    print(f"[MERGE] {len(files)} file dibaca -> {len(unique)} hotel unik")
    print(f"[SAVE]  Tersimpan ke {out_path}")

    return unique, out_path


# ─────────────────────────────────────────────
# Main scraper
# ─────────────────────────────────────────────
async def fetch_agoda_all_pages():
    os.makedirs(RESPONSES_DIR, exist_ok=True)

    response_index = 0
    pending        = 0
    lock           = asyncio.Lock()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
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

        # ─── Listener: simpan setiap response graphql/search ke file ───
        async def on_response(response):
            nonlocal response_index, pending

            if "graphql/search" not in response.url or response.request.method != "POST":
                return

            async with lock:
                pending += 1

            idx = response_index
            response_index += 1

            try:
                body = await response.json()
            except Exception as e:
                print(f"  [WARN] Response #{idx}: gagal parse JSON - {e}")
                async with lock:
                    pending -= 1
                return

            # Cek apakah ada properties di response ini
            props = (
                body.get("data", {})
                    .get("citySearch", {})
                    .get("properties", [])
            )

            fname = os.path.join(RESPONSES_DIR, f"response_{idx:03d}.json")
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(body, f, indent=2, ensure_ascii=False)

            if props:
                print(f"  [+{len(props):>3} hotel] response_{idx:03d}.json tersimpan")
            else:
                print(f"  [  --   ] response_{idx:03d}.json tersimpan (bukan citySearch/properties)")

            async with lock:
                pending -= 1

        page.on("response", on_response)

        # ─── Buka halaman ───
        print(f"\n{'='*60}")
        print("Agoda Scraper - Scroll + Pagination + Auto-Merge")
        print(f"{'='*60}")
        print(f"\n[Hal. 1] Membuka {SEARCH_URL}")
        await page.goto(SEARCH_URL, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(2000)

        page_num = 1
        print(f"[Hal. {page_num}] Halaman awal dimuat.")

        # ─── Loop: scroll -> cari Next -> klik -> ulangi ───
        while page_num <= MAX_PAGES:
            print(f"\n[Hal. {page_num}] Scroll perlahan ke bawah...")
            await slow_scroll_to_bottom(page)

            await page.wait_for_timeout(SCROLL_DELAY * 1000)
            for _ in range(40):
                async with lock:
                    if pending == 0:
                        break
                await asyncio.sleep(0.5)

            print(f"[Hal. {page_num}] Mencari tombol 'Next'...")
            next_btn = await find_next_button(page)

            if next_btn is None:
                print(f"[Hal. {page_num}] Tidak ada tombol 'Next' - selesai scraping.")
                break

            print(f"[Hal. {page_num}] Klik 'Next'...")
            await next_btn.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)
            await next_btn.click()

            print(f"[Hal. {page_num}] Menunggu halaman baru...")
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                await page.wait_for_timeout(3000)

            for _ in range(20):
                async with lock:
                    if pending == 0:
                        break
                await asyncio.sleep(0.5)

            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)

            page_num += 1
            print(f"[Hal. {page_num}] Halaman baru siap.")

        await browser.close()

    return response_index


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
async def main():
    # Ambil keyword otomatis dari nilai city= di URL
    keyword = get_keyword_from_url(SEARCH_URL)

    total_responses = await fetch_agoda_all_pages()

    print(f"\n{'='*60}")
    print(f"[STAT] Total file response tersimpan : {total_responses}")
    print(f"[STAT] Keyword dari URL               : city={keyword}")
    print(f"{'='*60}")

    # Merge otomatis setelah scraping selesai
    print(f"\n[MERGE] Menggabungkan semua response dan deduplikasi...")
    unique_props, out_path = merge_and_save(keyword)

    if not unique_props:
        print("[WARN] Tidak ada hotel yang berhasil di-merge.")
        print(f"       Cek isi file di '{RESPONSES_DIR}/' untuk struktur response asli.")
        return

    print(f"\n[OK] Selesai! {len(unique_props)} hotel unik tersimpan di folder {OUTPUT_DIR}")

    print(f"\n{'='*60}")
    print("[NEXT] Memulai scraping detail hotel (GraphQL & Reviews)...")
    print(f"{'='*60}")
    await fetch_details.main(out_path)

    print(f"\n{'='*60}")
    print("[NEXT] Memulai pembersihan dan ekstraksi data final...")
    print(f"{'='*60}")
    clean_details.process_all()

    print(f"\n🎉 [SELESAI] Seluruh pipeline scraping berhasil dijalankan!")


if __name__ == "__main__":
    asyncio.run(main())