with open('automators/mabang_export_bot.py', 'r') as f:
    content = f.read()

start_idx = content.find('            # --- Open Advanced Search ---')
end_idx = content.find('            # --- Scroll to bottom and take screenshot ---')

if start_idx != -1 and end_idx != -1:
    new_logic = """            # --- Locate Target Frame ---
            log("[*] 查找订单列表所在的 iframe...")
            target = page
            for f in page.frames:
                if 'order.list' in f.url:
                    target = f
                    log("[*] 找到目标 iframe: " + f.url)
                    break
            if target == page:
                log("[!] 未找到指定的 iframe，将使用主页面上下文。")

            # --- Open Advanced Search ---
            log("[*] 打开高级搜索面板并持续清理弹窗...")
            for _ in range(15):
                try:
                    await page.evaluate("document.querySelectorAll('.layui-layer, .layui-layer-shade, .modal-backdrop, #oauth-modal').forEach(el => el.remove());")
                except: pass
                
                try:
                    btn = target.locator('a:has-text("高级搜索")').first
                    if await btn.is_visible():
                        await btn.click(timeout=1000)
                        log("[*] 成功点击高级搜索面板")
                        break
                except:
                    pass
                await asyncio.sleep(1)
            
            await asyncio.sleep(2)
            # --- Configure Search Conditions ---
            log("[*] 开始配置高级搜索条件...")
            
            # 1. 滚动到顶部
            try:
                await target.evaluate("let mb = document.querySelector('.modal-body'); if(mb) mb.scrollTop = 0;")
            except: pass
            await asyncio.sleep(0.5)

            # 2. 查询时间段 -> 创建时间
            log("[*] 设置查询时间段为创建时间...")
            await target.locator('select[name="queryTime"]').select_option(value="createDate")
            await asyncio.sleep(1)

            # 3. 截止时间
            log("[*] 设置截止时间为今天...")
            await target.locator('#AdvanceSearch #datepicker-to').first.click(force=True)
            await asyncio.sleep(1)
            try:
                if await target.locator('#dpTodayInput').count() > 0:
                    await target.locator('#dpTodayInput').click(force=True)
                    await asyncio.sleep(0.5)
                    if await target.locator('#dpOkInput').is_visible():
                        await target.locator('#dpOkInput').click(force=True)
            except Exception as e:
                pass
            await asyncio.sleep(1)

            # 4. 起始时间
            log("[*] 设置起始时间（默认前一天）...")
            start_time = datetime.now() - timedelta(days=1)
            start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
            try:
                await target.evaluate("let el = document.getElementById('datepicker-from2'); if(!el) el = document.querySelector('.datepicker-from'); if(el) el.disabled = false;")
                await target.locator('#AdvanceSearch #datepicker-from2, .datepicker-from').first.fill(start_str, force=True)
            except Exception:
                try:
                    await target.evaluate(f"let el = document.getElementById('datepicker-from2'); if(!el) el = document.querySelector('.datepicker-from'); if(el) {{ el.value = '{start_str}'; el.dispatchEvent(new Event('change', {{ bubbles: true }})); }}")
                except: pass
            await asyncio.sleep(1)

            # 5. 查询条件1 -> 客户ID
            log("[*] 展开查询条件1下拉框并选择客户ID...")
            try:
                await target.locator('input[placeholder="-查询条件1-"]').first.click(force=True)
                await asyncio.sleep(1)
                await target.locator('.selectize-dropdown-content .option:has-text("客户ID")').first.click(force=True)
            except Exception:
                try:
                    await target.evaluate(\"""() => {
                        let s = document.querySelector('#AdvanceSearch #fuzzySearchKey');
                        if(!s) s = document.getElementById('fuzzySearchKey');
                        if(s) {
                            if(s.selectize) s.selectize.setValue('buyerUserId');
                            s.value = 'buyerUserId';
                            s.dispatchEvent(new Event('change', {bubbles: true}));
                        }
                    }\""")
                except: pass
            await asyncio.sleep(1)

            # 6. 输入 Customer ID
            customer_id = "1000000257".strip()
            log(f"[*] 填写客户ID: {customer_id}")
            try:
                fuzzy_input = target.locator('#AdvanceSearch #fuzzySearchValue, input[name="OrderSearch.fuzzySearchValue"]').first
                await target.evaluate("let el = document.getElementById('fuzzySearchValue'); if(!el) el = document.querySelector('input[name=\"OrderSearch.fuzzySearchValue\"]'); if(el) el.disabled = false;")
                await fuzzy_input.click(force=True)
                await fuzzy_input.fill("", force=True)
                await target.page.keyboard.type(customer_id) if hasattr(target, 'page') else await page.keyboard.type(customer_id)
                await asyncio.sleep(0.5)
            except Exception:
                try:
                    await target.evaluate(f\"""(cid) => {{
                        let el = document.querySelector('#AdvanceSearch #fuzzySearchValue');
                        if(!el) el = document.getElementById('fuzzySearchValue');
                        if(el) {{ el.disabled = false; el.value = cid; el.dispatchEvent(new Event('change', {{ bubbles: true }})); }}
                    }}\""", customer_id)
                except: pass
            await asyncio.sleep(1)
"""
    new_content = content[:start_idx] + new_logic + content[end_idx:]
    with open('automators/mabang_export_bot.py', 'w') as f:
        f.write(new_content)
    print("Patch iframe applied")
else:
    print("Patch iframe failed")
