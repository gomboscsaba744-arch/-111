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
        
        # 等待重定向
        while "login" in page.url.lower():
            await asyncio.sleep(1)
        await asyncio.sleep(5) # 给一点渲染时间
        
        print("当前 URL:", page.url)
        
        # 获取所有可见按钮和其文本
        buttons = await page.evaluate("""() => {
            let btns = Array.from(document.querySelectorAll('button, a, div[role="button"]')).filter(e => e.offsetHeight > 0 && e.innerText);
            return btns.map(b => b.innerText.trim()).filter(t => t.length > 0 && t.length < 30);
        }""")
        print("可见的按钮文本列表:", buttons)
        
        # 尝试截图和保存HTML
        await page.screenshot(path="test_dsers_page.png")
        html = await page.content()
        with open("test_dsers_page.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        await context.close()

asyncio.run(run())
