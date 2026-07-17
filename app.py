import streamlit as st
import pandas as pd
import asyncio
import os
import subprocess
import glob

from config import MODE1_EXCEL, MODE2_EXCEL, MODE3_EXCEL, MODE4_EXCEL, TELEGRAM_SESSION_DIR, DATA_DIR, DSERS_SESSION_DIR, DSERS_TEMPLATE, DSERS_IMPORT_XLSX, DSERS_IMPORT_CSV, SCRIPT_TEMPLATE, ORDER_TEMPLATE, SESSIONS_DIR
from automators.telegram_cpf_bot import run_cpf_query
from automators.dsers_update_bot import run_dsers_rename
from automators.order_template_utils import clean_order_template_to_script, sync_cpf_results_to_order_template

st.set_page_config(page_title="Global Pipeline Studio", layout="wide", initial_sidebar_state="collapsed")

if 'route' not in st.session_state:
    st.session_state.route = None

@st.dialog("选择表格类型")
def select_uploaded_template_dialog(file_buffer, file_id):
    st.markdown("请指定您刚上传的表格属于以下哪种类型：")
    template_choice = st.radio(
        "请选择对应模板：",
        ["dsers模板.xlsx", "import_orders.xlsx", "脚本模板.xlsx", "下单模板.xlsx"],
        index=0,
        label_visibility="collapsed"
    )
    if st.button("确认并载入", type="primary", use_container_width=True):
        st.session_state["handled_file_id"] = file_id
        st.session_state["active_template_type"] = template_choice
        
        if template_choice == "dsers模板.xlsx":
            dest_path = DSERS_TEMPLATE
        elif template_choice == "import_orders.xlsx":
            dest_path = DSERS_IMPORT_XLSX
        elif template_choice == "脚本模板.xlsx":
            dest_path = SCRIPT_TEMPLATE
        else:
            dest_path = ORDER_TEMPLATE
            
        with open(dest_path, "wb") as f:
            f.write(file_buffer)
            
        if template_choice == "下单模板.xlsx":
            clean_order_template_to_script(dest_path, SCRIPT_TEMPLATE, st.session_state.route, sw_dsers_rename=False)
            
        st.rerun()

def on_dsers_rename_change():
    if st.session_state.get("sw_dsers_rename_key", False):
        st.session_state["sw_dsers_clean_key"] = False
        st.session_state["sw_dsers_cpf_check_key"] = False
        st.session_state["sw_dsers_cpf_merge_key"] = False
        st.session_state["sw_dsers_mabang_key"] = False
        st.session_state["sw_dsers_import_key"] = False

def on_dsers_normal_change():
    if any([
        st.session_state.get("sw_dsers_clean_key", False),
        st.session_state.get("sw_dsers_cpf_check_key", False),
        st.session_state.get("sw_dsers_cpf_merge_key", False),
        st.session_state.get("sw_dsers_mabang_key", False),
        st.session_state.get("sw_dsers_import_key", False)
    ]):
        st.session_state["sw_dsers_rename_key"] = False

