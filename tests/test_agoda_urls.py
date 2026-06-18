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

        urls = []

        async def intercept(request):
            if "agoda" in request.url and "graphql" in request.url:
                urls.append((request.method, request.url, request.headers.keys()))

        page.on("request", intercept)
        print("Navigating...")
        await page.goto("https://www.agoda.com/search?city=17193", wait_until="networkidle")
        await page.wait_for_timeout(3000)
        
        for m, u, h in urls:
            print(f"{m} {u} - headers: {h}")
        await browser.close()

asyncio.run(test())
