import os
import sys
import pandas as pd

# 导入中心化配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DSERS_IMPORT_XLSX, SCRIPT_TEMPLATE

def map_import_to_cpf():
    input_file = DSERS_IMPORT_XLSX
    output_file = SCRIPT_TEMPLATE
    
    print("[*] 开始将 DSers 格式映射为 CPF 脚本模板...")
    try:
        df_in = pd.read_excel(input_file, dtype=str)
    except Exception as e:
        print(f"❌ 读取 {input_file} 失败: {e}")
        sys.exit(1)
        
    df_out = pd.DataFrame()
    df_out['订单编号'] = df_in.get('Order_number', '')
    df_out['客户姓名'] = df_in.get('Contact_person', '')
    
    # 获取并清理 CPF
    cpf_raw = df_in.get('CPF(Brazil; Optional)', '').fillna('').astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
    df_out['abnnumber'] = cpf_raw
    
    # 核心：第4列(D列)必须是加了前缀的CPF，因为机器人就是读第4列发给TG的
    df_out['cpf1_abn'] = '/cpf1 ' + cpf_raw
    
    # 预留第5列给机器人写结果
    df_out['查询结果'] = ''
    
    try:
        df_out.to_excel(output_file, index=False)
        print(f"✅ 映射完成！列结构完全符合原装 CPF 机器人标准。已生成: {output_file}")
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    map_import_to_cpf()
