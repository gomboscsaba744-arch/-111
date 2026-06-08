import asyncio
import os
from playwright.async_api import async_playwright

async def dump():
    user_data_dir = "/Users/a171325./Documents/Global_Order_Pipeline/sessions/mabang_session"
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=True
        )
        page = await context.new_page()
        await page.goto("https://901067.private.mabangerp.com/index.php?mod=order.list", wait_until='domcontentloaded', timeout=60000)
        await asyncio.sleep(3)
        
        # Open advanced search
        await page.evaluate("""() => {
            let els = Array.from(document.querySelectorAll('a, button, span, div.btn')).filter(e => e.innerText && e.innerText.trim() === '高级搜索' && e.offsetParent !== null);
            if (els.length > 0) {
                els[0].click();
            } else {
                let btn = document.querySelector('#AdvanceSearchBtn button') || document.querySelector('#AdvanceSearchBtn');
                if(btn) btn.click();
            }
        }""")
        await asyncio.sleep(3)
        
        # Dump main page HTML
        html = await page.content()
        with open("mabang_dom.html", "w") as f:
            f.write(html)
            
        await context.close()

asyncio.run(dump())
