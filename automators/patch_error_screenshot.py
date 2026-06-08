with open('automators/mabang_export_bot.py', 'r') as f:
    content = f.read()

old_except = """        except Exception as e:
            log(f"[!] 发生全局错误: {e}")"""

new_except = """        except Exception as e:
            await page.screenshot(path="debug_search_error.png")
            log(f"[!] 发生全局错误: {e}")"""

if old_except in content:
    with open('automators/mabang_export_bot.py', 'w') as f:
        f.write(content.replace(old_except, new_except))
    print("Patch error screenshot applied")
else:
    print("Patch error screenshot failed")
