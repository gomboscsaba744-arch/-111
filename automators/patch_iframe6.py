with open('automators/mabang_export_bot.py', 'r') as f:
    content = f.read()

old_loop = """            for _ in range(15):
                try:
                    await page.evaluate("document.querySelectorAll('.layui-layer, .layui-layer-shade, .modal-backdrop, #oauth-modal').forEach(el => el.remove());")
                except: pass
                
                try:
                    btn = target.locator('a:has-text("高级搜索")').first"""

new_loop = """            for _ in range(15):
                try:
                    await page.evaluate("document.querySelectorAll('.layui-layer, .layui-layer-shade, .modal-backdrop, #oauth-modal').forEach(el => el.remove());")
                    if target != page:
                        await target.evaluate("document.querySelectorAll('.layui-layer, .layui-layer-shade, .modal-backdrop, #oauth-modal').forEach(el => el.remove());")
                except: pass
                
                try:
                    btn = target.locator('a:has-text("高级搜索")').first"""

if old_loop in content:
    with open('automators/mabang_export_bot.py', 'w') as f:
        f.write(content.replace(old_loop, new_loop))
    print("Patch iframe6 applied")
else:
    print("Patch iframe6 failed")
