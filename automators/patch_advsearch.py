with open('automators/mabang_export_bot.py', 'r') as f:
    content = f.read()

old_search = """            # --- Open Advanced Search ---
            log("[*] 打开高级搜索面板...")
            await page.locator('a:has-text("高级搜索")').click()
            await asyncio.sleep(2)"""

new_search = """            # --- Open Advanced Search ---
            log("[*] 打开高级搜索面板...")
            try:
                await page.locator('a:has-text("高级搜索")').first.click(timeout=10000)
            except Exception:
                await page.evaluate('''() => {
                    let a = Array.from(document.querySelectorAll('a')).find(el => el.innerText && el.innerText.includes('高级搜索'));
                    if(a) a.click();
                }''')
            await asyncio.sleep(2)"""

if old_search in content:
    with open('automators/mabang_export_bot.py', 'w') as f:
        f.write(content.replace(old_search, new_search))
    print("Patch search applied")
else:
    print("Patch search failed")
