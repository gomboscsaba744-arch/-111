import re
import urllib.parse

with open('app.py', 'r') as f:
    content = f.read()

# Make sure we don't inject twice
if "vanguard-3d-bg" not in content:
    inject_code = """
import streamlit.components.v1 as components
import os
import urllib.parse

try:
    bg_html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "3d_background", "dist", "index.html")
    if os.path.exists(bg_html_path):
        with open(bg_html_path, "r", encoding="utf-8") as f:
            html_data = f.read()
        
        html_data_encoded = urllib.parse.quote(html_data)
        
        inject_script = f'''
        <script>
            const parentDoc = window.parent.document;
            if (!parentDoc.getElementById("vanguard-3d-bg")) {{
                const iframe = parentDoc.createElement("iframe");
                iframe.id = "vanguard-3d-bg";
                iframe.style.position = "fixed";
                iframe.style.top = "0";
                iframe.style.left = "0";
                iframe.style.width = "100vw";
                iframe.style.height = "100vh";
                iframe.style.zIndex = "0";
                iframe.style.border = "none";
                iframe.style.pointerEvents = "none";
                iframe.srcdoc = decodeURIComponent("{html_data_encoded}");
                parentDoc.body.appendChild(iframe);
            }}
        </script>
        '''
        components.html(inject_script, height=0, width=0)
except Exception as e:
    pass

"""
    # Insert right before 'if st.session_state.route is None:'
    content = content.replace('if st.session_state.route is None:', inject_code + 'if st.session_state.route is None:')

    with open('app.py', 'w') as f:
        f.write(content)
        print("Injected successfully")
else:
    print("Already injected")
