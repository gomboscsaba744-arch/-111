import asyncio
import os
from playwright.async_api import async_playwright

async def run_dsers_import(csv_path: str, user_data_dir: str, headless: bool = False, progress_callback=None):
    def log(msg):
        print(msg)
        if progress_callback:
            progress_callback(msg)

    if not os.path.exists(csv_path):
        log(f"[!] 找不到 CSV 文件: {csv_path}")
        return

    log("[*] 启动 DSers 自动导入引擎...")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            channel="chrome",
            headless=headless,
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()

        try:
            # 1. 登录与导航
            TARGET_URL = "https://accounts.dsers.com/accounts/login?redirect_url=https%3A%2F%2Fwww.dsers.com%2Fapplication%2Forders%2F159831080"
            log(f"[*] 尝试访问 DSers 仪表盘: {TARGET_URL} ...")
            try:
                await page.goto(TARGET_URL, wait_until='domcontentloaded', timeout=15000)
            except Exception as e:
                log(f"[!] 网络访问异常 ({e})，正在重试...")
                await asyncio.sleep(2)
                await page.goto(TARGET_URL, wait_until='domcontentloaded')
            
            while "login" in page.url.lower():
                await asyncio.sleep(1)
            
            log("[*] 检测到处于主控台状态。等待页面缓冲...")
            await asyncio.sleep(3)

            # 2. 点击左侧 CSV Upload
            log("[*] 正在点击【CSV Upload】...")
            try:
                # DSers左侧菜单可能嵌套，使用精确匹配文本
                await page.get_by_text("CSV Upload", exact=True).locator("visible=true").first.click(timeout=8000, force=True)
            except Exception:
                await page.evaluate("""() => {
                    let els = Array.from(document.querySelectorAll('a, li, span, div')).filter(e => e.innerText && e.innerText.trim() === 'CSV Upload' && e.offsetHeight > 0);
                    // 找出没有子元素也叫 CSV Upload 的最内层元素
                    let target = els.find(e => !Array.from(e.children).some(c => c.innerText && c.innerText.trim() === 'CSV Upload')) || els[0];
                    if (target) target.click();
                }""")
            await asyncio.sleep(4)

            # 3. 点击 Orders 选项卡
            log("[*] 正在切换至【Orders】标签页...")
            try:
                # 只点击可见的 Orders 选项卡
                await page.locator('.ant-tabs-tab, [role="tab"]').filter(has_text="Orders").locator("visible=true").first.click(timeout=5000, force=True)
            except Exception:
                await page.evaluate("""() => {
                    let tabs = Array.from(document.querySelectorAll('[role="tab"], .ant-tabs-tab')).filter(e => e.offsetHeight > 0);
                    let orderTab = tabs.find(t => t.innerText && t.innerText.trim() === 'Orders');
                    if (orderTab) orderTab.click();
                }""")
            await asyncio.sleep(3)

            # 4. 点击面板外层的 + IMPORT 按钮唤出上传弹窗
            log("[*] 正在面板上触发【+ IMPORT】按钮以打开对话框...")
            try:
                # 首先确保在页面上找到大写的 IMPORT 按钮并点击
                await page.locator('button, div[role="button"]').filter(has_text="IMPORT").locator("visible=true").first.click(timeout=5000)
            except Exception:
                await page.evaluate("""() => {
                    let btns = Array.from(document.querySelectorAll('button, div[role="button"]')).filter(b => b.innerText && b.innerText.includes('IMPORT') && b.offsetHeight > 0);
                    if (btns.length > 0) btns[0].click();
                }""")
            
            # 给予弹窗渲染时间
            await asyncio.sleep(2)

            # 5. 在弹窗中点击 CHOOSE CSV FILE 触发选择器并装载
            log("[*] 正在弹窗中装载 CSV 文件...")
            try:
                await page.wait_for_selector('.ant-modal-content, .el-dialog, [role="dialog"]', state='visible', timeout=4000)
            except:
                pass
                
            try:
                await page.locator('input[type="file"]').first.set_files(csv_path, timeout=3000)
                log("[*] 文件直接挂载成功！等待导入按钮激活...")
            except:
                log("[!] 底层 input 未命中，尝试触发界面交互 (点击 CHOOSE CSV FILE 唤起选择器)...")
                async with page.expect_file_chooser(timeout=10000) as fc_info:
                    try:
                        await page.locator('button, div[role="button"], span').filter(has_text="CHOOSE CSV FILE").locator("visible=true").first.click(timeout=3000)
                    except:
                        await page.evaluate("""() => {
                            let dialogs = document.querySelectorAll('[role="dialog"], .el-dialog, .modal, .ant-modal, .v-dialog');
                            let root = dialogs.length > 0 ? dialogs[dialogs.length - 1] : document;
                            let btn = Array.from(root.querySelectorAll('button, div, span, a'))
                                .filter(e => e.offsetHeight > 0)
                                .find(e => {
                                    let t = (e.innerText || '').toLowerCase();
                                    return (t.includes('choose') || t.includes('upload')) && 
                                           (t.includes('csv') || t.includes('file'));
                                });
                            if(btn) btn.click();
                            else {
                                let inputs = root.querySelectorAll('input[type="file"]');
                                if(inputs.length > 0 && inputs[inputs.length - 1].parentElement) {
                                    inputs[inputs.length - 1].parentElement.click();
                                }
                            }
                        }""")
                file_chooser = await fc_info.value
                await file_chooser.set_files(csv_path)
                log("[*] 传统交互挂载成功！等待导入按钮激活...")
                
            await asyncio.sleep(3)

            # 6. 点击弹窗中的确认 IMPORT 按钮
            log("[*] 正在提交导入请求...")
            try:
                await page.evaluate("""() => {
                    let dialogs = document.querySelectorAll('[role="dialog"], .el-dialog, .modal, .ant-modal, .v-dialog');
                    let root = dialogs.length > 0 ? dialogs[dialogs.length - 1] : document;
                    let btns = Array.from(root.querySelectorAll('button')).filter(b => b.innerText && b.innerText.includes('IMPORT') && !b.disabled);
                    // 点击弹窗里的最后一个 IMPORT 按钮
                    if (btns.length > 0) btns[btns.length - 1].click();
                }""")
            except Exception as e:
                log(f"[!] 提交导入时发生异常: {e}")
            
            log("[*] 提交指令已发送，等待页面响应...")
            await asyncio.sleep(3)
            log("✅ DSers 订单批量导入指令已执行完毕！")
            log("[*] 浏览器将保持开启 15 秒钟供您检查导入结果，随后将自动安全关闭...")
            await asyncio.sleep(15)

        except Exception as e:
            log(f"❌ 自动化导入中途报错: {e}")
            if not page.is_closed():
                try:
                    await page.screenshot(path="debug_dsers_import_error.png")
                except:
                    pass
            import sys
            sys.exit(1)
        finally:
            await context.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()

    SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sessions", "dsers_session")
    asyncio.run(run_dsers_import(args.csv, SESSION_DIR, False))
