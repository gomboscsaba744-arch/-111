import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("[*] 正在打开马帮首页...")
        await page.goto("https://www.mabangerp.com/index.php?mod=admin.login", timeout=60000)
        
        print("[*] 检查是否需要登录...")
        try:
            if await page.locator('#developerId').is_visible(timeout=5000):
                await page.locator('#developerId').fill("109138")
                await page.locator('#username').fill("109138030")
                await page.locator('#password').fill("ABCabc123")
                await page.locator('#login-submit').click()
                print("[*] 登录已提交，等待页面加载...")
                await page.wait_for_load_state('networkidle', timeout=30000)
            else:
                print("[*] 已登录，无需填写密码。")
        except Exception:
            print("[*] 已经是登录状态。")
            
        print("[*] 导航至【订单列表】...")
        await asyncio.sleep(3)
        await page.goto("https://901067.private.mabangerp.com/index.php?mod=order.list", timeout=60000)
        await page.wait_for_load_state('domcontentloaded', timeout=60000)
        await asyncio.sleep(5)
        
        print("[*] 获取 iframe 列表:")
        for frame in page.frames:
            print(f"Name: {frame.name}, URL: {frame.url}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
