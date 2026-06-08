with open('automators/mabang_export_bot.py', 'r') as f:
    content = f.read()

old_frame = """            for f in page.frames:
                if 'order.list' in f.url:
                    target = f
                    log("[*] 找到目标 iframe: " + f.url)
                    break
            if target == page:
                log("[!] 未找到指定的 iframe，将使用主页面上下文。")"""

new_frame = """            for f in page.frames:
                log("[*] 找到 frame URL: " + f.url)
                if 'order' in f.url or 'mabangerp' in f.url:
                    if target == page and f != page.main_frame:
                        target = f
                        log("[*] 选择目标 iframe: " + f.url)
            
            if target == page:
                log("[!] 未找到指定的 iframe，将使用主页面上下文。")"""

if old_frame in content:
    with open('automators/mabang_export_bot.py', 'w') as f:
        f.write(content.replace(old_frame, new_frame))
    print("Patch iframe3 applied")
else:
    print("Patch iframe3 failed")
