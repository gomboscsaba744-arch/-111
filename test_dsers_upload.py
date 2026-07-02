import asyncio
import os
from playwright.async_api import async_playwright

async def run():
    SESSION_DIR = os.path.join(os.getcwd(), "sessions", "dsers_session")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            channel="chrome",
            headless=True,
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        TARGET_URL = "https://accounts.dsers.com/accounts/login?redirect_url=https%3A%2F%2Fwww.dsers.com%2Fapplication%2Forders%2F159831080"
        await page.goto(TARGET_URL, wait_until='domcontentloaded')
        
        while "login" in page.url.lower():
            await asyncio.sleep(1)
        await asyncio.sleep(5)
        
        # 1. 尝试点击 CSV Upload
        await page.evaluate("""() => {
            let els = Array.from(document.querySelectorAll('*')).filter(e => e.innerText && e.innerText.trim() === 'CSV Upload' && e.offsetHeight > 0);
            let target = els.find(e => !Array.from(e.children).some(c => c.innerText && c.innerText.trim() === 'CSV Upload')) || els[0];
            if (target) target.click();
        }""")
        await asyncio.sleep(3)
        
        # 打印点击后的弹窗按钮
        buttons = await page.evaluate("""() => {
            let btns = Array.from(document.querySelectorAll('button, div[role="tab"]')).filter(e => e.offsetHeight > 0 && e.innerText);
            return btns.map(b => b.innerText.trim()).filter(t => t.length > 0 && t.length < 50);
        }""")
        print("点击 CSV Upload 后的按钮/标签:", buttons)
        
        html = await page.content()
        with open("test_dsers_upload.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        await context.close()

asyncio.run(run())
