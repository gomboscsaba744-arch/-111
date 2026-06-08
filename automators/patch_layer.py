with open('automators/mabang_export_bot.py', 'r') as f:
    content = f.read()

old_popup = """                await page.evaluate('''() => {
                    document.querySelectorAll('.layui-layer-close, .layui-layer-btn0, .close, [data-dismiss="modal"]').forEach(b => {
                        try { b.click(); } catch(e){}
                    });
                    document.querySelectorAll('.modal-backdrop, .layui-layer-shade').forEach(el => el.remove());
                }''')"""

new_popup = """                await page.evaluate('''() => {
                    try { if(window.layer) layer.closeAll(); } catch(e){}
                    document.querySelectorAll('.layui-layer-close, .layui-layer-btn0, .close, [data-dismiss="modal"]').forEach(b => {
                        try { b.click(); } catch(e){}
                    });
                    document.querySelectorAll('.layui-layer, .layui-layer-shade, .modal-backdrop').forEach(el => el.remove());
                }''')"""

if old_popup in content:
    with open('automators/mabang_export_bot.py', 'w') as f:
        f.write(content.replace(old_popup, new_popup))
    print("Patch layer applied")
else:
    print("Patch layer failed")
