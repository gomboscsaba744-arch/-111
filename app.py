import streamlit as st
import pandas as pd
import asyncio
import os
import subprocess

from config import MODE1_EXCEL, MODE2_EXCEL, MODE3_EXCEL, MODE4_EXCEL, TELEGRAM_SESSION_DIR, DATA_DIR, DSERS_SESSION_DIR, DSERS_TEMPLATE, DSERS_IMPORT_XLSX, DSERS_IMPORT_CSV, SCRIPT_TEMPLATE
from automators.telegram_cpf_bot import run_cpf_query
from automators.dsers_update_bot import run_dsers_rename

st.set_page_config(page_title="Global Pipeline Studio", layout="wide", initial_sidebar_state="collapsed")

if 'route' not in st.session_state:
    st.session_state.route = None

# COMMON CSS (Morandi Background, Glassmorphism, hide sidebar)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', -apple-system, sans-serif;
    }

    /* 绝对隐藏侧边栏和顶栏 */
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    header { visibility: hidden !important; }

    /* 莫兰迪色系毛玻璃渐变背景 */
    .stApp {
        background-color: #F8F7F5 !important;
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(212, 196, 199, 0.45) 0%, transparent 40%),  /* 莫兰迪粉 */
            radial-gradient(circle at 90% 80%, rgba(186, 195, 198, 0.45) 0%, transparent 40%),  /* 莫兰迪灰蓝 */
            radial-gradient(circle at 50% 50%, rgba(198, 203, 195, 0.3) 0%, transparent 50%);  /* 莫兰迪绿 */
        background-attachment: fixed;
    }

    /* 通用毛玻璃卡片 */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(255, 255, 255, 0.5) !important;
        backdrop-filter: blur(40px) saturate(150%) !important;
        -webkit-backdrop-filter: blur(40px) saturate(150%) !important;
        border: 1px solid rgba(255, 255, 255, 0.9) !important;
        border-radius: 32px !important;
        box-shadow: 0 20px 40px -10px rgba(0,0,0,0.03), inset 0 1px 0 rgba(255,255,255,0.8) !important;
        padding: 2.5rem !important;
        transition: transform 0.4s ease, box-shadow 0.4s ease;
    }

    h1, h2, h3 {
        color: #2D3748 !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    
    /* 调整顶部空白 */
    .block-container {
        padding-top: 3rem !important;
    }
</style>
""", unsafe_allow_html=True)

if st.session_state.route is None:
    # ==========================
    # 首页大屏视觉效果 (Home Screen)
    # ==========================
    st.markdown("""
    <style>
        /* 巨大按钮动效 */
        [data-testid="stButton"] button {
            height: 450px !important;
            width: 100% !important;
            border-radius: 48px !important;
            background: rgba(255, 255, 255, 0.25) !important;
            border: 1px solid rgba(255, 255, 255, 0.5) !important;
            backdrop-filter: blur(20px) !important;
            box-shadow: 0 15px 35px rgba(0,0,0,0.02) !important;
            transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1) !important;
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        /* 扫光动效 */
        [data-testid="stButton"] button::before {
            content: "";
            position: absolute;
            top: 0; left: -100%;
            width: 50%; height: 100%;
            background: linear-gradient(to right, transparent, rgba(255,255,255,0.4), transparent);
            transform: skewX(-20deg);
            transition: all 0.7s;
        }
        
        [data-testid="stButton"] button:hover::before {
            left: 150%;
        }
        
        /* 悬浮飞跃动效 */
        [data-testid="stButton"] button:hover {
            transform: translateY(-20px) scale(1.02) !important;
            background: rgba(255, 255, 255, 0.7) !important;
            border-color: rgba(255, 255, 255, 1) !important;
            box-shadow: 0 40px 80px rgba(0,0,0,0.1) !important;
        }
        
        /* 字体样式 */
        [data-testid="stButton"] button p {
            font-size: 38px !important;
            font-weight: 800 !important;
            color: #2D3748 !important;
            line-height: 1.5 !important;
            text-shadow: 0 4px 15px rgba(255,255,255,0.8);
            white-space: pre-wrap;
        }
        
        .main-title {
            text-align: center;
            font-size: 5rem;
            font-weight: 800;
            margin-top: 4vh;
            margin-bottom: 8vh;
            color: #1A202C;
            letter-spacing: -2px;
            text-shadow: 0 10px 30px rgba(0,0,0,0.05);
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title">Global Pipeline Studio</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([1, 4, 4, 1], gap="large")
    with c2:
        if st.button("🎯\n路线 A\nCPF 洗白补全流", use_container_width=True):
            st.session_state.route = "A"
            st.rerun()
    with c3:
        if st.button("📦\n路线 B\nDSers 铺货代发流", use_container_width=True):
            st.session_state.route = "B"
            st.rerun()

else:
    # ==========================
    # 具体管线内页配置 (Route Screen)
    # ==========================
    st.markdown("""
    <style>
        /* 返回主界面特定按钮伪装 */
        .back-btn-container [data-testid="stButton"] button {
            background: rgba(255,255,255,0.6) !important;
            color: #4A5568 !important;
            border-radius: 12px !important;
            padding: 0.5rem 1rem !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.02) !important;
            border: 1px solid rgba(255,255,255,1) !important;
            transition: all 0.3s ease !important;
        }
        .back-btn-container [data-testid="stButton"] button:hover {
            background: #fff !important;
            transform: translateY(-2px) !important;
        }
        
        /* 底部超级启动按钮 */
        .launch-btn-container [data-testid="stButton"] button {
            background: linear-gradient(135deg, #1A202C 0%, #2D3748 100%) !important;
            color: #ffffff !important;
            border: none !important;
            border-radius: 24px !important;
            padding: 1.5rem 2rem !important;
            font-size: 1.3rem !important;
            font-weight: 800 !important;
            width: 100% !important;
            box-shadow: 0 20px 40px -10px rgba(26, 32, 44, 0.4) !important;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
        }
        .launch-btn-container [data-testid="stButton"] button:hover {
            transform: translateY(-5px) scale(1.01) !important;
            box-shadow: 0 30px 60px -10px rgba(26, 32, 44, 0.5) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    route_name = "🎯 路线 A : CPF 洗白补全流" if st.session_state.route == "A" else "📦 路线 B : DSers 铺货代发流"
    
    col1, col2 = st.columns([8, 2])
    with col1:
        st.markdown(f'<h1 style="margin-top:0;">{route_name}</h1>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="back-btn-container">', unsafe_allow_html=True)
        if st.button("⬅️ 返回分流室 (Back)"):
            st.session_state.route = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    current_excel_path = MODE1_EXCEL

    with st.container(border=True):
        st.markdown("### 🔌 1. 燃料接入 (Data Source)")
        data_source = st.radio("选择数据接入方式", ["调用马帮脚本提取", "上传全新本地表格", "使用前端已有表格"], horizontal=True, label_visibility="collapsed")
        sw_auto_export = (data_source == "调用马帮脚本提取")
        use_vault = (data_source == "使用前端已有表格")

        if sw_auto_export:
            st.markdown("<br><b>马帮引擎检索参数：</b>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                days = st.number_input("提取天数范围", min_value=1, max_value=30, value=1)
            with c2:
                if st.session_state.route == "A":
                    search_val = st.text_input("目标客户 ID (精准提取)", value="1000000257")
                else:
                    search_val = st.text_input("库存 SKU (反向排除过滤)", value="code")
        elif data_source == "上传全新本地表格":
            st.markdown("<br>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("请将您的 .xlsx 表格拖入此玻璃舱内", type=["xlsx", "xls"])
            if uploaded_file:
                with open(current_excel_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("✅ 数据源已挂载，燃料充足。")
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            vault_file_choice = st.selectbox("🎯 请指定要继续往下执行流转的【起始表格】", ["dsers模板.xlsx", "import_orders.xlsx", "脚本模板.xlsx"])
            if vault_file_choice == "dsers模板.xlsx":
                current_excel_path = DSERS_TEMPLATE
            elif vault_file_choice == "import_orders.xlsx":
                current_excel_path = DSERS_IMPORT_XLSX
            else:
                current_excel_path = SCRIPT_TEMPLATE
            
            if os.path.exists(current_excel_path):
                st.success(f"✅ 已瞄准前端保险库中的 {vault_file_choice}，可以直接执行后续选中的环节！")
            else:
                st.warning(f"⚠️ {vault_file_choice} 尚未生成，请先执行前置环节。")

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    if st.session_state.route == "A":
        with st.container(border=True):
            st.markdown("### ⚙️ 2. 后置管线调配 (Actions)")
            sw_cpf_rename = st.toggle("💬 连通 Telegram 接口开启 CPF 智能查名", value=True)
            sw_mabang_update = st.toggle("🔄 将清洗结果全自动闭环回填至马帮 ERP", value=True)
    else:
        with st.container(border=True):
            st.markdown("### ⚙️ 2. 后置管线调配 (Actions)")
            sw_dsers_clean = st.toggle("深度清洗并倒模映射到 DSers 标准模板", value=True)
            sw_dsers_cpf_check = st.toggle("映射后进行 Telegram CPF 查名，并自动修正模板姓名", value=True)
            sw_dsers_mabang = st.toggle("姓名查明后，回填更新到马帮 ERP (需配合查名使用)", value=True)
            sw_dsers_import = st.toggle("执行全自动一键上传/建单到 DSers", value=True)
            st.markdown("---")
            sw_dsers_rename = st.toggle("独立分支：针对已在 DSers 的订单做网页版精准改名", value=False)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # ==========================
    # 数据保险库 Data Vault (实时预览)
    # ==========================
    with st.expander("🗄️ 前端数据保险库 (Data Vault) - 实时查看内部底层表格", expanded=False):
        st.markdown("在这里，您可以直接预览隐藏流转的各种关键数据表，无需再去寻找源文件。")
        vault_tabs = st.tabs(["dsers模板.xlsx", "import_orders.xlsx", "脚本模板.xlsx"])
        
        with vault_tabs[0]:
            if os.path.exists(DSERS_TEMPLATE):
                try:
                    df1 = pd.read_excel(DSERS_TEMPLATE, dtype=str)
                    st.caption(f"📊 当前表格规格：共 **{df1.shape[0]}** 行 (数据) × **{df1.shape[1]}** 列 (字段)")
                    edited_df1 = st.data_editor(df1, num_rows="dynamic", use_container_width=True, key="edit_dsers")
                    
                    colA, colB = st.columns(2)
                    with colA:
                        if st.button("💾 手动保存修改", key="save_dsers"):
                            if not df1.equals(edited_df1):
                                edited_df1.to_excel(DSERS_TEMPLATE, index=False)
                                st.success("✅ 修改已永久保存至 dsers模板.xlsx")
                            else:
                                st.info("内容无变化，无需保存。")
                    with colB:
                        with open(DSERS_TEMPLATE, "rb") as f:
                            st.download_button("📥 下载最新版 dsers模板", f, "dsers模板.xlsx", key="dl_dsers")
                except Exception as e:
                    st.warning(f"无法读取: {e}")
            else:
                st.info("尚无该文件流转。")
                
        with vault_tabs[1]:
            if os.path.exists(DSERS_IMPORT_XLSX):
                try:
                    df2 = pd.read_excel(DSERS_IMPORT_XLSX, dtype=str)
                    st.caption(f"📊 当前表格规格：共 **{df2.shape[0]}** 行 (数据) × **{df2.shape[1]}** 列 (字段)")
                    edited_df2 = st.data_editor(df2, num_rows="dynamic", use_container_width=True, key="edit_import")
                    
                    colA, colB = st.columns(2)
                    with colA:
                        if st.button("💾 手动保存修改", key="save_import"):
                            if not df2.equals(edited_df2):
                                edited_df2.to_excel(DSERS_IMPORT_XLSX, index=False)
                                st.success("✅ 修改已永久保存至 import_orders.xlsx")
                            else:
                                st.info("内容无变化，无需保存。")
                    with colB:
                        with open(DSERS_IMPORT_XLSX, "rb") as f:
                            st.download_button("📥 下载最新版 import_orders", f, "import_orders.xlsx", key="dl_import")
                except Exception as e:
                    st.warning(f"无法读取: {e}")
            else:
                st.info("尚无该文件流转。")
                
        with vault_tabs[2]:
            if os.path.exists(SCRIPT_TEMPLATE):
                try:
                    df3 = pd.read_excel(SCRIPT_TEMPLATE, dtype=str)
                    st.caption(f"📊 当前表格规格：共 **{df3.shape[0]}** 行 (数据) × **{df3.shape[1]}** 列 (字段)")
                    edited_df3 = st.data_editor(df3, num_rows="dynamic", use_container_width=True, key="edit_script")
                    
                    colA, colB = st.columns(2)
                    with colA:
                        if st.button("💾 手动保存修改", key="save_script"):
                            if not df3.equals(edited_df3):
                                edited_df3.to_excel(SCRIPT_TEMPLATE, index=False)
                                st.success("✅ 修改已永久保存至 脚本模板.xlsx")
                            else:
                                st.info("内容无变化，无需保存。")
                    with colB:
                        with open(SCRIPT_TEMPLATE, "rb") as f:
                            st.download_button("📥 下载最新版 脚本模板", f, "脚本模板.xlsx", key="dl_script")
                except Exception as e:
                    st.warning(f"无法读取: {e}")
            else:
                st.info("尚无该文件流转。")

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    st.markdown('<div class="launch-btn-container">', unsafe_allow_html=True)
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        btn_launch = st.button("🚀 启动流水线 (LAUNCH PIPELINE)")
    with c_btn2:
        btn_kill = st.button("🛑 紧急复位 (KILL PROCESSES)")
        
    if btn_kill:
        st.warning("⚠️ 正在强制终止所有后台自动化残余进程...")
        os.system("pkill -f playwright")
        os.system("pkill -f chrome")
        st.success("✅ 僵尸进程已清零，您可以安全地重新启动流水线！")
        st.stop()

    if btn_launch:
        if not sw_auto_export and not os.path.exists(current_excel_path):
            if use_vault:
                st.error(f"❌ 引擎无法启动：所选的基础表格 '{vault_file_choice}' 不存在，请先执行前置步骤生成它！")
            else:
                st.error("❌ 引擎无法启动：请先上传本地表格燃料！")
        else:
            log_container = st.empty()
            
            # --- 阶段 1 ---
            if sw_auto_export:
                log_container.info("🔄 [阶段 1] 正在驱动马帮自动化萃取引擎...")
                try:
                    export_script = "automators/mabang_export_bot.py" if st.session_state.route == "A" else "automators/mabang_dsers_export.py"
                    flag = "--customer_id" if st.session_state.route == "A" else "--sku"
                    cmd = ["python3", export_script, "--days", str(days), flag, search_val]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        log_container.success(f"✅ [阶段 1] 数据源萃取圆满成功！")
                    else:
                        log_container.error(f"❌ 马帮引擎报错:\n{result.stderr}")
                        st.stop()
                except Exception as e:
                    log_container.error(f"执行异常: {e}")
                    st.stop()
                    
            # --- 阶段 2: 依据管线执行 ---
            if st.session_state.route == "A":
                if sw_cpf_rename:
                    log_container.info("🔄 [阶段 2] 跨域连接 Telegram CPF 查名终端...")
                    def on_progress_cpf(msg):
                        log_container.info(f"[TG 实时] {msg}")
                    try:
                        asyncio.run(run_cpf_query(current_excel_path, TELEGRAM_SESSION_DIR, False, on_progress_cpf))
                        log_container.success("✅ [阶段 2] Telegram 查名与洗白任务收工！")
                    except Exception as e:
                        log_container.error(f"❌ CPF终端故障: {e}")
                        st.stop()

                if sw_mabang_update:
                    log_container.info("🔄 [阶段 3] 执行马帮 ERP 更新注入...")
                    try:
                        up_cmd = ["python3", "automators/mabang_update_bot.py"]
                        up_res = subprocess.run(up_cmd, capture_output=True, text=True)
                        if up_res.returncode == 0:
                            log_container.success("✅ [阶段 3] 马帮更新注入完成！闭环完毕。")
                        else:
                            log_container.error(f"❌ 马帮更新故障:\n{up_res.stderr}")
                            st.stop()
                    except Exception as e:
                        log_container.error(f"回填马帮执行异常: {e}")
                        st.stop()
            else:
                if sw_dsers_clean:
                    log_container.info("🔄 [阶段 2] 启动深度清洗与格式倒模...")
                    try:
                        map_cmd = ["python3", "automators/dsers_clean_and_map.py"]
                        map_res = subprocess.run(map_cmd, capture_output=True, text=True)
                        if map_res.returncode == 0:
                            log_container.success("✅ [阶段 2] 无菌清洗与倒模映射完毕！")
                        else:
                            log_container.error(f"❌ 模板映射故障:\n{map_res.stderr}")
                            st.stop()
                    except Exception as e:
                        log_container.error(f"模板映射执行异常: {e}")
                        st.stop()
                        
                if sw_dsers_cpf_check:
                    log_container.info("🔄 [阶段 2.5] 拦截检查 1/3: 提取 DSers 订单桥接至 CPF 模板...")
                    try:
                        bridge_res = subprocess.run(["python3", "automators/dsers_cpf_bridge.py", "--mode", "export"], capture_output=True, text=True)
                        if bridge_res.returncode != 0:
                            log_container.error(f"❌ 桥接提取失败:\n{bridge_res.stderr}")
                            st.stop()
                            
                        log_container.info("🔄 [阶段 2.5] 拦截检查 2/3: 跨域连接 Telegram 逐个纠正姓名...")
                        def on_progress_cpf(msg):
                            log_container.info(f"[TG 实时] {msg}")
                        asyncio.run(run_cpf_query(SCRIPT_TEMPLATE, TELEGRAM_SESSION_DIR, False, on_progress_cpf))
                        
                        log_container.info("🔄 [阶段 2.5] 拦截检查 3/3: 将正确姓名完美熔炼回填至 DSers 导入模板...")
                        bridge_merge_res = subprocess.run(["python3", "automators/dsers_cpf_bridge.py", "--mode", "merge"], capture_output=True, text=True)
                        if bridge_merge_res.returncode != 0:
                            log_container.error(f"❌ 姓名回填失败:\n{bridge_merge_res.stderr}")
                            st.stop()
                        log_container.success("✅ [阶段 2.5] 极限界哨完毕，所有订单姓名已通过官方系统修正为真名！")
                    except Exception as e:
                        log_container.error(f"拦截检查执行异常: {e}")
                        st.stop()
                        
                if sw_dsers_mabang:
                    log_container.info("🔄 [阶段 2.8] 将查明的新名字同步回填至马帮 ERP...")
                    try:
                        up_cmd = ["python3", "automators/mabang_update_bot.py"]
                        up_res = subprocess.run(up_cmd, capture_output=True, text=True)
                        if up_res.returncode == 0:
                            log_container.success("✅ [阶段 2.8] 马帮 ERP 更新同步完毕！")
                        else:
                            log_container.error(f"❌ 马帮更新故障:\n{up_res.stderr}")
                            st.stop()
                    except Exception as e:
                        log_container.error(f"回填马帮执行异常: {e}")
                        st.stop()
                        
                if sw_dsers_import:
                    log_container.info("🔄 [阶段 3] 唤醒 DSers 自动化跨域上传引擎...")
                    try:
                        import_cmd = ["python3", "automators/dsers_import_bot.py", "--csv", DSERS_IMPORT_CSV]
                        import_res = subprocess.run(import_cmd, capture_output=True, text=True)
                        if import_res.returncode == 0:
                            log_container.success("✅ [阶段 3] 纯净订单批量倾倒至 DSers 控制台成功！")
                        else:
                            log_container.error(f"❌ 导入 DSers 失败:\n{import_res.stderr}\n\nStdout:\n{import_res.stdout}")
                            st.stop()
                    except Exception as e:
                        log_container.error(f"DSers 导入执行异常: {e}")
                        st.stop()

                if sw_dsers_rename:
                    log_container.info("🔄 [阶段 独立] 接管 DSers 自动改名狙击系统...")
                    def on_progress_dsers(msg):
                        log_container.info(f"[DSers 实时] {msg}")
                    try:
                        asyncio.run(run_dsers_rename(current_excel_path, DSERS_SESSION_DIR, False, on_progress_dsers))
                        log_container.success("✅ [阶段 独立] DSers 目标改名修正任务完成！")
                    except Exception as e:
                        log_container.error(f"❌ DSers机器故障: {e}")
                        st.stop()
                        
            st.balloons()
            log_container.success("🎉 报告 Commander，您下达的全链条战术指令已全栈执行完毕！")
    st.markdown('</div>', unsafe_allow_html=True)
