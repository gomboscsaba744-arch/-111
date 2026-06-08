with open('automators/mabang_export_bot.py', 'r') as f:
    content = f.read()

start_idx = content.find('            # 清理订单列表页可能弹出的系统通知')
end_idx = content.find('            # --- Configure Search Conditions ---')

if start_idx != -1 and end_idx != -1:
    new_logic = """            # --- Open Advanced Search ---
            log("[*] 打开高级搜索面板并持续清理弹窗...")
            for _ in range(15):
                try:
                    await page.evaluate("document.querySelectorAll('.layui-layer, .layui-layer-shade, .modal-backdrop, #oauth-modal').forEach(el => el.remove());")
                except: pass
                
                try:
                    btn = page.locator('a:has-text("高级搜索")').first
                    if await btn.is_visible():
                        await btn.click(timeout=1000)
                        log("[*] 成功点击高级搜索面板")
                        break
                except:
                    pass
                await asyncio.sleep(1)
            
            await asyncio.sleep(2)
"""
    new_content = content[:start_idx] + new_logic + content[end_idx:]
    with open('automators/mabang_export_bot.py', 'w') as f:
        f.write(new_content)
    print("Patch popup loop applied")
else:
    print("Patch popup loop failed")
