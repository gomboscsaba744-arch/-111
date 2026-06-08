import re

with open("automators/mabang_export_bot.py", "r") as f:
    content = f.read()

new_search_logic = """
            # 1. 滚动到最底部确保元素可见
            await page.evaluate("let mb = document.querySelector('.modal-body'); if(mb) mb.scrollTop = 9999;")
            
            # 2. 查询时间段 -> 创建时间
            log("[*] 设置查询时间段为创建时间...")
            await page.locator('select[name="queryTime"]').select_option(value="createDate")
            await asyncio.sleep(1)
            
            # 3. 截止时间 -> 真实点击选择“今天”并确定
            log("[*] 设置截止时间为今天...")
            from datetime import datetime, timedelta
            await page.locator('#AdvanceSearch #datepicker-to').first.click(force=True)
            await asyncio.sleep(1)
            try:
                if await page.locator('#dpTodayInput').count() > 0:
                    await page.locator('#dpTodayInput').click(force=True)
                    await asyncio.sleep(0.5)
                    if await page.locator('#dpOkInput').is_visible():
                        await page.locator('#dpOkInput').click(force=True)
            except Exception as e:
                pass
            await asyncio.sleep(1)
            
            # 起始时间 -> 直接填写
            log("[*] 设置起始时间（默认前一天）...")
            start_time = datetime.now() - timedelta(days=1)
            start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
            # 强制解除 disabled 并物理 fill
            await page.evaluate("let el = document.getElementById('datepicker-from2'); if(!el) el = document.querySelector('.datepicker-from'); if(el) el.disabled = false;")
            await page.locator('#AdvanceSearch #datepicker-from2, .datepicker-from').first.fill(start_str)
            await asyncio.sleep(1)
            
            # (2) 查询条件1选择客户id，完全物理点击！
            log("[*] 展开查询条件1下拉框并选择客户ID...")
            try:
                # 物理点击 Selectize 输入框展开下拉菜单
                await page.locator('input[placeholder="-查询条件1-"]').first.click(force=True)
                await asyncio.sleep(1)
                # 物理点击下拉菜单中的选项
                await page.locator('.selectize-dropdown-content .option:has-text("客户ID")').first.click(force=True)
            except Exception as e:
                log(f"[!] 选择客户ID下拉框出错: {e}")
            await asyncio.sleep(1)
            
            # (3) 输入 Customer ID
            customer_id = "1000000257".strip()
            log(f"[*] 填写客户ID: {customer_id}")
            try:
                # 必须确保它 enable
                await page.evaluate("let el = document.getElementById('fuzzySearchValue'); if(!el) el = document.querySelector('input[name=\"OrderSearch.fuzzySearchValue\"]'); if(el) el.disabled = false;")
                fuzzy_input = page.locator('#AdvanceSearch #fuzzySearchValue, input[name="OrderSearch.fuzzySearchValue"]').first
                await fuzzy_input.click(force=True)
                await fuzzy_input.fill("")
                await page.keyboard.type(customer_id)
                await page.keyboard.press("Enter")
            except Exception as e:
                log(f"[!] 填写客户ID失败: {e}")
            await asyncio.sleep(1)
            
            # (4) 【双重保险】同时填写高级搜索的隐藏专属 clientId 字段
            log(f"[*] 额外填写高级搜索专属 clientId 字段以防万一...")
            await page.evaluate(f"let el = document.querySelector('input[name=\"clientId\"]'); if(el) {{ el.value = '{customer_id}'; el.dispatchEvent(new Event('change', {{ bubbles: true }})); }}")
            await asyncio.sleep(1)
            
            # 在提交搜索之前截个图
            await page.screenshot(path="debug_search_form.png")
            
            # 4. 点击面板最下方的搜索按钮
            log("[*] 提交高级搜索...")
            try:
                search_btn = page.locator('#AdvanceSearch button.btn-primary:has-text("搜索")').first
                await search_btn.click(force=True)
            except Exception as e:
                log(f"[!] 搜索按钮物理点击失败，使用 JS 降级方案: {e}")
                await page.evaluate("let b = document.getElementById('searchMore'); if(b) b.click();")
            await asyncio.sleep(3)
"""

start_idx = content.find('# 1. 滚动到最底部确保元素可见')
end_idx = content.find('log("[*] 正在勾选全选当前页订单...")')

if start_idx != -1 and end_idx != -1:
    while content[start_idx-1] in ' \t':
        start_idx -= 1
        
    new_content = content[:start_idx] + new_search_logic.strip() + '\n            \n            ' + content[end_idx:]
    with open("automators/mabang_export_bot.py", "w") as f:
        f.write(new_content)
    print("PATCH SUCCESS")
else:
    print("PATCH FAILED")
