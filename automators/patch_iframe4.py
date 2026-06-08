with open('automators/mabang_export_bot.py', 'r') as f:
    content = f.read()

old_frame = """            # --- Locate Target Frame ---
            log("[*] 查找订单列表所在的 iframe...")
            target = page
            for f in page.frames:
                log("[*] 找到 frame URL: " + f.url)
                if 'order' in f.url or 'mabangerp' in f.url:
                    if target == page and f != page.main_frame:
                        target = f
                        log("[*] 选择目标 iframe: " + f.url)
            
            if target == page:
                log("[!] 未找到指定的 iframe，将使用主页面上下文。")"""

new_frame = """            # --- Locate Target Frame ---
            log("[*] 等待 iframe[name='myiframe'] 出现...")
            try:
                await page.wait_for_selector("iframe[name='myiframe']", timeout=10000)
            except: pass
            
            target = page.frame_locator("iframe[name='myiframe']")
            log("[*] 使用 frame_locator 锁定 iframe[name='myiframe']")"""

if old_frame in content:
    with open('automators/mabang_export_bot.py', 'w') as f:
        f.write(content.replace(old_frame, new_frame))
    print("Patch iframe4 applied")
else:
    print("Patch iframe4 failed")
