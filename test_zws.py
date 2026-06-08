import pandas as pd
df = pd.DataFrame({'订单编号': ['202606080531432384\u200b', '202606080531432385\u200b']})
df.to_excel('test_zws.xlsx', index=False)
