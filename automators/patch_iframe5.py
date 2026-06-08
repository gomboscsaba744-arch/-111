with open('automators/mabang_export_bot.py', 'r') as f:
    content = f.read()

old_frame = """            # --- Locate Target Frame ---
            log("[*] 等待 iframe[name='myiframe'] 出现...")
            try:
                await page.wait_for_selector("iframe[name='myiframe']", timeout=10000)
            except: pass
            
            target = page.frame_locator("iframe[name='myiframe']")
            log("[*] 使用 frame_locator 锁定 iframe[name='myiframe']")"""

new_frame = """            # --- Locate Target Frame ---
            log("[*] 等待 iframe[name='myiframe'] 出现...")
            try:
                await page.wait_for_selector("iframe[name='myiframe']", timeout=10000)
            except: pass
            
            target = page
            for f in page.frames:
                if f.name == 'myiframe':
                    target = f
                    log("[*] 找到并选择目标 frame: myiframe")
                    break
            
            if target == page:
                log("[!] 未能找到 myiframe，将使用主页面作为 target。")"""

if old_frame in content:
    with open('automators/mabang_export_bot.py', 'w') as f:
        f.write(content.replace(old_frame, new_frame))
    print("Patch iframe5 applied")
else:
    print("Patch iframe5 failed")
