with open('automators/mabang_export_bot.py', 'r') as f:
    content = f.read()

old_btn = """            # 7. 提交搜索
            log("[*] 提交高级搜索...")
            try:
                search_btn = page.locator('#AdvanceSearch button.btn-primary:has-text("搜索")').first
                await search_btn.click(force=True)
            except Exception:
                await page.evaluate("let b = document.getElementById('searchMore'); if(b) b.click();")
            await asyncio.sleep(3)"""

new_btn = """            # 7. 提交搜索
            log("[*] 提交高级搜索...")
            try:
                search_btn = target.locator('#AdvanceSearch button.btn-primary:has-text("搜索")').first
                await search_btn.click(force=True)
            except Exception:
                try:
                    await target.evaluate("let b = document.getElementById('searchMore'); if(b) b.click();")
                except: pass
            await asyncio.sleep(3)"""

if old_btn in content:
    with open('automators/mabang_export_bot.py', 'w') as f:
        f.write(content.replace(old_btn, new_btn))
    print("Patch iframe2 applied")
else:
    print("Patch iframe2 failed")
