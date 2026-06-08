import asyncio
import os
import yaml
import pandas as pd
from playwright.async_api import async_playwright
import sys

# 导入中心化配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SCRIPT_TEMPLATE

async def run_mabang_export(user_data_dir: str, days: int = 1, customer_id: str = '1000000257', headless: bool = False, progress_callback=None):
    def log(msg):
        print(msg)
        if progress_callback:
            progress_callback(msg)

    # 1. 读取配置文件获取账号密码
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    mb_user = str(config['mabang']['username'])
    mb_pwd = str(config['mabang']['password'])

    log("[*] 启动浏览器...")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=headless,
            viewport={'width': 1280, 'height': 800},
            accept_downloads=True
        )
        page = await context.new_page()
        
        try:
            # === 第一步：从首页进入并处理自动登录 ===
            log("[*] 正在打开马帮首页...")
            await page.goto("https://901067.private.mabangerp.com/index.htm", wait_until='domcontentloaded', timeout=60000)
            
            # 判断是否需要登录
            await asyncio.sleep(2)
            if await page.locator('#login-but').is_visible():
                log("[*] 检测到未登录状态，开始自动登录...")
                await page.locator('input[name="username"]').first.fill(mb_user)
                await page.locator('input[name="password"]').first.fill(mb_pwd)
                await page.locator('#login-but').click()
                log("[*] 登录已提交，等待页面加载...")
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(3)
            
            # === 第二步：处理首页的“店铺授权提醒”弹窗 ===
            log("[*] 等待并检查是否有授权提醒弹窗...")
            try:
                await page.wait_for_selector('text="店铺授权提醒"', timeout=5000)
                log("[*] 发现授权提醒弹窗，正在关闭...")
                checkbox = page.locator('text="7天内不再重复提醒"')
                if await checkbox.count() > 0:
                    await checkbox.click()
                await page.locator('.layui-layer-btn0, a:has-text("确认")').first.click()
                log("[*] 已点击确认关闭弹窗。")
                await asyncio.sleep(2)
            except Exception:
                log("[*] 没有发现弹窗，继续操作。")
            
            # === 第三步：导航到订单列表 ===
            log("[*] 导航至【订单列表】...")
            await page.goto("https://901067.private.mabangerp.com/index.php?mod=order.list&Order_orderStatus=2", wait_until='domcontentloaded')
            await page.wait_for_selector('span.text.mr5.ml5:has-text("批处理功能")', timeout=30000)
            await asyncio.sleep(3)
            
            # === 第四步：高级搜索 (257cpf改名前置过滤) ===
            log("[*] 打开高级搜索面板...")
            # 点击高级搜索按钮
            log("[*] 正在查找并点击【高级搜索】按钮...")
            try:
                await page.locator('text="高级搜索"').last.click(timeout=5000)
            except Exception:
                await page.evaluate("""() => {
                    let els = Array.from(document.querySelectorAll('a, button, span, div.btn')).filter(e => e.innerText && e.innerText.trim() === '高级搜索' && e.offsetParent !== null);
                    if (els.length > 0) {
                        els[0].click();
                    } else {
                        let btn = document.querySelector('#AdvanceSearchBtn button') || document.querySelector('#AdvanceSearchBtn');
                        if(btn) btn.click();
                    }
                }""")
            await asyncio.sleep(3)
            
            log("[*] 配置高级搜索条件：创建时间、起始时间、客户ID...")
            try:
                from datetime import datetime, timedelta
                now_dt = datetime.now()
                now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
                # 计算起始日期：当前时间减去 days 天
                start_dt_str = (now_dt - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
                
                await page.evaluate(f"""() => {{
                    // 1. 设置创建时间
                    let qTime = document.querySelector('#searchDetail select[name="queryTime"]');
                    if(qTime) {{
                        qTime.value = 'createDate';
                        qTime.dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                    
                    // 2. 设置起始和截止时间
                    let startTime = document.querySelector('#searchDetail input[name="startTime1"]');
                    if(startTime) {{
                        startTime.value = '{start_dt_str}';
                        startTime.dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                    
                    let endTime = document.querySelector('#searchDetail input[name="endTime1"]');
                    if(endTime) {{
                        endTime.value = '{now_str}';
                        endTime.dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                    
                    // 3. 设置客户ID筛选条件 (查询条件1)
                    let fKey = document.querySelector('#searchDetail #fuzzySearchKey');
                    if(fKey && fKey.selectize) {{
                        let opts = fKey.selectize.options;
                        let targetVal = null;
                        for(let k in opts) {{
                            if(opts[k].text.includes('客户ID') && !opts[k].text.includes('模糊')) {{
                                targetVal = opts[k].value;
                                break;
                            }}
                        }}
                        if(targetVal) {{
                            fKey.selectize.setValue(targetVal);
                        }} else {{
                            // 尝试硬编码 Fallback
                            fKey.selectize.setValue('a.buyerUserId');
                        }}
                    }}
                    
                    // 4. 填入搜索值
                    let fVal = document.querySelector('#searchDetail #fuzzySearchValue');
                    if(fVal) {{
                        fVal.disabled = false; // 确保不被禁用
                        fVal.value = '{customer_id}';
                        fVal.dispatchEvent(new Event('input', {{bubbles: true}}));
                        fVal.dispatchEvent(new Event('change', {{bubbles: true}}));
                    }}
                }}""")
            except Exception as e:
                log(f"[!] 配置筛选条件发生错误: {e}")
            await asyncio.sleep(2)
            
            # 增加一层保险：如果 JS 注入没生效，使用 Playwright 原生点击尝试选择
            try:
                # 检查是否还是显示 -查询条件1-
                if await page.locator('input[placeholder="-查询条件1-"]').count() > 0:
                    input_box = page.locator('input[placeholder="-查询条件1-"]').last
                    if await input_box.is_visible():
                        log("[*] JS可能未生效，使用原生点击选择 '按客户ID'")
                        await input_box.click(force=True)
                        await asyncio.sleep(1)
                        # 在下拉列表中点击包含“客户ID”的选项
                        await page.locator('.selectize-dropdown-content div.option:has-text("按客户ID")').last.click(force=True)
                        await asyncio.sleep(1)
            except Exception as e:
                log(f"[!] 原生点击选择查询条件1失败: {e}")
            
            # 4. 点击面板的搜索按钮
            log("[*] 提交高级搜索...")
            try:
                async with page.expect_navigation(timeout=8000):
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
            except Exception:
                # AJAX load or timeout
                pass

            await asyncio.sleep(4)
            
            # 由于可能出现面板未自动关闭导致遮挡，强制隐藏遮罩和面板
            try:
                await page.evaluate("""() => {
                    let modal = document.querySelector('#AdvanceSearch') || document.querySelector('#searchDetail');
                    if (modal) modal.style.display = 'none';
                    document.querySelectorAll('.modal-backdrop').forEach(el => el.style.display = 'none');
                }""")
            except Exception as e:
                log(f"[*] 隐藏弹窗面板失败 (可能页面正在跳转): {e}")
            await asyncio.sleep(2)
            
            # === 第4.5步：设置每页显示500条 ===
            log("[*] 设置每页显示 500 条...")
            try:
                # 尝试点击每页显示数量下拉框
                dropdown_btn = page.locator('button:has-text("每页")').last
                if await dropdown_btn.count() > 0:
                    await dropdown_btn.click(force=True)
                    await asyncio.sleep(1)
                    # 点击 500
                    await page.locator('a[onclick*="getPaginationData"]').filter(has_text="500").last.click(force=True)
                    log("[*] 已点击 500 条/页，等待数据重新加载...")
                    await asyncio.sleep(6)  # 给足够的时间让大量数据加载出来
                else:
                    # Fallback
                    await page.evaluate("if(typeof getPaginationData === 'function') getPaginationData(1,500);")
                    await asyncio.sleep(6)
            except Exception as e:
                log(f"[!] 设置每页 500 条失败: {e}")
            
            # === 第五步：全选当前页订单 ===
            log("[*] 正在勾选全选当前页订单...")
            # 找到全选按钮或者直接全选订单复选框
            await page.evaluate("""() => {
                let checkallBtn = document.getElementById('checkall');
                if(checkallBtn) {
                    checkallBtn.click();
                } else {
                    document.querySelectorAll('input.orderCheck').forEach(cb => {
                        if(!cb.checked) cb.click();
                    });
                }
            }""")
            await asyncio.sleep(1)
            
            # === 第六步：点击导出菜单 ===
            log("[*] 点击【导入/出相关】菜单...")
            await page.locator('#upLoadMenu button').click()
            await asyncio.sleep(1)
            
            log("[*] 点击【订单导出】并接管新标签页...")
            export_link = page.locator('#upLoadMenu a:text-is("订单导出")')
            
            async with context.expect_page() as new_page_info:
                await export_link.click(force=True)
                
            export_page = await new_page_info.value
            await export_page.wait_for_load_state('domcontentloaded')
            log(f"[*] 成功进入新标签页，URL: {export_page.url}")
            await asyncio.sleep(2)
            
            # === 第七步：配置导出字段 ===
            log("[*] 配置CPF导出弹窗字段...")
            await asyncio.sleep(5)
            
            # 点击全选/清空，保证所有复选框都被清空
            log("[*] 清空默认选中字段...")
            for f in export_page.frames:
                try:
                    await f.evaluate("""() => {
                        document.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                            if(cb.parentElement && cb.parentElement.innerText && cb.parentElement.innerText.includes("全选/清空")) return;
                            if(cb.checked) cb.click();
                        });
                    }""")
                except Exception:
                    pass
            await asyncio.sleep(1)
            
            # 重新精确勾选那三个：订单编号 客户姓名 abnnumber
            log("[*] 勾选：订单编号、客户姓名、abnnumber")
            for f in export_page.frames:
                try:
                    await f.evaluate("""() => {
                        let fields = ["订单编号", "客户姓名", "abnnumber"];
                        let checkboxes = document.querySelectorAll('input[type="checkbox"]');
                        checkboxes.forEach(cb => {
                            let parent = cb.parentElement;
                            if (parent && parent.innerText) {
                                let txt = parent.innerText.trim();
                                // 只使用精确匹配，防止包含关键字的其他多余字段被勾选
                                if (fields.some(f => txt === f)) {
                                    if (!cb.checked) {
                                        cb.click();
                                        console.log("Checked: " + txt);
                                    }
                                }
                            }
                        });
                    }""")
                except Exception:
                    pass
            await asyncio.sleep(1)
            
            # === 第八步：点击实时导出并接管下载 ===
            log("[*] 正在提交【实时导出】...")
            
            # Dump the iframe HTML to debug why the button is missing or not clicked
            for i, f in enumerate(export_page.frames):
                try:
                    f_html = await f.content()
                    with open(f"debug_export_frame_{i}.html", "w") as fp:
                        fp.write(f_html)
                except:
                    pass
            
            # 使用事件监听器而不是 context manager，防止页面关闭导致异常
            download_future = asyncio.get_event_loop().create_future()
            
            def handle_download(d):
                if not download_future.done():
                    download_future.set_result(d)
                    
            export_page.on("download", handle_download)
            page.on("download", handle_download)
            context.on("page", lambda p: p.on("download", handle_download)) # Catch all future pages just in case
            
            try:
                for f in export_page.frames:
                    try:
                        await f.evaluate("""() => {
                            let btns = Array.from(document.querySelectorAll('button, a, input[type="button"], span'));
                            let exportBtn = btns.find(b => b.innerText && b.innerText.includes("实时导出"));
                            if(exportBtn) exportBtn.click();
                        }""")
                    except Exception:
                        pass
                
                # 等待下载开始
                download = await asyncio.wait_for(download_future, timeout=120.0)
            except asyncio.TimeoutError:
                log(f"[!] 实时导出下载超时 (可能是因为搜索结果为空，导致没有弹出下载框)")
                if not export_page.is_closed():
                    try:
                        await export_page.screenshot(path="debug_export_download_fail.png")
                    except:
                        pass
                raise Exception("下载超时")
            except Exception as e:
                log(f"[!] 实时导出下载失败: {e}")
                if not export_page.is_closed():
                    try:
                        await export_page.screenshot(path="debug_export_download_fail.png")
                    except:
                        pass
                raise e
                
            download_dir = os.path.dirname(os.path.abspath(__file__))
            temp_path = os.path.join(download_dir, download.suggested_filename)
            log(f"[*] 正在下载文件至: {temp_path}")
            await download.save_as(temp_path)
            
            # === 第八步：使用 Pandas 处理表格并生成模板 ===
            log("[*] 读取并处理导出的文件...")
            try:
                try:
                    df = pd.read_excel(temp_path, dtype=str)
                except:
                    try:
                        df = pd.read_csv(temp_path, dtype=str)
                    except:
                        from bs4 import BeautifulSoup
                        with open(temp_path, 'r', encoding='utf-8', errors='replace') as f:
                            soup = BeautifulSoup(f.read(), 'html.parser')
                        tables = soup.find_all('table')
                        rows = []
                        for tr in tables[0].find_all('tr'):
                            rows.append([td.get_text(strip=True) for td in tr.find_all(['th', 'td'])])
                        df = pd.DataFrame(rows[1:], columns=rows[0])
                
                # 清洗列名中的空格
                df.columns = df.columns.str.strip()
                
                log(f"[*] 读取到的列: {list(df.columns)}")
                
                # 检查列是否存在
                abn_col = [c for c in df.columns if 'abnnumber' in c.lower()]
                if not abn_col:
                    log("[!] 找不到 abnnumber 列！")
                else:
                    abn_col = abn_col[0]
                    # 生成 D 列：文本格式的 "/cpf1 " + abnnumber
                    df['cpf1_abn'] = '/cpf1 ' + df[abn_col].astype(str)
                    
                    # 保存为最终的模板文件
                    if '订单编号' in df.columns:
                        df['订单编号'] = "\t" + df['订单编号'].astype(str)
                    output_excel = SCRIPT_TEMPLATE
                    df.to_excel(output_excel, index=False)
                    log(f"[*] 成功生成更新模板: {output_excel}")
                    log(f"[*] 预览前几行数据:\n{df.head(3)}")
            except Exception as e:
                log(f"[!] 处理表格文件时出错: {e}")
                
        except Exception as e:
            log(f"[!] 发生错误: {e}")
            if not page.is_closed():
                try:
                    await page.screenshot(path="debug_export_error.png")
                except:
                    pass
            
        finally:
            await context.close()
            log("[*] 测试结束。")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=1)
    parser.add_argument("--customer_id", default="1000000257")
    args = parser.parse_args()

    SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sessions", "mabang_session")
    asyncio.run(run_mabang_export(
        user_data_dir=SESSION_DIR, 
        days=args.days, 
        customer_id=args.customer_id, 
        headless=False
    ))
