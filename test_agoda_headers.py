import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()

        agoda_headers = {}

        async def intercept(request):
            nonlocal agoda_headers
            if "graphql" in request.url and request.method == "POST":
                if "agoda-api-key" in request.headers:
                    agoda_headers = request.headers

        page.on("request", intercept)
        print("Navigating...")
        await page.goto("https://www.agoda.com/search?city=17193", wait_until="networkidle")
        await page.wait_for_timeout(5000)
        
        print("Headers found:", "agoda-api-key" in agoda_headers)
        if "agoda-api-key" in agoda_headers:
            print("Key:", agoda_headers["agoda-api-key"])
        await browser.close()

asyncio.run(test())
