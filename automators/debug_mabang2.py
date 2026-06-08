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
        await page.goto("https://901067.private.mabangerp.com/index.php?mod=order.list&Order_orderStatus=2", wait_until='domcontentloaded')
        await asyncio.sleep(5)
        
        print("Clicking 批处理功能...")
        batch_btn = page.locator('span.text.mr5.ml5:has-text("批处理功能")').first
        await batch_btn.click()
        await asyncio.sleep(1.5)
        
        print("Hovering 批量更新订单信息...")
        menu_item = page.locator('li[data-customlink="批量更新订单信息"]').first
        await menu_item.hover()
        await asyncio.sleep(1)
        
        print("Clicking 更新订单基本信息...")
        await menu_item.locator('text="更新订单基本信息"').first.click()
        await asyncio.sleep(3)
        
        html = await page.content()
        with open("debug_dom_modal.html", "w") as f: f.write(html)
        print("Saved debug_dom_modal.html")
        await context.close()

asyncio.run(debug())
