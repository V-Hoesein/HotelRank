import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        captured_headers = {}
        async def intercept(request):
            nonlocal captured_headers
            if not captured_headers and "agoda.com" in request.url:
                captured_headers = dict(request.headers)
                
        page.on("request", intercept)
        await page.goto("https://www.agoda.com/", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)
        
        headers = captured_headers
        for key in ["content-length", "accept-encoding", "content-type", "accept"]:
            headers.pop(key, None)
        headers["content-type"] = "application/json"
        headers["accept"] = "application/json, text/plain, */*"
        headers["origin"] = "https://www.agoda.com"
        headers["referer"] = "https://www.agoda.com/hotel/86738595"

        payload = {
            "hotelId": 86738595,
            "hotelProviderId": 332,
            "demographicId": 0,
            "pageNo": 1,
            "pageSize": 50,
            "sorting": 7,
            "reviewProviderIds": [332, 3038, 27901, 28999, 29100, 27999, 27980, 27989, 29014],
            "isReviewPage": False,
            "isCrawlablePage": True,
            "paginationSize": 50
        }
        
        print("Fetching ReviewComments...")
        resp = await context.request.post(
            "https://www.agoda.com/api/cronos/property/review/ReviewComments",
            data=json.dumps(payload),
            headers=headers
        )
        
        print("Status:", resp.status)
        if resp.status == 200:
            data = await resp.json()
            print("Keys in response:", list(data.keys()))
            if "comments" in data:
                print("Number of comments:", len(data["comments"]))
            elif "commentList" in data:
                print("Number of comments:", len(data["commentList"]))
            # Dump a bit of structure
            with open("debug_review.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print("Saved full response to debug_review.json")
        else:
            print(await resp.text())
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
