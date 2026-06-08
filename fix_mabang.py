with open('automators/mabang_export_bot.py', 'r') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if "f.write(html_dump)" in line:
        # start replacing here
        new_lines.append("""            log("[*] 配置高级搜索条件：创建时间、客户ID...")
            
            # 点击查询时间段下拉框并选择“创建时间”
            try:
                await page.evaluate("let s = document.querySelector('select[name=\\"Order.timeType\\"]'); if(s){ s.value='1'; s.dispatchEvent(new Event('change')); }")
            except Exception:
                pass
            await asyncio.sleep(1)
            
            # 截止时间 -> 今天
            log("[*] 设置截止时间为今天...")
            try:
                from datetime import datetime, timedelta
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await page.evaluate(f"let el = document.getElementById('datepicker-to'); if(el) el.value = '{now_str}';")
            except Exception:
                pass
            await asyncio.sleep(1)
            
            log("[*] 设置起始时间（默认前一天）...")
            try:
                from datetime import datetime, timedelta
                yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
                await page.evaluate(f"let el = document.getElementById('datepicker-from'); if(el) el.value = '{yesterday_str}';")
            except Exception:
                pass
            await asyncio.sleep(1)
            
            # 填入条件1：客户ID
            customer_id = "1000000257"
            log(f"[*] 填写客户ID: {customer_id}")
            try:
                await page.evaluate(f"let el = document.querySelector('input[name=\\"clientId\\"]'); if(el) el.value = '{customer_id}';")
            except Exception:
                pass
            await asyncio.sleep(1)
            
            # 4. 点击面板的搜索按钮
            log("[*] 提交高级搜索...")
            await page.evaluate('''() => {
                let btn = document.getElementById('searchMore');
                if(btn) {
                    btn.click();
                } else {
                    let btns = Array.from(document.querySelectorAll('button'));
                    let b = btns.find(x => x.innerText && x.innerText.trim() === '搜索');
                    if(b) b.click();
                }
            }''')
\n""")
        skip = True
    
    if skip and "await asyncio.sleep(4)" in line:
        skip = False
        new_lines.append(line)
        continue
        
    if not skip:
        new_lines.append(line)

with open('automators/mabang_export_bot.py', 'w') as f:
    f.writelines(new_lines)
