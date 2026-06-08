with open('automators/mabang_export_bot.py', 'r') as f:
    content = f.read()

old_login = """            # --- Login ---
            log("[*] 检测到未登录状态，开始自动登录...")
            await page.locator('#developerId').fill("109138")
            await page.locator('#username').fill("109138030")
            await page.locator('#password').fill("ABCabc123")
            await page.locator('#login-submit').click()
            log("[*] 登录已提交，等待页面加载...")
            await page.wait_for_load_state('networkidle', timeout=30000)"""

new_login = """            # --- Login ---
            log("[*] 检查是否需要登录...")
            try:
                if await page.locator('#developerId').is_visible(timeout=5000):
                    await page.locator('#developerId').fill("109138")
                    await page.locator('#username').fill("109138030")
                    await page.locator('#password').fill("ABCabc123")
                    await page.locator('#login-submit').click()
                    log("[*] 登录已提交，等待页面加载...")
                    await page.wait_for_load_state('networkidle', timeout=30000)
                else:
                    log("[*] 已登录，无需填写密码。")
            except Exception:
                log("[*] 已经是登录状态。")"""

if old_login in content:
    with open('automators/mabang_export_bot.py', 'w') as f:
        f.write(content.replace(old_login, new_login))
    print("Patch applied")
else:
    print("Patch failed")
