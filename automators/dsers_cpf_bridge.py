import pandas as pd
import argparse
import sys
import os

# 导入中心化配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DSERS_IMPORT_XLSX, DSERS_IMPORT_CSV, SCRIPT_TEMPLATE

def export_to_cpf_template():
    import_path = DSERS_IMPORT_XLSX
    script_template_path = SCRIPT_TEMPLATE
    
    print("[*] 正在读取 DSers 映射文件...")
    try:
        df_dsers = pd.read_excel(import_path, dtype=str)
    except Exception as e:
        print(f"❌ 读取 import_orders.xlsx 失败: {e}")
        sys.exit(1)
        
    print(f"[*] 成功读取 {len(df_dsers)} 条订单数据。")
    
    # 构造 Telegram 机器人需要的 脚本模板.xlsx (D列是CPF, E列是结果)
    # 标准列：A: 交易编号, B: 买家姓名, C: 客户账号, D: CPF, E: 结果
    df_cpf = pd.DataFrame()
    # 强制加上 \t 前缀，防止用户用 Excel 软件手动双击打开时被 Excel 强制转化为科学计数法并吞噬尾数
    df_cpf['订单编号'] = "\t" + df_dsers.get('Order_number', '').fillna('').astype(str).str.strip()
    df_cpf['客户姓名'] = df_dsers.get('Contact_person', '')
    
    cpf_raw = df_dsers.get('CPF(Brazil; Optional)', '').fillna('').astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    df_cpf['abnnumber'] = cpf_raw
    df_cpf['cpf1_abn'] = '/cpf1 ' + cpf_raw
    df_cpf['TG_Result'] = '' # 空列用于接收结果
    
    try:
        df_cpf.to_excel(script_template_path, index=False)
        print(f"✅ 成功将 DSers 订单桥接到 CPF 查名模板: {script_template_path}")
    except Exception as e:
        print(f"❌ 写入 脚本模板.xlsx 失败: {e}")
        sys.exit(1)

def merge_cpf_results():
    import_path = DSERS_IMPORT_XLSX
    import_csv_path = DSERS_IMPORT_CSV
    script_template_path = SCRIPT_TEMPLATE
    
    print("[*] 正在读取查名完成的 脚本模板.xlsx ...")
    try:
        df_cpf = pd.read_excel(script_template_path, dtype=str)
        df_dsers = pd.read_excel(import_path, dtype=str)
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        sys.exit(1)
        
    print(f"[*] 成功读取 DSers 模板 ({len(df_dsers)}条) 和 CPF 结果表 ({len(df_cpf)}条)。")
    
    # 建立映射字典：交易编号 -> 查名结果 (第五列)
    # 检查列名，可能是 TG_Result 或者未命名的第五列
    cols = df_cpf.columns.tolist()
    if len(cols) >= 5:
        result_col = cols[4] # 索引4即第五列(E列)
    else:
        print("❌ 脚本模板.xlsx 格式错误，缺少结果列(E列)！")
        sys.exit(1)
        
    update_count = 0
    # 为了避免订单编号有类型差异，全部转字符串处理
    df_cpf['订单编号'] = df_cpf['订单编号'].fillna('').astype(str).str.strip()
    df_dsers['Order_number'] = df_dsers['Order_number'].fillna('').astype(str).str.strip()
    
    # 构建字典 { order_number: real_name }
    # 过滤掉 "遇到验证码且未能通过" / "查询超时" / "提取失败" / "无" 等无效状态
    valid_names = {}
    for idx, row in df_cpf.iterrows():
        order_no = row['订单编号']
        result = str(row[result_col]).strip()
        if order_no and result and result not in ["", "nan", "无", "遇到验证码且未能通过", "查询超时", "提取失败"]:
            valid_names[order_no] = result

    # 遍历更新 DSers 模板 (import_orders.xlsx)
    for idx, row in df_dsers.iterrows():
        order_no = row['Order_number']
        if order_no in valid_names:
            df_dsers.at[idx, 'Contact_person'] = valid_names[order_no]
            update_count += 1
            
    # 同时更新原始 dsers模板.xlsx
    from config import DSERS_TEMPLATE
    try:
        df_raw = pd.read_excel(DSERS_TEMPLATE, dtype=str)
        if '交易编号' in df_raw.columns and '客户姓名' in df_raw.columns:
            for idx, row in df_raw.iterrows():
                order_no = str(row['交易编号']).strip()
                if order_no in valid_names:
                    df_raw.at[idx, '客户姓名'] = valid_names[order_no]
            df_raw.to_excel(DSERS_TEMPLATE, index=False)
            print(f"[*] 原始 dsers模板.xlsx 的 '客户姓名' 也已同步更新！")
    except Exception as e:
        print(f"[!] 同步更新 dsers模板.xlsx 失败: {e}")
            
    print(f"[*] 匹配完毕！共成功修正并回填了 {update_count} 个真实的客户姓名。")
    
    try:
        df_dsers.to_excel(import_path, index=False)
        df_dsers.to_csv(import_csv_path, index=False, encoding='utf-8-sig')
        print(f"✅ 修正后的 DSers 订单已重新保存并覆盖: {import_csv_path}")
    except Exception as e:
        print(f"❌ 保存覆写文件失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="DSers 和 Telegram CPF 的桥接器")
    parser.add_argument("--mode", choices=["export", "merge"], required=True, help="export: 将DSers提取成脚本模板 | merge: 将查名结果合回DSers模板")
    args = parser.parse_args()
    
    if args.mode == "export":
        export_to_cpf_template()
    elif args.mode == "merge":
        merge_cpf_results()
