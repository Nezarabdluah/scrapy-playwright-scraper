import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://en.your-uni.com/course-list", wait_until="domcontentloaded")
        # Wait a bit for dynamic content
        await page.wait_for_timeout(3000)
        html = await page.content()
        with open("temp.html", "w", encoding="utf-8") as f:
            f.write(html)
        await browser.close()
        print("HTML saved to temp.html")

if __name__ == "__main__":
    asyncio.run(main())
