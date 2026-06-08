import asyncio
import os
from playwright.async_api import async_playwright
import sys

# 添加父目录到 sys.path 以便导入 config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MABANG_SESSION_DIR

async def main():
    print("启动专门的马帮浏览器环境...")
    os.makedirs(MABANG_SESSION_DIR, exist_ok=True)
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=MABANG_SESSION_DIR,
            channel="chrome",  # 使用本地 Chrome，方便你调用各种密码库
            headless=False,
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        # 打开一个空白页，或者你可以直接输入马帮网址
        await page.goto("https://www.google.com")
        
        print("\n=============================================")
        print("👉 请在弹出的浏览器中，手动输入马帮的网址并进行登录。")
        print("👉 登录成功后（建议勾选'记住密码/保持登录'），请直接【关闭浏览器窗口】。")
        print("👉 关闭后，你的登录状态就会永久保存在 mabang_session 中！")
        print("=============================================\n")
        
        # 持续运行，直到用户把所有页面/浏览器关掉
        while len(context.pages) > 0:
            await asyncio.sleep(1)
            
        print("✅ 浏览器已关闭，马帮登录信息保存成功！")

if __name__ == '__main__':
    asyncio.run(main())
