import re

with open("automators/mabang_export_bot.py", "r") as f:
    content = f.read()

new_search_logic = """
            # 1. 滚动到最底部确保元素可见
            await page.evaluate("let mb = document.querySelector('.modal-body'); if(mb) mb.scrollTop = 9999;")
            
            # 2. 选择时间段 -> 创建时间
            log("[*] 设置查询时间段为创建时间...")
            await page.locator('select[name="queryTime"]').select_option(value="createDate")
            await asyncio.sleep(0.5)
            
            # 3. 点击截止时间并选择“今天” -> “确定”
            log("[*] 设置截止时间为今天...")
            await page.locator('#AdvanceSearch #datepicker-to').first.click(force=True)
            await asyncio.sleep(0.5)
            if await page.locator('#dpTodayInput').count() > 0:
                await page.locator('#dpTodayInput').click(force=True)
                await asyncio.sleep(0.5)
                if await page.locator('#dpOkInput').is_visible():
                    await page.locator('#dpOkInput').click(force=True)
            await asyncio.sleep(0.5)
            
            # 4. 设置起始时间为前一天
            log("[*] 设置起始时间...")
            from datetime import datetime, timedelta
            start_time = datetime.now() - timedelta(days=1)
            start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
            await page.evaluate(f"let el = document.getElementById('datepicker-from2'); if(!el) el = document.querySelector('.datepicker-from'); if(el) {{ el.disabled = false; el.value = '{start_str}'; }}")
            await asyncio.sleep(0.5)
            
            # 5. 查询条件1 -> 客户ID (即 buyerUserId)
            log("[*] 选择查询条件1下拉框为客户ID...")
            await page.evaluate('''() => {
                let s = document.querySelector('#AdvanceSearch #fuzzySearchKey');
                if(!s) s = document.getElementById('fuzzySearchKey');
                if(s) {
                    if(s.selectize) s.selectize.setValue('buyerUserId');
                    s.value = 'buyerUserId';
                    s.dispatchEvent(new Event('change', {bubbles: true}));
                }
            }''')
            await asyncio.sleep(0.5)
            
            # 6. 填入客户ID
            customer_id = "1000000257".strip()
            log(f"[*] 填写客户ID: {customer_id}")
            await page.evaluate(f'''(cid) => {{
                let el = document.querySelector('#AdvanceSearch #fuzzySearchValue');
                if(!el) el = document.getElementById('fuzzySearchValue');
                if(el) {{
                    el.disabled = false;
                    el.value = cid;
                }}
            }}''', customer_id)
            await asyncio.sleep(1)
            
            # 在提交搜索之前截个图
            await page.screenshot(path="debug_search_form.png")
            
            # 7. 物理点击搜索按钮
            log("[*] 提交高级搜索...")
            await page.evaluate('''() => {
                let btn = document.getElementById('searchMore');
                if(btn) btn.click();
            }''')
            await asyncio.sleep(3)
"""

start_idx = content.find('# 1. 查询时间段 -> 创建时间')
if start_idx == -1:
    start_idx = content.find('await page.locator(\'select[name="queryTime"]\').select_option(value="createDate")')

end_idx = content.find('log("[*] 正在勾选全选当前页订单...")')

if start_idx != -1 and end_idx != -1:
    # Go back a bit to catch the comment if needed, but we already have new comments.
    while content[start_idx-1] in ' \t#1.查询时间段->创建':
        start_idx -= 1
        
    new_content = content[:start_idx] + '\n' + new_search_logic.strip() + '\n            \n            ' + content[end_idx:]
    with open("automators/mabang_export_bot.py", "w") as f:
        f.write(new_content)
    print("PATCH SUCCESS")
else:
    print("PATCH FAILED")