# COMMON CSS (High-end Minimalist, High Transparency Glassmorphism)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol" !important;
    }

    /* 绝对隐藏侧边栏和顶栏 */
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    header { visibility: hidden !important; }

    /* =========================================
       VISION PRO 级：空间计算 3D 极致动态引擎 (Spatial Computing Engine)
       ========================================= */

    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    /* 沸腾的极光能量场背景 */
    .stApp::before {
        content: "";
        position: fixed;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: 
            radial-gradient(circle at 20% 30%, rgba(255, 107, 107, 0.4), transparent 60%),
            radial-gradient(circle at 80% 80%, rgba(72, 219, 251, 0.4), transparent 60%),
            radial-gradient(circle at 20% 80%, rgba(255, 159, 67, 0.4), transparent 60%),
            radial-gradient(circle at 80% 20%, rgba(84, 160, 255, 0.4), transparent 60%);
        animation: energyField 12s cubic-bezier(0.4, 0, 0.2, 1) infinite alternate;
        z-index: -2;
        filter: blur(80px);
    }
    
    .stApp::after {
        content: "";
        position: fixed;
        inset: 0;
        background: #f4f5f7;
        z-index: -3;
    }

    @keyframes energyField {
        0% { transform: scale(1) rotate(0deg); }
        100% { transform: scale(1.3) rotate(45deg); }
    }

    /* 恢复 liquidReveal 给按钮使用 */
    @keyframes liquidReveal {
        0% { opacity: 0; transform: translateY(40px) scale(0.98); filter: blur(12px); }
        100% { opacity: 1; transform: translateY(0) scale(1); filter: blur(0); }
    }

    /* 夸张的 3D 弹簧入场 (Hyper-Spring Reveal) */
    @keyframes hyperSpringReveal {
        0% { 
            opacity: 0; 
            transform: perspective(2000px) translateY(150px) translateZ(-300px) rotateX(20deg) scale(0.8); 
            filter: blur(30px); 
        }
        100% { 
            opacity: 1; 
            transform: perspective(2000px) translateY(0) translateZ(0) rotateX(0deg) scale(1); 
            filter: blur(0); 
        }
    }

    /* 极致高透毛玻璃容器 - 3D 悬浮态 */
    [data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stVerticalBlock"] > div[style*="border"],
    div[class*="st-emotion-cache"][style*="border"] {
        background: rgba(255, 255, 255, 0.2) !important;
        backdrop-filter: blur(60px) saturate(250%) !important;
        -webkit-backdrop-filter: blur(60px) saturate(250%) !important;
        border: 1px solid rgba(255, 255, 255, 0.7) !important;
        border-radius: 2.5rem !important; 
        box-shadow: 
            0 10px 30px rgba(0,0,0,0.05),
            inset 0 2px 0 0 rgba(255,255,255,0.8),
            inset 0 0 20px rgba(255,255,255,0.5) !important;
        padding: 3.5rem !important;
        
        /* 核心 3D 交互配置 */
        transform-style: preserve-3d;
        transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1), 
                    box-shadow 0.6s cubic-bezier(0.34, 1.56, 0.64, 1),
                    background 0.4s !important;
        
        /* 夸张弹簧入场 */
        animation: hyperSpringReveal 1.2s cubic-bezier(0.2, 0.8, 0.2, 1.2) forwards;
        position: relative;
        overflow: hidden;
    }
    
    /* 容器上的无限反射光效 (Infinite Shimmer Sweep) */
    [data-testid="stVerticalBlockBorderWrapper"]::after,
    div[data-testid="stVerticalBlock"] > div[style*="border"]::after {
        content: "";
        position: absolute;
        top: 0; left: -150%;
        width: 50%; height: 100%;
        background: linear-gradient(to right, rgba(255,255,255,0) 0%, rgba(255,255,255,0.6) 50%, rgba(255,255,255,0) 100%);
        transform: skewX(-25deg);
        animation: glassSweep 4s ease-in-out infinite;
        pointer-events: none;
    }

    @keyframes glassSweep {
        0% { left: -150%; }
        50% { left: 200%; }
        100% { left: 200%; }
    }
    
    /* 暴力 3D 翻转破雪交互 (Violent 3D Hover) */
    [data-testid="stVerticalBlockBorderWrapper"]:hover,
    div[data-testid="stVerticalBlock"] > div[style*="border"]:hover {
        background: rgba(255, 255, 255, 0.4) !important;
        /* 直接让卡片飞出来并发生 3D 偏转 */
        transform: perspective(2000px) translateZ(80px) translateY(-10px) rotateX(4deg) rotateY(-2deg) scale(1.02);
        box-shadow: 
            -20px 40px 80px -10px rgba(0,0,0,0.15), 
            inset 0 2px 0 0 rgba(255,255,255,1), 
            inset 0 0 60px rgba(255,255,255,0.8) !important;
        border: 1px solid rgba(255, 255, 255, 1) !important;
    }

    h1, h2, h3, h4, h5 {
        color: #1d1d1f !important; /* Apple typography color */
        font-weight: 600 !important;
        letter-spacing: -0.02em !important;
    }
    
    p, span, div {
        color: #424245 !important;
    }

    /* 调整顶部空白 */
    .block-container {
        padding-top: 4rem !important;
        max-width: 1200px !important;
    }
