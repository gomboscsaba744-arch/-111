with open('automators/mabang_export_bot.py', 'r') as f:
    content = f.read()

old_nav = """            # --- Go to Order List ---
            log("[*] 导航至【订单列表】...")
            await page.goto("https://901067.private.mabangerp.com/index.php?mod=order.list", timeout=60000)
            await asyncio.sleep(2)"""

new_nav = """            # --- Go to Order List ---
            log("[*] 导航至【订单列表】...")
            await asyncio.sleep(3)
            await page.goto("https://901067.private.mabangerp.com/index.php?mod=order.list", timeout=60000)
            await page.wait_for_load_state('domcontentloaded', timeout=60000)
            await asyncio.sleep(3)"""

if old_nav in content:
    with open('automators/mabang_export_bot.py', 'w') as f:
        f.write(content.replace(old_nav, new_nav))
    print("Patch Nav applied")
else:
    print("Patch Nav failed")
