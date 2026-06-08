with open('automators/mabang_export_bot.py', 'r') as f:
    content = f.read()

old_code = """            # --- Dismiss Popups ---
            log("[*] 等待并检查是否有授权提醒弹窗...")
            try:
                auth_modal = page.locator('#oauth-modal')
                await auth_modal.wait_for(state='visible', timeout=5000)
                log("[*] 发现授权提醒弹窗，准备关闭...")
                close_btn = auth_modal.locator('button.close, .modal-header .close')
                if await close_btn.is_visible():
                    await close_btn.click()
                    log("[*] 弹窗已关闭。")
            except Exception:
                log("[*] 没有发现弹窗，继续操作。")"""

new_code = """            # --- Dismiss Popups ---
            log("[*] 自动清理可能存在的系统提示/授权弹窗...")
            try:
                await page.evaluate('''() => {
                    document.querySelectorAll('.layui-layer-close, .layui-layer-btn0, .close, [data-dismiss="modal"]').forEach(b => {
                        try { b.click(); } catch(e){}
                    });
                    document.querySelectorAll('.modal-backdrop, .layui-layer-shade').forEach(el => el.remove());
                }''')
                await asyncio.sleep(1)
            except Exception:
                pass"""

if old_code in content:
    with open('automators/mabang_export_bot.py', 'w') as f:
        f.write(content.replace(old_code, new_code))
    print("Patch popup applied")
else:
    print("Patch popup failed")
