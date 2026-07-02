import re
import urllib.parse

with open('app.py', 'r') as f:
    content = f.read()

content = re.sub(r'import streamlit\.components\.v1 as components\nimport os\ntry:\n    dist_path =.*?\n    _r3f_bg\(height=800\)\nexcept Exception as e:\n    pass\n', '', content, flags=re.DOTALL)

content = re.sub(r'\s*/\* 强制 R3F Iframe 成为全屏背景，并且置于内容底层 \*/\n\s*iframe\[title="r3f_background"\] \{.*?\n\s*\}', '', content, flags=re.DOTALL)

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
        
        inject_script = f\"\"\"
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
                iframe.style.zIndex = "-1";
                iframe.style.border = "none";
                iframe.style.pointerEvents = "none";
                
                iframe.srcdoc = decodeURIComponent("{html_data_encoded}");
                
                parentDoc.body.appendChild(iframe);
            }}
        </script>
        \"\"\"
        components.html(inject_script, height=0, width=0)
except Exception as e:
    pass
"""

content = content.replace('if st.session_state.route is None:', inject_code + '\nif st.session_state.route is None:')

with open('app.py', 'w') as f:
    f.write(content)