</style>
""", unsafe_allow_html=True)


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
                iframe.style.zIndex = "-1";
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



if st.session_state.route is None:
    # ==========================
    # 首页大屏视觉效果 (Home Screen) - Agency Tier
    # ==========================
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
        
        /* 强制全屏容器使用特定字体，并去除强制深黑背景 */
        [data-testid="stAppViewContainer"], .block-container {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }
        
        .block-container {
            padding-top: 8rem !important;
            max-width: 1400px !important;
        }

        /* 完美隐藏原生按钮，不影响 DOM 布局 */
        [data-testid="stButton"] {
            position: absolute !important;
            opacity: 0 !important;
            height: 0 !important;
            width: 0 !important;
            overflow: hidden !important;
            pointer-events: none !important;
        }
        
        /* ====================
           ULTRA-CLEAR ETHEREAL GLASS CARDS (近乎全透玻璃材质)
           ==================== */
        .premium-card-outer {
            padding: 0.5rem;
            border-radius: 2.5rem;
            background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.02) 100%);
            border: 1px solid rgba(255, 255, 255, 0.4);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 30px 60px rgba(0,0,0,0.05);
            transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
            overflow: hidden;
            height: 460px;
            will-change: transform;
        }
        
        .premium-card-inner {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 2.125rem;
            height: 100%;
            padding: 2.6rem 2.8rem 2.4rem 2.8rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(50px) saturate(120%);
            -webkit-backdrop-filter: blur(50px) saturate(120%);
            transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
            z-index: 10;
        }
        
        /* 径向网格渐变背景 */
        .premium-card-outer::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle at 50% 0%, rgba(255,255,255,0.8), transparent 60%);
            opacity: 0.2;
            transition: opacity 0.8s ease;
            z-index: 1;
            pointer-events: none;
        }
        
        /* Kinetic Hover Physics */
        .premium-card-outer:hover {
            transform: translateY(-12px) scale(1.02);
            border: 1px solid rgba(255, 255, 255, 1);
            background: linear-gradient(135deg, rgba(255,255,255,0.6) 0%, rgba(255,255,255,0.1) 100%);
            box-shadow: 0 40px 80px rgba(0,0,0,0.1), 0 0 0 1px rgba(255,255,255,0.5);
            cursor: pointer;
        }
        
        .premium-card-outer:hover .premium-card-inner {
            background: rgba(255, 255, 255, 0.4);
            box-shadow: inset 0 1px 1px rgba(255, 255, 255, 1);
        }
        
        .premium-card-outer:hover::before {
            opacity: 1;
        }
        
        /* Active Scale Simulation */
        .premium-card-outer:active {
            transform: scale(0.97);
            transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        /* Typography inside cards */
        .card-icon-wrapper {
            width: 72px;
            height: 72px;
            border-radius: 1.4rem;
            background: linear-gradient(135deg, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0.1) 100%);
            border: 1px solid rgba(255, 255, 255, 1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.3rem;
            margin-bottom: 1.2rem;
            box-shadow: inset 0 2px 4px rgba(255,255,255,0.5), 0 10px 20px rgba(0,0,0,0.1);
            transition: all 0.8s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        .card-title {
            font-size: 3.4rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 0.8rem;
            color: #1d1d1f !important;
            background: linear-gradient(135deg, #000000 0%, #434345 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.1;
        }
        
        .card-desc {
            font-size: 1.3rem;
            color: #333333 !important;
            line-height: 1.65;
            font-weight: 600;
            letter-spacing: 0.01em;
        }
        
        /* Button-in-Button Architecture (Island CTA) */
        .island-btn {
            display: inline-flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.8);
            border-radius: 9999px;
            padding: 0.6rem 0.6rem 0.6rem 1.6rem;
            margin-top: 1.4rem;
            width: fit-content;
            transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        }
        
        .island-btn-text {
            font-size: 1.05rem;
            font-weight: 700;
            color: #222222 !important;
            margin-right: 1.8rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            transition: color 0.5s ease;
        }
        
        .island-btn-icon {
            width: 44px;
            height: 44px;
            border-radius: 50%;
            background: #1d1d1f;
            color: #ffffff !important;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            font-weight: 600;
            transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        /* 联动 Hover Physics */
        .premium-card-outer:hover .card-icon-wrapper {
            transform: scale(1.05) translateY(-4px);
            background: linear-gradient(135deg, rgba(255,255,255,1) 0%, rgba(255,255,255,0.4) 100%);
        }
        .premium-card-outer:hover .island-btn {
            background: rgba(255, 255, 255, 0.8);
            border-color: rgba(255, 255, 255, 1);
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.06);
        }
        .premium-card-outer:hover .island-btn-text {
            color: #000000 !important;
        }
        .premium-card-outer:hover .island-btn-icon {
            transform: translateX(4px) scale(1.05);
            background: #000000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
    </style>
    
    <div style="text-align: center; margin-bottom: 3.5rem; animation: liquidReveal 1s cubic-bezier(0.16, 1, 0.3, 1) forwards; opacity: 0; transform: translateY(20px);">
        <div style="display:inline-block; padding: 0.6rem 1.4rem; border-radius: 9999px; border: 1px solid rgba(0,0,0,0.1); background: rgba(255,255,255,0.4); font-size: 0.9rem; text-transform: uppercase; letter-spacing: 0.2em; margin-bottom: 1.8rem; color: #444444; backdrop-filter: blur(10px); font-weight: 600;">
            Vanguard Systems
        </div>
        <h1 style="font-size: 5.2rem; font-weight: 800; letter-spacing: -0.04em; background: linear-gradient(180deg, #1d1d1f 0%, #555555 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1.2rem; line-height: 1;">Pipeline Studio</h1>
        <p style="font-size: 1.6rem; font-weight: 500; color: #555555; letter-spacing: 0.02em;">Select your intelligence distribution route.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("""
        <div class="premium-card-outer" style="animation: liquidReveal 1s cubic-bezier(0.16, 1, 0.3, 1) 0.1s forwards; opacity: 0;">
            <div class="premium-card-inner">
                <div>
                    <div class="card-icon-wrapper">A</div>
                    <div class="card-title">CPF</div>
                    <div class="card-desc">
                        自动调取 Telegram CPF 接口<br>
                        核对并纠正错误的买家姓名<br>
                        同步更新至马帮和下单表格
                    </div>
                </div>
                <div class="island-btn">
                    <span class="island-btn-text">进入操作</span>
                    <span class="island-btn-icon">↗</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("CPF_ROUTE_HIDDEN_123"):
            st.session_state.route = "A"
            st.rerun()
            
    with col2:
        st.markdown("""
        <div class="premium-card-outer" style="animation: liquidReveal 1s cubic-bezier(0.16, 1, 0.3, 1) 0.2s forwards; opacity: 0;">
            <div class="premium-card-inner">
                <div>
                    <div class="card-icon-wrapper">B</div>
                    <div class="card-title">DSERS</div>
                    <div class="card-desc">
                        自动转换马帮订单为 DSERS 格式<br>
                        支持自动校验买家 CPF 并改名<br>
                        批量上传至 DSERS 后台创建订单
                    </div>
                </div>
                <div class="island-btn">
                    <span class="island-btn-text">进入操作</span>
                    <span class="island-btn-icon">↗</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("DSERS_ROUTE_HIDDEN_123"):
            st.session_state.route = "B"
            st.rerun()

    # ==========================
    # 彻底解决点击问题：JS 事件透传引擎
    # ==========================
    import streamlit.components.v1 as components
    components.html("""
    <script>
        // 监听顶级 window，跨 iframe 穿透
        const parentDoc = window.parent.document;
        
        // 由于 Streamlit 组件加载存在微小延迟，使用轮询确保绑定成功
        let attempts = 0;
        const bindClicks = setInterval(() => {
            attempts++;
            const cards = parentDoc.querySelectorAll('.premium-card-outer');
            const buttons = parentDoc.querySelectorAll('button[kind="secondary"]');
            
            // 确保找到了两个卡片和足够的按钮
            if (cards.length >= 2 && buttons.length >= 2) {
                clearInterval(bindClicks);
                
                cards.forEach((card, index) => {
                    // 只绑定前两个主页卡片
                    if (index > 1) return; 
                    
                    // 确保光标为手型
                    card.style.cursor = 'pointer';
                    
                    // 移除旧监听器避免重复绑定
                    card.onclick = null; 
                    
                    card.onclick = function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        // 触发对应按钮的点击
                        // Streamlit 的最新按钮可能在深层，直接对其原生节点 dispatchEvent
                        const btn = buttons[index];
                        btn.click();
                    };
                });
            }
            
            // 超时保护
            if (attempts > 20) {
                clearInterval(bindClicks);
                console.error("Vanguard Pipeline: JS Click Binding Failed");
            }
        }, 100);
    </script>
    """, height=0, width=0)

else:
    # ==========================
    # 内部操作流视图 (Inner Route View)
    # ==========================
    st.markdown("""
    <style>
        /* 返回主界面特定按钮伪装 */
        .back-btn-container [data-testid="stButton"] button,
        div.element-container:has(.back-btn-container) + div.element-container button,
        div.element-container:has(.back-btn-container) ~ div.element-container button {
            background: rgba(255, 255, 255, 0.45) !important;
            border: 1px solid rgba(255, 255, 255, 0.8) !important;
            color: #1d1d1f !important;
            border-radius: 9999px !important;
            padding: 0.5rem 1.4rem !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.03), inset 0 1px 1px rgba(255,255,255,0.8) !important;
            backdrop-filter: blur(40px) saturate(140%) !important;
            -webkit-backdrop-filter: blur(40px) saturate(140%) !important;
            transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1) !important;
            font-weight: 600 !important;
            animation: liquidReveal 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        div.element-container:has(.back-btn-container) + div.element-container button:hover {
            background: rgba(255, 255, 255, 0.85) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 10px 24px rgba(0,0,0,0.08), inset 0 1px 2px rgba(255,255,255,1) !important;
        }
        div.element-container:has(.back-btn-container) + div.element-container button:active {
            transform: scale(0.96) !important;
        }
        
        /* ====================
           底部控制按钮 Ethereal Glassmorphism (主页同款高级水晶半透玻璃质感)
           解决 Streamlit DOM 自动闭合，采用容器兄弟节点及全局属性直接命中
           ==================== */
        .launch-btn-container button,
        div.element-container:has(.launch-btn-container) + div.element-container button,
        div.element-container:has(.launch-btn-container) ~ div.element-container button,
        div[data-testid="stColumns"] button[data-testid="baseButton-primary"],
        div[data-testid="stColumns"] button[data-testid="baseButton-secondary"] {
            border-radius: 9999px !important;
            padding: 1.15rem 2.4rem !important;
            font-size: 1.18rem !important;
            font-weight: 700 !important;
            letter-spacing: 0.04em !important;
            width: 100% !important;
            transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1) !important;
            animation: liquidReveal 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
            animation-delay: 0.2s !important;
            backdrop-filter: blur(50px) saturate(140%) !important;
            -webkit-backdrop-filter: blur(50px) saturate(140%) !important;
            cursor: pointer !important;
        }

        /* 启动处理按钮 (Primary Crystal Glass - 主页卡片同款高亮高通透磨砂水晶) */
        div.element-container:has(.launch-btn-container) + div.element-container div[data-testid="stColumn"]:first-child button,
        div[data-testid="stColumns"] button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.55) 0%, rgba(255, 255, 255, 0.20) 100%) !important;
            border: 1px solid rgba(255, 255, 255, 0.9) !important;
            color: #1d1d1f !important;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.08), inset 0 1px 2px rgba(255, 255, 255, 0.9) !important;
        }

        /* 强制停止按钮 (Secondary Frosted Glass - 协调通透灰底水晶磨砂) */
        div.element-container:has(.launch-btn-container) + div.element-container div[data-testid="stColumn"]:last-child button,
        div[data-testid="stColumns"] button[data-testid="baseButton-secondary"] {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.35) 0%, rgba(255, 255, 255, 0.10) 100%) !important;
            border: 1px solid rgba(255, 255, 255, 0.6) !important;
            color: #333333 !important;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05), inset 0 1px 1px rgba(255, 255, 255, 0.6) !important;
        }

        /* 统一悬浮物理光感 (Kinetic Hover Physics) */
        div.element-container:has(.launch-btn-container) + div.element-container button:hover,
        div[data-testid="stColumns"] button[data-testid="baseButton-primary"]:hover,
        div[data-testid="stColumns"] button[data-testid="baseButton-secondary"]:hover {
            transform: translateY(-4px) scale(1.01) !important;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.85) 0%, rgba(255, 255, 255, 0.45) 100%) !important;
            border-color: rgba(255, 255, 255, 1) !important;
            color: #000000 !important;
            box-shadow: 0 24px 48px rgba(0, 0, 0, 0.12), inset 0 1px 2px rgba(255, 255, 255, 1) !important;
        }

        div.element-container:has(.launch-btn-container) + div.element-container button:active,
        div[data-testid="stColumns"] button[data-testid="baseButton-primary"]:active,
        div[data-testid="stColumns"] button[data-testid="baseButton-secondary"]:active {
            transform: translateY(0px) scale(0.98) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    route_name = "CPF" if st.session_state.route == "A" else "DSERS"
    
    col1, col2 = st.columns([8, 2])
    with col1:
        st.markdown(f'<h1 style="margin-top:0;">{route_name}</h1>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="back-btn-container">', unsafe_allow_html=True)
        if st.button("返回主页"):
            st.session_state.route = None
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    current_excel_path = SCRIPT_TEMPLATE if st.session_state.route == "A" else DSERS_TEMPLATE

    with st.container(border=True):
        st.markdown("### 第一步：获取要处理的订单数据")
        data_source = st.radio("选择获取方式", ["从马帮 ERP 提取", "上传本地表格", "使用已产生的表格"], horizontal=True, label_visibility="collapsed")
        sw_auto_export = (data_source == "从马帮 ERP 提取")
        use_vault = (data_source == "使用已产生的表格")

        if sw_auto_export:
            st.session_state["active_template_type"] = "脚本模板.xlsx"
            st.markdown("<br><b>马帮提取参数：</b>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                col_d, col_h = st.columns(2)
                with col_d:
                    days = st.number_input("提取最近几天", min_value=0, max_value=30, value=1)
                with col_h:
                    hours = st.number_input("精确到小时", min_value=0, max_value=23, value=0)
            with c2:
                if st.session_state.route == "A":
                    search_val = st.text_input("要提取的买家客户 ID", value="1000000257")
                else:
                    search_val = st.text_input("要过滤排除的 SKU", value="code")
        elif data_source == "上传本地表格":
            st.markdown("<br>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("请选择或拖入 .xlsx 表格文件", type=["xlsx", "xls"])
            if uploaded_file:
                file_id = f"{uploaded_file.name}_{uploaded_file.size}"
                if st.session_state.get("handled_file_id") != file_id:
                    select_uploaded_template_dialog(uploaded_file.getbuffer(), file_id)
                else:
                    t_type = st.session_state.get("active_template_type", "脚本模板.xlsx")
                    if t_type == "dsers模板.xlsx":
                        current_excel_path = DSERS_TEMPLATE
                    elif t_type == "import_orders.xlsx":
                        current_excel_path = DSERS_IMPORT_XLSX
                    elif t_type == "下单模板.xlsx":
                        current_excel_path = ORDER_TEMPLATE
                    else:
                        current_excel_path = SCRIPT_TEMPLATE
                    st.success(f"已选定表格（识别类型：{t_type}）")
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            vault_file_choice = st.selectbox("请选择要继续操作的表格文件", ["dsers模板.xlsx", "import_orders.xlsx", "脚本模板.xlsx", "下单模板.xlsx"])
            st.session_state["active_template_type"] = vault_file_choice
            if vault_file_choice == "dsers模板.xlsx":
                current_excel_path = DSERS_TEMPLATE
            elif vault_file_choice == "import_orders.xlsx":
                current_excel_path = DSERS_IMPORT_XLSX
            elif vault_file_choice == "下单模板.xlsx":
                current_excel_path = ORDER_TEMPLATE
            else:
                current_excel_path = SCRIPT_TEMPLATE
            
            if os.path.exists(current_excel_path):
                st.success(f"已选择 {vault_file_choice}，可以继续执行后续处理。")
            else:
                st.warning(f"系统还未生成 {vault_file_choice}，请先在第一步生成或上传该表格。")

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    if st.session_state.route == "A":
        with st.container(border=True):
            st.markdown("### 第二步：选择要执行的步骤")
            sw_cpf_rename = st.toggle("自动连接 Telegram 执行 CPF 查询与核对", value=True)
            sw_cpf_merge = st.toggle("将 CPF 查询结果回填至 DSERS 导入表格中", value=False)
            sw_mabang_update = st.toggle("将 CPF 查询核准后的姓名同步更新回马帮 ERP", value=True)
    else:
        with st.container(border=True):
            st.markdown("### 第二步：选择要执行的步骤")
            if "sw_dsers_clean_key" not in st.session_state: st.session_state["sw_dsers_clean_key"] = True
            if "sw_dsers_cpf_check_key" not in st.session_state: st.session_state["sw_dsers_cpf_check_key"] = True
            if "sw_dsers_cpf_merge_key" not in st.session_state: st.session_state["sw_dsers_cpf_merge_key"] = True
            if "sw_dsers_mabang_key" not in st.session_state: st.session_state["sw_dsers_mabang_key"] = True
            if "sw_dsers_import_key" not in st.session_state: st.session_state["sw_dsers_import_key"] = True
            if "sw_dsers_rename_key" not in st.session_state: st.session_state["sw_dsers_rename_key"] = False

            sw_dsers_clean = st.toggle("把马帮表格清理并转换成 DSERS 要求的数据格式", key="sw_dsers_clean_key", on_change=on_dsers_normal_change)
            sw_dsers_cpf_check = st.toggle("自动连接 Telegram 查询并核对买家 CPF 真实姓名", key="sw_dsers_cpf_check_key", on_change=on_dsers_normal_change)
            sw_dsers_cpf_merge = st.toggle("把 CPF 查询核准后的正确姓名填入 DSERS 表格中", key="sw_dsers_cpf_merge_key", on_change=on_dsers_normal_change)
            sw_dsers_mabang = st.toggle("把 CPF 查询核准完成的姓名同步更新回马帮 ERP", key="sw_dsers_mabang_key", on_change=on_dsers_normal_change)
            sw_dsers_import = st.toggle("一键把整理好的表格上传到 DSERS 后台并批量建单", key="sw_dsers_import_key", on_change=on_dsers_normal_change)
            st.markdown("---")
            sw_dsers_rename = st.toggle("直接打开 DSERS 网页端，针对后台已有订单自动修改买家姓名", key="sw_dsers_rename_key", on_change=on_dsers_rename_change)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # ==========================
    # 数据保险库 Data Vault (实时预览)
    # ==========================
    with st.expander("查看与检查数据表格 (点击展开或修改)", expanded=False):
        st.markdown("在这里可以直接查看、修改和保存系统中流转的数据表格，不用去文件夹里反复翻找。")
        vault_tabs = st.tabs(["dsers模板.xlsx", "import_orders.xlsx", "脚本模板.xlsx", "下单模板.xlsx"])
        
        with vault_tabs[0]:
            if os.path.exists(DSERS_TEMPLATE):
                try:
                    df1 = pd.read_excel(DSERS_TEMPLATE, dtype=str)
                    st.caption(f"当前规格：**{df1.shape[0]}** 行 × **{df1.shape[1]}** 列")
                    edited_df1 = st.data_editor(df1, num_rows="dynamic", use_container_width=True, key="edit_dsers")
                    
                    colA, colB = st.columns(2)
                    with colA:
                        if st.button("保存修改", key="save_dsers"):
                            if not df1.equals(edited_df1):
                                edited_df1.to_excel(DSERS_TEMPLATE, index=False)
                                st.success("修改已保存至 dsers模板.xlsx")
                            else:
                                st.info("内容无变化，无需保存。")
                    with colB:
                        with open(DSERS_TEMPLATE, "rb") as f:
                            st.download_button("下载 dsers模板", f, "dsers模板.xlsx", key="dl_dsers")
                except Exception as e:
                    st.warning(f"无法读取: {e}")
            else:
                st.info("暂无文件数据。")
                
        with vault_tabs[1]:
            if os.path.exists(DSERS_IMPORT_XLSX):
                try:
                    df2 = pd.read_excel(DSERS_IMPORT_XLSX, dtype=str)
                    st.caption(f"当前规格：**{df2.shape[0]}** 行 × **{df2.shape[1]}** 列")
                    edited_df2 = st.data_editor(df2, num_rows="dynamic", use_container_width=True, key="edit_import")
                    
                    colA, colB = st.columns(2)
                    with colA:
                        if st.button("保存修改", key="save_import"):
                            if not df2.equals(edited_df2):
                                edited_df2.to_excel(DSERS_IMPORT_XLSX, index=False)
                                st.success("修改已保存至 import_orders.xlsx")
                            else:
                                st.info("内容无变化，无需保存。")
                    with colB:
                        with open(DSERS_IMPORT_XLSX, "rb") as f:
                            st.download_button("下载 import_orders", f, "import_orders.xlsx", key="dl_import")
                except Exception as e:
                    st.warning(f"无法读取: {e}")
            else:
                st.info("暂无文件数据。")
                
        with vault_tabs[2]:
            if os.path.exists(SCRIPT_TEMPLATE):
                try:
                    df3 = pd.read_excel(SCRIPT_TEMPLATE, dtype=str)
                    st.caption(f"当前规格：**{df3.shape[0]}** 行 × **{df3.shape[1]}** 列")
                    edited_df3 = st.data_editor(df3, num_rows="dynamic", use_container_width=True, key="edit_script")
                    
                    colA, colB = st.columns(2)
                    with colA:
                        if st.button("保存修改", key="save_script"):
                            if not df3.equals(edited_df3):
                                edited_df3.to_excel(SCRIPT_TEMPLATE, index=False)
                                st.success("修改已保存至 脚本模板.xlsx")
                            else:
                                st.info("内容无变化，无需保存。")
                    with colB:
                        with open(SCRIPT_TEMPLATE, "rb") as f:
                            st.download_button("下载 脚本模板", f, "脚本模板.xlsx", key="dl_script")
                except Exception as e:
                    st.warning(f"无法读取: {e}")
            else:
                st.info("暂无文件数据。")
                
        with vault_tabs[3]:
            if os.path.exists(ORDER_TEMPLATE):
                try:
                    df4 = pd.read_excel(ORDER_TEMPLATE, dtype=str)
                    st.caption(f"当前规格：**{df4.shape[0]}** 行 × **{df4.shape[1]}** 列")
                    edited_df4 = st.data_editor(df4, num_rows="dynamic", use_container_width=True, key="edit_order")
                    
                    colA, colB = st.columns(2)
                    with colA:
                        if st.button("保存修改", key="save_order"):
                            if not df4.equals(edited_df4):
                                edited_df4.to_excel(ORDER_TEMPLATE, index=False)
                                st.success("修改已保存至 下单模板.xlsx")
                            else:
                                st.info("内容无变化，无需保存。")
                    with colB:
                        with open(ORDER_TEMPLATE, "rb") as f:
                            st.download_button("下载 下单模板", f, "下单模板.xlsx", key="dl_order")
                except Exception as e:
                    st.warning(f"无法读取: {e}")
            else:
                st.info("暂无文件数据。")

    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)

    st.markdown('<div class="launch-btn-container">', unsafe_allow_html=True)
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        btn_launch = st.button("立即开始处理", type="primary", use_container_width=True)
    with c_btn2:
        btn_kill = st.button("强制停止并清理卡死进程", type="secondary", use_container_width=True)
        
    if btn_kill:
        st.warning("正在停止所有后台程序并清理缓存锁...")
        os.system("pkill -i -f playwright")
        os.system("pkill -i -f 'remote-debugging-pipe'")
        os.system("pkill -i -f 'user-data-dir.*sessions'")
        for lock_file in glob.glob(os.path.join(SESSIONS_DIR, "*", "Singleton*")):
            try: os.remove(lock_file)
            except: pass
        st.success("后台程序已被完全停止清理，您可以重新开始执行了。")
        st.stop()

    if btn_launch:
        if not sw_auto_export and not os.path.exists(current_excel_path):
            if use_vault:
                st.error(f"无法开始：'{vault_file_choice}' 还不存在，请先执行第一步把它生成出来。")
            else:
                st.error("无法开始：请先在第一步中准备好表格数据。")
        else:
            log_container = st.empty()
            # --- 启动前自动清洗残余的浏览器单例锁文件，防止 "正在现有的浏览器会话中打开" 报错 ---
            for lock_file in glob.glob(os.path.join(SESSIONS_DIR, "*", "Singleton*")):
                try: os.remove(lock_file)
                except: pass
            
            # --- 新增：下单模板的运行前置清洗与映射 ---
            if st.session_state.get("active_template_type") == "下单模板.xlsx":
                is_rename_active = (st.session_state.route == "B" and st.session_state.get("sw_dsers_rename_key", False))
                clean_order_template_to_script(ORDER_TEMPLATE, SCRIPT_TEMPLATE, st.session_state.route, sw_dsers_rename=is_rename_active)
                current_excel_path = SCRIPT_TEMPLATE
            
            # --- 阶段 1 ---
            if sw_auto_export:
                log_container.info("[阶段 1] 正在调取马帮 ERP 订单数据...")
                try:
                    export_script = "automators/mabang_export_bot.py" if st.session_state.route == "A" else "automators/mabang_dsers_export.py"
                    flag = "--customer_id" if st.session_state.route == "A" else "--sku"
                    cmd = ["python3", export_script, "--days", str(days), "--hours", str(hours), flag, search_val]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0:
                        log_container.success("[阶段 1] 马帮订单数据提取完成。")
                        current_excel_path = SCRIPT_TEMPLATE
                    else:
                        log_container.error(f"马帮接口调用报错:\n[STDOUT]:\n{result.stdout}\n[STDERR]:\n{result.stderr}")
                        st.stop()
                except Exception as e:
                    log_container.error(f"执行异常: {e}")
                    st.stop()
                    
            # --- 阶段 2: 依据管线执行 ---
            if st.session_state.route == "A":
                if sw_cpf_rename:
                    log_container.info("[阶段 2] 正在进行 Telegram CPF 姓名查询...")
                    def on_progress_cpf(msg):
                        log_container.info(f"[TG 实时] {msg}")
                    try:
                        asyncio.run(run_cpf_query(current_excel_path, TELEGRAM_SESSION_DIR, False, on_progress_cpf))
                        log_container.success("[阶段 2] Telegram 查名与校验完成。")
                        
                        if st.session_state.get("active_template_type") == "下单模板.xlsx":
                            log_container.info("[同步] 正在同步最新姓名至下单模板 E 列...")
                            sync_cpf_results_to_order_template(SCRIPT_TEMPLATE, ORDER_TEMPLATE)
                            log_container.success("[同步] 下单模板 E 列已更新完成。")
                    except Exception as e:
                        log_container.error(f"CPF 查询过程异常: {e}")
                        st.stop()
                        
                if sw_cpf_merge:
                    log_container.info("[阶段 2.5] 独立同步：回填最新姓名至 DSers 导入模板...")
                    try:
                        bridge_merge_res = subprocess.run(["python3", "automators/dsers_cpf_bridge.py", "--mode", "merge"], capture_output=True, text=True)
                        if bridge_merge_res.returncode != 0:
                            log_container.error(f"姓名同步回填失败:\nSTDOUT:\n{bridge_merge_res.stdout}\nSTDERR:\n{bridge_merge_res.stderr}")
                            st.stop()
                        log_container.success("[阶段 2.5] 独立同步完成，DSers 订单姓名已更新。")
                    except Exception as e:
                        log_container.error(f"回填执行异常: {e}")
                        st.stop()

                if sw_mabang_update:
                    log_container.info("[阶段 3] 正在同步数据至马帮 ERP...")
                    try:
                        up_cmd = ["python3", "automators/mabang_update_bot.py"]
                        up_res = subprocess.run(up_cmd, capture_output=True, text=True)
                        if up_res.returncode == 0:
                            log_container.success("[阶段 3] 马帮 ERP 数据同步完成。")
                        else:
                            log_container.error(f"马帮同步更新异常:\n{up_res.stderr}")
                            st.stop()
                    except Exception as e:
                        log_container.error(f"回填马帮执行异常: {e}")
                        st.stop()
            else:
                if sw_dsers_clean:
                    log_container.info("[阶段 2] 正在清理数据字段并映射格式...")
                    try:
                        map_cmd = ["python3", "automators/dsers_clean_and_map.py"]
                        map_res = subprocess.run(map_cmd, capture_output=True, text=True)
                        if map_res.returncode == 0:
                            log_container.success("[阶段 2] 数据清理与格式映射完成。")
                        else:
                            log_container.error(f"格式映射发生错误:\n{map_res.stderr}")
                            st.stop()
                    except Exception as e:
                        log_container.error(f"模板映射执行异常: {e}")
                        st.stop()
                        
                if sw_dsers_cpf_check:
                    log_container.info("[阶段 2.4] 姓名核对 1/2: 提取 DSers 订单至 CPF 模板...")
                    try:
                        if use_vault and vault_file_choice == "脚本模板.xlsx":
                            log_container.info("[阶段 2.4] 姓名核对 1/2: (已从脚本模板继续，跳过桥接提取)")
                        else:
                            bridge_res = subprocess.run(["python3", "automators/dsers_cpf_bridge.py", "--mode", "export"], capture_output=True, text=True)
                            if bridge_res.returncode != 0:
                                log_container.error(f"桥接提取数据失败:\nSTDOUT:\n{bridge_res.stdout}\nSTDERR:\n{bridge_res.stderr}")
                                st.stop()
                            
                        log_container.info("[阶段 2.4] 姓名核对 2/2: 正在通过 Telegram 进行姓名校对...")
                        def on_progress_cpf(msg):
                            log_container.info(f"[TG 实时] {msg}")
                        asyncio.run(run_cpf_query(SCRIPT_TEMPLATE, TELEGRAM_SESSION_DIR, False, on_progress_cpf))
                        
                        if st.session_state.get("active_template_type") == "下单模板.xlsx":
                            log_container.info("[同步] 正在同步最新姓名至下单模板 E 列...")
                            sync_cpf_results_to_order_template(SCRIPT_TEMPLATE, ORDER_TEMPLATE)
                            log_container.success("[同步] 下单模板 E 列已更新完成。")
                    except Exception as e:
                        log_container.error(f"拦截检查执行异常: {e}")
                        st.stop()
                        
                if sw_dsers_cpf_merge:
                    log_container.info("[阶段 2.5] 正在同步真实姓名至 DSers 导入模板...")
                    try:
                        bridge_merge_res = subprocess.run(["python3", "automators/dsers_cpf_bridge.py", "--mode", "merge"], capture_output=True, text=True)
                        if bridge_merge_res.returncode != 0:
                            log_container.error(f"姓名同步回填失败:\nSTDOUT:\n{bridge_merge_res.stdout}\nSTDERR:\n{bridge_merge_res.stderr}")
                            st.stop()
                        log_container.success("[阶段 2.5] 姓名同步完成，所有 DSers 订单姓名已更新。")
                    except Exception as e:
                        log_container.error(f"回填执行异常: {e}")
                        st.stop()
                        
                if sw_dsers_mabang:
                    log_container.info("[阶段 2.8] 正在同步真实姓名至马帮 ERP...")
                    try:
                        up_cmd = ["python3", "automators/mabang_update_bot.py"]
                        up_res = subprocess.run(up_cmd, capture_output=True, text=True)
                        if up_res.returncode == 0:
                            log_container.success("[阶段 2.8] 马帮 ERP 数据同步完成。")
                        else:
                            log_container.error(f"马帮同步异常:\n{up_res.stderr}")
                            st.stop()
                    except Exception as e:
                        log_container.error(f"回填马帮执行异常: {e}")
                        st.stop()
                        
                if sw_dsers_import:
                    log_container.info("[阶段 3] 正在向 DSers 批量创建与推送订单...")
                    try:
                        import_cmd = ["python3", "automators/dsers_import_bot.py", "--csv", DSERS_IMPORT_CSV]
                        import_res = subprocess.run(import_cmd, capture_output=True, text=True)
                        if import_res.returncode == 0:
                            log_container.success("[阶段 3] 批量上传并创建 DSers 订单成功。")
                        else:
                            log_container.error(f"上传 DSers 发生错误:\n{import_res.stderr}\n\nStdout:\n{import_res.stdout}")
                            st.stop()
                    except Exception as e:
                        log_container.error(f"DSers 导入执行异常: {e}")
                        st.stop()

                if sw_dsers_rename:
                    log_container.info("[阶段 独立] 正在处理 DSers 网页端订单自动改名...")
                    def on_progress_dsers(msg):
                        log_container.info(f"[DSers 实时] {msg}")
                    try:
                        asyncio.run(run_dsers_rename(current_excel_path, DSERS_SESSION_DIR, False, on_progress_dsers))
                        log_container.success("[阶段 独立] DSers 订单网页改名处理完成。")
                    except Exception as e:
                        log_container.error(f"DSers 网页操作异常: {e}")
                        st.stop()
                        
            # 清理前端 Data Vault 的缓存，强制刷新显示最新数据
            for key in ['edit_dsers', 'edit_import', 'edit_script', 'edit_order']:
                if key in st.session_state:
                    del st.session_state[key]
                    
            st.balloons()
            log_container.success("全流程处理完毕。请刷新当前页面以在上方 Data View 中查看最新生成的数据表。")
    st.markdown('</div>', unsafe_allow_html=True)

with st.expander("页面背景光效调节", expanded=False):
    thickness = st.slider("核心厚度 (Thickness)", 0.05, 0.30, 0.131, 0.001)
    blur = st.slider("上下晕染 (Blur)", 0.01, 0.30, 0.12, 0.001)
    brightness = st.slider("整体曝光 (Brightness)", 0.1, 2.0, 0.8, 0.01)

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
