import os

# 全局基础配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SESSIONS_DIR = os.path.join(BASE_DIR, "sessions")

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)

# 默认状态文件夹路径
TELEGRAM_SESSION_DIR = os.path.join(SESSIONS_DIR, "telegram_session")
DSERS_SESSION_DIR = os.path.join(SESSIONS_DIR, "dsers_session")
MABANG_SESSION_DIR = os.path.join(SESSIONS_DIR, "mabang_session")

# 各模式独立的数据表路径
MODE1_EXCEL = os.path.join(DATA_DIR, "mode1_task.xlsx")
MODE2_EXCEL = os.path.join(DATA_DIR, "mode2_task.xlsx")
MODE3_EXCEL = os.path.join(DATA_DIR, "mode3_task.xlsx")
MODE4_EXCEL = os.path.join(DATA_DIR, "mode4_task.xlsx")

# 统一数据保险库路径 (Data Vault)
DSERS_TEMPLATE = os.path.join(DATA_DIR, "dsers模板.xlsx")
DSERS_IMPORT_XLSX = os.path.join(DATA_DIR, "import_orders.xlsx")
DSERS_IMPORT_CSV = os.path.join(DATA_DIR, "import_orders.csv")
SCRIPT_TEMPLATE = os.path.join(DATA_DIR, "脚本模板.xlsx")

