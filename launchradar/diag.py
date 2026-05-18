import asyncio
from playwright.async_api import async_playwright

async def dump_html():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Fetching Devpost...")
        await page.goto("https://devpost.com/hackathons")
        await page.wait_for_timeout(3000)
        with open("devpost.html", "w", encoding="utf-8") as f:
            f.write(await page.content())
            
        print("Fetching MassChallenge...")
        await page.goto("https://masschallenge.org/programs/")
        await page.wait_for_timeout(3000)
        with open("mc.html", "w", encoding="utf-8") as f:
            f.write(await page.content())
            
        print("Fetching Graham Walker...")
        await page.goto("https://grahamwalker.com/blog/grants-accelerators-for-early-stage-founders/")
        await page.wait_for_timeout(3000)
        with open("gw.html", "w", encoding="utf-8") as f:
            f.write(await page.content())
            
        await browser.close()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(dump_html())
