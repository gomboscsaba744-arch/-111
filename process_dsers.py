import pandas as pd

file_path = "/Users/a171325./Desktop/dsers_export_data.xlsx"
df = pd.read_excel(file_path, dtype=str)

print("处理前数据量:", len(df))

# 1. 客户账号
if '客户账号' in df.columns:
    df['客户账号'] = df['客户账号'].fillna('').astype(str).str.strip()
    df['客户账号'] = df['客户账号'].str.replace(r'\.0$', '', regex=True)
    mask1 = df['客户账号'] != ''
    mask2 = df['客户账号'] != '1000000257'
    mask3 = df['客户账号'] != '1000001876'
    mask4 = df['客户账号'].str.isdigit()
    df = df[mask1 & mask2 & mask3 & mask4]

# 2. 电话1
if '电话1' in df.columns:
    df['电话1'] = df['电话1'].fillna('').astype(str)
    df['电话1'] = df['电话1'].str.replace('+55', '', regex=False)
    df['电话1'] = df['电话1'].str.replace('+', '', regex=False)

# 3. 邮寄地址
if '邮寄地址' in df.columns:
    df['邮寄地址'] = df['邮寄地址'].fillna('').astype(str)
    df['邮寄地址'] = df['邮寄地址'].str.replace('(*)', '', regex=False)

# 4. 国家
if '国家' in df.columns:
    df['国家'] = df['国家'].fillna('').astype(str).str.strip()
    df = df[df['国家'].str.lower() == 'brazil']

print("处理后数据量:", len(df))
df.to_excel(file_path, index=False)
print("处理完成并已保存。")
