import asyncio
import os
import yaml
from playwright.async_api import async_playwright

async def debug():
    config_path = "/Users/a171325./Documents/Global_Order_Pipeline/config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    mb_user = str(config['mabang']['username'])
    mb_pwd = str(config['mabang']['password'])

    user_data_dir = "/Users/a171325./Documents/Global_Order_Pipeline/sessions/mabang_session"
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=True,
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        print("Goto index...")
        await page.goto("https://901067.private.mabangerp.com/index.htm", wait_until='domcontentloaded')
        await asyncio.sleep(2)
        if await page.locator('#login-but').is_visible():
            await page.locator('input[name="username"]').first.fill(mb_user)
            await page.locator('input[name="password"]').first.fill(mb_pwd)
            await page.locator('#login-but').click()
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(3)
        
        # Navigate to order list
        print("Navigating to order list...")
        await page.goto("https://901067.private.mabangerp.com/index.php?mod=order.list&Order_orderStatus=2", wait_until='domcontentloaded')
        await asyncio.sleep(5)
        
        print("Clicking 批处理功能...")
        batch_btn = page.locator('span.text.mr5.ml5:has-text("批处理功能")').first
        await batch_btn.click()
        await asyncio.sleep(2)
        
        html = await page.content()
        with open("debug_dom_orders.html", "w") as f: f.write(html)
        print("Saved debug_dom_orders.html")
        await context.close()

asyncio.run(debug())
