import pandas as pd
df = pd.DataFrame({'订单编号': ['="202606080531432384"', '="202606080531432385"']})
df.to_excel('test_formula.xlsx', index=False)
