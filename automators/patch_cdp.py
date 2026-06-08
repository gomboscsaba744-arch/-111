with open('automators/mabang_export_bot.py', 'r') as f:
    content = f.read()

old_launch = """    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()"""

new_launch = """    async with async_playwright() as p:
        log("[*] 连接到已打开的 Chrome 浏览器...")
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        
        # 激活当前页面
        await page.bring_to_front()"""

if old_launch in content:
    with open('automators/mabang_export_bot.py', 'w') as f:
        f.write(content.replace(old_launch, new_launch))
    print("Patch CDP launch applied")
else:
    print("Patch CDP launch failed")
