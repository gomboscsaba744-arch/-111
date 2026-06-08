import asyncio
import os
import yaml
from openpyxl import load_workbook
from playwright.async_api import async_playwright

async def run_mabang_batch_update(excel_path: str, user_data_dir: str, headless: bool = False, progress_callback=None):
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

    import pandas as pd
    log(f"[*] 读取 Excel 数据: {excel_path}")
    df = pd.read_excel(excel_path, dtype=str)
    
    update_data = []
    for idx, row in df.iterrows():
        order_id = str(row.iloc[0]).strip()
        new_name = str(row.iloc[4]).strip() # 第5列，通常是结果列
        
        # 过滤无效的名字（兼容各种可能的空或错误状态）
        if order_id and new_name and new_name not in ["", "nan", "None", "无", "遇到验证码且未能通过", "查询超时", "提取失败"]:
            # 防止读取出科学计数法（如果真的被Excel弄坏了的话，尝试去掉 .0 等）
            if 'e+' in order_id.lower() or 'E+' in order_id:
                # 这种情况下单号已经被彻底损坏，但尽量补救
                try:
                    order_id = str(int(float(order_id)))
                except:
                    pass
            elif order_id.endswith('.0'):
                order_id = order_id[:-2]
                
            update_data.append(f"{order_id}\t{new_name}")
            
    if not update_data:
        log("[!] 没有提取到任何数据。")
        return False
        
    tsv_text = "\n".join(update_data)
    log(f"[*] 成功提取 {len(update_data)} 条数据。")

    log("[*] 启动浏览器...")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=headless,
            viewport={'width': 1280, 'height': 800}
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
                # 弹窗加载可能较慢，等待最多8秒
                await page.wait_for_selector('text="店铺授权提醒"', timeout=8000)
                log("[*] 发现授权提醒弹窗，正在关闭...")
                
                # 尝试勾选 7天内不再重复提醒
                checkbox = page.locator('text="7天内不再重复提醒"')
                if await checkbox.count() > 0:
                    await checkbox.click()
                    
                # layui的确认按钮通常是一个 <a> 标签带有 layui-layer-btn0 class
                await page.locator('.layui-layer-btn0, a:has-text("确认")').first.click()
                log("[*] 已点击确认关闭弹窗。")
                await asyncio.sleep(2)
            except Exception:
                log("[*] 没有发现弹窗，继续操作。")
            
            # === 第三步：直接导航到订单列表（比模拟菜单点击更稳定） ===
            log("[*] 导航至【订单列表】...")
            await page.goto("https://901067.private.mabangerp.com/index.php?mod=order.list&Order_orderStatus=2", wait_until='domcontentloaded')
            
            # 等待订单列表页面完全加载（等待批处理功能按钮出现）
            await page.wait_for_selector('span.text.mr5.ml5:has-text("批处理功能")', timeout=30000)
            await asyncio.sleep(2) # 缓冲一下，防止 DOM 渲染中
            
            # === 第四步：操作批处理功能 ===
            log("[*] 正在点击【批处理功能】菜单...")
            await page.evaluate("""
                const btns = Array.from(document.querySelectorAll('span'));
                const batchBtn = btns.find(el => el.textContent.trim() === '批处理功能');
                if (batchBtn) {
                    batchBtn.click();
                } else {
                    console.error("找不到批处理功能按钮");
                }
            """)
            await asyncio.sleep(1.5)
            
            # 还原人类操作模式：精准定位带特定标记的菜单层级
            log("[*] 正在通过标准 UI 悬停【批量更新订单信息】...")
            menu_item = page.locator('li[data-customlink="批量更新订单信息"]').first
            await menu_item.hover()
            await asyncio.sleep(1)
            
            log("[*] 正在点击子菜单【更新订单基本信息】...")
            # 使用 JS 直接点击以防止任何覆盖阻挡，扫描所有没有子元素的节点
            await page.evaluate("""
                const items = Array.from(document.querySelectorAll('*'));
                const target = items.find(el => el.children.length === 0 && el.textContent.trim() === '更新订单基本信息');
                if (target) {
                    target.click();
                }
            """)
            await asyncio.sleep(2)
            
            # === 第五步：注入数据 ===
            log("[*] 已打开更新弹窗。正在切换更新字段为【客户姓名】...")
            
            # 使用 Playwright 专门处理原生 select 的 select_option 方法，绝对稳定
            await page.locator('select[name="select2"]').select_option(label="客户姓名")
            await asyncio.sleep(1)
            
            log("[*] 正在注入更新数据...")
            # 使用原生唯一的 name 属性定位输入框，不会和其他输入框冲突
            textarea = page.locator('textarea[name="updateData"]')
            await textarea.fill("")
            await textarea.fill(tsv_text)
            log("[*] 注入成功！脚本已停止操作。请手动检查数据无误后，自行点击【确定】保存。")
            log("[*] 脚本将无限期等待，直到你完成检查并关闭弹窗...")
            
            # 无限期等待，直到更新弹窗隐藏（用户点击了确定或取消，或者页面刷新了）
            try:
                await page.wait_for_selector('#updateEmail', state='hidden', timeout=0)
            except Exception:
                pass # 如果页面发生了刷新导致 context 销毁，忽略报错
                
            log("[*] 检测到弹窗已关闭（你已提交操作）。即将进入下一个模块...")
            await asyncio.sleep(2)
            
        except Exception as e:
            log(f"[!] 发生错误: {e}")
            try:
                await page.screenshot(path="debug_mabang_error.png")
            except:
                pass
            import sys
            sys.exit(1)
            
        finally:
            await context.close()
            log("[*] 测试结束。")

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import SCRIPT_TEMPLATE

    EXCEL_PATH = SCRIPT_TEMPLATE
    SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sessions", "mabang_session")
    asyncio.run(run_mabang_batch_update(EXCEL_PATH, SESSION_DIR, headless=False))
