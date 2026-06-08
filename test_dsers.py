import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir="./sessions/dsers_session",
            channel="chrome", headless=True
        )
        page = await context.new_page()
        await page.goto("https://www.dsers.com/dashboard/")
        await asyncio.sleep(5)
        href = await page.evaluate("""() => {
            let el = Array.from(document.querySelectorAll('a')).find(e => e.innerText && e.innerText.includes('CSV Upload'));
            return el ? el.href : 'not found';
        }""")
        print("CSV Upload URL:", href)
        await context.close()

asyncio.run(main())
