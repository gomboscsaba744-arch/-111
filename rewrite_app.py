import re

with open('app.py', 'r') as f:
    content = f.read()

# Remove the bg injection
content = re.sub(r'import streamlit\.components\.v1 as components\nimport os\nimport urllib\.parse\n\ntry:\n    bg_html_path = .*?components\.html\(inject_script, height=0, width=0\)\nexcept Exception as e:\n    pass\n\n', '', content, flags=re.DOTALL)

# Add declare component
replacement_component = """
import streamlit.components.v1 as components
import os
dist_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "3d_background", "dist")
_fluid_glass_button = components.declare_component("fluid_glass_button", path=dist_path)

"""

if "dist_path = " not in content:
    content = content.replace('if st.session_state.route is None:', replacement_component + 'if st.session_state.route is None:')

# Replace cols
content = re.sub(r'    col1, col2 = st\.columns\(2, gap="large"\).*?# 彻底解决点击问题', 
"""    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        clicked_A = _fluid_glass_button(title="CPF 解析管线", icon="🔍", desc="核心身份验真引擎<br>Telegram 智能辅助查名<br>与 ERP 无缝回填闭环", route="A", key="btn_A")
        if clicked_A == "A":
            st.session_state.route = "A"
            st.rerun()
            
    with col2:
        clicked_B = _fluid_glass_button(title="DSERS 铺货管线", icon="📦", desc="跨境订单深度倒模映射<br>一键推送建单发货流转<br>全链路自动追踪同步", route="B", key="btn_B")
        if clicked_B == "B":
            st.session_state.route = "B"
            st.rerun()

    # ==========================
    # 彻底解决点击问题""", content, flags=re.DOTALL)

content = re.sub(r'    # ==========================\n    # 彻底解决点击问题：JS 事件透传引擎\n    # ==========================\n    import streamlit\.components\.v1 as components\n    components\.html\("""\n    <script>.*?    </script>\n    """, height=0, width=0\)', '', content, flags=re.DOTALL)

with open('app.py', 'w') as f:
    f.write(content)
