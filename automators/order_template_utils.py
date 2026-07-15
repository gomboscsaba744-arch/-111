import os
import sys
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SCRIPT_TEMPLATE, ORDER_TEMPLATE
from automators.excel_utils import save_df_to_excel

def clean_order_template_to_script(order_path, script_path, route, sw_dsers_rename=False):
    """
    将下单模板清洗并倒模映射到脚本模板
    """
    if not os.path.exists(order_path):
        return
    try:
        df_order = pd.read_excel(order_path, dtype=str)
    except Exception as e:
        print(f"[!] 读取下单模板失败: {e}")
        return

    df_out = pd.DataFrame()
    
    # 查找订单编号列 (优先按表头名称，其次按索引1)
    col_b_name = next((col for col in df_order.columns if str(col).strip() in ['Shiopify order number', 'Shopify order number', '订单编号', 'order number']), None)
    if col_b_name:
        col_b = df_order[col_b_name].fillna("").astype(str).str.strip()
    elif len(df_order.columns) > 1:
        col_b = df_order.iloc[:, 1].fillna("").astype(str).str.strip()
    else:
        col_b = pd.Series([""] * len(df_order))
    df_out['订单编号'] = col_b

    # 查找客户姓名列 (优先按表头名称，其次按索引4)
    col_e_name = next((col for col in df_order.columns if str(col).strip() in ['客户姓名', '姓名', 'Contact Name', 'Customer Name']), None)
    if col_e_name:
        col_e = df_order[col_e_name].fillna("").astype(str).str.strip()
    elif len(df_order.columns) > 4:
        col_e = df_order.iloc[:, 4].fillna("").astype(str).str.strip()
    else:
        col_e = pd.Series([""] * len(df_order))
    df_out['客户姓名'] = col_e

    # 查找 abnnumber/CPF 列 (优先按表头名称，其次按索引5)
    col_f_name = next((col for col in df_order.columns if str(col).strip() in ['abnnumber', 'abn', 'cpf', 'CPF', '税号']), None)
    if col_f_name:
        cpf_raw = df_order[col_f_name].fillna("").astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    elif len(df_order.columns) > 5:
        cpf_raw = df_order.iloc[:, 5].fillna("").astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    else:
        cpf_raw = pd.Series([""] * len(df_order))
    df_out['abnnumber'] = cpf_raw

    # cpf_abn则是加了前缀“/cpf1 “的f列
    df_out['cpf1_abn'] = '/cpf1 ' + cpf_raw

    # 关键业务逻辑判断：
    # 若是在cpf管线里面 则客户姓名不用清洗到脚本模板的e列（也就是更改查询后的姓名）保持脚本模板里面的更改后姓名列空着
    # 若是在dsers里面 且打开独立分支，点击了运行后 需要把下单模板里的e列清洗到脚本模板里的e列（查询更改后的姓名）
    if route == "B" and sw_dsers_rename:
        df_out['查询结果'] = col_e
    else:
        df_out['查询结果'] = ""

    try:
        save_df_to_excel(df_out, script_path)
        print(f"✅ 已成功将下单模板清洗映射并生成至脚本模板: {script_path}")
    except Exception as e:
        print(f"❌ 写入脚本模板失败: {e}")

def sync_cpf_results_to_order_template(script_path, order_path):
    """
    如果在cpf管线里面，导入的是下单模板后，运行后获取的新姓名要新增返回到下单模板的e列/客户姓名列
    """
    if not os.path.exists(script_path) or not os.path.exists(order_path):
        return
    try:
        df_script = pd.read_excel(script_path, dtype=str)
        df_order = pd.read_excel(order_path, dtype=str)
    except Exception as e:
        print(f"[!] 读取待同步表格失败: {e}")
        return

    if len(df_script.columns) < 5 or len(df_order.columns) < 3:
        print("[!] 待同步表格列数不足，无法回填。")
        return

    # 确定下单模板中的订单号列和客户姓名列索引
    order_col_idx = next((i for i, col in enumerate(df_order.columns) if str(col).strip() in ['Shiopify order number', 'Shopify order number', '订单编号', 'order number']), 1)
    name_col_idx = next((i for i, col in enumerate(df_order.columns) if str(col).strip() in ['客户姓名', '姓名', 'Contact Name', 'Customer Name']), 4 if len(df_order.columns) > 4 else 2)

    # 从脚本模板第五列(索引4)读取查询结果
    valid_names = {}
    for idx, row in df_script.iterrows():
        order_no = str(row.iloc[0]).strip()
        result = str(row.iloc[4]).strip()
        if order_no and result and result not in ["", "nan", "无", "遇到验证码且未能通过", "查询超时", "提取失败"]:
            valid_names[order_no] = result

    update_count = 0
    # 更新下单模板对应的客户姓名列
    for idx, row in df_order.iterrows():
        order_no = str(row.iloc[order_col_idx]).strip()
        if order_no in valid_names:
            df_order.iat[idx, name_col_idx] = valid_names[order_no]
            update_count += 1
        elif idx < len(df_script):
            script_order = str(df_script.iloc[idx, 0]).strip()
            if not order_no or order_no == script_order:
                res = str(df_script.iloc[idx, 4]).strip()
                if res and res not in ["", "nan", "无", "遇到验证码且未能通过", "查询超时", "提取失败"]:
                    df_order.iat[idx, name_col_idx] = res
                    update_count += 1

    try:
        save_df_to_excel(df_order, order_path)
        print(f"✅ 成功回填更新 {update_count} 个最新查询姓名至下单模板客户姓名列: {order_path}")
    except Exception as e:
        print(f"❌ 同步保存下单模板失败: {e}")
