with open('automators/mabang_export_bot.py', 'r') as f:
    content = f.read()

old_search = """            # --- Open Advanced Search ---"""
new_search = """            # 清理订单列表页可能弹出的系统通知
            log("[*] 自动清理订单列表页可能的系统提示/授权弹窗...")
            try:
                await page.evaluate('''() => {
                    document.querySelectorAll('.layui-layer-close, .layui-layer-btn0, .close, [data-dismiss="modal"]').forEach(b => {
                        try { b.click(); } catch(e){}
                    });
                    document.querySelectorAll('.modal-backdrop, .layui-layer-shade').forEach(el => el.remove());
                }''')
                await asyncio.sleep(1)
            except Exception:
                pass

            # --- Open Advanced Search ---"""

if old_search in content:
    with open('automators/mabang_export_bot.py', 'w') as f:
        f.write(content.replace(old_search, new_search))
    print("Patch popup2 applied")
else:
    print("Patch popup2 failed")
