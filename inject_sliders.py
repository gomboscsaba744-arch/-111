with open('app.py', 'r') as f:
    content = f.read()

if "光效微调控制台" not in content:
    sliders_code = """
st.sidebar.markdown("### 🎛️ 光效微调控制台")
thickness = st.sidebar.slider("核心厚度 (Thickness)", 0.05, 0.30, 0.131, 0.001)
blur = st.sidebar.slider("上下晕染 (Blur)", 0.01, 0.30, 0.12, 0.001)
brightness = st.sidebar.slider("整体曝光 (Brightness)", 0.1, 2.0, 0.8, 0.01)

st.components.v1.html(f'''
<script>
    const parentDoc = window.parent.document;
    const iframe = parentDoc.getElementById("vanguard-3d-bg");
    if (iframe && iframe.contentWindow) {{
        iframe.contentWindow.postMessage({{
            type: "UPDATE_STRANDS",
            payload: {{ thickness: {thickness}, blur: {blur}, brightness: {brightness} }}
        }}, "*");
    }}
</script>
''', height=0)
"""
    # Insert safely into app.py
    content = content.replace('if st.session_state.route is None:', sliders_code + '\n    if st.session_state.route is None:')
    
    with open('app.py', 'w') as f:
        f.write(content)
        print("Sliders injected successfully.")
else:
    print("Already injected.")
