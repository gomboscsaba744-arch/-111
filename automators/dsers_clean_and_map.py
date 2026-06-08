import pandas as pd
import numpy as np
import os
import sys
import re

# 导入中心化配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DSERS_TEMPLATE, DSERS_IMPORT_XLSX, DSERS_IMPORT_CSV

file_path = DSERS_TEMPLATE
template_path = DSERS_IMPORT_XLSX

print("[*] 开始执行 DSers 数据五重清洗与模板映射...")
try:
    # ==========================
    # 阶段一：数据清洗
    # ==========================
    df = pd.read_excel(file_path, dtype=str)
    print(f"处理前数据量: {len(df)}")

    # 1. 客户账号
    if '客户账号' in df.columns:
        df['客户账号'] = df['客户账号'].fillna('').astype(str).str.strip()
        df['客户账号'] = df['客户账号'].str.replace(r'\.0$', '', regex=True)
        mask1 = df['客户账号'] != ''
        mask2 = df['客户账号'] != '1000000257'
        mask3 = df['客户账号'] != '1000001876'
        mask4 = df['客户账号'].str.isdigit()
        df = df[mask1 & mask2 & mask3 & mask4]
        print(f"客户账号过滤后剩余: {len(df)}")

    # 2. 电话1
    if '电话1' in df.columns:
        df['电话1'] = df['电话1'].fillna('').astype(str)
        df['电话1'] = df['电话1'].str.replace('+55', '', regex=False)
        df['电话1'] = df['电话1'].str.replace('+', '', regex=False)
        df['电话1'] = df['电话1'].str.replace('(', '', regex=False)
        df['电话1'] = df['电话1'].str.replace(')', '', regex=False)
        df['电话1'] = df['电话1'].str.replace(' ', '', regex=False)
        df['电话1'] = df['电话1'].str.replace('-', '', regex=False)
        print("电话1字符清洗完毕")

    # 3. 邮寄地址
    if '邮寄地址' in df.columns:
        df['邮寄地址'] = df['邮寄地址'].fillna('').astype(str)
        df['邮寄地址'] = df['邮寄地址'].str.replace(r'\(.*?\)', '', regex=True)
        df['邮寄地址'] = df['邮寄地址'].str.replace(r'（.*?）', '', regex=True)
        print("邮寄地址括号内容清洗完毕")

    # 4. 国家
    if '国家' in df.columns:
        df['国家'] = df['国家'].fillna('').astype(str).str.strip()
        df = df[df['国家'].str.lower() == 'brazil']
        print(f"国家Brazil过滤后剩余: {len(df)}")

    # 5. SKU最后处理
    if 'SKU' in df.columns:
        df['SKU'] = df['SKU'].fillna('').astype(str)
        mask5 = ~df['SKU'].str.lower().str.contains('code')
        df = df[mask5]
        print(f"SKU排除code后剩余: {len(df)}")

    # 覆盖保存原文件
    df.to_excel(file_path, index=False)
    print("✅ 第一阶段：数据清洗完成，已覆盖保存原文件。")

    # ==========================
    # 阶段二：格式映射
    # ==========================
    df_clean = df  # 直接使用清洗好的数据框
    
    cols = [
        'Order_number', 'Date', 'Country(Short Name of Country)', 'Product_id', 'Sku', 
        'Product_count', 'Order_memo', 'Contact_person', 'Mobile_no', 'Email(Optional)', 
        'Address', 'Address2', 'Province', 'City', 'ZIP', 'RUT(Chile; Optional)', 
        'Personal Clearance ID(Korea, Oman; Optional)', 
        'Passport/Alien registration Card Number(Korea, Oman; Optional)', 
        'CPF(Brazil; Optional)', 'Turkish ID Number(Turkey; Optional)', 
        'Passport Number(Turkey; Optional)', 'RUC(Peru; Optional)', 'RFC/CURP(Mexico; Optional)'
    ]
    
    # 新建对应 Dsers 的表结构，并只提取所需的列
    df_out = pd.DataFrame(columns=cols)
    if '交易编号' in df_clean.columns:
        # 强制加上 \t 防止后续打开被 Excel 转成科学计数法
        df_out['Order_number'] = df_clean['交易编号'].apply(lambda x: "\t" + str(x).strip() if not str(x).strip().startswith("\t") else str(x).strip())
        
    # --- 强常量覆盖 ---
    df_out['Country(Short Name of Country)'] = 'Brazil'
    df_out['Product_id'] = '1005008288285560'
    df_out['Product_count'] = '1'
    df_out['Sku'] = '\xa0200007763:201336100#CHINA;73:350852#Style M-null'
    
    # --- 动态字段映射 ---
    if '客户姓名' in df_clean.columns:
        df_out['Contact_person'] = df_clean['客户姓名']
    if '电话1' in df_clean.columns:
        df_out['Mobile_no'] = df_clean['电话1']
    if '联系邮箱' in df_clean.columns:
        df_out['Email(Optional)'] = df_clean['联系邮箱']
    if '邮寄地址' in df_clean.columns:
        df_out['Address'] = df_clean['邮寄地址']
    if '备用地址' in df_clean.columns:
        df_out['Address2'] = df_clean['备用地址']
    if '所属地区（省/州）' in df_clean.columns:
        df_out['Province'] = df_clean['所属地区（省/州）']
    if '所属城市' in df_clean.columns:
        df_out['City'] = df_clean['所属城市']
    if '邮政编码' in df_clean.columns:
        df_out['ZIP'] = df_clean['邮政编码']
    if 'abnnumber' in df_clean.columns:
        df_out['CPF(Brazil; Optional)'] = df_clean['abnnumber'].astype(str).str.replace('.', '', regex=False).str.replace('-', '', regex=False).replace('nan', '')
        
    # 保存映射文件 (Excel 中保留 \t 防截断)
    df_out.to_excel(template_path, index=False)
    
    # 保存 CSV 文件 (供上传 DSers 使用，必须移除 \t 防止解析失败)
    df_csv = df_out.copy()
    if 'Order_number' in df_csv.columns:
        df_csv['Order_number'] = df_csv['Order_number'].astype(str).str.strip()
    csv_path = template_path.replace('.xlsx', '.csv')
    df_csv.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    print(f"✅ 第二阶段：成功将 {len(df_out)} 条数据完美映射到 DSers 导入模板！")
    print(f"📂 生成文件: {template_path}")
    print(f"📂 生成文件: {csv_path}")

except Exception as e:
    print(f"❌ 脚本执行错误: {e}")
