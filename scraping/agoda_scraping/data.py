import asyncio
import json
import os
from playwright.async_api import async_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
DEBUG_DIR = os.path.join(RESULTS_DIR, "debug")

SEARCH_URL = "https://www.agoda.com/search?city=19806&checkIn=2026-06-21&los=1&adults=2&rooms=1"

# Ganti isi variabel ini dengan query & variabel yang ingin Anda gunakan
# Jika None, script akan memakai payload ASLI dari Agoda (berguna untuk melihat
# struktur payload dan response sebelum Anda membuat custom PAYLOAD)
CUSTOM_PAYLOAD = None  # Ubah ke dict payload Anda, atau biarkan None untuk memakai payload asli


async def fetch_agoda_graphql():
    captured = {}
    done_event = asyncio.Event()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = await context.new_page()

        # Gunakan page.route() agar kita bisa MODIFIKASI request dari dalam browser
        async def handle_route(route, request):
            if "graphql/search" in request.url and request.method == "POST":
                # Simpan headers & payload asli untuk referensi
                captured["headers"] = request.headers
                captured["original_payload"] = request.post_data

                # Tentukan payload yang akan dikirim
                if CUSTOM_PAYLOAD is not None:
                    post_data = json.dumps(CUSTOM_PAYLOAD)
                    print("📦 Menggunakan CUSTOM_PAYLOAD...")
                else:
                    post_data = request.post_data
                    print("📦 Menggunakan payload ASLI dari Agoda...")

                # Lanjutkan request dengan payload yang sudah ditentukan
                response = await route.fetch(post_data=post_data)

                # Tangkap response-nya
                try:
                    body = await response.json()
                    captured["data"] = body
                    captured["status"] = response.status
                except Exception:
                    captured["data"] = await response.body()
                    captured["status"] = response.status

                # Kirim respons asli kembali ke browser (agar halaman normal)
                await route.fulfill(response=response)

                # Tandai bahwa kita sudah selesai
                if not done_event.is_set():
                    done_event.set()
            else:
                await route.continue_()

        await page.route("**", handle_route)

        print(f"1. Membuka halaman pencarian Agoda: {SEARCH_URL}")
        await page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=60000)

        print("2. Menunggu request GraphQL terpicu...")
        try:
            await asyncio.wait_for(done_event.wait(), timeout=30)
            print(f"✅ Berhasil! Status: {captured.get('status')}")
        except asyncio.TimeoutError:
            print("⚠️  Timeout — tidak ada request graphql/search yang terpicu.")

        await browser.close()

    return captured


async def main():
    result = await fetch_agoda_graphql()

    if "data" not in result:
        print("Tidak ada data yang berhasil ditangkap.")
        return

    data = result["data"]

    # Simpan seluruh response ke file JSON untuk referensi
    os.makedirs(DEBUG_DIR, exist_ok=True)
    search_resp_path = os.path.join(DEBUG_DIR, "agoda_search_response.json")
    with open(search_resp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 Response disimpan ke {search_resp_path}")

    # Simpan juga payload asli ke file untuk referensi pembuatan CUSTOM_PAYLOAD
    if result.get("original_payload"):
        orig_payload_path = os.path.join(DEBUG_DIR, "agoda_original_payload.json")
        with open(orig_payload_path, "w", encoding="utf-8") as f:
            try:
                f.write(json.dumps(json.loads(result["original_payload"]), indent=2, ensure_ascii=False))
            except Exception:
                f.write(result["original_payload"])
        print(f"💾 Payload asli disimpan ke {orig_payload_path}")

    # Ekstraksi data properti hotel dari response
    if isinstance(data, dict):
        properties = (
            data.get("data", {})
            .get("rectangleSearch", {})
            .get("properties", [])
        )

        if not properties:
            print(f"\n⚠️  Properties kosong — lihat {search_resp_path} untuk memeriksa struktur response.")
            return

        print(f"\n=== HASIL EKSTRAKSI ({len(properties)} hotel) ===")
        for prop in properties:
            content = prop.get("content", {})
            info = content.get("informationSummary", {})
            reviews = content.get("reviews", {})
            facilities = content.get("facilities", [])

            print({
                "propertyId": prop.get("propertyId"),
                "name": info.get("displayName"),
                "rating": info.get("rating"),
                "review_score": reviews.get("cumulative", {}).get("score"),
                "review_count": reviews.get("cumulative", {}).get("reviewCount"),
                "facility_ids": [f.get("id") for f in facilities],
            })


if __name__ == "__main__":
    asyncio.run(main())