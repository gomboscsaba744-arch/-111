import re

with open("automators/mabang_export_bot.py", "r") as f:
    content = f.read()

new_search_logic = """
            # 1. 查询时间段 -> 创建时间
            await page.locator('select[name="queryTime"]').select_option(value="createDate")
            await asyncio.sleep(1)
            
            # 截止时间 -> 真实点击选择“今天”并确定
            log("[*] 设置截止时间为今天...")
            from datetime import datetime, timedelta
            
            await page.locator('#searchDetail #datepicker-to, #AdvanceSearch #datepicker-to').first.click(force=True)
            await asyncio.sleep(1)
            try:
                # WdatePicker
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
            # 强制解禁并填写
            await page.evaluate(f"let el = document.getElementById('datepicker-from2'); if(!el) el = document.querySelector('.datepicker-from'); if(el) {{ el.disabled = false; el.value = '{start_str}'; el.dispatchEvent(new Event('change', {{ bubbles: true }})); }}")
            await asyncio.sleep(1)
            
            # (2) 查询条件1选择客户id，完全物理点击！
            log("[*] 展开查询条件1下拉框并选择客户ID...")
            try:
                # 物理点击 Selectize 输入框展开下拉菜单
                await page.locator('input[placeholder="-查询条件1-"]').first.click(force=True)
                await asyncio.sleep(1)
                # 物理点击下拉菜单中的选项 (因为下拉框会被挂载到body下面或者紧跟输入框)
                await page.locator('.selectize-dropdown-content .option:has-text("客户ID")').first.click(force=True)
            except Exception as e:
                log(f"[!] 选择客户ID下拉框出错: {e}")
            await asyncio.sleep(1)
            
            # (3) 输入 Customer ID
            customer_id = "1000000257".strip()
            log(f"[*] 填写客户ID: {customer_id}")
            # 用物理键盘输入
            try:
                fuzzy_input = page.locator('#searchDetail #fuzzySearchValue, #AdvanceSearch #fuzzySearchValue').first
                await fuzzy_input.click(force=True)
                await fuzzy_input.fill("")
                await page.keyboard.type(customer_id)
            except Exception as e:
                pass
            await asyncio.sleep(1)
            
            # (4) 【双重保险】同时填写高级搜索的隐藏专属 clientId 字段
            log(f"[*] 额外填写高级搜索专属 clientId 字段以防万一...")
            await page.evaluate(f"let el = document.querySelector('input[name=\"clientId\"]'); if(el) {{ el.value = '{customer_id}'; el.dispatchEvent(new Event('change', {{ bubbles: true }})); }}")
            await asyncio.sleep(1)
            
            # 在提交搜索之前截个图，核对一下表单填得对不对
            await page.screenshot(path="debug_search_form.png")
            
            # 4. 点击面板最下方的搜索按钮
            log("[*] 提交高级搜索...")
            try:
                # 物理点击搜索按钮，就像人类一样
                search_btn = page.locator('#AdvanceSearch button.btn-primary:has-text("搜索")').first
                await search_btn.click(force=True)
            except Exception as e:
                log(f"[!] 搜索按钮物理点击失败，使用 JS 降级方案: {e}")
                await page.evaluate("let b = document.getElementById('searchMore'); if(b) b.click();")
            await asyncio.sleep(3)
"""

# replace the chunk
start_idx = content.find('# 1. 查询时间段 -> 创建时间')
end_idx = content.find('log("[*] 正在勾选全选当前页订单...")')

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_search_logic.strip() + '\n            \n            ' + content[end_idx:]
    with open("automators/mabang_export_bot.py", "w") as f:
        f.write(content)
    print("PATCH SUCCESS")
else:
    print("PATCH FAILED")
