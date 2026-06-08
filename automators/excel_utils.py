import pandas as pd

def save_df_to_excel(df, path):
    writer = pd.ExcelWriter(path, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    text_format = workbook.add_format({'num_format': '@'})
    # Set all columns to text format to prevent Excel from converting large numbers to scientific notation
    worksheet.set_column(0, len(df.columns) - 1, None, text_format)
    writer.close()
